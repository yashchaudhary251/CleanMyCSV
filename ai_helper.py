# ai_helper.py
import os
import re
import pandas as pd
import numpy as np
import json
import textwrap

# LLM (optional): enable if OPENAI_API_KEY is set in Streamlit secrets
try:
    import streamlit as st
    OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY", "")
except Exception:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

OPENAI_READY = bool(OPENAI_API_KEY)

# If openai package is available, use it; otherwise fallback to heuristics only
try:
    from openai import OpenAI
    _client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_READY else None
except Exception:
    _client = None

# ---------------- Data Quality Report ----------------
def data_quality_report(df_original: pd.DataFrame, df_clean: pd.DataFrame) -> str:
    def profile(df):
        rows, cols = df.shape
        nulls = int(df.isna().sum().sum())
        dups = int(df.duplicated().sum())
        types = df.dtypes.astype(str).to_dict()
        sample = {c: df[c].dropna().astype(str).head(3).tolist() for c in df.columns}
        return rows, cols, nulls, dups, types, sample

    orows, ocols, onulls, odups, otypes, osample = profile(df_original)
    crows, ccols, cnulls, cdups, ctypes, csample = profile(df_clean)

    def dict_to_md(d):
        return "<br>".join([f"<code>{k}</code>: {v}" for k, v in d.items()])

    md = f"""
**Original**: {orows} rows × {ocols} cols | Null values: {onulls} | Duplicates: {odups}  
**Cleaned**: {crows} rows × {ccols} cols | Null values: {cnulls} | Duplicates: {cdups}

**Column types (cleaned)**  
{dict_to_md(ctypes)}

**Sample values per column (cleaned)**  
""" + "<br>".join([f"• <code>{c}</code>: " + ", ".join([f"`{s}`" for s in v]) for c, v in csample.items()])
    return md

# ---------------- AI Suggestions ----------------
SUGGESTION_SYSTEM = """You are a data-cleaning expert. Given a summary of a dataset (columns, null counts, possible types, duplicates),
produce short bullet-point suggestions for cleaning. Keep it practical and focused on Pandas-friendly operations. Return Markdown bullets.
"""

def ai_suggest_cleaning(df_original: pd.DataFrame, df_clean: pd.DataFrame) -> str:
    # Heuristic summary
    issues = []
    if df_original.duplicated().any():
        issues.append("There are duplicate rows in the original dataset.")
    if df_original.isna().any().any():
        issues.append("There are missing values in one or more columns.")
    for c in df_original.columns:
        if df_original[c].dtype == object:
            # check leading/trailing spaces or commas-in-numbers hint
            s = df_original[c].dropna().astype(str)
            if s.str.startswith(" ").any() or s.str.endswith(" ").any():
                issues.append(f"Column '{c}' may contain leading/trailing spaces.")
            if s.str.contains(",").mean() > 0.2:
                issues.append(f"Column '{c}' may contain numeric values with commas.")
    if not issues:
        issues.append("No major issues found. Consider standardizing column names and ensuring correct dtypes.")

    heuristic_md = "### Heuristic suggestions\n" + "\n".join([f"- {x}" for x in issues])

    if not OPENAI_READY or _client is None:
        return heuristic_md

    # Build compact schema for the LLM
    schema = {
        "original_columns": df_original.columns.tolist(),
        "cleaned_columns": df_clean.columns.tolist(),
        "null_counts": df_original.isna().sum().to_dict(),
        "dtypes_guess": df_original.dtypes.astype(str).to_dict(),
        "duplicates_in_original": int(df_original.duplicated().sum()),
    }
    prompt = f"Dataset summary:\n{json.dumps(schema) }\n\nProvide concise bullet suggestions."

    try:
        resp = _client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SUGGESTION_SYSTEM},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )
        ai_md = resp.choices[0].message.content.strip()
        return heuristic_md + "\n\n### LLM suggestions\n" + ai_md
    except Exception as e:
        return heuristic_md + f"\n\n> LLM unavailable: {e}"

# ---------------- Natural-Language Cleaning (Safe Parser) ----------------
# Supported actions (intentionally limited/safe):
# - rename A -> a (comma/semicolon separated list allowed)
# - drop columns: X, Y
# - drop rows where COL is null / equals VALUE
# - fill nulls in COL with VALUE
# - convert COL to numeric
# - parse COL as date (optionally with format)
REN_RE = re.compile(r"rename\s+(.+)", re.I)
DROP_COLS_RE = re.compile(r"drop\s+columns?\s*:\s*(.+)", re.I)
DROP_NULL_RE = re.compile(r"drop\s+rows\s+where\s+(.+?)\s+is\s+null", re.I)
DROP_EQ_RE = re.compile(r"drop\s+rows\s+where\s+(.+?)\s*=\s*(.+)", re.I)
FILL_RE = re.compile(r"fill\s+nulls\s+in\s+(.+?)\s+with\s+(.+)", re.I)
NUMERIC_RE = re.compile(r"convert\s+(.+?)\s+to\s+numeric", re.I)
DATE_RE = re.compile(r"parse\s+(.+?)\s+as\s+date(?:\s+format\s+(.+))?", re.I)

def _split_items(s):
    return [x.strip() for x in re.split(r"[;,]", s) if x.strip()]

def ai_apply_instructions_safe(df: pd.DataFrame, instructions: str):
    """
    Applies a small, safe subset of transformations parsed from natural language.
    Returns (df_out, change_log).
    """
    out = df.copy()
    log = []
    text = (instructions or "").strip()
    if not text:
        return out, log

    # RENAME: "rename A->a; B->b" or "rename Full Name -> full_name"
    m = REN_RE.search(text)
    if m:
        pairs = _split_items(m.group(1))
        mapping = {}
        for p in pairs:
            if "->" in p:
                left, right = [x.strip() for x in p.split("->", 1)]
                mapping[left] = right
        # Try also support "rename Full Name -> full_name" even if alone
        if not mapping and "->" in m.group(1):
            left, right = [x.strip() for x in m.group(1).split("->", 1)]
            mapping[left] = right
        if mapping:
            out = out.rename(columns=mapping)
            log.append(f"Renamed columns: {mapping}")

    # DROP COLUMNS: "drop columns: X, Y"
    m = DROP_COLS_RE.search(text)
    if m:
        cols = [c for c in _split_items(m.group(1)) if c in out.columns]
        if cols:
            out = out.drop(columns=cols, errors="ignore")
            log.append(f"Dropped columns: {cols}")

    # DROP ROWS WHERE COL IS NULL
    m = DROP_NULL_RE.search(text)
    if m:
        col = m.group(1).strip()
        if col in out.columns:
            before = len(out)
            out = out[~out[col].isna()].copy()
            log.append(f"Dropped {before - len(out)} rows where {col} is null")

    # DROP ROWS WHERE COL = VALUE
    m = DROP_EQ_RE.search(text)
    if m:
        col = m.group(1).strip()
        val = m.group(2).strip().strip("'\"")
        if col in out.columns:
            before = len(out)
            out = out[out[col] != val].copy()
            log.append(f"Dropped {before - len(out)} rows where {col} == {val}")

    # FILL NULLS
    m = FILL_RE.search(text)
    if m:
        col = m.group(1).strip()
        val = m.group(2).strip().strip("'\"")
        if col in out.columns:
            # try numeric or leave as text
            try:
                val_cast = float(val) if "." in val or val.isdigit() else val
            except Exception:
                val_cast = val
            out[col] = out[col].fillna(val_cast)
            log.append(f"Filled nulls in {col} with {val_cast}")

    # CONVERT TO NUMERIC
    m = NUMERIC_RE.search(text)
    if m:
        col = m.group(1).strip()
        if col in out.columns:
            out[col] = (
                out[col].astype(str).str.replace(",", "", regex=False).str.strip()
            )
            out[col] = pd.to_numeric(out[col], errors="coerce")
            log.append(f"Converted {col} to numeric")

    # PARSE DATE (optional format)
    m = DATE_RE.search(text)
    if m:
        col = m.group(1).strip()
        fmt = (m.group(2) or "").strip()
        if col in out.columns:
            if fmt:
                out[col] = pd.to_datetime(out[col], errors="coerce", format=fmt)
                log.append(f"Parsed {col} as date with format {fmt}")
            else:
                out[col] = pd.to_datetime(out[col], errors="coerce")
                log.append(f"Parsed {col} as date (auto-detect)")

    out = out.reset_index(drop=True)
    return out, log

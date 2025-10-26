
import re
import pandas as pd
import numpy as np

def detect_delimiter(sample: str, default=","):
    candidates = [",",";","|","\t"]
    counts = {d: sample.count(d) for d in candidates}
    best = max(counts, key=counts.get)
    return default if counts[best] == 0 else best

def standardize_column_name(name: str) -> str:
    name = name.strip()
    name = re.sub(r"[^\w\s]", " ", name)
    name = re.sub(r"\s+", "_", name)
    return name.lower()

def coerce_numeric_series(s: pd.Series) -> pd.Series:
    if s.dtype.kind in "biufc":
        return s
    s2 = s.astype(str).str.replace(",", "", regex=False).str.strip()
    return pd.to_numeric(s2, errors="ignore")

def try_parse_dates(df: pd.DataFrame) -> pd.DataFrame:
    for col in df.columns:
        if df[col].dtype == object:
            sample = df[col].dropna().astype(str).head(20)
            ok = 0
            for v in sample:
                try:
                    pd.to_datetime(v, errors="raise")
                    ok += 1
                except Exception:
                    pass
            if ok >= 3:
                df[col] = pd.to_datetime(df[col], errors="coerce")
    return df

def clean_dataframe(
    df: pd.DataFrame,
    trim_spaces: bool = True,
    standardize_columns: bool = True,
    drop_empty_rows: bool = True,
    drop_empty_cols: bool = True,
    drop_duplicates: bool = True,
    fix_numbers: bool = True,
    parse_dates: bool = False,
) -> pd.DataFrame:
    out = df.copy()

    if trim_spaces:
        out = out.applymap(lambda x: x.strip() if isinstance(x, str) else x)

    if standardize_columns:
        out.columns = [standardize_column_name(c) for c in out.columns]

    if drop_empty_rows:
        out = out.dropna(how="all")

    if drop_empty_cols:
        out = out.dropna(axis=1, how="all")

    if drop_duplicates:
        out = out.drop_duplicates()

    if fix_numbers:
        for col in out.columns:
            out[col] = coerce_numeric_series(out[col])

    if parse_dates:
        out = try_parse_dates(out)

    return out.reset_index(drop=True)

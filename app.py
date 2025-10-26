# app.py
import io
import pandas as pd
import streamlit as st
from cleaner import clean_dataframe, detect_delimiter

# ---------- Page config ----------
st.set_page_config(
    page_title="CleanMyCSV — Instant Excel/CSV Cleaner",
    page_icon="🧹",
    layout="wide",
)

# ---------- Header ----------
st.title("🧹 CleanMyCSV — Instant Excel/CSV Cleaner")
st.caption("Upload messy data → Get back a clean file. Built with Streamlit + Pandas.")
st.info(
    "⚠️ Your file is processed in memory only and is **not stored** on the server. "
    "Close the page to clear the session."
)

# ---------- Sidebar: cleaning options ----------
with st.sidebar:
    st.header("⚙️ Cleaning Options")
    opt_trim = st.checkbox("Trim spaces in cells", value=True)
    opt_standardize_cols = st.checkbox("Standardize column names (snake_case)", value=True)
    opt_drop_empty_rows = st.checkbox("Remove fully empty rows", value=True)
    opt_drop_empty_cols = st.checkbox("Remove fully empty columns", value=True)
    opt_drop_duplicates = st.checkbox("Remove duplicate rows", value=True)
    opt_fix_numbers = st.checkbox("Fix numeric columns (remove commas, coerce)", value=True)
    opt_parse_dates = st.checkbox("Try to parse dates", value=False)
    st.markdown("---")
    st.caption("Tip: You can toggle options and re-run without re-uploading.")

# ---------- Sample CSV helper (optional) ----------
with st.expander("Need a sample file? Click here to download a demo CSV"):
    sample_df = pd.DataFrame(
        {
            "Name": ["Alice", "Bob", "  Charlie  ", "Alice"],
            "Email": ["alice@example.com", "bob@example.com", "charlie@example.com", "alice@example.com"],
            "Amount": ["1,200", "450", " 300 ", "1,200"],
            "Date": ["2024-01-05", "05/01/2024", "Jan 5, 2024", "2024/01/05"],
            "Notes": ["hello  ", None, "", "  duplicate "],
        }
    )
    st.download_button(
        "Download sample.csv",
        data=sample_df.to_csv(index=False).encode("utf-8"),
        file_name="sample.csv",
        mime="text/csv",
        help="A small demo file you can try with the app",
    )

# ---------- Uploader ----------
uploaded = st.file_uploader("Upload a CSV or Excel file", type=["csv", "xlsx", "xls"])

# File-size guard (avoid huge uploads on free hosting)
MAX_MB = 50
if uploaded and uploaded.size > MAX_MB * 1024 * 1024:
    st.error(f"File is too large ({uploaded.size/1024/1024:.1f} MB). Max {MAX_MB} MB.")
    st.stop()

# ---------- Main logic ----------
if uploaded:
    # 1) Read file
    try:
        if uploaded.name.lower().endswith(".csv"):
            content = uploaded.getvalue().decode("utf-8", errors="ignore")
            delim = detect_delimiter(content)
            df_original = pd.read_csv(io.StringIO(content), delimiter=delim)
        else:
            df_original = pd.read_excel(uploaded)
    except Exception as e:
        st.error(f"Failed to read file: {e}")
        st.stop()

    # 2) Show original (unchanged)
    st.subheader("👀 Preview (Original)")
    st.dataframe(df_original.head(50), use_container_width=True)
    st.caption("👀 Original uploaded dataset — column format unchanged.")

    # 3) Cleaned dataframe (analysis-friendly)
    df_cleaned = clean_dataframe(
        df_original,
        trim_spaces=opt_trim,
        standardize_columns=opt_standardize_cols,  # snake_case if True
        drop_empty_rows=opt_drop_empty_rows,
        drop_empty_cols=opt_drop_empty_cols,
        drop_duplicates=opt_drop_duplicates,
        fix_numbers=opt_fix_numbers,
        parse_dates=opt_parse_dates,
    )

    st.subheader("✅ Preview (Cleaned)")
    st.dataframe(df_cleaned.head(50), use_container_width=True)
    st.caption("✅ Cleaned dataset — columns standardized to **snake_case** (data-analysis friendly).")

    # 4) Cleaning summary
    st.subheader("📊 Cleaning Summary")
    changes = []
    if opt_trim:
        changes.append("Trimmed spaces")
    if opt_standardize_cols:
        changes.append("Standardized column names (snake_case)")
    if opt_drop_empty_rows:
        changes.append("Removed fully empty rows")
    if opt_drop_empty_cols:
        changes.append("Removed fully empty columns")
    if opt_drop_duplicates:
        changes.append("Removed duplicate rows")
    if opt_fix_numbers:
        changes.append("Fixed numeric columns (removed commas, coerced types)")
    if opt_parse_dates:
        changes.append("Parsed dates where possible")
    if not changes:
        changes = ["No cleaning options selected"]

    st.markdown("• " + "<br>• ".join(changes), unsafe_allow_html=True)

    # 5) Downloads
    st.subheader("⬇️ Download Cleaned File")
    col1, col2 = st.columns(2)
    with col1:
        csv_bytes = df_cleaned.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Download as CSV",
            data=csv_bytes,
            file_name="cleaned.csv",
            mime="text/csv",
        )
    with col2:
        xls_buffer = io.BytesIO()
        with pd.ExcelWriter(xls_buffer, engine="openpyxl") as writer:
            df_cleaned.to_excel(writer, index=False, sheet_name="Cleaned Data")
        st.download_button(
            label="Download as Excel (.xlsx)",
            data=xls_buffer.getvalue(),
            file_name="cleaned.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
else:
    st.info("Upload a CSV/XLSX file to start cleaning. Need a sample? Open the expander above and download `sample.csv`.")

# ---------- Footer ----------
st.markdown(
    "<hr style='opacity:0.2'>"
    "<div style='text-align:center; opacity:0.75'>"
    "Built by <b>Yash Chaudhary</b> • "
    "<a href='https://github.com/yashchaudhary251/CleanMyCSV' target='_blank'>GitHub</a>"
    "</div>",
    unsafe_allow_html=True,
)


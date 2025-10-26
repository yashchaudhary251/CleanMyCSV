
import io
import pandas as pd
import streamlit as st
from cleaner import clean_dataframe, detect_delimiter

st.set_page_config(page_title="CleanMyCSV — Instant Excel Cleaner", page_icon="🧹", layout="wide")

st.title("🧹 CleanMyCSV — Instant Excel/CSV Cleaner")
st.caption("Upload messy data → Get back a clean file. Built with Streamlit + Pandas.")

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

uploaded = st.file_uploader("Upload a CSV or Excel file", type=["csv","xlsx","xls"])

if uploaded:
    try:
        if uploaded.name.lower().endswith(".csv"):
            content = uploaded.getvalue().decode("utf-8", errors="ignore")
            delim = detect_delimiter(content)
            df = pd.read_csv(io.StringIO(content), delimiter=delim)
        else:
            df = pd.read_excel(uploaded)
    except Exception as e:
        st.error(f"Failed to read file: {e}")
        st.stop()

    st.subheader("👀 Preview (Original)")
    st.dataframe(df.head(50), use_container_width=True)

    cleaned = clean_dataframe(
        df,
        trim_spaces=opt_trim,
        standardize_columns=opt_standardize_cols,
        drop_empty_rows=opt_drop_empty_rows,
        drop_empty_cols=opt_drop_empty_cols,
        drop_duplicates=opt_drop_duplicates,
        fix_numbers=opt_fix_numbers,
        parse_dates=opt_parse_dates,
    )

    st.subheader("✅ Preview (Cleaned)")
    st.dataframe(cleaned.head(50), use_container_width=True)

    st.subheader("📊 Cleaning Summary")
    changes = []
    if opt_trim: changes.append("Trimmed spaces")
    if opt_standardize_cols: changes.append("Standardized column names")
    if opt_drop_empty_rows: changes.append("Removed empty rows")
    if opt_drop_empty_cols: changes.append("Removed empty columns")
    if opt_drop_duplicates: changes.append("Removed duplicate rows")
    if opt_fix_numbers: changes.append("Fixed numeric columns")
    if opt_parse_dates: changes.append("Parsed dates where possible")
    if not changes:
        changes = ["No cleaning options selected"]
    st.write("• " + "\n• ".join(changes))

    st.subheader("⬇️ Download Cleaned File")
    col1, col2 = st.columns(2)
    with col1:
        csv_bytes = cleaned.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Download as CSV",
            data=csv_bytes,
            file_name="cleaned.csv",
            mime="text/csv",
        )
    with col2:
        xls_buffer = io.BytesIO()
        with pd.ExcelWriter(xls_buffer, engine="openpyxl") as writer:
            cleaned.to_excel(writer, index=False, sheet_name="Cleaned Data")
        st.download_button(
            label="Download as Excel (.xlsx)",
            data=xls_buffer.getvalue(),
            file_name="cleaned.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

else:
    st.info("Upload a CSV/XLSX file to start cleaning. Need a sample? Try exporting any table to CSV.")

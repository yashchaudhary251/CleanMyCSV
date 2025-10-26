
# CleanMyCSV — Instant Excel/CSV Cleaner 🧹

Upload messy data → download a clean file.  
Built with **Streamlit + Pandas**.

## Features
- Trim spaces
- Standardize column names (snake_case)
- Drop empty rows/columns
- Remove duplicates
- Coerce numeric columns
- Optional: parse dates
- Download as CSV or Excel

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```
Then open the URL Streamlit prints (usually http://localhost:8501).

## Deploy (Streamlit Community Cloud)
1. Push this folder to a GitHub repo
2. Go to https://share.streamlit.io/
3. Connect your repo, pick `app.py` as entrypoint
4. Deploy!

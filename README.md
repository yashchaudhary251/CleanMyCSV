# 🧹 CleanMyCSV — Instant Excel/CSV Cleaner

Upload messy data → download a clean dataset in seconds.  
Perfect for Data Analysts, Engineers & Business Teams.

🔗 **Live App:**  
https://cleanmycsv-6swrktzuhcqfzbild95nyk.streamlit.app/

---

## 🚀 Features

✅ Supports `.csv`, `.xlsx`, `.xls`  
✅ Auto-detect delimiter  
✅ Standardizes column names → `snake_case` (Python-friendly)  
✅ Removes:
- Duplicate rows
- Fully empty rows & columns
- Extra spaces in text fields  
✅ Fixes numbers → removes commas, coerces to numeric  
✅ Optional auto date parsing  
✅ Download results in CSV or Excel format  
✅ Privacy safe — file processed in memory only ✅  
✅ Fully open-source project ✅  

---

## 🧠 Tech Stack

| Technology | Purpose |
|-----------|---------|
| **Python** | Data processing logic |
| **Pandas** | Cleaning & transformations |
| **Streamlit** | Web interface |
| **OpenPyXL** | Excel export |
| **NumPy** | Numeric handling |

---

## 🖥️ Preview (Screenshots)

> 📌 Add screenshots here once ready (UI & cleaning preview)

| Original Input | Cleaned Output |
|----------------|----------------|
| (screenshot) | (screenshot) |

---

## 📦 Installation (Run Locally)

```bash
git clone https://github.com/yashchaudhary251/CleanMyCSV.git
cd CleanMyCSV
pip install -r requirements.txt
streamlit run app.py

import streamlit as st
import pandas as pd
from pymongo import MongoClient
from dotenv import load_dotenv
# ---------------- MongoDB Setup ----------------

load_dotenv()

DB_NAME = "task_planner_db"
client = MongoClient()
db = client[DB_NAME]

# ---------------- Page Setup ----------------
st.set_page_config("📂 Projects Viewer", layout="wide", page_icon="🗂️")
st.title("📂 Project Work Plan Sheets Viewer")

# ---------------- Collection Selection ----------------
collections = db.list_collection_names()

if not collections:
    st.error("❌ No Project found in the database.")
    st.stop()

selected_collection = st.selectbox("🔽 Select Project", collections)

# ---------------- Load Data ----------------
collection = db[selected_collection]
data = list(collection.find({}))

if not data:
    st.warning("⚠️ This Project is empty.")
    st.stop()

# Drop ObjectId for display
for doc in data:
    doc.pop("_id", None)

df = pd.DataFrame(data)

# ---------------- Show Data ----------------
st.markdown(f"### 📄 Data in `{selected_collection}`")
st.dataframe(df, use_container_width=True)

# ---------------- Download as CSV ----------------
csv_data = df.to_csv(index=False).encode("utf-8")
st.download_button("⬇️ Download CSV", csv_data, f"{selected_collection}.csv", "text/csv")

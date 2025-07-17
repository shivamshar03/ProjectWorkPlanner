# app.py
import streamlit as st
import PyPDF2
import pandas as pd

from datetime import date, timedelta
import json
import joblib
from backend.llm_utils import generate_tasks_with_llm
from backend.classification_embeddings import get_embeddings

# ----------------- PDF Reader -----------------
def extract_text_from_pdfs(files):
    text = ""
    for file in files:
        reader = PyPDF2.PdfReader(file)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text
    return text

# ----------------- Remove Weekends -----------------
def get_working_days(start, end):
    working = []
    current = start
    while current <= end:
        if current.weekday() < 5:
            working.append(current)
        current += timedelta(days=1)
    return working

# ----------------- Load SVM model -----------------
@st.cache_resource
def load_model():
    return joblib.load("modelsvm.pk1")

model = load_model()

# ----------------- Predict Module for Tasks -----------------
def classify_module(task_name):
    try:
        embeddings = get_embeddings()
        query_result = embeddings.embed_query(task_name)
        return model.predict([query_result])[0]
    except Exception as e:
        print(f"Classification Error: {e}")
        return "Uncategorized"

# ----------------- Streamlit UI -----------------
st.set_page_config("Project Work Planner", layout="wide", page_icon="assets/project-logo.png")
st.title("📅 AI Project Analysis")

# --- File Upload & Description ---
col1, col2, col3 = st.columns([5, 0.5, 2])
with col1:
    st.session_state.description = st.text_area("📝 Project Description / Specifications", height=150, key="desc_input")
    st.session_state.files_uploaded = st.file_uploader("📄 Upload Project Files (PDF)", type="pdf", accept_multiple_files=True, key="pdf_input")
with col3:
    st.image("assets/AI-project.png", width=350, use_container_width=False)

# --- Date Inputs ---
with st.form("setup_form"):
    col1, col2 = st.columns([1, 1])
    start_date = col1.date_input("📅 Project Start Date", value=date.today())
    end_date = col2.date_input("🏁 Estimated End Date")
    submitted = st.form_submit_button("✅ Confirm Date Range")

# --- Save Dates ---
if submitted:
    if start_date >= end_date:
        st.error("⚠️ End date must be after start date")
        st.stop()
    st.session_state.start_date = start_date
    st.session_state.end_date = end_date

# --- Holiday Selection & Task Gen ---
if "start_date" in st.session_state and "end_date" in st.session_state:
    with st.form("task_generation_form"):
        all_working_days = get_working_days(st.session_state.start_date, st.session_state.end_date)

        selected_holidays = st.multiselect(
            "🎉 Select Custom Holidays (Optional)",
            options=all_working_days,
            format_func=lambda x: x.strftime("%A %d-%b-%Y"),
            key="selected_holidays"
        )

        net_working_days = [d for d in all_working_days if d not in selected_holidays]
        st.session_state.net_working_days = net_working_days

        st.info(f"🧮 Total Net Working Days: `{len(net_working_days)}`")

        confirm = st.form_submit_button("🧠 Generate Tasks via LLaMA3")

        if confirm:
            if not st.session_state.files_uploaded or not st.session_state.description:
                st.warning("📌 Upload at least one PDF and enter a description.")
                st.stop()

            pdf_text = extract_text_from_pdfs(st.session_state.files_uploaded)
            working_day_strs = [d.strftime("%Y-%m-%d") for d in net_working_days]

            context = f"""
Project Description:
{st.session_state.description}

Extracted Document Content:
{pdf_text}

Start Date: {st.session_state.start_date}
End Date: {st.session_state.end_date}
Net Working Days (excluding weekends + custom holidays):
{working_day_strs}
"""

            with st.spinner("🔍 Generating tasks via LLM..."):
                try:
                    llm_response = generate_tasks_with_llm(context)
                    task_list = json.loads(llm_response)
                    df = pd.DataFrame(task_list)

                except json.JSONDecodeError as e:
                    st.error(f"❌ Failed to parse LLM output as JSON. Error: {e}")
                    st.code(llm_response)

            with st.spinner("🧠 Classifying tasks into modules..."):
                df["Module"] = df["Task"].apply(classify_module)
                if "Task" in df.columns and "Module" in df.columns:
                    cols = df.columns.tolist()
                    task_idx = cols.index("Task")
                    cols.insert(task_idx, cols.pop(cols.index("Module")))
                    df = df[cols]
                st.session_state.tasks_df = df
                st.success("✅ Tasks Generated Successfully")


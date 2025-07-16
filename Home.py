import streamlit as st
import PyPDF2
import pandas as pd
import plotly.express as px
from datetime import date, timedelta
from io import StringIO
import json
from backend.llm_utils import generate_tasks_with_llm

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
    col1, col2, col3 = st.columns([5, 5, 5])
    with col1:
        start_date = st.date_input("📅 Project Start Date", value=date.today())
    with col2:
        end_date = st.date_input("🏁 Estimated End Date")
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
                llm_response = generate_tasks_with_llm(context)

            try:
                task_list = json.loads(llm_response)
                df = pd.DataFrame(task_list)
                st.session_state.tasks_df = df
                st.success("✅ Tasks Generated Successfully")
            except json.JSONDecodeError as e:
                st.error(f"❌ Failed to parse LLM output as JSON. Error: {e}")
                st.code(llm_response)

# --- Display Task Table & Gantt Chart ---
if "tasks_df" in st.session_state:
    st.markdown("### ✍️ Editable Task Table")
    edited_df = st.data_editor(st.session_state.tasks_df, num_rows="dynamic", use_container_width=True)

    csv_data = edited_df.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download CSV", csv_data, "task_schedule.csv", "text/csv")

    if "Start" in edited_df.columns and "End" in edited_df.columns:
        st.markdown("### 📊 Gantt Chart Visualization")
        fig = px.timeline(
            edited_df,
            x_start="Start",
            x_end="End",
            y="Task",
            color="Sprint",
            title="🗓️ Project Timeline (If Start/End Dates Available)"
        )
        fig.update_yaxes(autorange="reversed")
        fig.update_layout(height=min(800, 40 * len(edited_df)))
        st.plotly_chart(fig, use_container_width=True)

# --- Reset Button ---
st.divider()
if st.button("🔁 Reset All"):
    for key in st.session_state.keys():
        del st.session_state[key]
    st.experimental_rerun()

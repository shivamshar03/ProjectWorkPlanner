import streamlit as st
import PyPDF2
import pandas as pd
from datetime import date, timedelta
import json
import joblib
import logging
from backend.llm_utils import generate_tasks_with_llm
from backend.classification_embeddings import get_embeddings

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def extract_text_from_pdfs(files):
    text = ""
    for file in files:
        try:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        except Exception as e:
            logger.error(f"Error reading PDF file {file.name}: {str(e)}")
            st.warning(f"⚠️ Error reading PDF file {file.name}: {str(e)}")
    if not text.strip() and files:
        st.warning("⚠️ No text extracted from uploaded PDFs. Please check the files.")
    return text

def get_working_days(start, end):
    working = []
    current = start
    while current <= end:
        if current.weekday() < 5:  # Monday to Friday
            working.append(current)
        current += timedelta(days=1)
    return working

@st.cache_resource
def load_model(model_path):
    try:
        return joblib.load(model_path)
    except Exception as e:
        logger.error(f"Error loading model {model_path}: {str(e)}")
        st.error(f"❌ Error loading model: {str(e)}. Please ensure the model file exists.")
        return None

def classify_module(task_name, model):
    try:
        embeddings = get_embeddings()
        query_result = embeddings.embed_query(task_name)
        return model.predict([query_result])[0]
    except Exception as e:
        logger.error(f"Classification Error for task '{task_name}': {str(e)}")
        st.error(f"Classification Error for task '{task_name}': {str(e)}")
        return "Uncategorized"

# Streamlit UI
st.set_page_config(page_title="Project Work Planner", layout="wide", page_icon="assets/project-logo.png")
st.title("📅 AI Project Analysis")

# File Upload & Description
col1, col2, col3 = st.columns([5, 0.2, 2])
with col1:
    st.session_state.project_name = st.text_input("Project Name")
    col1_1, col1_2 = st.columns([5, 2])
    st.session_state.description = col1_1.text_area(
        "📝 Project Description / Specifications",
        height=160,
        key="desc_input",
        placeholder="Enter a brief overview of your project (or type 'na' / 'none' if not available)"
    )
    st.session_state.files_uploaded = col1_2.file_uploader(
        "Upload Project Files (PDF)", type="pdf", accept_multiple_files=True, key="uploadedFile"
    )

with col3:
    try:
        st.image("assets/AI-project.png", width=290, use_container_width=False)
    except Exception as e:
        logger.warning(f"Error loading image: {str(e)}")
        st.warning("⚠️ Could not load logo image")

col4, col5 = st.columns([1, 1])
project_domain = col4.selectbox("Project Domain", ["Game Development", "Web Development", "App Development"])
st.session_state.sprint = col5.selectbox("Sprint Timeline", ["Weekly", "Biweekly", "Monthly"])

# Date Inputs
with st.form("setup_form"):
    col6, col7 = st.columns([1, 1])
    start_date = col6.date_input("📅 Project Start Date", value=date.today())
    end_date = col7.date_input("🏁 Estimated End Date")
    submitted = st.form_submit_button("✅ Confirm Date Range")

# Save Dates and Load Model
if submitted:
    if start_date >= end_date:
        st.error("⚠️ End date must be after start date.")
        st.stop()
    if start_date < date.today():
        st.warning("⚠️ Start date is in the past. Please confirm this is intentional.")
    if (end_date - start_date).days > 365:
        st.warning("⚠️ Date range exceeds 1 year. Please confirm this is intentional.")
    st.session_state.start_date = start_date
    st.session_state.end_date = end_date

    # Load appropriate model based on domain
    if project_domain == "Game Development":
        model = load_model("models/game_dev.pk1")
    elif project_domain in ["Web Development", "App Development"]:
        model = load_model("models/web_dev.pk1")
    else:
        model = load_model("models/modelsvm.pk1")

    if model is None:
        st.error("❌ Failed to load model. Please check the model files.")
        st.stop()
    st.session_state.model = model  # Store model for potential reuse

# Holiday Selection & Task Generation
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

        confirm = st.form_submit_button("🧠 Generate Tasks")

        if confirm:
            if not st.session_state.files_uploaded and (not st.session_state.description or st.session_state.description.lower() in ["na", "none"]):
                st.warning("📌 Please provide either a project description or upload at least one PDF.")
                st.stop()

            pdf_text = extract_text_from_pdfs(st.session_state.files_uploaded) if st.session_state.files_uploaded else ""
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

            with st.spinner("🔍 Generating tasks..."):
                try:
                    llm_response = generate_tasks_with_llm(context, st.session_state.sprint)
                    task_list = json.loads(llm_response)
                    if not task_list:
                        st.error("❌ LLM returned an empty task list. Please try again.")
                        st.stop()
                    df = pd.DataFrame(task_list)
                except (ValueError, json.JSONDecodeError) as e:
                    logger.error(f"LLM response causing error: {repr(llm_response)}")
                    st.error(f"❌ Failed to parse LLM output: {str(e)}. Using default tasks.")
                    default_tasks = [{"Task": "Default Task", "Module": "Uncategorized"}]
                    df = pd.DataFrame(default_tasks)

            with st.spinner("🧠 Classifying tasks into modules..."):
                if "model" not in st.session_state or st.session_state.model is None:
                    st.error("❌ No model loaded. Task classification skipped.")
                    df["Module"] = "Uncategorized"
                else:
                    df["Module"] = df["Task"].apply(lambda x: classify_module(x, st.session_state.model))
                    if "Task" in df.columns and "Module" in df.columns:
                        cols = df.columns.tolist()
                        task_idx = cols.index("Task")
                        cols.insert(task_idx + 1, cols.pop(cols.index("Module")))
                        df = df[cols]
                st.session_state.tasks_df = df
                st.session_state.is_ai_generated = True
                st.success("✅ Tasks Generated Successfully")
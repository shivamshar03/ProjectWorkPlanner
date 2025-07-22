import streamlit as st
import pandas as pd
import plotly.express as px
from pymongo import MongoClient
from datetime import datetime, date, time

# ---------------- MongoDB Setup ----------------
MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "task_planner_db"
try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    client.server_info()  # Test connection
    db = client[DB_NAME]
except Exception as e:
    st.error(f"❌ Failed to connect to MongoDB: {e}")
    st.stop()

# ---------------- Streamlit Setup ----------------
st.set_page_config("📋 Task Plan", layout="wide", page_icon="📁")
st.title("📋 Project Task Schedule")

# ---------------- Load or Select Collection ----------------
# Initialize is_ai_generated if not present
if "is_ai_generated" not in st.session_state:
    st.session_state.is_ai_generated = False

# Show dropdown unless tasks are AI-generated
if not st.session_state.is_ai_generated:
    st.markdown("### 📁 Select a Task Collection")
    collections = db.list_collection_names()
    if not collections:
        st.error("❌ No Projects found in database.")
        st.stop()

    # Use current project_name as default if available
    default_index = (
        collections.index(st.session_state.project_name)
        if "project_name" in st.session_state and st.session_state.project_name in collections
        else 0
    )
    selected_collection = st.selectbox(
        "🔽 Choose Project",
        collections,
        index=default_index,
        key="collection_select"
    )

    # Update session state if collection changes
    if "project_name" not in st.session_state or st.session_state.project_name != selected_collection:
        st.session_state.project_name = selected_collection
        collection = db[selected_collection]
        data = list(collection.find({}))
        if not data:
            st.warning(f"⚠️ Selected Project '{selected_collection}' is empty.")
            st.stop()
        for doc in data:
            doc.pop("_id", None)
        st.session_state.tasks_df = pd.DataFrame(data)
else:
    # AI-generated tasks: show project name
    if "project_name" not in st.session_state:
        st.error("⚠️ `project_name` not found in session. Please define it on the Home page.")
        st.stop()
    st.markdown(f"### 📋 Working on Project: {st.session_state.project_name}")

# ---------------- Continue With Loaded tasks_df ----------------
df = st.session_state.tasks_df

# Ensure required columns
required_columns = ["Task", "Start", "End", "Sprint"]
if not all(col in df.columns for col in required_columns):
    st.error(f"❌ Missing required columns: {set(required_columns) - set(df.columns)}")
    st.stop()

if "Resource" not in df.columns:
    df["Resource"] = ""
if "Progress" not in df.columns:
    df["Progress"] = "PENDING"
if "Task_Dependency" not in df.columns:
    df["Task_Dependency"] = [[] for _ in range(len(df))]
if "Module" not in df.columns:
    df["Module"] = ""

# Convert dates
df["Start"] = pd.to_datetime(df["Start"]).dt.date
df["End"] = pd.to_datetime(df["End"]).dt.date

# Format dependencies for editing
df["Task_Dependency"] = df["Task_Dependency"].apply(
    lambda x: ", ".join(x) if isinstance(x, list) else x
)

# Add Y index for Gantt chart
df["Y_Index"] = list(range(len(df)))

# ---------------- Editable Table ----------------
st.markdown("### ✍️ Editable Task Table")

edited_df = st.data_editor(
    df,
    num_rows="dynamic",
    use_container_width=True,
    key="editable_table",
    column_config={
        "Progress": st.column_config.SelectboxColumn(
            "Progress",
            options=["PENDING", "IN PROGRESS", "COMPLETED", "BLOCKED"],
            required=True,
        ),
        "Task_Dependency": st.column_config.TextColumn(
            "Task Dependency (comma-separated Task_IDs)"
        ),
    },
)

# Update session_state with edited DataFrame


# ---------------- Save to Collection ----------------
def fix_for_mongo(record):
    record.pop("_id", None)
    for k in ["Start", "End"]:
        if isinstance(record.get(k), date) and not isinstance(record.get(k), datetime):
            record[k] = datetime.combine(record[k], time.min)
    if isinstance(record.get("Task_Dependency"), str):
        record["Task_Dependency"] = [x.strip() for x in record["Task_Dependency"].split(",") if x.strip()]
    return record

col1, col2 = st.columns([1, 1])

with col1:
    if st.button("💾 Save Project"):
        st.session_state.tasks_df = edited_df
        if "project_name" not in st.session_state:
            st.error("⚠️ `project_name` not found in session.")
        elif st.checkbox("Confirm overwrite of existing collection"):
            try:
                project_name = st.session_state.project_name
                collection = db[project_name]
                records = edited_df.to_dict("records")
                cleaned = [fix_for_mongo(r) for r in records]
                collection.delete_many({})  # Clear existing data
                collection.insert_many(cleaned)
                st.success(f"✅ Project `{project_name}` saved!")
            except Exception as e:
                st.error(f"❌ Failed to save to DataBase: {e}")
        else:
            st.warning("⚠️ Please confirm to overwrite the Project.")

with col2:
    csv = edited_df.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download CSV", csv, "project_tasks.csv", "text/csv")

# ---------------- Gantt Chart ----------------
st.markdown("### 📊 Gantt Chart")
selected_sprint = st.multiselect(
    "Select Sprints",
    options=edited_df["Sprint"].unique(),
    default=edited_df["Sprint"].unique()
)
filtered_df = edited_df[edited_df["Sprint"].isin(selected_sprint)]
fig = px.timeline(
    filtered_df,
    x_start="Start",
    x_end="End",
    y="Task",
    color="Sprint",
    title="🗓️ Project Timeline",
    hover_data=["Resource", "Progress", "Task_Dependency", "Module"]
)
fig.update_yaxes(autorange="reversed")
fig.update_layout(height=min(800, 40 * len(filtered_df)))
st.plotly_chart(fig, use_container_width=True)

# ---------------- Reset Session State ----------------
if st.button("🔄 Reset and Select New Project"):
    st.session_state.pop("tasks_df", None)
    st.session_state.pop("project_name", None)
    st.session_state.pop("is_ai_generated", None)
    st.rerun()
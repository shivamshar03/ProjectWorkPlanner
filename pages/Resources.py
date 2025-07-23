import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pymongo import MongoClient
from datetime import datetime, date, time
import logging
from urllib.parse import quote_plus
from dotenv import load_dotenv
import os

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# MongoDB Setup
try:
    username = quote_plus(os.getenv("MONGO_USER"))
    password = quote_plus(os.getenv("MONGO_PASS"))
    cluster = os.getenv("MONGO_CLUSTER")
    DB_NAME = os.getenv("MONGO_DB")
    uri = f"mongodb+srv://{username}:{password}@{cluster}/{DB_NAME}?retryWrites=true&w=majority"
    logger.info(f"Connecting to MongoDB: mongodb+srv://{username}:****@{cluster}/{DB_NAME}")
    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    client.server_info()  # Test connection
    db = client[DB_NAME]
except Exception as e:
    st.error(f"❌ Failed to connect to MongoDB: {e}")
    logger.error(f"MongoDB connection failed: {str(e)}")
    st.stop()

# Streamlit UI
st.set_page_config(page_title="Resource Allocation", layout="wide", page_icon="👥")
st.title("👥 Resource Allocation")

# Initialize session state
if "tasks_df" not in st.session_state or "project_name" not in st.session_state:
    st.error("⚠️ No project or tasks found. Please generate or select a project on the main page.")
    st.stop()

# Load tasks
df = st.session_state.tasks_df.copy()

# Ensure required columns
required_columns = ["Task_ID", "Task", "Resource"]
for col in required_columns:
    if col not in df.columns:
        if col == "Resource":
            df["Resource"] = ""
        else:
            st.error(f"❌ Missing required column: {col}")
            st.stop()

# Resource Profile Management
st.markdown("### 🧑‍💼 Manage Resource Profiles")
resource_collection = db["resources"]
if "resources" not in st.session_state:
    resource_data = list(resource_collection.find({}))
    for doc in resource_data:
        doc.pop("_id", None)
    st.session_state.resources = resource_data if resource_data else [
        {"name": "Team Member 1", "role": "Developer", "skills": ["Python", "JavaScript"], "availability": "Available"},
        {"name": "Team Member 2", "role": "Designer", "skills": ["UI/UX", "Figma"], "availability": "Available"},
        {"name": "Team Member 3", "role": "Manager", "skills": ["Project Management"], "availability": "Available"}
    ]

# Resource Profile Form
with st.form("resource_profile_form"):
    st.markdown("#### Add/Edit Resource Profile")
    col1, col2, col3 = st.columns([1, 1, 1])
    resource_name = col1.text_input("Resource Name", placeholder="e.g., John Doe")
    resource_role = col2.selectbox("Role", ["Developer", "Designer", "Manager", "Tester", "Other"])
    resource_skills = col3.text_input("Skills (comma-separated)", placeholder="e.g., Python, UI/UX")
    resource_availability = st.selectbox("Status", ["Available", "Assigned"])
    submit_resource = st.form_submit_button("➕ Add/Update Resource")
    if submit_resource:
        if not resource_name:
            st.warning("⚠️ Please enter a resource name.")
        elif resource_name in [r["name"] for r in st.session_state.resources if r["name"] != resource_name]:
            st.warning(f"⚠️ Resource name '{resource_name}' already exists. Please choose a unique name.")
        else:
            skills = [s.strip() for s in resource_skills.split(",") if s.strip()] if resource_skills else []
            resource_doc = {
                "name": resource_name,
                "role": resource_role,
                "skills": skills,
                "availability": resource_availability
            }
            resource_collection.update_one(
                {"name": resource_name},
                {"$set": resource_doc},
                upsert=True
            )
            existing = next((r for r in st.session_state.resources if r["name"] == resource_name), None)
            if existing:
                existing.update(resource_doc)
            else:
                st.session_state.resources.append(resource_doc)
            st.success(f"✅ Resource '{resource_name}' added/updated.")

# Editable Resource Profiles Table
st.markdown("### 📋 Editable Resource Profiles")
resource_df = pd.DataFrame(st.session_state.resources)
resource_df["Skills"] = resource_df["skills"].apply(lambda x: ", ".join(x) if isinstance(x, list) else x)
edited_resource_df = st.data_editor(
    resource_df[["name", "role", "Skills", "availability"]],
    num_rows="dynamic",
    use_container_width=True,
    key="resource_profile_table",
    column_config={
        "name": st.column_config.TextColumn("Resource Name", required=True),
        "role": st.column_config.SelectboxColumn(
            "Role",
            options=["Developer", "Designer", "Manager", "Tester", "Other"],
            required=True
        ),
        "Skills": st.column_config.TextColumn(
            "Skills (comma-separated)",
            help="Enter skills as a comma-separated list (e.g., Python, UI/UX)"
        ),
        "availability": st.column_config.SelectboxColumn(
            "Status",
            options=["Available", "Assigned"],
            required=True
        )
    }
)

# Save Edited Resource Profiles
if st.button("💾 Save Resource Profiles"):
    try:
        if len(edited_resource_df["name"].unique()) < len(edited_resource_df):
            st.error("⚠️ Duplicate resource names detected. Please ensure unique names.")
            st.stop()
        updated_resources = []
        old_names = {r["name"] for r in st.session_state.resources}
        new_names = set(edited_resource_df["name"])
        deleted_names = old_names - new_names
        for _, row in edited_resource_df.iterrows():
            skills = [s.strip() for s in row["Skills"].split(",") if s.strip()] if row["Skills"] else []
            resource_doc = {
                "name": row["name"],
                "role": row["role"],
                "skills": skills,
                "availability": row["availability"]
            }
            resource_collection.update_one(
                {"name": row["name"]},
                {"$set": resource_doc},
                upsert=True
            )
            updated_resources.append(resource_doc)
        for name in deleted_names:
            resource_collection.delete_one({"name": name})
            # Remove resource from tasks
            st.session_state.tasks_df.loc[st.session_state.tasks_df["Resource"] == name, "Resource"] = ""
            project_name = st.session_state.project_name
            collection = db[project_name]
            records = st.session_state.tasks_df.to_dict("records")
            cleaned = [fix_for_mongo(r) for r in records]
            collection.delete_many({})
            collection.insert_many(cleaned)
        st.session_state.resources = updated_resources
        st.success("✅ Resource profiles saved!")
    except Exception as e:
        st.error(f"❌ Failed to save resource profiles to MongoDB: {e}")
        logger.error(f"Error saving resource profiles: {str(e)}")

# Tasks Across All Projects
st.markdown("### 📊 Tasks Assigned to Resources (All Projects)")
all_tasks = []
collections = db.list_collection_names()
for collection_name in collections:
    if collection_name != "resources":
        collection = db[collection_name]
        tasks = list(collection.find({}))
        for task in tasks:
            task["Project"] = collection_name
            task.pop("_id", None)
            all_tasks.append(task)
all_tasks_df = pd.DataFrame(all_tasks)
if not all_tasks_df.empty:
    assigned_tasks = all_tasks_df[all_tasks_df["Resource"] != ""]
    if not assigned_tasks.empty:
        st.dataframe(
            assigned_tasks[["Project", "Task_ID", "Task", "Resource", "Start", "End", "Sprint", "Module", "Progress"]],
            use_container_width=True
        )
    else:
        st.info("ℹ️ No tasks with assigned resources across projects.")
else:
    st.info("ℹ️ No tasks found in any project collections.")

# Editable Resource Allocation Table
st.markdown("### ✍️ Assign Resources to Tasks (Current Project)")
edited_df = st.data_editor(
    df[["Task_ID", "Task", "Resource", "Start", "End", "Sprint", "Module"]],
    num_rows="fixed",
    use_container_width=True,
    key="resource_table",
    column_config={
        "Task_ID": st.column_config.TextColumn("Task ID", disabled=True),
        "Task": st.column_config.TextColumn("Task", disabled=True),
        "Resource": st.column_config.SelectboxColumn(
            "Resource",
            options=[""] + [r["name"] for r in st.session_state.resources],
            required=False,
            help="Select a resource for the task"
        ),
        "Start": st.column_config.DateColumn("Start Date", disabled=True),
        "End": st.column_config.DateColumn("End Date", disabled=True),
        "Sprint": st.column_config.TextColumn("Sprint", disabled=True),
        "Module": st.column_config.TextColumn("Module", disabled=True),
    },
)

# Save Task Allocations
def fix_for_mongo(record):
    record.pop("_id", None)
    for k in ["Start", "End"]:
        if isinstance(record.get(k), date) and not isinstance(record.get(k), datetime):
            record[k] = datetime.combine(record[k], time.min)
        elif isinstance(record.get(k), str):
            try:
                record[k] = pd.to_datetime(record[k]).to_pydatetime()
            except ValueError:
                logger.error(f"Invalid date format for {k}: {record.get(k)}")
                record[k] = datetime.combine(date.today(), time.min)
    if isinstance(record.get("Task_Dependency"), str):
        record["Task_Dependency"] = [x.strip() for x in record["Task_Dependency"].split(",") if x.strip()]
    elif not isinstance(record.get("Task_Dependency"), list):
        record["Task_Dependency"] = []
    return record

col1, col2 = st.columns([1, 1])
with col1:
    if st.button("💾 Save Resource Allocations"):
        try:
            project_name = st.session_state.project_name
            collection = db[project_name]
            st.session_state.tasks_df["Resource"] = edited_df["Resource"]
            records = st.session_state.tasks_df.to_dict("records")
            cleaned = [fix_for_mongo(r) for r in records]
            collection.delete_many({})
            collection.insert_many(cleaned)
            st.success(f"✅ Resource allocations saved to project `{project_name}`")
        except Exception as e:
            st.error(f"❌ Failed to save to MongoDB: {e}")
            logger.error(f"Error saving task allocations: {str(e)}")
with col2:
    csv = edited_df.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download Resource Allocations", csv, f"{st.session_state.project_name}_resources.csv", "text/csv")

# Resource Allocation Visualization
st.markdown("### 📊 Resource Allocation Overview")
resource_counts = edited_df["Resource"].value_counts().reset_index()
resource_counts.columns = ["Resource", "Task Count"]
if not resource_counts.empty and resource_counts["Resource"].iloc[0] != "":
    fig = go.Figure(
        go.Bar(
            x=resource_counts["Resource"],
            y=resource_counts["Task Count"],
            text=resource_counts["Task Count"],
            textposition="auto",
            marker=dict(color="#636EFA"),
        )
    )
    fig.update_layout(
        title="Tasks per Resource (Current Project)",
        xaxis=dict(title="Resource"),
        yaxis=dict(title="Number of Tasks", tickmode="linear", tick0=0, dtick=1),
        height=400,
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("ℹ️ No resources assigned to tasks in the current project.")

# Resource Timeline
st.markdown("### 🗓️ Resource Timeline (Current Project)")
filtered_df = edited_df[edited_df["Resource"] != ""]
if not filtered_df.empty:
    fig = go.Figure()
    for resource in filtered_df["Resource"].unique():
        res_df = filtered_df[filtered_df["Resource"] == resource]
        for row in res_df.itertuples():
            fig.add_trace(
                go.Bar(
                    x=[(row.End - row.Start).days],
                    y=[resource],
                    base=[row.Start],
                    text=[row.Task],
                    textposition="inside",
                    orientation="h",
                    width=0.4,
                    showlegend=False,
                    hovertemplate=(
                        f"Task: {row.Task}<br>"
                        f"Start: {row.Start:%Y-%m-%d}<br>"
                        f"End: {row.End:%Y-%m-%d}<br>"
                        f"Resource: {resource}<br>"
                    ),
                )
            )
    fig.update_layout(
        title="Resource Task Timeline",
        xaxis=dict(title="Timeline", type="date", tickformat="%d-%b-%Y", gridcolor="lightgrey"),
        yaxis=dict(
            title="Resources",
            tickvals=list(filtered_df["Resource"].unique()),
            ticktext=list(filtered_df["Resource"].unique()),
            showgrid=False,
        ),
        height=max(400, 40 * len(filtered_df["Resource"].unique())),
        margin=dict(l=150, r=50, t=50, b=50),
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("ℹ️ No tasks with assigned resources in the current project.")
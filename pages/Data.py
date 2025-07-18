import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config("📋Task Plan", layout="wide", page_icon="📁")
st.title("📋 Project Task Schedule")

# --- Check if saved table exists ---
if "tasks_df" not in st.session_state:
    st.warning("⚠️ No saved tasks found. Please edit and save from the previous page.")
    st.stop()

# Ensure columns exist
if "Resource" not in st.session_state.tasks_df.columns:
    st.session_state.tasks_df["Resource"] = ""

if "Progress" not in st.session_state.tasks_df.columns:
    st.session_state.tasks_df["Progress"] = "PENDING"

# Convert to datetime
st.session_state.tasks_df["Start"] = pd.to_datetime(st.session_state.tasks_df["Start"]).dt.date
st.session_state.tasks_df["End"] = pd.to_datetime(st.session_state.tasks_df["End"]).dt.date
st.session_state.tasks_df["Y_Index"] = list(range(len(st.session_state.tasks_df)))

# Editable Data Table
st.markdown("### ✍️ Editable Task Table")
edited_df = st.data_editor(
    st.session_state.tasks_df,
    num_rows="dynamic",
    use_container_width=True,
    key="editable_table",
    column_config={
        "Progress": st.column_config.SelectboxColumn(
            "Progress",
            help="Select the current task status",
            options=["PENDING", "IN PROGRESS", "COMPLETED", "BLOCKED"],
            required=True,
            default="PENDING"
        )
    }
)
col1, col2 = st.columns([1 , 1])

with col1:
    if st.button("💾 Save Changes"):
        st.session_state.tasks_df = edited_df
        st.success("✅ Changes saved to session!")
        print(st.session_state.tasks_df)

with col2:
    # CSV Download
    csv_data = edited_df.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download CSV", csv_data, "project_task_planner.csv", "text/csv")

# Gantt Chart
if "Start" in edited_df.columns and "End" in edited_df.columns:
    st.markdown("### 📊 Gantt Chart Visualization")
    fig = px.timeline(
        edited_df,
        x_start="Start",
        x_end="End",
        y="Task",
        color="Sprint",
        title="🗓️ Project Timeline Gantt Chart"
    )
    fig.update_yaxes(autorange="reversed",showgrid=True)
    fig.update_xaxes( showgrid=True)

    fig.update_layout(height=min(800, 40 * len(edited_df)))
    st.plotly_chart(fig, use_container_width=True)

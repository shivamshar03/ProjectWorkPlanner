import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# --- Check if data is loaded ---
if "tasks_df" not in st.session_state:
    st.warning("⚠️ No saved tasks found. Please edit and save from the previous page.")
    st.stop()

df = st.session_state.tasks_df

# --- Ensure resource info exists ---
if df["Resource"].eq("").all():
    st.warning("⚠️ No Resources Found")
    st.stop()

# --- Streamlit UI ---
st.set_page_config(layout="wide")
st.title("📊 Project Gantt Chart with Task Progress and Dependencies")

# --- Base Gantt chart ---
fig = px.timeline(
    df,
    x_start="Start",
    x_end="End",
    y="Y_Index",
    color="Resource",
    hover_data=["Task", "Task_ID", "Task_Dependency", "Progress"]
)

# --- Y-axis formatting ---
fig.update_yaxes(
    tickfont=dict(size=14, color="#367178"),
    tickvals=df["Y_Index"],
    ticktext=df["Task"],
    autorange="reversed",
    showgrid=True,
    gridcolor="#2b6170"
)

# --- X-axis formatting ---
fig.update_xaxes(showgrid=True, gridcolor="#2b6170", dtick="D1")

# --- Status-to-Progress & Color Maps ---
status_to_progress = {
    "PENDING": 0,
    "IN PROGRESS": 50,
    "COMPLETED": 100,
    "BLOCKED": 0
}


# --- Overlay progress bars ---
for row in df.itertuples():
    try:
        status = str(getattr(row, "Progress", "PENDING")).strip().upper()
        progress_value = status_to_progress.get(status, 0)
        start_date = pd.to_datetime(row.Start)
        end_date = pd.to_datetime(row.End)

        # If 0% progress, make a tiny visible bar
        if progress_value == 0:
            progress_end = start_date + pd.Timedelta(hours=0.1)
        else:
            progress_end = start_date + (end_date - start_date) * (progress_value / 100)

        fig.add_trace(go.Scatter(
            x=[start_date, progress_end],
            y=[row.Y_Index, row.Y_Index],
            mode="lines",
            line=dict(color= "black", width=6),
            showlegend=False,
            hoverinfo="skip"
        ))

    except Exception as e:
        st.error(f"⚠️ Error processing task: {row.Task_ID if hasattr(row, 'Task_ID') else 'Unknown'}")
        st.exception(e)


# --- Dependency Arrows ---
task_pos = {
    str(row.Task_ID): {"x_start": row.Start, "x_end": row.End, "y": row.Y_Index}
    for row in df.itertuples()
}

for row in df.itertuples():
    dependencies = row.Task_Dependency if "Task_Dependency" in df.columns else []
    if isinstance(dependencies, str):
        dependencies = [dep.strip() for dep in dependencies.split(",") if dep.strip()]
    if isinstance(dependencies, list) and dependencies:
        for dep_id in dependencies:
            dep_id = str(dep_id).strip()
            if dep_id in task_pos and str(row.Task_ID) in task_pos:
                dep = task_pos[dep_id]
                cur = task_pos[str(row.Task_ID)]
                fig.add_annotation(
                    x=cur["x_start"],
                    y=cur["y"],
                    ax=dep["x_end"],
                    ay=dep["y"],
                    xref="x",
                    yref="y",
                    axref="x",
                    ayref="y",
                    showarrow=True,
                    arrowhead=3,
                    arrowsize=1,
                    arrowwidth=3,
                    arrowcolor="#9769cf",
                )

# --- Final Layout Fixes ---
fig.update_layout(
    height=min(800, 40 * len(df)),  # Uniform row height
    bargap=0.2,
    title="📌 Gantt Chart with Task Progress and Dependencies",
    yaxis_title="Task",
    plot_bgcolor="#d5eaf0"
)

# --- Show chart ---
st.plotly_chart(fig, use_container_width=True)

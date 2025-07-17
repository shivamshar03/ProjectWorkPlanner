import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


if "tasks_df" not in st.session_state :
    st.warning("⚠️ No saved tasks found. Please edit and save from the previous page.")
    st.stop()

df = st.session_state.tasks_df

if   df["Resource"].eq("").all():
    st.warning("⚠️No Resources Found")
    st.stop()

# Streamlit UI
st.set_page_config(layout="wide")
st.title("📊 Project Gantt Chart with Task Progress and Dependencies")

# Create base Gantt chart
fig = px.timeline(df, x_start="Start", x_end="End", y="Y_Index", color="Resource",
                  hover_data=["Task", "Task_ID", "Task_Dependency", "Progress"])
fig.update_yaxes(tickfont=dict(size=16, color="#367178"), tickvals=df["Y_Index"], ticktext=df["Task"], autorange="reversed", showgrid=True, gridcolor="#2b6170")
fig.update_xaxes(showgrid=True, gridcolor="#2b6170" , dtick = "D1")

# Add task progress overlay
for row in df.itertuples():
    progress_end = row.Start + (row.End - row.Start) * (row.Progress / 100)
    fig.add_trace(go.Scatter(
        x=[row.Start, progress_end],
        y=[row.Y_Index, row.Y_Index],
        mode="lines",
        line=dict(color="black", width=6),
        showlegend=False,
        hoverinfo="skip"
    ))

# Add dependency arrows
task_pos = {
    str(row.Task_ID): {"x_start": row.Start, "x_end": row.End, "y": row.Y_Index}
    for row in df.itertuples()
}

for row in df.itertuples():
    dependencies = row.Task_Dependency
    if isinstance(dependencies, list) and dependencies:
        for dep_id in dependencies:
            dep_id = str(dep_id).strip()
            if dep_id in task_pos and row.Task_ID in task_pos:
                dep = task_pos[dep_id]
                cur = task_pos[row.Task_ID]

                fig.add_annotation(
                    x=cur["x_start"], y=cur["y"],
                    ax=dep["x_end"], ay=dep["y"],
                    xref="x", yref="y", axref="x", ayref="y",
                    showarrow=True, arrowhead=3, arrowsize=1,
                    arrowwidth=3, arrowcolor="#9769cf"
                )

# Final chart rendering


fig.update_layout(height=min(800, 40 * len(df)), title="📌 Gantt Chart with Task Progress and Dependencies", yaxis_title="Task" , plot_bgcolor="#d5eaf0")
st.plotly_chart(fig, use_container_width=True)
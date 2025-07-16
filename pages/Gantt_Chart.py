import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Define task data
data = [
    dict(Task="Smooth transition animations for seating interactions.", Start='2025-06-25', Finish='2025-06-27', Resource='Shubham', DependsOn="T002", Progress=70),
    dict(Task="Sitting animations (sitting, getting up, sitting idle)", Start='2025-06-09', Finish='2025-06-17', Resource='Shubham', Progress=100),
    dict(Task="Idle Animation while Sitting", Start='2025-06-18', Finish='2025-06-20', Resource='Shubham', Progress=100),
    dict(Task="Animated curtain system for booths/stages.", Start='2025-06-25', Finish='2025-06-29', Resource='Shubham', DependsOn="T005", Progress=30),
    dict(Task="Curtain open animations", Start='2025-06-23', Finish='2025-07-01', Resource='Shubham', Progress=60),
    dict(Task="Animation sequences", Start='2025-06-24', Finish='2025-06-28', Resource='Shubham', Progress=40),
    dict(Task="Raise hand animation during the event", Start='2025-06-25', Finish='2025-06-27', Resource='Shubham', Progress=20),
    dict(Task="UI for host during the meet where he manages the question", Start='2025-06-09', Finish='2025-06-13', Resource='Pukhraj, Ayush', Progress=100),
    dict(Task="Assets for curtain", Start='2025-06-18', Finish='2025-06-20', Resource='Shubham', Progress=100),
    dict(Task="UI screen for removing users from sessions.", Start='2025-06-09', Finish='2025-06-17', Resource='Pukhraj, Ayush', Progress=100),
    dict(Task="UI screen for rejecting user requests.", Start='2025-06-09', Finish='2025-06-17', Resource='Pukhraj, Ayush', Progress=100),
    dict(Task="UI for managing AI/NPC booth interactions.", Start='2025-06-09', Finish='2025-06-17', Resource='Pukhraj, Ayush', Progress=100),
    dict(Task="UI for receiving cards.", Start='2025-06-09', Finish='2025-06-17', Resource='Pukhraj, Ayush', Progress=100),
    dict(Task="UI for lending cards.", Start='2025-06-09', Finish='2025-06-17', Resource='Pukhraj, Ayush', Progress=100),
    dict(Task="AWS server setup", Start='2025-06-12', Finish='2025-06-16', Resource='Abhimanyu', Progress=100),
    dict(Task="Pixel streaming setup", Start='2025-06-03', Finish='2025-06-10', Resource='Abhimanyu', Progress=100),
    dict(Task="Handling input outputs on Pixel Streaming", Start='2025-06-17', Finish='2025-06-20', Resource='Abhimanyu', DependsOn="T016", Progress=80),
    dict(Task="Wave hand animations for avatar gestures.", Start='2025-06-09', Finish='2025-06-09', Resource='Shubham', Progress=100),
    dict(Task="Handshake animation between avatars.", Start='2025-06-10', Finish='2025-06-10', Resource='Shubham', Progress=100),
    dict(Task="Group chat with emoji support", Start='2025-06-11', Finish='2025-06-12', Resource='Ayush', Progress=100),
    dict(Task="Q&A mode with guest question selection", Start='2025-06-13', Finish='2025-06-16', Resource='Ayush', Progress=100),
    dict(Task="Booth zone text interaction", Start='2025-06-18', Finish='2025-06-19', Resource='Ayush', Progress=100),
    dict(Task="Max 2 simultaneous conversations for booth manager", Start='2025-06-20', Finish='2025-06-20', Resource='Ayush', Progress=100),
    dict(Task="Interaction with VIP speakers by guests", Start='2025-06-23', Finish='2025-06-25', Resource='Ayush', Progress=100),
    dict(Task="Spatial sound integration", Start='2025-06-25', Finish='2025-06-28', Resource='Shubham', DependsOn="T016", Progress=50),
]

# Create DataFrame
df = pd.DataFrame(data)
df.insert(0, 'TaskID', [f"T{str(i+1).zfill(3)}" for i in range(len(df))])
df['Start'] = pd.to_datetime(df['Start'])
df['Finish'] = pd.to_datetime(df['Finish'])
df["Y_Index"] = list(range(len(df)))

# Streamlit UI
st.set_page_config(layout="wide")
st.title("📊 Project Gantt Chart with Task Progress and Dependencies")

# Create base Gantt chart
fig = px.timeline(df, x_start="Start", x_end="Finish", y="Y_Index", color="Resource",
                  hover_data=["Task", "TaskID", "DependsOn", "Progress"])
fig.update_yaxes(tickfont=dict(size=16, color="#367178"), tickvals=df["Y_Index"], ticktext=df["Task"], autorange="reversed", showgrid=True, gridcolor="#2b6170")
fig.update_xaxes(showgrid=True, gridcolor="#2b6170" , dtick = "D1")

# Add task progress overlay
for row in df.itertuples():
    progress_end = row.Start + (row.Finish - row.Start) * (row.Progress / 100)
    fig.add_trace(go.Scatter(
        x=[row.Start, progress_end],
        y=[row.Y_Index, row.Y_Index],
        mode="lines",
        line=dict(color="black", width=6),
        showlegend=False,
        hoverinfo="skip"
    ))

# Add dependency arrows
task_pos = {row.TaskID: {"x_start": row.Start, "x_end": row.Finish, "y": row.Y_Index} for row in df.itertuples()}
for row in df.itertuples():
    if isinstance(row.DependsOn, str) and row.DependsOn in task_pos:
        dep = task_pos[row.DependsOn]
        cur = task_pos[row.TaskID]
        fig.add_annotation(
            x=cur["x_start"], y=cur["y"],
            ax=dep["x_end"], ay=dep["y"],
            xref="x", yref="y", axref="x", ayref="y",
            showarrow=True, arrowhead=3, arrowsize=1, arrowwidth=3, arrowcolor="#9769cf"
        )

# Final chart rendering
fig.update_layout(height=1200, title="📌 Gantt Chart with Task Progress and Dependencies", yaxis_title="Task" , plot_bgcolor="#d5eaf0" , paper_bgcolor = "#e4f5f7")
st.plotly_chart(fig, use_container_width=True)

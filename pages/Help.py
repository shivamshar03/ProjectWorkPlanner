import streamlit as st

st.set_page_config("📖 Help - Project Work Planner", layout="wide", page_icon="❓")
st.title("🛠️ Help Center - Project Work Planner")

# --- Tabs for Help and Chatbot ---
tab1, tab2 = st.tabs(["📖 Help Guide", "💬 Chatbot Support"])

# ----------------------- TAB 1: HELP GUIDE -----------------------
with tab1:
    st.markdown("""
Welcome to the **Project Work Planner**! This tool helps you break down your project into actionable tasks, organize them into sprints, manage dependencies, and track progress effectively.

---

## 🔧 Features Overview

### 🗂️ Project Setup
- **Project Name**: Title of your project.
- **Project Description**: Provide a short overview. If not available, type `na` or `none`.
- **Start & End Dates**: Define your project timeline.

### 📌 Task Management
- **Sprint**: Group tasks into time-boxed sprints.
- **Task ID**: Unique ID like `T1`, `T2`.
- **Module**: Category (UI, Dev, Design, etc.)
- **Dependencies**: Tasks that must be completed first.
- **Estimated Time**: e.g., `3 days`, `4 hrs`.

### ⛑️ Resource Management
- Assign team members.
- Conflicts are flagged if a resource is already busy.

### 📊 Visualization
- Gantt chart view of timelines.
- Status tracking for `PENDING`, `IN PROGRESS`, etc.

### 📤 Data Storage
- Save and load data from MongoDB (optional).
- Export plans to CSV/JSON.

---

## ❓ FAQs

**Q: No description yet?**  
A: Enter `na` or `none`.

**Q: How are dependencies handled?**  
A: The planner will auto-adjust start dates based on the selected dependencies.

**Q: Can I edit tasks after creating them?**  
A: Yes, all task fields are editable in the planner table.

---

## 📫 Contact Support

- 📧 Email: `shivamshar03@gmail.com`
- 💻 GitHub: [@shivamshar03](https://github.com/shivamshar03)

---
    """)

# ----------------------- TAB 2: CHATBOT -----------------------
with tab2:
    st.subheader("💬 Project Help Assistant")
    st.caption("Ask me anything about using the Project Work Planner.")

    from langchain_groq import ChatGroq
    from langchain.schema import HumanMessage, SystemMessage
    from dotenv import  load_dotenv

    load_dotenv()


    # --- Initialize Chat Model ---
    chat = ChatGroq(model_name="llama3-70b-8192")

    # --- Contextual System Prompt ---
    context_prompt = SystemMessage(
        content="""
You are an AI help assistant embedded in the **Project Work Planner**, an internal project management tool built for Carina Soft Labs Inc.

Your job is to help employees understand how to:
- Create and manage software projects across multiple sprints.
- Add, edit, or delete project tasks and organize them by module (UI, Design, Rigging, Animation, Development, VFX/SFX).
- Assign tasks to specific developers while detecting resource conflicts if someone is already working on another project.
- Use task dependencies so a task starts only after its dependent tasks are completed.
- Use estimated time and date ranges to visualize work in a Gantt chart.
- Export project plans as CSV or JSON, or store them in MongoDB.
- Use 'na' or 'none' when a project description is not provided.
- Track status using flags like `PENDING`, `IN PROGRESS`, `COMPLETED`, and `BLOCKED`.

You're a knowledgeable, helpful assistant that understands Carina Soft Labs' internal workflow standards.

FAQs you should handle confidently:
- "How are developers assigned?" → Based on their availability; conflicts are flagged.
- "Can I skip descriptions?" → Yes. Just enter `na` or `none`.
- "What if two tasks overlap?" → Use dependencies and proper estimation to avoid overlap.
- "Can I view the full timeline?" → Use the Gantt chart feature.
- "How is data stored?" → In a MongoDB database if available, or exported manually.

Always give clear, friendly, and helpful responses. Assume the user is a team member at Carina Soft Labs Inc.
"""
    )

    # --- Chat History Handling ---
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Display Previous Messages
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat Input
    user_query = st.chat_input("Ask your question here...")

    if user_query:
        # st.chat_message("user").markdown(user_query)
        st.session_state.chat_history.append({"role": "user", "content": user_query})

        # Send system context + user message
        response = chat([
            context_prompt,
            *[HumanMessage(content=msg["content"]) for msg in st.session_state.chat_history if msg["role"] == "user"]
        ])

        reply = response.content
        st.chat_message("assistant").markdown(reply)
        st.session_state.chat_history.append({"role": "assistant", "content": reply})


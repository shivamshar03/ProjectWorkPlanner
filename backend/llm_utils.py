from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv()

def get_llm():
    return ChatGroq(model_name="llama3-70b-8192")

def generate_tasks_with_llm(context_text: str):
    prompt = ChatPromptTemplate.from_template(
        """
You are an expert project planner AI.

Given the following project information, generate a project task breakdown as a JSON list of dictionaries.

Each task dictionary should contain the following fields:
- "Sprint": Sprint number (e.g., "Sprint 1")
- "Task_ID": A unique ID (e.g., "T1", "T2", etc.)
- "Task": A short task description
- "Task_Dependency": List of Task IDs this task depends on, or an empty list
- "Estimated Time": Estimated time in "X hours" or "Y days"
- "Start": Start date (format: YYYY-MM-DD)
- "End": End date (format: YYYY-MM-DD)

⚠️ Rules:
- Use the provided working days and holidays to plan scheduling.
- Do not assign work on weekends or the listed holidays.
- You may slightly extend the project timeline if needed.
- Return only valid JSON — no explanation, markdown, or extra text.
- Do not include notes like "Here is the task plan" or any other commentary.

📄 Project Context:
{context_text}
"""
    )

    llm = get_llm()
    chain = prompt | llm | StrOutputParser()
    return chain.invoke({"context_text": context_text})

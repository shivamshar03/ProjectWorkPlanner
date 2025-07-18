from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv()

def get_llm():
    return ChatGroq(model_name="llama3-70b-8192")

def generate_tasks_with_llm(context_text: str,sprints):
    prompt = ChatPromptTemplate.from_template(
        """
     You are an expert project planner AI.

     🎯 Objective:
     Generate a structured task breakdown for the project using valid JSON format only.

     📦 Sprint Setup:
     - Sprint Duration Type: {sprints} (e.g., weekly = 7 days, biweekly = 14 days, monthly = approx. 30 days)
     - Tasks must be assigned strictly within the boundaries of their respective sprint windows.
     - Sprint 1 should begin on the project start date.
     - Sprint 2 starts after Sprint 1 ends, and so on.

     📄 Input Context:
     {context_text}

     📌 Output JSON format:
     [
       {{
         "Sprint": "Sprint 1",
         "Task_ID": "T1",
         "Task": "Design the landing page UI",
         "Task_Dependency": [],
         "Estimated Time": "2 days",
         "Start": "YYYY-MM-DD",
         "End": "YYYY-MM-DD"
       }},
       ...
     ]

     🚫 Constraints:
     - Output must be pure valid JSON only — no comments, markdown, explanation, or extra text.
     - Use only the working days provided in the context.
     - Exclude weekends and user-defined holidays.
     - Respect task dependencies: a task must start **after** all its dependencies end.
     - Distribute tasks logically across all sprints.
     - If the timeline is tight, slightly extend the project end date, but stay close.
     """
    )

    llm = get_llm()
    chain = prompt | llm | StrOutputParser()
    return chain.invoke({"context_text": context_text , "sprints": sprints})

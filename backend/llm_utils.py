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
- Tasks can run in **parallel** (i.e., multiple tasks can occur on the same day) **as long as they do not conflict by dependency.**
- If the timeline is tight, slightly extend the project end date, but stay close.

     """
    )

    llm = get_llm()
    chain = prompt | llm | StrOutputParser()
    return chain.invoke({"context_text": context_text , "sprints": sprints})


def example(pdf_txt,description):
    prompt = ChatPromptTemplate.from_template(

        """ Prompt for Generating a Project Task Table
        Prompt:
        You are a project management assistant tasked with creating a structured table to organize tasks for a given project. The table should have three columns: Planning, Assets, and Feature. Based on the project description provided below, generate a comprehensive list of tasks required to complete the project. Classify each task into one of the three columns (Planning, Assets, or Feature) and list them in the order they should be executed. Ensure the tasks are specific, actionable, and relevant to the project description. Format the output as a markdown table.
        Project Description:{pdf_txt}
        Instructions:
    
        Analyze the project description to identify all necessary tasks.
        Categorize each task into one of the following columns:
        Planning: Tasks related to project strategy, timelines, research, or coordination (e.g., defining scope, creating timelines, stakeholder meetings).
        Assets: Tasks related to creating or acquiring resources, tools, or materials (e.g., designing assets, purchasing software, gathering data).
        Feature: Tasks related to developing or implementing specific functionalities or deliverables (e.g., coding a feature, testing a component, deploying a module).
    
    
        List tasks in the chronological order of execution, ensuring dependencies are considered (e.g., planning tasks typically come before asset creation, which precedes feature development).
        Present the tasks in a markdown table with the columns Planning, Assets, and Feature. If a task does not apply to a column for a given row, leave that cell empty.
        Ensure the table is clear, concise, and professional, with tasks described in a way that is actionable and specific to the project.
    
        Example Output:
    
        | Planning                          | Assets                         | Feature                      |
        |-----------------------------------|--------------------------------|------------------------------|
        | Define project scope and objectives |                                |                              |
        | Create project timeline           |                                |                              |
        |                                   | Design UI mockups             |                              |
        |                                   | Set up development environment |                              |
        |                                   |                                | Implement user authentication |
        |                                   |                                | Test feature compatibility   |
        |                                   |                                | Deploy project to production  |
    
    
        Project Description for Processing:{description}
        """)

    llm = get_llm()
    chain = prompt | llm | StrOutputParser()
    return chain.invoke({"pdf_txt": pdf_txt, "description": description})



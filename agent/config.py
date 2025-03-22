"""Configuration for the CrewAI agent."""

import os
import sys
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
from crewai.memory import EntityMemory
from langchain_google_genai import ChatGoogleGenerativeAI
import google.generativeai as genai

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.run_sql import SQLTool
from tools.get_schema import SchemaTool
from tools.summarizer import SummarizerTool

# Load environment variables
load_dotenv()

# Configure Google API
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
llm = ChatGoogleGenerativeAI(model="gemini-pro", google_api_key=os.getenv('GEMINI_API_KEY'))

# Define agent roles and personas
AGENT_ROLES = {
    "data_analyst": {
        "name": "Data Analyst",
        "description": "Analyzes sales data to identify patterns and trends.",
        "goal": "Extract meaningful insights from sales data through SQL analysis.",
        "backstory": """
        You are an expert data analyst with 10+ years of experience in SQL and data analysis.
        You excel at:
        - Writing complex SQL queries to extract meaningful insights
        - Identifying patterns and trends in time-series data
        - Performing statistical analysis on sales metrics
        - Breaking down complex business questions into data-driven investigations
        
        Your approach is methodical:
        1. Always start by understanding the data structure
        2. Write clear, efficient SQL queries
        3. Validate your findings through multiple queries
        4. Present data in a clear, structured format
        """
    },
    "business_analyst": {
        "name": "Business Analyst",
        "description": "Translates data insights into actionable business recommendations.",
        "goal": "Provide business-focused insights and recommendations based on data analysis.",
        "backstory": """
        You are a seasoned business analyst with deep expertise in sales operations and market dynamics.
        You excel at:
        - Interpreting complex data patterns into business implications
        - Identifying root causes of business problems
        - Providing actionable recommendations
        - Communicating insights to non-technical stakeholders
        
        Your approach is business-focused:
        1. Review data analysis with a business lens
        2. Consider market context and external factors
        3. Focus on actionable insights
        4. Present recommendations in clear, business-friendly language
        """
    }
}


def create_data_analyst_agent() -> Agent:
    """Create a data analyst agent with database tools."""
    sql_tool = SQLTool()
    schema_tool = SchemaTool()
    summarizer_tool = SummarizerTool()
    
    return Agent(
        role=AGENT_ROLES["data_analyst"]["name"],
        goal=AGENT_ROLES["data_analyst"]["goal"],
        backstory=AGENT_ROLES["data_analyst"]["backstory"],
        verbose=True,
        allow_delegation=True,
        memory=EntityMemory(),
        tools=[
            sql_tool.run,
            schema_tool.get_tables,
            schema_tool.get_table_info,
            schema_tool.get_table_relationships,
            summarizer_tool.summarize,
            summarizer_tool.analyze_metrics
        ],
        llm=llm
    )


def create_business_analyst_agent() -> Agent:
    """Create a business analyst agent with analysis tools."""
    sql_tool = SQLTool()
    summarizer_tool = SummarizerTool()
    
    return Agent(
        role=AGENT_ROLES["business_analyst"]["name"],
        goal=AGENT_ROLES["business_analyst"]["goal"],
        backstory=AGENT_ROLES["business_analyst"]["backstory"],
        verbose=True,
        allow_delegation=True,
        memory=EntityMemory(),
        tools=[
            sql_tool.run,
            summarizer_tool.summarize,
            summarizer_tool.analyze_metrics,
            summarizer_tool.investigate_anomaly
        ],
        llm=llm
    )


def create_sales_analysis_task(
    user_query: str,
    context: Optional[Dict[str, Any]] = None
) -> Task:
    """
    Create a task for analyzing sales data.
    
    Args:
        user_query: User's analysis query
        context: Optional context information
        
    Returns:
        Task: CrewAI task for analysis
    """
    # Define the task description based on user query
    task_description = f"""
    Analyze the sales data to answer: "{user_query}"
    
    Follow these steps:
    1. Understand the database schema and table relationships
    2. Write and execute SQL queries to investigate the data
    3. Identify patterns, trends, and anomalies
    4. Provide a clear, structured analysis
    
    IMPORTANT:
    - Be data-driven - support all conclusions with data
    - Consider multiple dimensions (time, region, product, etc.)
    - Look for both positive and negative trends
    - Validate findings through multiple queries
    """
    
    # Add any context if provided
    if context:
        context_str = "\n\nAdditional context:\n"
        for key, value in context.items():
            context_str += f"- {key}: {value}\n"
        task_description += context_str
    
    return Task(
        description=task_description,
        expected_output="A comprehensive analysis of the sales data with findings and evidence.",
        agent=create_data_analyst_agent(),
        context=context or {}
    )


def create_business_interpretation_task() -> Task:
    """
    Create a task for business interpretation of the analysis.
    
    Returns:
        Task: CrewAI task for business interpretation
    """
    return Task(
        description="""
        Review the data analysis and provide business-focused insights.
        
        Include:
        1. Key findings and their business implications
        2. Potential root causes
        3. Recommendations for improvement
        
        Make sure to:
        - Consider market context and external factors
        - Focus on actionable insights
        - Present recommendations in clear, business-friendly language
        - Support conclusions with data when possible
        
        Your output should be immediately actionable for product managers.
        """,
        expected_output="Business-focused insights and recommendations based on the data analysis.",
        agent=create_business_analyst_agent()
    )


def create_crew(user_query: str, context: Optional[Dict[str, Any]] = None) -> Crew:
    """
    Create a crew of agents to analyze sales data.
    
    Args:
        user_query: User's analysis query
        context: Optional context information
        
    Returns:
        Crew: CrewAI crew for analysis
    """
    # Create the tasks
    analysis_task = create_sales_analysis_task(user_query, context)
    interpretation_task = create_business_interpretation_task()
    
    # Create the crew with sequential process
    crew = Crew(
        agents=[
            create_data_analyst_agent(),
            create_business_analyst_agent()
        ],
        tasks=[analysis_task, interpretation_task],
        verbose=2,
        process=Process.sequential,
        memory=EntityMemory()
    )
    
    return crew 
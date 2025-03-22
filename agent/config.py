"""Configuration for the CrewAI agent."""

import os
import sys
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.run_sql import SQLTool
from tools.get_schema import SchemaTool
from tools.summarizer import SummarizerTool

# Load environment variables
load_dotenv()

# Define agent roles and personas
AGENT_ROLES = {
    "data_detective": {
        "name": "Data Detective",
        "description": "Investigates anomalies in marketing data to find root causes.",
        "goal": "Determine the cause of performance anomalies in marketing campaigns.",
        "backstory": """
        You are a highly skilled data analyst with expertise in marketing analytics.
        Your specialty is identifying the root causes of anomalies in campaign performance.
        You're methodical, detail-oriented, and can navigate complex datasets to find
        hidden patterns and insights.
        """
    },
    "sql_expert": {
        "name": "SQL Expert",
        "description": "Crafts efficient SQL queries to analyze marketing campaign data.",
        "goal": "Extract relevant data through optimized SQL queries.",
        "backstory": """
        You're a database expert who specializes in writing sophisticated SQL queries.
        You know how to design queries that join across tables efficiently and can
        analyze marketing performance metrics to find meaningful patterns.
        """
    }
}


def create_sql_agent() -> Agent:
    """Create a SQL expert agent with database tools."""
    sql_tool = SQLTool()
    schema_tool = SchemaTool()
    
    return Agent(
        role=AGENT_ROLES["sql_expert"]["name"],
        goal=AGENT_ROLES["sql_expert"]["goal"],
        backstory=AGENT_ROLES["sql_expert"]["backstory"],
        verbose=True,
        allow_delegation=True,
        tools=[
            sql_tool.run,
            schema_tool.get_tables,
            schema_tool.get_table_info,
            schema_tool.get_table_relationships
        ]
    )


def create_detective_agent() -> Agent:
    """Create a data detective agent with analysis tools."""
    sql_tool = SQLTool()
    schema_tool = SchemaTool()
    summarizer_tool = SummarizerTool()
    
    return Agent(
        role=AGENT_ROLES["data_detective"]["name"],
        goal=AGENT_ROLES["data_detective"]["goal"],
        backstory=AGENT_ROLES["data_detective"]["backstory"],
        verbose=True,
        allow_delegation=True,
        tools=[
            sql_tool.run_and_format,
            schema_tool.format_table_schema,
            schema_tool.generate_schema_summary,
            summarizer_tool.summarize,
            summarizer_tool.analyze_metrics,
            summarizer_tool.investigate_anomaly
        ]
    )


def create_task_investigation(
    user_query: str,
    context: Optional[Dict[str, Any]] = None
) -> Task:
    """
    Create a task for investigating a data anomaly.
    
    Args:
        user_query: User's investigation query
        context: Optional context information
        
    Returns:
        Task: CrewAI task for investigation
    """
    # Define the task description based on user query
    task_description = f"""
    Investigate the following issue: "{user_query}"
    
    Follow these steps:
    1. Understand the database schema and table relationships
    2. Look for relevant data in the appropriate tables
    3. Query for patterns and anomalies related to the issue
    4. Analyze the data to find the root cause
    5. Summarize your findings with supporting evidence
    
    IMPORTANT:
    - Be data-driven - support all conclusions with data
    - Be thorough in your investigation
    - Consider multiple possible causes
    - Prioritize findings by importance and confidence
    """
    
    # Add any context if provided
    if context:
        context_str = "\n\nAdditional context:\n"
        for key, value in context.items():
            context_str += f"- {key}: {value}\n"
        task_description += context_str
    
    return Task(
        description=task_description,
        expected_output="A comprehensive analysis of the issue with findings and evidence.",
        agent=create_detective_agent()
    )


def create_data_extraction_task(query_description: str) -> Task:
    """
    Create a task for extracting relevant data.
    
    Args:
        query_description: Description of the data needed
        
    Returns:
        Task: CrewAI task for data extraction
    """
    return Task(
        description=f"""
        Extract the data needed to answer: "{query_description}"
        
        Follow these steps:
        1. Understand the database schema
        2. Identify relevant tables and relationships
        3. Write efficient SQL queries to extract the necessary data
        4. Format the results in a clear, readable way
        5. Provide a brief explanation of your approach
        
        IMPORTANT:
        - Use joins efficiently
        - Include proper WHERE clauses to filter relevant data
        - Consider using aggregations where appropriate
        - Make sure to include all relevant dimensions for analysis
        """,
        expected_output="SQL query results with clear formatting and explanation.",
        agent=create_sql_agent()
    )


def create_crew(user_query: str, context: Optional[Dict[str, Any]] = None) -> Crew:
    """
    Create a crew of agents to investigate an issue.
    
    Args:
        user_query: User's investigation query
        context: Optional context information
        
    Returns:
        Crew: CrewAI crew for investigation
    """
    # Create the investigation task
    investigation_task = create_task_investigation(user_query, context)
    
    # Create the crew with sequential process
    crew = Crew(
        agents=[
            create_detective_agent(), 
            create_sql_agent()
        ],
        tasks=[investigation_task],
        verbose=2,
        process=Process.sequential
    )
    
    return crew 
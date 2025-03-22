"""Tool for summarizing data using Google's Gemini API."""

import os
import sys
import json
import google.generativeai as genai
from typing import Dict, List, Any, Optional, Union
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

# Get API key from environment
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables")

# Configure the generative AI library
genai.configure(api_key=GEMINI_API_KEY)


class SummarizerTool:
    """Tool for summarizing data using Google's Gemini API."""
    
    def __init__(self, model_name: str = "gemini-1.5-pro"):
        """
        Initialize the summarizer tool.
        
        Args:
            model_name (str): Name of the Gemini model to use
        """
        self.model_name = model_name
        self.model = genai.GenerativeModel(model_name)
        
        # Load default summarizer prompt
        prompt_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "prompts/summarizer_prompt.txt"
        )
        
        try:
            with open(prompt_path, "r") as file:
                self.default_prompt = file.read()
        except FileNotFoundError:
            self.default_prompt = """
            You are a data analyst specialized in marketing and sales data.
            Analyze the following data and provide a clear, concise summary of the key insights.
            Focus on identifying anomalies, trends, and potential root causes.
            
            If there are any significant changes or anomalies, highlight those and suggest possible explanations.
            
            Format your response as markdown with sections for:
            1. Summary - A brief overview of what you found
            2. Key Metrics - Important numbers and their significance
            3. Anomalies - Any unusual patterns or outliers
            4. Possible Causes - Plausible explanations for the findings
            5. Recommendations - Suggested next steps or areas to investigate further
            
            DATA:
            {data}
            """
    
    def summarize(
        self, 
        data: Union[Dict, List, str],
        custom_prompt: Optional[str] = None,
        context: Optional[str] = None
    ) -> str:
        """
        Summarize data using Gemini.
        
        Args:
            data: Data to summarize (dict, list, or str)
            custom_prompt: Optional custom prompt to use
            context: Optional context to add to the prompt
            
        Returns:
            str: Generated summary
        """
        # Convert data to string if it's a dict or list
        if isinstance(data, (dict, list)):
            data_str = json.dumps(data, indent=2)
        else:
            data_str = str(data)
        
        # Prepare prompt
        prompt = custom_prompt if custom_prompt else self.default_prompt
        
        # Add context if provided
        if context:
            prompt = f"{prompt}\n\nADDITIONAL CONTEXT:\n{context}"
        
        # Replace placeholder with actual data
        prompt = prompt.replace("{data}", data_str)
        
        # Generate summary
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error generating summary: {str(e)}"
    
    def analyze_metrics(
        self,
        metrics: Dict[str, Any],
        time_period: str = "daily",
        focus_area: Optional[str] = None,
        threshold: float = 0.2
    ) -> str:
        """
        Analyze marketing metrics to identify anomalies and trends.
        
        Args:
            metrics: Dictionary containing marketing metrics
            time_period: Time period of the data (daily, weekly, monthly)
            focus_area: Optional specific area to focus on
            threshold: Threshold for anomaly detection (percentage change)
            
        Returns:
            str: Analysis summary
        """
        # Create specialized prompt for metrics analysis
        prompt = f"""
        You are a marketing analyst specializing in campaign performance metrics.
        
        Analyze the following {time_period} metrics data and identify:
        1. Any significant changes (>{threshold*100}% change) in key metrics
        2. Trends over time
        3. Correlations between different metrics
        4. Possible root causes for performance changes
        
        {f"Focus specifically on analyzing {focus_area}." if focus_area else ""}
        
        Format your response as markdown with sections for:
        1. Summary - A brief overview of what you found
        2. Key Anomalies - Significant changes or unusual patterns
        3. Trends - How metrics changed over time
        4. Correlations - Relationships between different metrics
        5. Root Cause Analysis - Likely explanations for the findings
        
        DATA:
        {{data}}
        """
        
        return self.summarize(metrics, custom_prompt=prompt)
    
    def investigate_anomaly(
        self,
        data: Dict[str, Any],
        anomaly_description: str,
        related_context: Optional[str] = None
    ) -> str:
        """
        Investigate a specific anomaly in the data.
        
        Args:
            data: Data related to the anomaly
            anomaly_description: Description of the anomaly
            related_context: Optional additional context
            
        Returns:
            str: Investigation summary
        """
        # Create specialized prompt for anomaly investigation
        prompt = f"""
        You are a data detective specializing in marketing and sales analytics.
        
        ANOMALY TO INVESTIGATE:
        {anomaly_description}
        
        Analyze the provided data to determine the most likely root cause of this anomaly.
        Consider different factors such as:
        - Technical factors (tracking issues, data collection problems)
        - Campaign changes (creative changes, targeting adjustments)
        - External factors (seasonality, competition, market conditions)
        - User behavior changes
        
        Format your response as markdown with sections for:
        1. Summary - What you discovered about the anomaly
        2. Evidence - What data points support your findings
        3. Root Cause Analysis - Most likely causes ranked by probability
        4. Confidence Level - How confident you are in the assessment
        5. Recommended Actions - What steps should be taken next
        
        DATA:
        {{data}}
        """
        
        return self.summarize(data, custom_prompt=prompt, context=related_context) 
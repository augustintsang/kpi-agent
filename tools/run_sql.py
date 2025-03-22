"""Tool for executing SQL queries on the PostgreSQL database."""

import os
import sys
import pandas as pd
from typing import Optional, Dict, Any, List, Union

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.connection import execute_query, test_connection

class SQLTool:
    """Tool for executing SQL queries and processing results."""
    
    def __init__(self):
        """Initialize the SQL tool."""
        # Test database connection
        if not test_connection():
            raise ConnectionError("Failed to connect to the database. Please check your connection settings.")
    
    def run(self, query: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute a SQL query and return the results.
        
        Args:
            query (str): SQL query to execute
            params (dict, optional): Parameters for the query
            
        Returns:
            dict: Dictionary containing query results and metadata
        """
        try:
            # Execute the query
            results = execute_query(query, params)
            
            # Process results if any
            if results:
                # Extract column names from the first row's keys
                if hasattr(results[0], '_fields'):
                    # Handle SQLAlchemy result proxy
                    columns = results[0]._fields
                    data = [list(row) for row in results]
                else:
                    # Handle raw tuple results
                    try:
                        # Try to infer column names from the query
                        # This is a simple approach and may not work for complex queries
                        column_part = query.lower().split("select")[1].split("from")[0].strip()
                        columns = [c.strip().split(' ')[-1] for c in column_part.split(',')]
                        # Remove any alias prefixes (table.column -> column)
                        columns = [c.split('.')[-1] for c in columns]
                    except:
                        # Fallback to generic column names
                        columns = [f"column_{i}" for i in range(len(results[0]))]
                    
                    data = [list(row) for row in results]
                
                # Convert to pandas DataFrame for easier processing
                df = pd.DataFrame(data, columns=columns)
                
                # Calculate basic statistics for numeric columns
                stats = {}
                for col in df.select_dtypes(include=['number']).columns:
                    stats[col] = {
                        'min': df[col].min(),
                        'max': df[col].max(),
                        'mean': df[col].mean(),
                        'median': df[col].median()
                    }
                
                # Generate preview table formatted as markdown
                preview = df.head(10).to_markdown(index=False) if len(df) > 0 else "No results"
                
                # Return detailed response
                return {
                    'success': True,
                    'row_count': len(df),
                    'columns': list(df.columns),
                    'preview': preview,
                    'data': df.to_dict(orient='records'),
                    'statistics': stats
                }
            
            # Handle queries that don't return results (INSERT, UPDATE, etc.)
            return {
                'success': True,
                'row_count': 0,
                'message': 'Query executed successfully, but no results were returned.'
            }
                
        except Exception as e:
            # Return error information
            return {
                'success': False,
                'error': str(e),
                'query': query
            }
    
    def run_and_format(self, query: str, params: Optional[Dict[str, Any]] = None) -> str:
        """
        Execute a SQL query and return results formatted for display in a markdown report.
        
        Args:
            query (str): SQL query to execute
            params (dict, optional): Parameters for the query
            
        Returns:
            str: Markdown formatted results
        """
        result = self.run(query, params)
        
        if not result['success']:
            return f"❌ Query error: {result['error']}"
        
        if result.get('row_count', 0) == 0:
            return "Query executed successfully, but no results were returned."
        
        # Return formatted preview
        output = f"Query returned {result['row_count']} rows\n\n"
        output += result['preview']
        
        # Add basic statistics for numeric columns if available
        if result.get('statistics'):
            output += "\n\n**Basic Statistics:**\n"
            for col, stats in result['statistics'].items():
                output += f"\n- **{col}**: min={stats['min']:.4f}, max={stats['max']:.4f}, mean={stats['mean']:.4f}, median={stats['median']:.4f}"
        
        return output 
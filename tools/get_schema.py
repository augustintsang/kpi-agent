"""Tool for retrieving database schema information."""

import os
import sys
from typing import Dict, List, Any, Optional, Union

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.connection import execute_query, test_connection


class SchemaTool:
    """Tool for retrieving and analyzing database schema information."""
    
    def __init__(self):
        """Initialize the schema tool."""
        # Test database connection
        if not test_connection():
            raise ConnectionError("Failed to connect to the database. Please check your connection settings.")
    
    def get_tables(self) -> List[str]:
        """
        Get a list of all tables in the database.
        
        Returns:
            list: List of table names
        """
        query = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name
        """
        
        results = execute_query(query)
        return [row[0] for row in results]
    
    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific table.
        
        Args:
            table_name (str): Name of the table
            
        Returns:
            dict: Dictionary containing table schema information
        """
        # Get column information
        column_query = """
        SELECT 
            column_name, 
            data_type, 
            character_maximum_length,
            column_default,
            is_nullable
        FROM 
            information_schema.columns
        WHERE 
            table_schema = 'public' AND 
            table_name = %s
        ORDER BY 
            ordinal_position
        """
        
        columns = execute_query(column_query, (table_name,))
        
        # Get constraint information (primary keys, foreign keys, etc.)
        constraint_query = """
        SELECT
            tc.constraint_name,
            tc.constraint_type,
            kcu.column_name,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name
        FROM
            information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
              ON tc.constraint_name = kcu.constraint_name
              AND tc.table_schema = kcu.table_schema
            LEFT JOIN information_schema.constraint_column_usage AS ccu
              ON ccu.constraint_name = tc.constraint_name
              AND ccu.table_schema = tc.table_schema
        WHERE
            tc.table_schema = 'public' AND
            tc.table_name = %s
        ORDER BY
            tc.constraint_name, kcu.column_name
        """
        
        constraints = execute_query(constraint_query, (table_name,))
        
        # Get index information
        index_query = """
        SELECT
            indexname,
            indexdef
        FROM
            pg_indexes
        WHERE
            schemaname = 'public' AND
            tablename = %s
        ORDER BY
            indexname
        """
        
        indexes = execute_query(index_query, (table_name,))
        
        # Get row count
        count_query = f"SELECT COUNT(*) FROM {table_name}"
        row_count = execute_query(count_query)[0][0]
        
        # Process column information
        columns_info = []
        for col in columns:
            column_name, data_type, max_length, default_value, is_nullable = col
            column_info = {
                "name": column_name,
                "type": data_type,
                "max_length": max_length,
                "default": default_value,
                "nullable": is_nullable == "YES"
            }
            columns_info.append(column_info)
        
        # Process constraint information
        constraints_info = []
        for constraint in constraints:
            constraint_name, constraint_type, column_name, foreign_table, foreign_column = constraint
            constraint_info = {
                "name": constraint_name,
                "type": constraint_type,
                "column": column_name,
                "foreign_table": foreign_table,
                "foreign_column": foreign_column
            }
            constraints_info.append(constraint_info)
        
        # Process index information
        indexes_info = []
        for idx in indexes:
            index_name, index_def = idx
            indexes_info.append({
                "name": index_name,
                "definition": index_def
            })
        
        return {
            "name": table_name,
            "row_count": row_count,
            "columns": columns_info,
            "constraints": constraints_info,
            "indexes": indexes_info
        }
    
    def get_all_schemas(self) -> Dict[str, Dict[str, Any]]:
        """
        Get schema information for all tables in the database.
        
        Returns:
            dict: Dictionary with table names as keys and schema info as values
        """
        tables = self.get_tables()
        schemas = {}
        
        for table_name in tables:
            schemas[table_name] = self.get_table_info(table_name)
        
        return schemas
    
    def get_table_relationships(self) -> Dict[str, List[Dict[str, str]]]:
        """
        Get relationships between tables (foreign key constraints).
        
        Returns:
            dict: Dictionary with table names as keys and lists of related tables
        """
        query = """
        SELECT
            tc.table_name AS table_name,
            kcu.column_name AS column_name,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name
        FROM
            information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
              ON tc.constraint_name = kcu.constraint_name
              AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu
              ON ccu.constraint_name = tc.constraint_name
              AND ccu.table_schema = tc.table_schema
        WHERE
            tc.constraint_type = 'FOREIGN KEY' AND
            tc.table_schema = 'public'
        ORDER BY
            tc.table_name, kcu.column_name
        """
        
        results = execute_query(query)
        
        relationships = {}
        for row in results:
            table, column, foreign_table, foreign_column = row
            
            if table not in relationships:
                relationships[table] = []
            
            relationships[table].append({
                "column": column,
                "references_table": foreign_table,
                "references_column": foreign_column
            })
        
        return relationships
    
    def format_table_schema(self, table_name: str) -> str:
        """
        Get formatted schema information for a specific table.
        
        Args:
            table_name (str): Name of the table
            
        Returns:
            str: Markdown formatted schema information
        """
        try:
            schema = self.get_table_info(table_name)
            
            # Format the output
            output = f"# Table: {table_name}\n\n"
            output += f"Row count: {schema['row_count']}\n\n"
            
            # Columns
            output += "## Columns\n\n"
            output += "| Column | Type | Nullable | Default | Description |\n"
            output += "|--------|------|----------|---------|-------------|\n"
            
            for column in schema["columns"]:
                nullable = "YES" if column["nullable"] else "NO"
                default = column["default"] or ""
                type_info = column["type"]
                if column["max_length"]:
                    type_info += f"({column['max_length']})"
                
                output += f"| {column['name']} | {type_info} | {nullable} | {default} | |\n"
            
            # Constraints
            if schema["constraints"]:
                output += "\n## Constraints\n\n"
                output += "| Name | Type | Column | References |\n"
                output += "|------|------|--------|------------|\n"
                
                for constraint in schema["constraints"]:
                    constraint_type = constraint["type"]
                    refs = ""
                    if constraint["foreign_table"] and constraint["foreign_column"]:
                        refs = f"{constraint['foreign_table']}({constraint['foreign_column']})"
                    
                    output += f"| {constraint['name']} | {constraint_type} | {constraint['column']} | {refs} |\n"
            
            # Indexes
            if schema["indexes"]:
                output += "\n## Indexes\n\n"
                output += "| Name | Definition |\n"
                output += "|------|------------|\n"
                
                for idx in schema["indexes"]:
                    output += f"| {idx['name']} | {idx['definition']} |\n"
            
            return output
            
        except Exception as e:
            return f"Error retrieving schema for table '{table_name}': {str(e)}"
    
    def generate_schema_summary(self) -> str:
        """
        Generate a summary of the entire database schema.
        
        Returns:
            str: Markdown formatted schema summary
        """
        try:
            tables = self.get_tables()
            relationships = self.get_table_relationships()
            
            output = "# Database Schema Summary\n\n"
            
            # Tables overview
            output += f"## Tables ({len(tables)})\n\n"
            for table in tables:
                row_count = self.get_table_info(table)["row_count"]
                output += f"- **{table}** ({row_count} rows)\n"
            
            # Relationships overview
            output += "\n## Relationships\n\n"
            for table, relations in relationships.items():
                if relations:
                    output += f"### {table}\n\n"
                    for relation in relations:
                        output += f"- {table}.{relation['column']} → {relation['references_table']}.{relation['references_column']}\n"
            
            return output
            
        except Exception as e:
            return f"Error generating schema summary: {str(e)}" 
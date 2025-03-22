"""SalesIQ Agent CLI entrypoint."""

import os
import sys
import argparse
import datetime
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agent.config import create_crew
from agent.scratchpad import Scratchpad
from db.connection import test_connection


def validate_environment():
    """Check if all required environment variables are set."""
    required_vars = [
        ("GEMINI_API_KEY", "API key for Google Gemini"),
        ("DB_NAME", "Database name"),
        ("DB_USER", "Database user"),
        ("DB_PASSWORD", "Database password"),
        ("DB_HOST", "Database host"),
        ("DB_PORT", "Database port")
    ]
    
    missing = []
    for var, description in required_vars:
        if not os.getenv(var):
            missing.append((var, description))
    
    if missing:
        print("ERROR: Missing required environment variables:")
        for var, description in missing:
            print(f"  - {var}: {description}")
        print("\nPlease set these variables in your .env file or environment.")
        return False
    
    return True


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="SalesIQ Agent - AI-powered marketing data anomaly investigator"
    )
    
    parser.add_argument(
        "query",
        type=str,
        nargs="?",
        help="The investigation query (e.g., 'Investigate CTR drop for Campaign 5')"
    )
    
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        help="Save investigation results to this file"
    )
    
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output"
    )
    
    parser.add_argument(
        "--test-connection",
        action="store_true",
        help="Test database connection and exit"
    )
    
    parser.add_argument(
        "--context",
        "-c",
        type=str,
        help="Additional context for the investigation (format: key1=value1,key2=value2)"
    )
    
    return parser.parse_args()


def parse_context(context_str: str) -> Dict[str, str]:
    """Parse context string into a dictionary."""
    if not context_str:
        return {}
    
    context = {}
    pairs = context_str.split(",")
    
    for pair in pairs:
        if "=" in pair:
            key, value = pair.split("=", 1)
            context[key.strip()] = value.strip()
    
    return context


def run_investigation(query: str, context: Optional[Dict[str, Any]] = None, verbose: bool = False):
    """
    Run an investigation using the CrewAI agent.
    
    Args:
        query: User's investigation query
        context: Optional context information
        verbose: Whether to enable verbose output
    
    Returns:
        tuple: (Scratchpad instance, crew result)
    """
    # Create scratchpad for tracking the investigation
    scratchpad = Scratchpad()
    scratchpad.add_context("query", query)
    if context:
        for key, value in context.items():
            scratchpad.add_context(key, value)
    
    # Log investigation start
    scratchpad.log_action(
        action_type="investigation_start",
        description=f"Starting investigation: {query}",
        details={"context": context or {}}
    )
    
    # Create crew for the investigation
    crew = create_crew(query, context)
    
    # Add hooks for logging actions if verbose
    if verbose:
        def on_agent_start(agent):
            print(f"\n[{agent.role}] Starting work...")
            scratchpad.log_action(
                action_type="agent_start",
                description=f"Agent {agent.role} starting work",
                details={"agent": agent.role}
            )
        
        def on_agent_end(agent, result):
            print(f"\n[{agent.role}] Completed work")
            scratchpad.log_action(
                action_type="agent_end",
                description=f"Agent {agent.role} completed work",
                details={
                    "agent": agent.role,
                    "result_preview": result[:100] + "..." if len(result) > 100 else result
                }
            )
            
            # Try to extract findings from the result
            if "finding" in result.lower() or "anomaly" in result.lower():
                lines = result.split("\n")
                for line in lines:
                    if line.strip().startswith(("#", "##", "###")) and len(line) > 2:
                        title = line.strip("#").strip()
                        scratchpad.log_finding(
                            title=title,
                            description="(Extracted from agent output)",
                            importance="medium"
                        )
        
        crew.on_agent_start(on_agent_start)
        crew.on_agent_end(on_agent_end)
    
    # Run the crew
    print(f"\n{'='*60}\nINVESTIGATING: {query}\n{'='*60}\n")
    result = crew.kickoff()
    
    # Log the final result
    scratchpad.log_action(
        action_type="investigation_complete",
        description="Investigation completed",
        details={"result_preview": result[:200] + "..." if len(result) > 200 else result}
    )
    
    # Extract key findings from the result
    extraction_completed = False
    try:
        # Simple extraction logic - look for sections in markdown
        sections = result.split("\n## ")
        for section in sections:
            if section.lower().startswith(("finding", "anomal", "cause", "result")):
                lines = section.split("\n")
                title = lines[0].strip()
                description = "\n".join(lines[1:]).strip()
                
                scratchpad.log_finding(
                    title=title,
                    description=description,
                    importance="high"
                )
                extraction_completed = True
    except Exception as e:
        print(f"Error extracting findings: {e}")
    
    # If no structured findings were extracted, add the whole result as a finding
    if not extraction_completed:
        scratchpad.log_finding(
            title="Investigation Results",
            description=result,
            importance="medium"
        )
    
    return scratchpad, result


def main():
    """Main CLI entrypoint."""
    # Load environment variables
    load_dotenv()
    
    # Validate environment
    if not validate_environment():
        sys.exit(1)
    
    # Parse arguments
    args = parse_arguments()
    
    # Test database connection if requested
    if args.test_connection:
        print("Testing database connection...")
        if test_connection():
            print("Success! Connected to the database.")
            sys.exit(0)
        else:
            print("Failed to connect to the database. Check your connection settings.")
            sys.exit(1)
    
    # Check if a query was provided
    if not args.query:
        print("ERROR: Please provide an investigation query.")
        print("Example: python -m agent.run_agent \"Investigate CTR drop for Campaign 5\"")
        sys.exit(1)
    
    # Parse context if provided
    context = parse_context(args.context) if args.context else None
    
    try:
        # Run the investigation
        scratchpad, result = run_investigation(args.query, context, args.verbose)
        
        # Print the report
        scratchpad.print_report()
        
        # Print the detailed result
        print("\n## DETAILED RESULTS\n")
        print(result)
        
        # Save results to file if specified
        if args.output:
            print(f"\nSaving results to {args.output}...")
            
            # Determine file extension
            _, ext = os.path.splitext(args.output)
            
            if ext.lower() == '.json':
                # Save as JSON
                scratchpad.save_to_file(args.output)
            else:
                # Save as text file with report + result
                with open(args.output, 'w') as f:
                    # Write timestamp
                    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    f.write(f"# SalesIQ Investigation Report: {args.query}\n")
                    f.write(f"Generated: {timestamp}\n\n")
                    
                    # Write summary
                    summary = scratchpad.get_summary()
                    f.write(f"## Summary\n")
                    f.write(f"- Duration: {summary['duration_seconds']:.2f} seconds\n")
                    f.write(f"- Actions: {summary['action_count']}\n")
                    f.write(f"- Findings: {summary['finding_count']}\n\n")
                    
                    # Write key findings
                    f.write("## Key Findings\n\n")
                    findings = scratchpad.get_findings(min_importance="high")
                    for i, finding in enumerate(findings):
                        f.write(f"### {i+1}. {finding['title']}\n")
                        f.write(f"{finding['description']}\n\n")
                    
                    # Write detailed results
                    f.write("## Detailed Results\n\n")
                    f.write(result)
            
            print(f"Results saved to {args.output}")
        
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 
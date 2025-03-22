"""In-memory scratchpad for agent to log actions and findings."""

from typing import Dict, List, Any, Optional
import datetime
import json


class Scratchpad:
    """
    In-memory scratchpad to log agent actions, intermediate results, and findings.
    Helps maintain a record of the investigation and provides context for summarization.
    """
    
    def __init__(self):
        """Initialize an empty scratchpad."""
        self.actions = []
        self.findings = []
        self.context = {}
        self.start_time = datetime.datetime.now()
    
    def log_action(self, action_type: str, description: str, details: Optional[Dict[str, Any]] = None) -> None:
        """
        Log an action taken by the agent.
        
        Args:
            action_type: Type of action (e.g., "sql_query", "schema_lookup")
            description: Brief description of the action
            details: Additional details or parameters of the action
        """
        timestamp = datetime.datetime.now()
        action = {
            "timestamp": timestamp.isoformat(),
            "type": action_type,
            "description": description,
            "details": details or {}
        }
        self.actions.append(action)
    
    def log_finding(
        self, 
        title: str, 
        description: str, 
        importance: str = "medium", 
        related_actions: Optional[List[int]] = None,
        evidence: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log a finding or insight discovered by the agent.
        
        Args:
            title: Brief title of the finding
            description: Detailed description of the finding
            importance: Importance level (low, medium, high, critical)
            related_actions: Indices of related actions
            evidence: Supporting evidence for the finding
        """
        timestamp = datetime.datetime.now()
        finding = {
            "timestamp": timestamp.isoformat(),
            "title": title,
            "description": description,
            "importance": importance,
            "related_actions": related_actions or [],
            "evidence": evidence or {}
        }
        self.findings.append(finding)
    
    def add_context(self, key: str, value: Any) -> None:
        """
        Add contextual information to the scratchpad.
        
        Args:
            key: Context key
            value: Context value
        """
        self.context[key] = value
    
    def get_action_history(self) -> List[Dict[str, Any]]:
        """Get the full action history."""
        return self.actions
    
    def get_findings(self, min_importance: str = "low") -> List[Dict[str, Any]]:
        """
        Get findings filtered by minimum importance.
        
        Args:
            min_importance: Minimum importance level to include
            
        Returns:
            List of findings meeting the importance threshold
        """
        importance_levels = {
            "low": 0,
            "medium": 1,
            "high": 2,
            "critical": 3
        }
        
        min_level = importance_levels.get(min_importance.lower(), 0)
        
        return [
            finding for finding in self.findings
            if importance_levels.get(finding["importance"].lower(), 0) >= min_level
        ]
    
    def get_context(self, key: Optional[str] = None) -> Any:
        """
        Get context information.
        
        Args:
            key: Optional specific context key
            
        Returns:
            Context value if key is provided, otherwise all context
        """
        if key is not None:
            return self.context.get(key)
        return self.context
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the scratchpad contents.
        
        Returns:
            Dictionary with summary information
        """
        end_time = datetime.datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        return {
            "start_time": self.start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": duration,
            "action_count": len(self.actions),
            "finding_count": len(self.findings),
            "context_keys": list(self.context.keys()),
            "high_importance_findings": [
                f["title"] for f in self.findings 
                if f["importance"].lower() in ("high", "critical")
            ]
        }
    
    def print_report(self) -> None:
        """Print a formatted report of the agent's findings and actions."""
        print("\n" + "="*60)
        print(f"## SALESIQ AGENT INVESTIGATION REPORT")
        print("="*60)
        
        # Summary section
        summary = self.get_summary()
        print(f"\n## SUMMARY")
        print(f"Start time: {summary['start_time']}")
        print(f"Duration: {summary['duration_seconds']:.2f} seconds")
        print(f"Actions taken: {summary['action_count']}")
        print(f"Findings: {summary['finding_count']}")
        
        # Key findings section
        print(f"\n## KEY FINDINGS")
        critical_findings = [f for f in self.findings if f["importance"].lower() == "critical"]
        high_findings = [f for f in self.findings if f["importance"].lower() == "high"]
        
        if critical_findings:
            print("\n### CRITICAL FINDINGS")
            for i, finding in enumerate(critical_findings):
                print(f"\n{i+1}. {finding['title']}")
                print(f"   {finding['description']}")
        
        if high_findings:
            print("\n### HIGH IMPORTANCE FINDINGS")
            for i, finding in enumerate(high_findings):
                print(f"\n{i+1}. {finding['title']}")
                print(f"   {finding['description']}")
        
        if not critical_findings and not high_findings:
            print("\nNo high or critical findings identified.")
        
        # Medium findings
        medium_findings = [f for f in self.findings if f["importance"].lower() == "medium"]
        if medium_findings:
            print("\n### OTHER FINDINGS")
            for i, finding in enumerate(medium_findings):
                print(f"\n{i+1}. {finding['title']}")
        
        # Action log summary
        print(f"\n## ACTION LOG")
        for i, action in enumerate(self.actions):
            action_time = datetime.datetime.fromisoformat(action["timestamp"]).strftime("%H:%M:%S")
            print(f"{i+1}. [{action_time}] {action['type']}: {action['description']}")
        
        print("\n" + "="*60)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert scratchpad contents to a dictionary.
        
        Returns:
            Dictionary representation of the scratchpad
        """
        return {
            "actions": self.actions,
            "findings": self.findings,
            "context": self.context,
            "start_time": self.start_time.isoformat(),
            "summary": self.get_summary()
        }
    
    def to_json(self, pretty: bool = True) -> str:
        """
        Convert scratchpad contents to JSON.
        
        Args:
            pretty: Whether to format the JSON with indentation
            
        Returns:
            JSON string representation of the scratchpad
        """
        indent = 2 if pretty else None
        return json.dumps(self.to_dict(), indent=indent, default=str)
    
    def save_to_file(self, filename: str) -> None:
        """
        Save scratchpad contents to a JSON file.
        
        Args:
            filename: Path to the output file
        """
        with open(filename, "w") as f:
            f.write(self.to_json())
            
    @classmethod
    def from_json(cls, json_str: str) -> 'Scratchpad':
        """
        Create a Scratchpad instance from a JSON string.
        
        Args:
            json_str: JSON string representation of a scratchpad
            
        Returns:
            Scratchpad instance
        """
        data = json.loads(json_str)
        scratchpad = cls()
        
        # Restore data
        scratchpad.actions = data.get("actions", [])
        scratchpad.findings = data.get("findings", [])
        scratchpad.context = data.get("context", {})
        
        # Restore start time
        start_time_str = data.get("start_time")
        if start_time_str:
            scratchpad.start_time = datetime.datetime.fromisoformat(start_time_str)
        
        return scratchpad 
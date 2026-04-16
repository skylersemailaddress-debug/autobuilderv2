from typing import Dict, List, Optional


def build_planning_context(goal: str, durable_memory: Dict[str, dict], recent_summary: Optional[Dict] = None, repo_context: Optional[Dict] = None) -> Dict:
    """Build planning context from goal, durable memory, recent run summary, and repository metadata."""
    context = {
        "goal": goal,
        "memory_entries": durable_memory,
        "recent_summary": recent_summary,
        "repo_context": repo_context,
        "memory_insights": [],
        "repo_insights": [],
    }
    
    # Extract insights from memory
    if durable_memory:
        for key, value in durable_memory.items():
            if isinstance(value, dict):
                # Look for relevant patterns in memory
                if "goal" in value and any(word in goal.lower() for word in value["goal"].lower().split()):
                    context["memory_insights"].append(f"Similar goal found in memory: {value['goal']}")
                if "risk_level" in value and value["risk_level"] == "high":
                    context["memory_insights"].append("Previous high-risk action detected")
                if "confidence" in value and value["confidence"] < 0.8:
                    context["memory_insights"].append("Previous run had low confidence")
    
    # Add insights from recent summary
    if recent_summary:
        if recent_summary.get("repair_used"):
            context["memory_insights"].append("Recent run required repairs")
        if recent_summary.get("confidence", 1.0) < 0.9:
            context["memory_insights"].append("Recent run had reduced confidence")

    # Add insights from repository metadata
    if repo_context:
        if repo_context.get("framework_hints"):
            context["repo_insights"].append(
                f"Detected frameworks: {', '.join(repo_context['framework_hints'])}"
            )
        if repo_context.get("config_files"):
            context["repo_insights"].append(
                f"Key config files: {', '.join(repo_context['config_files'])}"
            )
        if repo_context.get("test_folders"):
            context["repo_insights"].append(
                f"Existing test folders: {', '.join(repo_context['test_folders'])}"
            )
    
    return context

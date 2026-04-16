from typing import Dict, List, Optional


def build_planning_context(goal: str, durable_memory: Dict[str, dict], recent_summary: Optional[Dict] = None) -> Dict:
    """Build planning context from goal, durable memory, and recent run summary."""
    context = {
        "goal": goal,
        "memory_entries": durable_memory,
        "recent_summary": recent_summary,
        "memory_insights": [],
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
    
    return context

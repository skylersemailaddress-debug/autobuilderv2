from __future__ import annotations

import hashlib
import json
from typing import List, Optional, Dict
from .task import Task


# ---------------------------------------------------------------------------
# Goal → task decomposition rules
# ---------------------------------------------------------------------------

_GOAL_DECOMPOSITION_RULES: list[tuple[list[str], list[tuple[str, str]]]] = [
    (
        ["delete", "destroy", "remove", "purge"],
        [
            ("validate_pre_delete_safety", "validation"),
            ("checkpoint_state_before_deletion", "mutation"),
            ("execute_deletion_with_approval", "destructive"),
            ("validate_post_delete_state", "validation"),
        ],
    ),
    (
        ["migrate", "refactor", "rename"],
        [
            ("analyze_current_state", "read"),
            ("plan_migration_steps", "creation"),
            ("apply_migration_with_checkpoint", "mutation"),
            ("validate_migrated_state", "validation"),
        ],
    ),
    (
        ["update", "modify", "edit", "write", "patch"],
        [
            ("analyze_target_for_update", "read"),
            ("generate_updated_artifact", "mutation"),
            ("validate_updated_artifact", "validation"),
        ],
    ),
    (
        ["validate", "proof", "check", "verify", "inspect", "audit"],
        [
            ("collect_validation_evidence", "read"),
            ("run_contract_checks", "validation"),
            ("emit_proof_bundle", "validation"),
        ],
    ),
    (
        ["build", "create", "add", "new", "generate"],
        [
            ("analyze_goal_and_context", "read"),
            ("generate_artifact", "creation"),
            ("validate_generated_artifact", "validation"),
        ],
    ),
]

_DEFAULT_TASKS: list[tuple[str, str]] = [
    ("analyze_goal", "read"),
    ("generate_artifact", "creation"),
    ("validate_output", "validation"),
]


def _infer_decomposition(goal: str) -> list[tuple[str, str]]:
    lowered = goal.lower()
    for keywords, task_specs in _GOAL_DECOMPOSITION_RULES:
        if any(kw in lowered for kw in keywords):
            return task_specs
    return _DEFAULT_TASKS


def _plan_signature(goal: str, task_titles: list[str]) -> str:
    payload = json.dumps({"goal": goal, "tasks": task_titles}, sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()[:20]


class Planner:
    def create_plan(self, goal: str, context: Optional[Dict] = None) -> Dict:
        """Create a decomposed, context-aware plan from a goal."""
        repo_context = context.get("repo_context") if context else None
        repo_mode = bool(repo_context)

        task_specs = _infer_decomposition(goal)
        tasks = [
            Task(
                task_id=f"task-{i + 1}",
                title=f"{spec[0].replace('_', ' ').capitalize()}: {goal[:40]}",
            )
            for i, spec in enumerate(task_specs)
        ]

        plan_signature = _plan_signature(goal, [t.title for t in tasks])

        plan_metadata: Dict = {
            "goal": goal,
            "task_count": len(tasks),
            "memory_used": context is not None,
            "memory_insights": [],
            "repo_mode": repo_mode,
            "repo_signals": {},
            "decomposition_strategy": (
                "goal_based" if task_specs != _DEFAULT_TASKS else "default"
            ),
            "plan_signature": plan_signature,
            "action_classes": [spec[1] for spec in task_specs],
        }

        if repo_context:
            if repo_context.get("framework_hints"):
                plan_metadata["repo_signals"]["framework_hints"] = repo_context["framework_hints"]
            if repo_context.get("config_files"):
                plan_metadata["repo_signals"]["config_files"] = repo_context["config_files"]
            if repo_context.get("test_folders"):
                plan_metadata["repo_signals"]["test_folders"] = repo_context["test_folders"]

        if context:
            insights = context.get("memory_insights", [])
            plan_metadata["memory_insights"] = insights

            if insights:
                for task in tasks:
                    task.result = {
                        "memory_context": f"Planning with {len(insights)} memory insights",
                        "insights": insights[:2],
                    }

        if repo_context:
            detected = repo_context.get("framework_hints", [])
            config_files = repo_context.get("config_files", [])
            test_folders = repo_context.get("test_folders", [])

            tasks[0].title = f"Analyze repository structure for: {goal[:40]}"
            tasks[0].result = {
                "repo_mode": True,
                "framework_hints": detected,
                "config_files": config_files,
                "test_folders": test_folders,
            }
            if len(tasks) >= 2:
                tasks[1].title = f"Generate artifact aligned with existing codebase: {goal[:30]}"
                tasks[1].result = {
                    "repo_mode": True,
                    "target_frameworks": detected,
                    "repository_signals": repo_context,
                }
            if len(tasks) >= 3:
                tasks[-1].title = f"Validate artifact against repository test structure: {goal[:30]}"
                tasks[-1].result = {
                    "repo_mode": True,
                    "test_folders": test_folders,
                }

        return {
            "tasks": tasks,
            "metadata": plan_metadata,
        }


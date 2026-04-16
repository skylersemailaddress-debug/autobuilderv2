from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Callable

from chat_builder.compiler import parse_conversation_intent, synthesize_spec_bundle, write_spec_bundle
from chat_builder.project_memory import ChatProjectMemoryStore
from chat_builder.steering import build_steering_decision


def run_chat_first_workflow(
    *,
    prompt: str,
    target_path: str,
    approve: bool,
    project_memory_root: str | Path,
    ship_runner: Callable[[str, str], dict],
) -> dict[str, object]:
    intent = parse_conversation_intent(prompt)
    steering = build_steering_decision(intent)
    spec_bundle = synthesize_spec_bundle(intent)

    memory_store = ChatProjectMemoryStore(project_memory_root)
    session_id = memory_store.derive_session_id(prompt)
    project_id = memory_store.derive_project_id(target_path)
    snapshot = memory_store.load_or_create(session_id=session_id, project_id=project_id)

    snapshot.conversation_turns.append(
        {
            "user": prompt,
            "assistant_summary": steering.simple_summary,
            "critical_questions": steering.critical_questions,
            "warnings": steering.warnings,
        }
    )
    snapshot.decisions.append(
        {
            "lane_id": intent.lane_id,
            "app_type": intent.app_type,
            "stack": intent.stack,
        }
    )
    snapshot.accepted_defaults.extend(intent.inferred_defaults)
    snapshot.tradeoffs.extend(steering.tradeoffs)

    if intent.unsupported_requests:
        snapshot.failures.append(
            {
                "type": "unsupported_request",
                "messages": intent.unsupported_requests,
            }
        )
        memory_path = memory_store.save(snapshot)
        return {
            "status": "unsupported",
            "conversation_surface": {
                "prompt": prompt,
                "assistant_message": "I found unsupported requests and paused before build.",
                "next_steps": ["Remove unsupported engine/stack requests and retry."],
            },
            "plan_summary": {
                "lane": intent.lane_id,
                "app_type": intent.app_type,
                "warnings": steering.warnings,
                "unsupported": intent.unsupported_requests,
            },
            "memory": {
                "session_id": session_id,
                "project_id": project_id,
                "memory_path": memory_path,
            },
        }

    preview_payload = {
        "lane": intent.lane_id,
        "app_type": intent.app_type,
        "stack": intent.stack,
        "defaults": intent.inferred_defaults,
        "tradeoffs": steering.tradeoffs,
        "critical_questions": steering.critical_questions,
        "spec_preview": spec_bundle.to_dict(),
        "simple_explanations": spec_bundle.explanations,
    }

    if not approve:
        memory_path = memory_store.save(snapshot)
        return {
            "status": "preview_ready" if not steering.critical_questions else "needs_clarification",
            "conversation_surface": {
                "prompt": prompt,
                "assistant_message": steering.simple_summary,
                "next_steps": steering.next_steps,
            },
            "plan_summary": preview_payload,
            "build_progress": ["preview_generated"],
            "memory": {
                "session_id": session_id,
                "project_id": project_id,
                "memory_path": memory_path,
            },
        }

    with TemporaryDirectory(prefix="autobuilder_chat_specs_") as temp_specs:
        spec_root = write_spec_bundle(spec_bundle, Path(temp_specs))
        build_progress = [
            "conversation_parsed",
            "spec_preview_approved",
            "build_started",
        ]
        try:
            ship_result = ship_runner(str(spec_root), target_path)
            build_progress.extend(["build_completed", "proof_ready"])
            snapshot.generated_components.append(
                {
                    "lane_id": intent.lane_id,
                    "archetype": ship_result.get("archetype"),
                    "proof_status": ship_result.get("proof_result", {}).get("status"),
                }
            )
            # Capture generated hardening artifacts/components for memory traceability.
            artifacts = ship_result.get("proof_result", {}).get("artifacts", {}).get("artifact_paths", {})
            if artifacts:
                snapshot.generated_components.append(
                    {
                        "generated_artifacts": sorted(artifacts.keys()),
                        "artifact_paths": artifacts,
                    }
                )
        except Exception as exc:  # pragma: no cover - defensive branch
            snapshot.failures.append({"type": "build_failure", "message": str(exc)})
            memory_path = memory_store.save(snapshot)
            return {
                "status": "build_failed",
                "conversation_surface": {
                    "prompt": prompt,
                    "assistant_message": "Build failed after preview approval.",
                    "next_steps": ["Review failure details and retry."],
                },
                "plan_summary": preview_payload,
                "build_progress": build_progress,
                "failure": str(exc),
                "memory": {
                    "session_id": session_id,
                    "project_id": project_id,
                    "memory_path": memory_path,
                },
            }

    repair_actions = ship_result.get("repair_actions_taken", {})
    if isinstance(repair_actions, dict) and repair_actions.get("repairs_applied", 0) > 0:
        snapshot.fixes.append(repair_actions)

    memory_path = memory_store.save(snapshot)

    return {
        "status": "built",
        "conversation_surface": {
            "prompt": prompt,
            "assistant_message": "Preview approved and build completed.",
            "next_steps": ["Review proof/readiness artifacts in the output path."],
        },
        "plan_summary": preview_payload,
        "build_progress": build_progress,
        "final_outputs": {
            "target_path": ship_result.get("final_target_path"),
            "proof_result": ship_result.get("proof_result", {}),
            "readiness_result": ship_result.get("readiness_result", {}),
            "packaged_app_artifact_summary": ship_result.get("packaged_app_artifact_summary", {}),
        },
        "ship_result": ship_result,
        "memory": {
            "session_id": session_id,
            "project_id": project_id,
            "memory_path": memory_path,
        },
    }

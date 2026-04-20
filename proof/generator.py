from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


def generate_proof_bundle(scorecard: Dict[str, Any], output_dir: str = "artifacts/proof") -> Dict[str, str]:
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)

    score_path = root / "scorecard.json"
    summary_path = root / "summary.txt"

    score_path.write_text(json.dumps(scorecard, indent=2, sort_keys=True), encoding="utf-8")

    summary = f"pass_rate={scorecard.get('pass_rate', 0)} total={scorecard.get('total', 0)}"
    summary_path.write_text(summary, encoding="utf-8")

    return {
        "scorecard": str(score_path),
        "summary": str(summary_path),
    }

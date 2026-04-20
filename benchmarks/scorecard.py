from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, Iterable, List


@dataclass
class BenchmarkResult:
    name: str
    passed: bool
    detail: Dict[str, Any]


def summarize(results: Iterable[BenchmarkResult]) -> Dict[str, Any]:
    items: List[BenchmarkResult] = list(results)
    passed = sum(1 for r in items if r.passed)
    total = len(items)
    return {
        "total": total,
        "passed": passed,
        "failed": total - passed,
        "pass_rate": (passed / total) if total else 0.0,
        "results": [asdict(r) for r in items],
    }

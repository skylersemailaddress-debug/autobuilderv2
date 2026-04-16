from dataclasses import dataclass
from typing import Dict


@dataclass
class Artifact:
    artifact_id: str
    artifact_type: str
    content: Dict
    created_at: str

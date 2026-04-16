from dataclasses import dataclass


@dataclass
class NexusMode:
    project_name: str = "Nexus0.5"
    repo_mode: bool = True
    memory_enabled: bool = True
    approvals_enabled: bool = True
    resumability_enabled: bool = True
    contract_validation_enabled: bool = True

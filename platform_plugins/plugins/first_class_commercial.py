from __future__ import annotations

from archetypes.catalog import ARCHETYPES, resolve_archetype
from generator.template_packs import first_class_validation_plan, generate_first_class_templates
from platform_hardening.proof_enrichment import enrich_proof_with_platform_hardening
from platform_hardening.repair_runtime import repair_with_lane_policy
from platform_plugins.contracts import PluginMetadata
from platform_plugins.registry import register_plugin
from stack_registry.registry import resolve_stack_bundle
from validator.generated_app import validate_generated_app
from validator.generated_app_proof import emit_generated_app_proof_artifacts


SUPPORTED_ARCHETYPES = sorted(ARCHETYPES.keys())
SUPPORTED_STACKS = {
    "frontend": ["react_next"],
    "backend": ["fastapi"],
    "database": ["postgres"],
    "deployment": ["docker_compose"],
}


class FirstClassCommercialArchetypePlugin:
    metadata = PluginMetadata(
        plugin_id="first_class_commercial.archetype",
        plugin_type="archetype",
        lane_id="first_class_commercial",
        capabilities=["archetype_resolution"],
        supported_archetypes=SUPPORTED_ARCHETYPES,
        supported_stacks=SUPPORTED_STACKS,
        priority=10,
    )

    def resolve_archetype(self, app_type: str) -> object:
        return resolve_archetype(app_type)


class FirstClassCommercialStackPlugin:
    metadata = PluginMetadata(
        plugin_id="first_class_commercial.stack",
        plugin_type="stack",
        lane_id="first_class_commercial",
        capabilities=["stack_resolution"],
        supported_archetypes=SUPPORTED_ARCHETYPES,
        supported_stacks=SUPPORTED_STACKS,
        priority=10,
    )

    def resolve_stack_bundle(self, selection: dict[str, str]) -> dict[str, object]:
        return resolve_stack_bundle(selection)


class FirstClassCommercialGenerationPlugin:
    metadata = PluginMetadata(
        plugin_id="first_class_commercial.generation",
        plugin_type="generation",
        lane_id="first_class_commercial",
        capabilities=["code_generation_backend"],
        supported_archetypes=SUPPORTED_ARCHETYPES,
        supported_stacks=SUPPORTED_STACKS,
        priority=10,
    )

    def generate_templates(self, ir):
        return generate_first_class_templates(ir)

    def validation_plan(self) -> list[str]:
        return first_class_validation_plan()


class FirstClassCommercialValidationPlugin:
    metadata = PluginMetadata(
        plugin_id="first_class_commercial.validation",
        plugin_type="validation",
        lane_id="first_class_commercial",
        capabilities=["generated_app_validation"],
        supported_archetypes=SUPPORTED_ARCHETYPES,
        supported_stacks=SUPPORTED_STACKS,
        priority=10,
    )

    def validate_generated_app(self, target_repo: str) -> dict[str, object]:
        return validate_generated_app(target_repo)


class FirstClassCommercialRepairPlugin:
    metadata = PluginMetadata(
        plugin_id="first_class_commercial.repair",
        plugin_type="repair",
        lane_id="first_class_commercial",
        capabilities=["bounded_repair_policy", "failure_classification"],
        supported_archetypes=SUPPORTED_ARCHETYPES,
        supported_stacks=SUPPORTED_STACKS,
        priority=10,
    )

    def repair_generated_app(self, target_repo, validation_report, expected_templates, max_repairs):
        return repair_with_lane_policy(
            lane_id=self.metadata.lane_id,
            target_repo=target_repo,
            validation_report=validation_report,
            expected_templates=expected_templates,
            max_repairs=max_repairs,
        )


class FirstClassCommercialPackagingPlugin:
    metadata = PluginMetadata(
        plugin_id="first_class_commercial.packaging",
        plugin_type="packaging",
        lane_id="first_class_commercial",
        capabilities=[
            "proof_artifacts",
            "packaging_targets",
            "runtime_verification",
            "pack_composition",
            "security_governance_contracts",
            "commerce_pack_contracts",
            "failure_corpus_logging",
            "deterministic_replay_harness",
        ],
        supported_archetypes=SUPPORTED_ARCHETYPES,
        supported_stacks=SUPPORTED_STACKS,
        priority=10,
    )

    def emit_proof_artifacts(
        self,
        target_repo: str,
        build_status: str,
        validation_report: dict[str, object],
        determinism: dict[str, object],
        repair_report: dict[str, object],
    ) -> dict[str, object]:
        base = emit_generated_app_proof_artifacts(
            target_repo=target_repo,
            build_status=build_status,
            validation_report=validation_report,
            determinism=determinism,
            repair_report=repair_report,
        )
        return enrich_proof_with_platform_hardening(
            lane_id=self.metadata.lane_id,
            target_repo=target_repo,
            determinism=determinism,
            validation_report=validation_report,
            repair_report=repair_report,
            proof_artifacts=base,
        )


register_plugin(FirstClassCommercialArchetypePlugin())
register_plugin(FirstClassCommercialStackPlugin())
register_plugin(FirstClassCommercialGenerationPlugin())
register_plugin(FirstClassCommercialValidationPlugin())
register_plugin(FirstClassCommercialRepairPlugin())
register_plugin(FirstClassCommercialPackagingPlugin())

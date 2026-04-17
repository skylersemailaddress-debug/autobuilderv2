from __future__ import annotations

# ---------------------------------------------------------------------------
# Commerce platform model definitions
# ---------------------------------------------------------------------------

PLAN_CATALOG: list[dict[str, object]] = [
    {
        "plan_id": "free",
        "display_name": "Free",
        "price_usd_monthly": 0,
        "trial_days": 0,
        "features": ["core_access"],
        "seat_limit": 1,
        "metered_limit_placeholder": None,
    },
    {
        "plan_id": "trial",
        "display_name": "Trial",
        "price_usd_monthly": 0,
        "trial_days": 14,
        "features": ["core_access", "pro_features_trial"],
        "seat_limit": 1,
        "metered_limit_placeholder": None,
    },
    {
        "plan_id": "pro",
        "display_name": "Pro",
        "price_usd_monthly": 29,
        "trial_days": 0,
        "features": ["core_access", "pro_features", "api_access"],
        "seat_limit": None,
        "metered_limit_placeholder": "api_calls_per_month",
    },
    {
        "plan_id": "enterprise",
        "display_name": "Enterprise",
        "price_usd_monthly": None,  # negotiated
        "trial_days": 0,
        "features": ["core_access", "pro_features", "api_access", "sso", "audit_logs", "dedicated_support"],
        "seat_limit": None,
        "metered_limit_placeholder": None,
    },
]

ENTITLEMENT_MODEL: dict[str, object] = {
    "model": "feature_entitlements",
    "supports_metered": True,
    "supports_seat_based": True,
    "supports_tier_gates": True,
    "feature_flags_integrated": True,
    "entitlement_check_contract": {
        "check_entitlement(user_id, feature_id)": "returns bool",
        "get_limits(subscription_id)": "returns dict of limit_key → value",
        "record_usage(subscription_id, metric, amount)": "metered usage tracking",
    },
}

BILLING_WEBHOOKS: dict[str, object] = {
    "event_types": [
        "subscription.created",
        "subscription.updated",
        "subscription.canceled",
        "invoice.paid",
        "invoice.payment_failed",
        "trial.will_end",
        "payment_method.updated",
        "customer.deleted",
    ],
    "signature_verification_required": True,
    "idempotency_required": True,
    "replay_protection": True,
    "handler_contract": {
        "verify_signature(raw_body, header)": "raises on invalid signature",
        "get_idempotency_key(event)": "returns str key for dedup",
        "dispatch_event(event_type, payload)": "routes to domain handler",
    },
}

ADMIN_BILLING_SURFACES: list[str] = [
    "admin/billing/overview",
    "admin/billing/subscriptions",
    "admin/billing/invoices",
    "admin/billing/plans",
    "admin/billing/payment-methods",
    "admin/billing/usage",
]


def build_commerce_pack_contract(lane_id: str) -> dict[str, object]:
    return {
        "lane_id": lane_id,
        "contract_version": "v2",
        "subscription_models": [p["plan_id"] for p in PLAN_CATALOG],
        "plan_catalog": PLAN_CATALOG,
        "checkout_billing_structure": {
            "provider_agnostic": True,
            "checkout_session_placeholder": True,
            "billing_customer_placeholder": True,
            "payment_method_placeholder": True,
            "stripe_adapter_scaffold": True,
        },
        "entitlements": ENTITLEMENT_MODEL,
        "billing_webhooks": BILLING_WEBHOOKS,
        "admin_billing_surfaces": ADMIN_BILLING_SURFACES,
        "invoice_trial_plan_concepts": {
            "invoice_generation_placeholder": True,
            "trial_lifecycle_placeholder": True,
            "plan_catalog_placeholder": True,
            "upgrade_downgrade_scaffold": True,
        },
        "commerce_maturity": "bounded_prototype",
        "known_limitations": [
            "payment provider credentials must be supplied by operator",
            "metered usage tracking requires operator data pipeline integration",
            "billing admin UI surfaces are scaffold/placeholder only",
        ],
    }


# ---------------------------------------------------------------------------
# Deeper generated commerce scaffolds
# ---------------------------------------------------------------------------

COMMERCE_GENERATED_SCAFFOLD: dict[str, object] = {
    "scaffold_version": "v2",
    "maturity": "bounded_prototype",
    "description": "Generated billing and entitlement code scaffolds",
    "generated_files": {
        "backend/api/billing.py": {
            "purpose": "Billing API: checkout, portal, webhook handler",
            "endpoints": [
                "POST /billing/checkout — create checkout session",
                "POST /billing/portal — create customer portal session",
                "POST /billing/webhooks — verified webhook receiver",
                "GET /billing/subscription — current subscription status",
                "POST /billing/cancel — cancel subscription",
            ],
            "security_controls": [
                "webhook_signature_verified before processing",
                "idempotency_key enforced on all mutation endpoints",
                "billing endpoints require authn",
                "billing_admin role required for admin operations",
            ],
        },
        "backend/api/entitlements.py": {
            "purpose": "Feature entitlement check and tier gate",
            "exports": [
                "check_entitlement(user_id, feature_id) → bool",
                "get_subscription_limits(subscription_id) → dict",
                "record_usage(subscription_id, metric, amount) → None",
                "require_feature(feature_id) → FastAPI dependency",
            ],
            "patterns": [
                "gate_by_plan_tier: free/trial/pro/enterprise checks",
                "metered_quota_enforcement",
                "trial_expiry_check",
            ],
        },
        "backend/api/admin_billing.py": {
            "purpose": "Admin billing surfaces: subscription management, usage reports",
            "role_guard": "require_role('admin') | require_role('billing_admin')",
            "endpoints": [
                "GET /admin/billing/subscriptions",
                "GET /admin/billing/invoices",
                "GET /admin/billing/usage",
                "PATCH /admin/billing/subscriptions/{id}/plan",
                "POST /admin/billing/subscriptions/{id}/credits",
            ],
        },
        "frontend/components/billing": {
            "purpose": "Billing UI components: plan selector, upgrade modal, usage dashboard",
            "components": [
                "PlanSelector — displays plan catalog with CTA",
                "UpgradeModal — upsell with feature comparison",
                "BillingDashboard — current plan, usage, invoices",
                "EntitlementGate — hides/disables features not in plan",
            ],
        },
    },
    "validation_checks": [
        "webhook_signature_verification_present",
        "idempotency_enforced_on_mutations",
        "entitlement_check_function_wired",
        "billing_endpoints_auth_guarded",
        "plan_catalog_consistent",
        "admin_billing_role_guarded",
    ],
}


ADMIN_OPERATIONS_SCAFFOLD: dict[str, object] = {
    "scaffold_version": "v1",
    "maturity": "bounded_prototype",
    "description": "Admin and billing operations surface scaffold",
    "admin_surfaces": {
        "user_management": {
            "endpoints": [
                "GET /admin/users — paginated user list",
                "GET /admin/users/{id} — user detail",
                "PATCH /admin/users/{id} — update user details or role",
                "DELETE /admin/users/{id} — soft-delete account",
                "POST /admin/users/{id}/suspend",
                "POST /admin/users/{id}/reinstate",
            ],
        },
        "org_management": {
            "endpoints": [
                "GET /admin/orgs",
                "GET /admin/orgs/{id}",
                "PATCH /admin/orgs/{id}",
                "GET /admin/orgs/{id}/members",
            ],
        },
        "audit_log_surface": {
            "endpoints": [
                "GET /admin/audit-log — filterable immutable log",
                "GET /admin/audit-log/export — CSV/JSON export hook",
            ],
            "fields": ["actor", "action", "scope", "outcome", "timestamp", "request_id"],
        },
    },
    "validation_checks": [
        "admin_surfaces_role_guarded",
        "audit_log_endpoint_present",
        "user_suspend_soft_delete_only",
    ],
}


def build_generated_commerce_scaffolds(lane_id: str) -> dict[str, object]:
    """Return full generated commerce scaffold definitions for a lane."""
    return {
        "lane_id": lane_id,
        "scaffold_version": "v2",
        "maturity": "bounded_prototype",
        "commerce_scaffold": COMMERCE_GENERATED_SCAFFOLD,
        "admin_operations_scaffold": ADMIN_OPERATIONS_SCAFFOLD,
        "combined_validation_checks": sorted(set(
            COMMERCE_GENERATED_SCAFFOLD["validation_checks"]
            + ADMIN_OPERATIONS_SCAFFOLD["validation_checks"]
        )),
        "known_limitations": [
            "payment provider credentials must be supplied by operator",
            "live webhook handling requires operator TLS endpoint",
            "metered usage tracking requires operator data pipeline",
            "admin surfaces are scaffold only; actual CMS/ERP not included",
        ],
    }


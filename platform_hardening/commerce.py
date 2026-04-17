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

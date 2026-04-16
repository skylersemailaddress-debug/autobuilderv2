from __future__ import annotations


def build_commerce_pack_contract(lane_id: str) -> dict[str, object]:
    return {
        "lane_id": lane_id,
        "subscription_models": ["free", "trial", "pro", "enterprise"],
        "checkout_billing_structure": {
            "provider_agnostic": True,
            "checkout_session_placeholder": True,
            "billing_customer_placeholder": True,
            "payment_method_placeholder": True,
        },
        "entitlements": {
            "model": "feature_entitlements",
            "supports_metered": True,
            "supports_seat_based": True,
            "supports_tier_gates": True,
        },
        "billing_webhooks": {
            "event_types": [
                "subscription.created",
                "subscription.updated",
                "subscription.canceled",
                "invoice.paid",
                "invoice.payment_failed",
                "trial.will_end",
            ],
            "signature_verification_required": True,
            "idempotency_required": True,
        },
        "admin_billing_surfaces": [
            "admin/billing/overview",
            "admin/billing/subscriptions",
            "admin/billing/invoices",
            "admin/billing/plans",
        ],
        "invoice_trial_plan_concepts": {
            "invoice_generation_placeholder": True,
            "trial_lifecycle_placeholder": True,
            "plan_catalog_placeholder": True,
        },
    }

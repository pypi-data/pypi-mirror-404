"""
Example: Integrating IdentityPlanKit with Payment Provider Webhooks.

This example shows how to sync payment provider events (Stripe, Paddle, etc.)
with IdentityPlanKit's plan state. IPK handles the plan/usage state - you handle
the payment provider integration.

Flow:
    Payment Provider (Stripe) --> Your Webhook Handler --> IPK Plan Service

IPK doesn't process payments - it manages:
    - Which plan a user is on
    - When their plan expires
    - Usage tracking against plan limits
    - Custom limit overrides

You are responsible for:
    - Setting up payment provider (Stripe account, products, prices)
    - Webhook signature verification
    - Mapping Stripe events to IPK service calls
"""

from datetime import date, datetime
from typing import Any
from uuid import UUID

from fastapi import FastAPI, Header, HTTPException, Request

# =============================================================================
# Assume you have IPK setup like in fastapi_integration.py
# =============================================================================

from identity_plan_kit import IdentityPlanKit, IdentityPlanKitConfig

# Your IPK instance (see fastapi_integration.py for full setup)
config = IdentityPlanKitConfig(
    database_url="postgresql+asyncpg://user:pass@localhost:5432/mydb",
    secret_key="your-secret-key-at-least-32-characters",
    google_client_id="your-google-client-id",
    google_client_secret="your-google-client-secret",
    google_redirect_uri="http://localhost:8000/auth/google/callback",
)
kit = IdentityPlanKit(config)

app = FastAPI(lifespan=kit.lifespan)
kit.setup(app)


# =============================================================================
# Your User-Stripe Mapping (you manage this)
# =============================================================================

async def get_user_id_from_stripe_customer(customer_id: str) -> UUID | None:
    """
    Look up your user by Stripe customer ID.

    You need to store this mapping when users subscribe.
    This is YOUR responsibility - IPK doesn't know about Stripe.

    Example implementation:
        async with session_factory() as session:
            result = await session.execute(
                select(UserModel.id).where(UserModel.stripe_customer_id == customer_id)
            )
            return result.scalar_one_or_none()
    """
    # Your implementation here
    raise NotImplementedError("Implement your user<->stripe mapping")


def get_plan_code_from_stripe_price(price_id: str) -> str:
    """
    Map Stripe price IDs to your plan codes.

    You define this mapping based on your Stripe product setup.
    """
    # Example mapping - customize for your Stripe products
    price_to_plan = {
        "price_free_monthly": "free",
        "price_pro_monthly": "pro",
        "price_pro_yearly": "pro",
        "price_enterprise_monthly": "enterprise",
        "price_enterprise_yearly": "enterprise",
    }
    return price_to_plan.get(price_id, "free")


# =============================================================================
# Stripe Webhook Verification (use stripe library in production)
# =============================================================================

STRIPE_WEBHOOK_SECRET = "whsec_your_webhook_secret"


async def verify_stripe_signature(
    payload: bytes,
    signature: str,
) -> dict[str, Any]:
    """
    Verify Stripe webhook signature and parse event.

    In production, use the official stripe library:
        import stripe
        event = stripe.Webhook.construct_event(payload, signature, STRIPE_WEBHOOK_SECRET)
    """
    # Example - use stripe library in production
    import json

    # In production:
    # import stripe
    # event = stripe.Webhook.construct_event(payload, signature, STRIPE_WEBHOOK_SECRET)

    # Simplified for example:
    return json.loads(payload)


# =============================================================================
# Webhook Handler
# =============================================================================

@app.post("/webhooks/stripe")
async def handle_stripe_webhook(
    request: Request,
    stripe_signature: str = Header(alias="Stripe-Signature"),
) -> dict[str, str]:
    """
    Handle Stripe webhook events.

    Stripe sends events like:
        - customer.subscription.created: New subscription
        - customer.subscription.updated: Plan change, renewal
        - customer.subscription.deleted: Cancellation
        - invoice.paid: Successful payment (good for renewal)
        - invoice.payment_failed: Payment failed
    """
    payload = await request.body()

    try:
        event = await verify_stripe_signature(payload, stripe_signature)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid signature: {e}") from e

    event_type = event["type"]
    data = event["data"]["object"]

    # Route to appropriate handler
    handlers = {
        "customer.subscription.created": handle_subscription_created,
        "customer.subscription.updated": handle_subscription_updated,
        "customer.subscription.deleted": handle_subscription_deleted,
        "invoice.paid": handle_invoice_paid,
        "invoice.payment_failed": handle_payment_failed,
    }

    handler = handlers.get(event_type)
    if handler:
        await handler(data)

    return {"status": "ok"}


# =============================================================================
# Event Handlers - Map Stripe events to IPK service calls
# =============================================================================

async def handle_subscription_created(data: dict[str, Any]) -> None:
    """
    Handle new subscription.

    Stripe event: customer.subscription.created

    This is called when:
        - User subscribes for the first time
        - User resubscribes after cancellation
    """
    customer_id = data["customer"]
    price_id = data["items"]["data"][0]["price"]["id"]
    current_period_end = data["current_period_end"]

    # Get your user ID from Stripe customer
    user_id = await get_user_id_from_stripe_customer(customer_id)
    if user_id is None:
        # Customer not found - log and skip
        # This shouldn't happen if you create the mapping on checkout
        return

    # Map Stripe price to your plan code
    plan_code = get_plan_code_from_stripe_price(price_id)

    # Convert Unix timestamp to date
    ends_at = datetime.fromtimestamp(current_period_end).date()

    # Assign the plan using IPK
    await kit.plan_service.assign_plan(
        user_id=user_id,
        plan_code=plan_code,
        ends_at=ends_at,
        expire_current=True,  # Expire any existing plan
    )


async def handle_subscription_updated(data: dict[str, Any]) -> None:
    """
    Handle subscription update.

    Stripe event: customer.subscription.updated

    This is called when:
        - User upgrades/downgrades plan
        - Subscription renews (period changes)
        - Subscription is set to cancel at period end
    """
    customer_id = data["customer"]
    price_id = data["items"]["data"][0]["price"]["id"]
    current_period_end = data["current_period_end"]
    cancel_at_period_end = data.get("cancel_at_period_end", False)

    user_id = await get_user_id_from_stripe_customer(customer_id)
    if user_id is None:
        return

    plan_code = get_plan_code_from_stripe_price(price_id)
    ends_at = datetime.fromtimestamp(current_period_end).date()

    # Check if this is a plan change or just a period extension
    current_plan = await kit.plan_service.get_user_plan_or_none(user_id)

    if current_plan is None or current_plan.plan_code != plan_code:
        # Plan changed - assign new plan
        await kit.plan_service.assign_plan(
            user_id=user_id,
            plan_code=plan_code,
            ends_at=ends_at,
            expire_current=True,
        )
    else:
        # Same plan - just extend the period
        await kit.plan_service.extend_plan(
            user_id=user_id,
            new_ends_at=ends_at,
        )

    # If cancellation is scheduled, you might want to track that
    # (IPK doesn't have a "cancel scheduled" state - plan just expires naturally)
    if cancel_at_period_end:
        # Optionally log or notify the user
        pass


async def handle_subscription_deleted(data: dict[str, Any]) -> None:
    """
    Handle subscription cancellation.

    Stripe event: customer.subscription.deleted

    This is called when:
        - Subscription is cancelled (after period ends or immediately)
        - Payment fails repeatedly and subscription is terminated
    """
    customer_id = data["customer"]

    user_id = await get_user_id_from_stripe_customer(customer_id)
    if user_id is None:
        return

    # Cancel immediately - plan becomes inactive
    await kit.plan_service.cancel_plan(
        user_id=user_id,
        immediate=True,
    )

    # Optionally: Assign a "free" plan so user still has something
    # await kit.plan_service.assign_plan(
    #     user_id=user_id,
    #     plan_code="free",
    #     expire_current=False,  # We just cancelled, no current plan
    # )


async def handle_invoice_paid(data: dict[str, Any]) -> None:
    """
    Handle successful payment.

    Stripe event: invoice.paid

    This is called when:
        - Initial subscription payment succeeds
        - Renewal payment succeeds

    This is a good place to:
        - Reset usage counters for new billing period
        - Extend plan if not already extended by subscription.updated
    """
    customer_id = data["customer"]
    subscription_id = data.get("subscription")

    if not subscription_id:
        # One-time payment, not subscription
        return

    user_id = await get_user_id_from_stripe_customer(customer_id)
    if user_id is None:
        return

    # Option 1: Reset usage on new billing period
    # This is useful for monthly quotas that reset each billing cycle
    await kit.plan_service.reset_usage(user_id)

    # Option 2: If you need to sync period end from invoice
    # (Usually subscription.updated handles this, but just in case)
    # period_end = data.get("period_end")
    # if period_end:
    #     ends_at = datetime.fromtimestamp(period_end).date()
    #     await kit.plan_service.extend_plan(user_id, ends_at)


async def handle_payment_failed(data: dict[str, Any]) -> None:
    """
    Handle failed payment.

    Stripe event: invoice.payment_failed

    This is called when:
        - Renewal payment fails
        - Initial payment fails

    You might want to:
        - Send notification to user
        - Set a grace period before cancelling
        - Downgrade to limited functionality

    Note: Stripe has built-in dunning (retry logic). The subscription
    isn't automatically cancelled on first failure. Wait for
    subscription.deleted event for actual cancellation.
    """
    customer_id = data["customer"]
    attempt_count = data.get("attempt_count", 1)

    user_id = await get_user_id_from_stripe_customer(customer_id)
    if user_id is None:
        return

    # Example: After 3 failed attempts, reduce limits
    if attempt_count >= 3:
        # Reduce their limits while payment is failing
        await kit.plan_service.update_plan_limits(
            user_id=user_id,
            custom_limits={
                "api_calls": 10,  # Reduced from normal limit
            },
        )

    # You should also notify the user to update payment method
    # await send_payment_failed_email(user_id)


# =============================================================================
# Manual Plan Management (Admin APIs)
# =============================================================================

@app.post("/admin/users/{user_id}/assign-plan")
async def admin_assign_plan(
    user_id: UUID,
    plan_code: str,
    ends_at: date | None = None,
) -> dict[str, Any]:
    """
    Admin endpoint to manually assign a plan.

    Useful for:
        - Customer support overrides
        - Enterprise contracts
        - Trial extensions
        - Testing
    """
    # Add your admin auth check here
    # if not is_admin(current_user):
    #     raise HTTPException(403)

    user_plan = await kit.plan_service.assign_plan(
        user_id=user_id,
        plan_code=plan_code,
        ends_at=ends_at,
    )

    return {
        "user_id": str(user_id),
        "plan_code": user_plan.plan_code,
        "ends_at": str(user_plan.ends_at),
    }


@app.post("/admin/users/{user_id}/extend-plan")
async def admin_extend_plan(
    user_id: UUID,
    days: int,
) -> dict[str, Any]:
    """
    Admin endpoint to extend a user's plan.

    Useful for:
        - Compensating for downtime
        - Trial extensions
        - Customer goodwill
    """
    current_plan = await kit.plan_service.get_user_plan(user_id)
    new_ends_at = date(
        current_plan.ends_at.year,
        current_plan.ends_at.month,
        current_plan.ends_at.day,
    )
    # Add days
    from datetime import timedelta
    new_ends_at = new_ends_at + timedelta(days=days)

    updated_plan = await kit.plan_service.extend_plan(
        user_id=user_id,
        new_ends_at=new_ends_at,
    )

    return {
        "user_id": str(user_id),
        "new_ends_at": str(updated_plan.ends_at),
        "days_added": days,
    }


@app.post("/admin/users/{user_id}/reset-usage")
async def admin_reset_usage(
    user_id: UUID,
    feature_code: str | None = None,
) -> dict[str, str]:
    """
    Admin endpoint to reset a user's usage.

    Useful for:
        - Customer support (user hit limit due to bug)
        - Testing
        - Manual billing period sync
    """
    await kit.plan_service.reset_usage(
        user_id=user_id,
        feature_code=feature_code,
    )

    return {
        "status": "reset",
        "user_id": str(user_id),
        "feature": feature_code or "all",
    }


@app.post("/admin/users/{user_id}/custom-limits")
async def admin_set_custom_limits(
    user_id: UUID,
    limits: dict[str, int],
) -> dict[str, Any]:
    """
    Admin endpoint to set custom limits for a user.

    Useful for:
        - Enterprise contracts with custom quotas
        - Promotional offers
        - Power users who need more
    """
    updated_plan = await kit.plan_service.update_plan_limits(
        user_id=user_id,
        custom_limits=limits,
    )

    return {
        "user_id": str(user_id),
        "custom_limits": updated_plan.custom_limits,
    }


# =============================================================================
# Summary: Complete Webhook Flow
# =============================================================================

"""
STRIPE WEBHOOK FLOW:

1. User clicks "Subscribe to Pro" on your frontend
2. You create a Stripe Checkout Session with:
   - customer: stripe_customer_id (create or get existing)
   - price: price_pro_monthly
   - success_url: /payment-success
   - cancel_url: /pricing

3. User completes payment on Stripe

4. Stripe sends webhook: customer.subscription.created
   - You receive it at POST /webhooks/stripe
   - You call: kit.plan_service.assign_plan(user_id, "pro", ends_at)

5. User now has access to Pro features
   - kit.plan_service.check_feature_access(user_id, "advanced_analytics")
   - kit.plan_service.check_and_consume_quota(user_id, "api_calls")

6. Monthly renewal:
   - Stripe sends: invoice.paid
   - You call: kit.plan_service.reset_usage(user_id)
   - Stripe sends: customer.subscription.updated
   - You call: kit.plan_service.extend_plan(user_id, new_period_end)

7. User cancels:
   - Stripe sends: customer.subscription.deleted
   - You call: kit.plan_service.cancel_plan(user_id, immediate=True)

That's it! IPK handles the plan state, you handle Stripe.
"""


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

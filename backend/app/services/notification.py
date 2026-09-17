from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.models import DecommissionedNumber, ServiceProvider, ProviderNotification
from app.core.privacy import generate_pseudonym_ref
from app.adapters.provider_adapter import provider_adapter

async def dispatch_notifications_for_number(
    db: AsyncSession,
    number: DecommissionedNumber,
    target_provider_codes: Optional[List[str]] = None
) -> List[ProviderNotification]:
    """
    Creates and dispatches pseudonymized remediation notifications to registered providers.
    """
    query = select(ServiceProvider).where(ServiceProvider.status == "ACTIVE")
    if target_provider_codes and len(target_provider_codes) > 0:
        query = query.where(ServiceProvider.code.in_([c.upper() for c in target_provider_codes]))

    result = await db.execute(query)
    providers = result.scalars().all()

    created_notifications = []
    now = datetime.now(timezone.utc)

    for provider in providers:
        pseudonym = generate_pseudonym_ref(f"{number.id}-{provider.id}")
        
        # Dispatch through adapter
        dispatch_result = await provider_adapter.dispatch_decommission_event(
            provider_name=provider.name,
            webhook_url=provider.webhook_url,
            pseudonym_ref=pseudonym,
            carrier=number.carrier,
            timestamp=now
        )

        notif = ProviderNotification(
            number_id=number.id,
            provider_id=provider.id,
            provider=provider,
            pseudonym_ref=pseudonym,
            notification_type="DECOMMISSION_ALERT",
            status=dispatch_result.get("status", "SENT"),
            sent_at=now,
            response_payload=dispatch_result.get("response_payload"),
            error_message=dispatch_result.get("error_message")
        )
        db.add(notif)
        created_notifications.append(notif)

        # Update provider stats
        provider.notification_count = (provider.notification_count or 0) + 1
        provider.unresolved_count = (provider.unresolved_count or 0) + 1

    await db.commit()
    return created_notifications

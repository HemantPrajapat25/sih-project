"""
NumberGuard — Adapter Factory (Phase 3)
Provides instantiated adapters based on environment settings and provider categories.
Allows seamless swapping between Mock (local dev / CI) and Real (production) integrations.
"""
from __future__ import annotations

from typing import Optional
from app.core.config import settings

from app.adapters.base import (
    DigitalServiceProviderAdapter,
    TelecomProviderAdapter,
    EmailAdapter,
    PhoneIntelligenceAdapter,
)

# Mock implementations
from app.adapters.mock.bank import MockBankProvider
from app.adapters.mock.fintech import MockFintechProvider
from app.adapters.mock.ecommerce import MockEcommerceProvider
from app.adapters.mock.telecom import MockTelecomProvider
from app.adapters.mock.email import MockEmailProvider
from app.adapters.mock.phone_intel import MockPhoneIntelligenceProvider

# Real implementations
from app.adapters.real.twilio import TwilioPhoneIntelAdapter
from app.adapters.real.smtp import SmtpEmailAdapter

# Singletons for mock state management and testing
_mock_bank = MockBankProvider()
_mock_fintech = MockFintechProvider()
_mock_ecommerce = MockEcommerceProvider()
_mock_telecom = MockTelecomProvider()
_mock_email = MockEmailProvider()
_mock_phone_intel = MockPhoneIntelligenceProvider()


def get_provider_adapter(category: str = "GENERAL") -> DigitalServiceProviderAdapter:
    """
    Returns appropriate digital service provider adapter based on category.
    """
    cat_upper = category.upper()
    if cat_upper in ("BANKING", "FINANCIAL"):
        return _mock_bank
    elif cat_upper in ("FINTECH", "WALLET", "PAYMENT", "UPI"):
        return _mock_fintech
    elif cat_upper in ("ECOMMERCE", "DELIVERY", "SHOPPING"):
        return _mock_ecommerce
    else:
        # Default mock bank / general unlinker
        return _mock_bank


def get_telecom_adapter() -> TelecomProviderAdapter:
    """
    Returns telecom switch adapter (HLR quarantine / release).
    """
    return _mock_telecom


def get_phone_intel_adapter() -> PhoneIntelligenceAdapter:
    """
    Returns Phone Intelligence Adapter.
    If PHONE_LOOKUP_PROVIDER == "twilio" and credentials present, returns Twilio;
    otherwise returns MockPhoneIntelligenceProvider.
    """
    if (
        settings.PHONE_LOOKUP_PROVIDER.lower() == "twilio"
        and settings.TWILIO_ACCOUNT_SID
        and settings.TWILIO_AUTH_TOKEN
    ):
        return TwilioPhoneIntelAdapter()
    return _mock_phone_intel


def get_email_adapter() -> EmailAdapter:
    """
    Returns Email Adapter.
    If EMAIL_PROVIDER == "smtp" and credentials present, returns SmtpEmailAdapter;
    otherwise returns MockEmailProvider.
    """
    if (
        settings.EMAIL_PROVIDER.lower() == "smtp"
        and settings.SMTP_HOST
        and settings.SMTP_USER
    ):
        return SmtpEmailAdapter()
    return _mock_email


def reset_all_mock_states():
    """Utility function to clear in-memory state across all mock adapters (used in test setup/teardown)."""
    _mock_bank.reset_state()
    _mock_fintech.reset_state()
    _mock_ecommerce.reset_state()
    _mock_telecom.reset_state()
    _mock_email.clear()
    _mock_phone_intel.clear_overrides()

"""
NumberGuard — Mock Adapters Package (Phase 3)
Realistic simulations for digital service providers, telecom switches, email, and phone intelligence.
"""
from .bank import MockBankProvider
from .fintech import MockFintechProvider
from .ecommerce import MockEcommerceProvider
from .telecom import MockTelecomProvider
from .email import MockEmailProvider
from .phone_intel import MockPhoneIntelligenceProvider

__all__ = [
    "MockBankProvider",
    "MockFintechProvider",
    "MockEcommerceProvider",
    "MockTelecomProvider",
    "MockEmailProvider",
    "MockPhoneIntelligenceProvider",
]

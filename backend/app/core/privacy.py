import re
import hmac
import hashlib
from typing import Optional
from app.core.config import settings

def normalize_phone_number(raw_phone: str) -> str:
    """
    Normalizes phone number to standard E.164 format.
    E.g. "9876543210" -> "+919876543210", "+91 98765-43210" -> "+919876543210"
    """
    cleaned = re.sub(r"[^\d+]", "", raw_phone)
    if not cleaned.startswith("+"):
        if len(cleaned) == 10:
            cleaned = "+91" + cleaned
        elif len(cleaned) == 12 and cleaned.startswith("91"):
            cleaned = "+" + cleaned
        else:
            cleaned = "+" + cleaned
    return cleaned

def mask_phone_number(phone: str) -> str:
    """
    Masks a normalized phone number preserving country code and last 4 digits.
    Never reveals the full subscriber number.
    Example: '+919876543210' -> '+91 98**** *210'
    """
    if not phone:
        return "Unknown"
    
    cleaned = normalize_phone_number(phone)
    # If standard 10 digit national format with +91:
    if len(cleaned) >= 12 and cleaned.startswith("+91"):
        country = "+91"
        national = cleaned[3:]
        # show first 2, mask middle, show last 3 or 4
        masked_part = f"{national[:2]}**** *{national[-3:]}"
        return f"{country} {masked_part}"
    
    # Generic fallback masking:
    if len(cleaned) > 6:
        return f"{cleaned[:3]}****{cleaned[-3:]}"
    return "****"

def compute_phone_hash(phone: str) -> str:
    """
    Produces an HMAC-SHA256 hash using a private server-side pepper.
    Provides collision resistance for indexing and lookup without exposing the plaintext number.
    """
    normalized = normalize_phone_number(phone)
    return hmac.new(
        settings.PHONE_HASH_PEPPER.encode("utf-8"),
        normalized.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

def generate_pseudonym_ref(number_id: str) -> str:
    """
    Generates a secure, non-reversible public challenge reference for service providers.
    """
    digest = hashlib.sha256(f"NG-REF-{number_id}-{settings.SECRET_KEY}".encode("utf-8")).hexdigest()[:12].upper()
    return f"REF-{digest}"

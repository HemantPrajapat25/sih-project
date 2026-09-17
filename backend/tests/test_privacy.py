from app.core.privacy import (
    normalize_phone_number,
    mask_phone_number,
    compute_phone_hash,
    generate_pseudonym_ref
)

def test_normalize_phone_number():
    assert normalize_phone_number("9876543210") == "+919876543210"
    assert normalize_phone_number("+91 98765-43210") == "+919876543210"
    assert normalize_phone_number("919876543210") == "+919876543210"

def test_mask_phone_number_privacy():
    raw = "+919876543210"
    masked = mask_phone_number(raw)
    
    # Must never contain middle 4-5 digits
    assert "7654" not in masked
    assert masked.startswith("+91 98")
    assert masked.endswith("210")
    assert "****" in masked

def test_compute_phone_hash_deterministic():
    phone1 = "+919876543210"
    phone2 = "9876543210" # should normalize to same
    hash1 = compute_phone_hash(phone1)
    hash2 = compute_phone_hash(phone2)
    assert hash1 == hash2
    assert len(hash1) == 64 # SHA-256 hex string

def test_pseudonym_ref_generation():
    ref1 = generate_pseudonym_ref("test-num-1")
    ref2 = generate_pseudonym_ref("test-num-2")
    assert ref1.startswith("REF-")
    assert ref1 != ref2
    assert len(ref1) == 16

from datetime import datetime, timedelta, timezone
from app.services.risk_engine import calculate_risk

class DummyProvider:
    def __init__(self, cat):
        self.category = cat

class DummyNotification:
    def __init__(self, cat, status):
        self.provider = DummyProvider(cat)
        self.status = status

def test_risk_calculation_banking_unremediated():
    now = datetime.now(timezone.utc)
    decom = now - timedelta(days=10)
    cooling_end = decom + timedelta(days=60)

    # 1 unacknowledged banking provider notification
    notifs = [DummyNotification("BANKING", "SENT")]
    score, level, eligibility, factors = calculate_risk(
        decommissioned_at=decom,
        cooling_end_date=cooling_end,
        notifications=notifs,
        historical_recycles=0
    )

    # Active banking alert must block reallocation
    assert eligibility == "BLOCKED"
    assert score > 30
    assert any(f["name"] == "Banking & Fintech Associations" for f in factors)

def test_risk_calculation_cooling_complete_eligible():
    now = datetime.now(timezone.utc)
    decom = now - timedelta(days=65)
    cooling_end = decom + timedelta(days=60) # cooling ended 5 days ago

    # All providers remediated
    notifs = [
        DummyNotification("BANKING", "REMEDIATED"),
        DummyNotification("ECOMMERCE", "REMEDIATED")
    ]
    score, level, eligibility, factors = calculate_risk(
        decommissioned_at=decom,
        cooling_end_date=cooling_end,
        notifications=notifs,
        historical_recycles=0
    )

    assert eligibility == "ELIGIBLE"
    assert level == "LOW"
    assert score <= 25

from datetime import datetime, timezone
from typing import List, Dict, Any, Tuple
from app.core.config import settings

def calculate_risk(
    decommissioned_at: datetime,
    cooling_end_date: datetime,
    notifications: List[Any],
    historical_recycles: int = 0
) -> Tuple[int, str, str, List[Dict[str, Any]]]:
    """
    Computes deterministic, privacy-preserving risk assessment.
    Returns:
    (score: 0-100, risk_level: str, eligibility: str, factors: List[Dict])
    """
    now = datetime.now(timezone.utc)
    if decommissioned_at.tzinfo is None:
        decommissioned_at = decommissioned_at.replace(tzinfo=timezone.utc)
    if cooling_end_date.tzinfo is None:
        cooling_end_date = cooling_end_date.replace(tzinfo=timezone.utc)

    total_cooling_seconds = max((cooling_end_date - decommissioned_at).total_seconds(), 1)
    elapsed_seconds = max((now - decommissioned_at).total_seconds(), 0)
    cooling_progress_ratio = min(elapsed_seconds / total_cooling_seconds, 1.0)
    cooling_completed = now >= cooling_end_date

    # 1. Banking & Fintech factor (Max 40 points)
    banking_count = 0
    fintech_count = 0
    unremediated_banking = 0
    unremediated_other = 0

    for notif in notifications:
        cat = getattr(notif.provider, "category", "") if hasattr(notif, "provider") and notif.provider else ""
        status = getattr(notif, "status", "SENT")
        is_done = status in ["REMEDIATED", "ACKNOWLEDGED"]

        if cat == "BANKING":
            banking_count += 1
            if not is_done:
                unremediated_banking += 1
        elif cat == "FINTECH":
            fintech_count += 1
            if not is_done:
                unremediated_banking += 1
        else:
            if not is_done:
                unremediated_other += 1

    banking_score = 0
    if unremediated_banking > 0:
        banking_score = min(unremediated_banking * 20, 40)
    elif banking_count > 0 and unremediated_banking == 0:
        banking_score = 5 # small residual weight until cooling completes

    # 2. Cooling Progress Decay factor (Max 30 points)
    # Starts at 30, decays toward 0 as cooling period finishes
    cooling_score = int((1.0 - cooling_progress_ratio) * 30)

    # 3. Provider Response SLA factor (Max 20 points)
    sla_score = min(unremediated_other * 7, 20)

    # 4. Recycling Velocity factor (Max 10 points)
    velocity_score = min(historical_recycles * 5, 10)

    total_score = min(banking_score + cooling_score + sla_score + velocity_score, 100)

    # Determine Risk Level
    if total_score <= settings.RISK_THRESHOLD_LOW:
        risk_level = "LOW"
    elif total_score <= settings.RISK_THRESHOLD_MEDIUM:
        risk_level = "MEDIUM"
    elif total_score <= settings.RISK_THRESHOLD_HIGH:
        risk_level = "HIGH"
    else:
        risk_level = "CRITICAL"

    # Determine Allocation Recommendation
    if unremediated_banking > 0:
        eligibility = "BLOCKED"
        recommendation_reason = f"Active unacknowledged banking alerts ({unremediated_banking})"
    elif not cooling_completed:
        eligibility = "COOLING_HOLD"
        days_remaining = max((cooling_end_date - now).days, 1)
        recommendation_reason = f"Cooling period active ({days_remaining} days remaining)"
    elif total_score > settings.RISK_THRESHOLD_HIGH:
        eligibility = "MANUAL_REVIEW_REQUIRED"
        recommendation_reason = f"Elevated residual risk score ({total_score})"
    else:
        eligibility = "ELIGIBLE"
        recommendation_reason = "Cooling completed & all high-risk service remediations confirmed"

    factors = [
        {
            "name": "Banking & Fintech Associations",
            "weight": 40,
            "score_contribution": banking_score,
            "description": f"{banking_count} banking/fintech links detected ({unremediated_banking} unacknowledged)"
        },
        {
            "name": "Cooling Period Progress",
            "weight": 30,
            "score_contribution": cooling_score,
            "description": f"{int(cooling_progress_ratio * 100)}% of quarantine period elapsed"
        },
        {
            "name": "General Service Remediation SLA",
            "weight": 20,
            "score_contribution": sla_score,
            "description": f"{unremediated_other} general provider acknowledgements pending"
        },
        {
            "name": "Historical Recycling Velocity",
            "weight": 10,
            "score_contribution": velocity_score,
            "description": f"Recycled {historical_recycles} times in telecom record history"
        }
    ]

    return total_score, risk_level, eligibility, factors

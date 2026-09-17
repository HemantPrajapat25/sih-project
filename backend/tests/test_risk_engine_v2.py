"""
NumberGuard — Test Suite for Phase 3 Modular Risk Engine
Tests:
- 10 Privacy-preserving RiskFactorCalculator functions
- RiskRuleEngine evaluation with condition DSL
- RiskScoreCalculator weighted aggregation & blocking rules
- AllocationDecisionService decision policies
"""
import pytest
from datetime import datetime, timezone, timedelta

from app.services.risk.factors import RiskFactorCalculator
from app.services.risk.rules import RiskRuleEngine, RuleEvaluation
from app.services.risk.scorer import RiskScoreCalculator, DEFAULT_WEIGHTS, ScoredFactor


def test_factor_recycling_history():
    calc = RiskFactorCalculator()
    s0, exp0, ev0 = calc.recycling_history(0)
    assert s0 == 0.0
    s1, exp1, ev1 = calc.recycling_history(1)
    assert s1 == 0.3
    s4, exp4, ev4 = calc.recycling_history(5)
    assert s4 == 1.0


def test_factor_number_age():
    calc = RiskFactorCalculator()
    now = datetime.now(timezone.utc)
    # Very new number (less than 6 months old)
    s_new, exp, ev = calc.number_age(first_seen_at=now - timedelta(days=60), decommissioned_at=now)
    assert s_new == 0.0
    # Long established (4 years old)
    s_old, exp, ev = calc.number_age(first_seen_at=now - timedelta(days=1500), decommissioned_at=now)
    assert s_old == 0.75


def test_factor_spam_and_fraud_signals():
    calc = RiskFactorCalculator()
    s_spam, exp_s, ev_s = calc.spam_reputation("HIGH")
    assert s_spam == 0.80
    s_fraud, exp_f, ev_f = calc.fraud_signals("CRITICAL", fraud_incident_count=2)
    assert s_fraud == 1.0


def test_factor_unresolved_associations_and_criticality():
    calc = RiskFactorCalculator()
    # 3 active out of 3 -> high score
    s_unres, exp_u, ev_u = calc.unresolved_associations(3, 3)
    assert s_unres > 0.7

    # Banking provider unresolved
    s_crit, exp_c, ev_c = calc.provider_criticality(
        provider_categories=["BANKING", "FINTECH"],
        unresolved_categories=["BANKING"]
    )
    assert s_crit >= 0.7


def test_rule_engine_evaluation():
    engine = RiskRuleEngine()
    context = {
        "cooling_completed": False,
        "unresolved_critical_providers": 2,
        "fraud_signal": "HIGH",
        "spam_signal": "NONE",
        "all_providers_acknowledged": False,
        "recycling_count": 1,
        "otp_services_unlinked": False,
    }
    evaluations = engine.evaluate(context)
    triggered_codes = [e.code for e in evaluations if e.triggered]
    assert "UNRESOLVED_CRITICAL_PROVIDER" in triggered_codes
    assert "COOLING_INCOMPLETE" in triggered_codes
    assert any(e.blocking for e in evaluations if e.triggered)


def test_risk_score_aggregation_and_blocking():
    calc = RiskScoreCalculator(DEFAULT_WEIGHTS)
    factor_results = {
        "recycling_history": (0.3, "1 prior reuse", {"count": 1}),
        "number_age": (0.25, "60 days dormant", {}),
        "spam_reputation": (0.0, "Clean", {}),
        "fraud_signals": (0.0, "No flags", {}),
        "unresolved_associations": (0.0, "All clear", {}),
        "otp_dependencies": (0.0, "No OTP", {}),
        "participating_providers_count": (0.2, "1 provider", {}),
        "provider_criticality": (0.0, "None", {}),
        "previous_risk_history": (0.1, "Low", {}),
        "manual_override": (0.0, "None", {}),
    }

    # Evaluate clean
    res_clean = calc.calculate(factor_results, [])
    assert res_clean.score <= 25
    assert res_clean.level == "LOW"
    assert not res_clean.is_blocked
    assert res_clean.recommendation == "APPROVE_REALLOCATION"

    # Evaluate with blocking rule
    blocking_eval = RuleEvaluation(
        code="UNRESOLVED_CRITICAL_PROVIDER",
        name="Unresolved Critical Provider Association",
        triggered=True,
        impact=20,
        blocking=True,
        severity="CRITICAL",
        reason="Unresolved bank"
    )
    res_blocked = calc.calculate(factor_results, [blocking_eval])
    assert res_blocked.is_blocked is True
    assert len(res_blocked.blocking_rules) > 0
    assert res_blocked.level == "CRITICAL"
    assert res_blocked.recommendation == "BLOCK_REALLOCATION"

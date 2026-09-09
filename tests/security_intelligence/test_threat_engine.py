from security_intelligence.soc import ThreatLevel, compute_threat_score
from security_intelligence.soc.threat_scoring import DEFAULT_WEIGHTS


def test_full_signal_coverage():
    signals = {k: 0.5 for k in DEFAULT_WEIGHTS}
    assessment = compute_threat_score(signals)
    assert assessment.coverage == 1.0
    assert assessment.missing_signals == []
    assert 0 <= assessment.score <= 100


def test_partial_coverage_excludes_missing_and_renormalizes():
    signals = {"mars_severity": 0.9}
    assessment = compute_threat_score(signals)
    assert assessment.coverage < 1.0
    assert "Layer 1 anomaly severity" in assessment.missing_signals
    # With only one signal available, its normalized weight is 1.0.
    assert len(assessment.contributing_factors) == 1
    assert assessment.contributing_factors[0]["normalized_weight"] == 1.0


def test_no_mars_signal():
    signals = {"layer1_severity": 0.5, "incident_severity": 0.5}
    assessment = compute_threat_score(signals)
    assert "MARS evidence" in assessment.missing_signals
    assert all(f["raw_signal"] != "mars_severity" for f in assessment.contributing_factors)


def test_no_attack_success_rate():
    signals = {"mars_severity": 0.5}
    assessment = compute_threat_score(signals)
    assert "Attack success rate" in assessment.missing_signals


def test_high_threat_score_and_level():
    signals = {k: 0.95 for k in DEFAULT_WEIGHTS}
    assessment = compute_threat_score(signals)
    assert assessment.level == ThreatLevel.CRITICAL
    assert assessment.score > 85


def test_low_threat_score_and_level():
    signals = {k: 0.02 for k in DEFAULT_WEIGHTS}
    assessment = compute_threat_score(signals)
    assert assessment.level == ThreatLevel.LOW
    assert assessment.score < 30


def test_no_signals_at_all_is_explicit_not_fabricated():
    assessment = compute_threat_score({})
    assert assessment.coverage == 0.0
    assert assessment.confidence == 0.0
    assert assessment.score == 0.0
    assert set(assessment.missing_signals) == set(
        ["Suspicious client ratio", "Layer 1 anomaly severity", "MARS evidence",
         "Incident severity", "Attack success rate", "Quarantine activity",
         "Trust distribution (Team A)", "Risk distribution (Team A)"]
    )


def test_explainability_every_assessment_has_factors_or_missing():
    signals = {"mars_severity": 0.6, "layer1_severity": 0.4}
    assessment = compute_threat_score(signals)
    assert len(assessment.contributing_factors) > 0
    for factor in assessment.contributing_factors:
        assert "name" in factor and "contribution" in factor and "value" in factor


def test_weights_renormalize_to_sum_one_over_available_signals():
    signals = {"mars_severity": 0.5, "layer1_severity": 0.5}
    assessment = compute_threat_score(signals)
    total_weight = sum(f["normalized_weight"] for f in assessment.contributing_factors)
    assert abs(total_weight - 1.0) < 1e-6


def test_missing_signal_never_silently_zero():
    # Score with mars only vs mars+zero others should differ: zero != missing.
    only_mars = compute_threat_score({"mars_severity": 0.9})
    with_zeroes = compute_threat_score({k: (0.9 if k == "mars_severity" else 0.0) for k in DEFAULT_WEIGHTS})
    assert only_mars.score != with_zeroes.score
    assert only_mars.coverage != with_zeroes.coverage

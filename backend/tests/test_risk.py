"""Tests for risk engine"""
import pytest
from app.risk import risk_engine

def test_calculate_risk_score_no_target():
    """Test risk score calculation with no target"""
    score, reasons = risk_engine.calculate_risk_score("", [], [])
    assert score == 0
    assert "No target specified" in reasons[0]

def test_calculate_risk_score_with_target_match():
    """Test risk score when target is found in documents"""
    target = "0xDEMO123"
    docs = [
        {"text": f"Wallet {target} involved in hack", "source": "NewsAPI"}
    ]
    
    score, reasons = risk_engine.calculate_risk_score(target, docs, [])
    assert score >= 70  # Target found adds 70 points
    assert any(target in reason for reason in reasons)

def test_calculate_risk_score_with_ofac():
    """Test risk score with OFAC source"""
    target = "test_entity"
    docs = [
        {"text": "Some content", "source": "OFAC"}
    ]
    
    score, reasons = risk_engine.calculate_risk_score(target, docs, [])
    assert score >= 40  # OFAC source adds 40 points

def test_calculate_risk_score_with_high_value_transaction():
    """Test risk score with high-value transaction"""
    target = "0xABC"
    transactions = [
        {"amount": 15000}  # Above threshold
    ]
    
    score, reasons = risk_engine.calculate_risk_score(target, [], transactions)
    assert score >= 15  # High-value transaction adds points

def test_risk_category():
    """Test risk category determination"""
    assert risk_engine.get_risk_category(80) == "HIGH"
    assert risk_engine.get_risk_category(50) == "MEDIUM"
    assert risk_engine.get_risk_category(20) == "LOW"

def test_recommendations():
    """Test recommendation generation"""
    high_risk_recs = risk_engine.get_recommendations(80, ["High risk"])
    assert any("block" in rec.lower() or "freeze" in rec.lower() for rec in high_risk_recs)
    
    low_risk_recs = risk_engine.get_recommendations(20, ["Low risk"])
    assert any("standard" in rec.lower() or "continue" in rec.lower() for rec in low_risk_recs)

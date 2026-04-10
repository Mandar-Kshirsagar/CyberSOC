"""Tests for CyberSOC graders"""

import pytest
from cybersoc.graders import PhishingGrader, MalwareGrader
from cybersoc.models import InvestigationAction


def test_phishing_grader_correct():
    """Test phishing grader with correct classification"""
    grader = PhishingGrader()

    history = [
        InvestigationAction(
            action_type="check_reputation", confidence=0.8, parameters={}
        ),
        InvestigationAction(action_type="query_logs", confidence=0.8, parameters={}),
    ]

    ground_truth = {"is_phishing": True}
    conclusion = {"label": "phishing", "confidence": 0.85}

    score = grader.grade(history, ground_truth, conclusion)

    assert 0.0 <= score <= 1.0
    assert score >= 0.7  # Should get base score for correct classification


def test_phishing_grader_incorrect():
    """Test phishing grader with incorrect classification"""
    grader = PhishingGrader()

    history = []
    ground_truth = {"is_phishing": True}
    conclusion = {"label": "legitimate", "confidence": 0.9}

    score = grader.grade(history, ground_truth, conclusion)

    assert 0.0 <= score <= 1.0
    assert score < 0.5  # Should get low score for incorrect classification


def test_phishing_grader_no_conclusion():
    """Test phishing grader with no conclusion"""
    grader = PhishingGrader()

    history = []
    ground_truth = {"is_phishing": True}
    conclusion = None

    score = grader.grade(history, ground_truth, conclusion)

    assert score == 0.0


def test_malware_grader_complete_investigation():
    """Test malware grader with complete investigation"""
    grader = MalwareGrader()

    history = [
        InvestigationAction(
            action_type="query_logs",
            confidence=0.8,
            parameters={"query_type": "process"},
        ),
        InvestigationAction(
            action_type="query_logs",
            confidence=0.8,
            parameters={"query_type": "network"},
        ),
        InvestigationAction(
            action_type="check_reputation", confidence=0.8, parameters={}
        ),
        InvestigationAction(
            action_type="collect_forensics", confidence=0.8, parameters={}
        ),
    ]

    ground_truth = {"is_malware": True}
    conclusion = {"label": "malware", "confidence": 0.85}

    score = grader.grade(history, ground_truth, conclusion)

    assert 0.0 <= score <= 1.0
    assert score >= 0.9  # Should get high score for complete investigation


def test_grader_determinism():
    """Test that graders are deterministic"""
    grader = PhishingGrader()

    history = [
        InvestigationAction(
            action_type="check_reputation", confidence=0.8, parameters={}
        )
    ]
    ground_truth = {"is_phishing": True}
    conclusion = {"label": "phishing", "confidence": 0.85}

    # Run grader multiple times
    scores = [grader.grade(history, ground_truth, conclusion) for _ in range(10)]

    # All scores should be identical
    assert len(set(scores)) == 1



def test_incident_grader_perfect_response():
    """Test incident grader with perfect response"""
    from cybersoc.graders import IncidentGrader
    
    grader = IncidentGrader()

    # Simulate thorough investigation
    history = [
        InvestigationAction(
            action_type="query_logs",
            confidence=0.8,
            parameters={"query_type": "timeline"},
        ),
        InvestigationAction(
            action_type="query_logs",
            confidence=0.8,
            parameters={"query_type": "timeline"},
            target="workstation_087",
        ),
        InvestigationAction(
            action_type="check_reputation", confidence=0.8, parameters={}
        ),
        InvestigationAction(
            action_type="collect_forensics", confidence=0.8, parameters={}
        ),
        InvestigationAction(
            action_type="isolate_host", confidence=0.9, target="workstation_042"
        ),
    ]

    ground_truth = {
        "is_true_positive": True,
        "attack_type": "ransomware",
        "correct_timeline": ["initial_access", "execution", "lateral_movement", "impact"],
        "required_containment": ["isolate_host", "block_ip"],
    }

    conclusion = {
        "classification": "true_positive",
        "timeline": ["initial_access", "execution", "lateral_movement", "impact"],
        "confidence": 0.85,
    }

    score = grader.grade(history, ground_truth, conclusion)

    assert 0.0 <= score <= 1.0
    assert score >= 0.7  # Should get high score for perfect response


def test_incident_grader_false_positive_handling():
    """Test incident grader correctly handles false positives"""
    from cybersoc.graders import IncidentGrader
    
    grader = IncidentGrader()

    # Investigation without aggressive containment
    history = [
        InvestigationAction(
            action_type="query_logs",
            confidence=0.8,
            parameters={"query_type": "timeline"},
        ),
        InvestigationAction(
            action_type="check_reputation", confidence=0.8, parameters={}
        ),
        InvestigationAction(
            action_type="collect_forensics", confidence=0.7, parameters={}
        ),
    ]

    ground_truth = {
        "is_true_positive": False,
        "attack_type": "false_positive",
        "correct_timeline": ["legitimate_admin", "legitimate_update"],
        "required_containment": [],
    }

    conclusion = {
        "classification": "false_positive",
        "timeline": ["legitimate_admin", "legitimate_update"],
        "confidence": 0.75,
    }

    score = grader.grade(history, ground_truth, conclusion)

    assert 0.0 <= score <= 1.0
    assert score >= 0.6  # Should get good score for correct false positive identification

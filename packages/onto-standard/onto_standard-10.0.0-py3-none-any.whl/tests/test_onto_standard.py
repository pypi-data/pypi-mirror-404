"""
ONTO Standard SDK Tests
"""

import pytest
from onto_standard import (
    evaluate,
    Prediction,
    GroundTruth,
    Label,
    ComplianceLevel,
    RiskLevel,
    __version__,
    __standard_version__,
)


class TestVersion:
    def test_version_exists(self):
        assert __version__ is not None
        assert __standard_version__ == "ONTO-ERS-1.0"


class TestPrediction:
    def test_valid_prediction(self):
        pred = Prediction("q1", Label.KNOWN, 0.9)
        assert pred.id == "q1"
        assert pred.label == Label.KNOWN
        assert pred.confidence == 0.9

    def test_confidence_bounds(self):
        with pytest.raises(ValueError):
            Prediction("q1", Label.KNOWN, 1.5)
        
        with pytest.raises(ValueError):
            Prediction("q1", Label.KNOWN, -0.1)

    def test_edge_confidence(self):
        pred0 = Prediction("q1", Label.KNOWN, 0.0)
        pred1 = Prediction("q2", Label.UNKNOWN, 1.0)
        assert pred0.confidence == 0.0
        assert pred1.confidence == 1.0


class TestGroundTruth:
    def test_valid_ground_truth(self):
        gt = GroundTruth("q1", Label.KNOWN)
        assert gt.id == "q1"
        assert gt.label == Label.KNOWN


class TestEvaluate:
    def test_perfect_known(self):
        """All known, all correct, high confidence"""
        predictions = [
            Prediction("q1", Label.KNOWN, 0.95),
            Prediction("q2", Label.KNOWN, 0.90),
            Prediction("q3", Label.KNOWN, 0.85),
        ]
        ground_truth = [
            GroundTruth("q1", Label.KNOWN),
            GroundTruth("q2", Label.KNOWN),
            GroundTruth("q3", Label.KNOWN),
        ]
        
        result = evaluate(predictions, ground_truth)
        
        assert result.accuracy == 1.0
        assert result.n_samples == 3

    def test_perfect_unknown_detection(self):
        """All unknowns correctly identified"""
        predictions = [
            Prediction("q1", Label.UNKNOWN, 0.8),
            Prediction("q2", Label.UNKNOWN, 0.9),
        ]
        ground_truth = [
            GroundTruth("q1", Label.UNKNOWN),
            GroundTruth("q2", Label.UNKNOWN),
        ]
        
        result = evaluate(predictions, ground_truth)
        
        assert result.unknown_detection.recall == 1.0
        assert result.unknown_detection.precision == 1.0

    def test_missed_unknowns(self):
        """Model predicts known but truth is unknown"""
        predictions = [
            Prediction("q1", Label.KNOWN, 0.9),
            Prediction("q2", Label.KNOWN, 0.9),
        ]
        ground_truth = [
            GroundTruth("q1", Label.UNKNOWN),
            GroundTruth("q2", Label.UNKNOWN),
        ]
        
        result = evaluate(predictions, ground_truth)
        
        assert result.unknown_detection.recall == 0.0
        assert result.unknown_detection.missed_unknowns == 2

    def test_compliance_levels(self):
        """Test compliance level determination"""
        # Create predictions that should achieve BASIC compliance
        # U-Recall >= 30%, ECE <= 0.20
        predictions = [
            Prediction("q1", Label.UNKNOWN, 0.9),  # Correct unknown
            Prediction("q2", Label.KNOWN, 0.9),    # Correct known
            Prediction("q3", Label.KNOWN, 0.9),    # Correct known
        ]
        ground_truth = [
            GroundTruth("q1", Label.UNKNOWN),
            GroundTruth("q2", Label.KNOWN),
            GroundTruth("q3", Label.KNOWN),
        ]
        
        result = evaluate(predictions, ground_truth)
        
        # 1/1 = 100% U-Recall (only 1 unknown, correctly identified)
        assert result.unknown_detection.recall == 1.0
        assert result.certification_ready == True

    def test_empty_predictions(self):
        """Handle empty input"""
        result = evaluate([], [])
        
        assert result.n_samples == 0
        assert result.accuracy == 0

    def test_result_to_dict(self):
        """Test JSON serialization"""
        predictions = [Prediction("q1", Label.KNOWN, 0.9)]
        ground_truth = [GroundTruth("q1", Label.KNOWN)]
        
        result = evaluate(predictions, ground_truth)
        d = result.to_dict()
        
        assert "compliance_level" in d
        assert "risk_score" in d
        assert "unknown_detection" in d
        assert "calibration" in d

    def test_result_to_json(self):
        """Test JSON string generation"""
        predictions = [Prediction("q1", Label.KNOWN, 0.9)]
        ground_truth = [GroundTruth("q1", Label.KNOWN)]
        
        result = evaluate(predictions, ground_truth)
        json_str = result.to_json()
        
        assert isinstance(json_str, str)
        assert "compliance_level" in json_str

    def test_citation(self):
        """Test citation generation"""
        predictions = [Prediction("q1", Label.KNOWN, 0.9)]
        ground_truth = [GroundTruth("q1", Label.KNOWN)]
        
        result = evaluate(predictions, ground_truth)
        citation = result.citation()
        
        assert "ONTO Epistemic Risk Standard" in citation
        assert result.compliance_level.value.upper() in citation


class TestRiskLevels:
    def test_risk_level_enum(self):
        assert RiskLevel.CRITICAL.value == "critical"
        assert RiskLevel.HIGH.value == "high"
        assert RiskLevel.MEDIUM.value == "medium"
        assert RiskLevel.LOW.value == "low"


class TestComplianceLevels:
    def test_compliance_level_enum(self):
        assert ComplianceLevel.NONE.value == "none"
        assert ComplianceLevel.BASIC.value == "basic"
        assert ComplianceLevel.STANDARD.value == "standard"
        assert ComplianceLevel.ADVANCED.value == "advanced"


class TestLabels:
    def test_label_enum(self):
        assert Label.KNOWN.value == "KNOWN"
        assert Label.UNKNOWN.value == "UNKNOWN"
        assert Label.CONTRADICTION.value == "CONTRADICTION"


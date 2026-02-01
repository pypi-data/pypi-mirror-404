"""
InsAIts SDK - Graceful Degradation Tests
==========================================
Tests that the SDK works correctly when premium features are unavailable.
Simulates the open-source-only scenario by mocking premium as absent.

Run with: python -m pytest tests/test_graceful_degradation.py -v
"""

import sys
import os
import time

os.environ['INSAITS_DEV_MODE'] = 'true'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from unittest.mock import patch, MagicMock
import numpy as np


# ============================================
# Test: Core functionality without premium
# ============================================

class TestDetectorWithoutPremium:
    """Verify AnomalyDetector works when premium is unavailable."""

    def _make_detector_without_premium(self):
        """Create AnomalyDetector with premium mocked as unavailable."""
        with patch.dict('sys.modules', {'insa_its.premium': None}):
            from insa_its.detector import AnomalyDetector
            d = AnomalyDetector.__new__(AnomalyDetector)
            d.auto_learn = True
            d._premium_detector = None
            d._adaptive_dict = None
            d._detect_anchor_drift = None
            d._suppress_anchor_aligned = None
            d.jargon_dict = {
                "known": d._get_seed_terms(),
                "candidate": {},
                "learned": set(),
                "expanded": {}
            }
            d.llm_patterns = {
                'gpt-4': {'avg_words': 40, 'jargon_heavy': False},
                'gpt-4o': {'avg_words': 35, 'jargon_heavy': False},
            }
            return d

    def test_detector_creates_without_premium(self):
        d = self._make_detector_without_premium()
        assert d._premium_detector is None
        assert d._adaptive_dict is None

    def test_fingerprint_mismatch_still_works(self):
        d = self._make_detector_without_premium()
        msg = {
            "text": "a " * 200,
            "word_count": 200,
            "embedding": np.random.rand(384).tolist(),
            "sender": "agent1",
            "message_id": "m1",
        }
        result = d._fingerprint_mismatch(msg, "gpt-4")
        assert result is not None
        assert result.type == "LLM_FINGERPRINT_MISMATCH"

    def test_jargon_stats_shows_premium_required(self):
        d = self._make_detector_without_premium()
        stats = d.get_jargon_stats()
        assert stats.get("premium_required") is True

    def test_load_domain_returns_error(self):
        d = self._make_detector_without_premium()
        result = d.load_domain("finance")
        assert "error" in result
        assert result.get("premium_required") is True

    def test_get_available_domains_returns_empty(self):
        d = self._make_detector_without_premium()
        domains = d.get_available_domains()
        assert domains == []

    def test_export_dictionary_returns_error(self):
        d = self._make_detector_without_premium()
        result = d.export_dictionary("/tmp/test.json")
        assert "error" in result
        assert result.get("premium_required") is True

    def test_import_dictionary_returns_error(self):
        d = self._make_detector_without_premium()
        result = d.import_dictionary("/tmp/test.json")
        assert "error" in result
        assert result.get("premium_required") is True

    def test_auto_expand_returns_error(self):
        d = self._make_detector_without_premium()
        result = d.auto_expand_terms(["TEST"])
        assert "error" in result
        assert result.get("premium_required") is True

    def test_add_learned_term_basic_fallback(self):
        d = self._make_detector_without_premium()
        d.add_learned_term("XYZZY", "test")
        assert "XYZZY" in d.jargon_dict["learned"]
        assert d.jargon_dict["expanded"]["XYZZY"] == "test"

    def test_detect_without_anchor_drift(self):
        """Detection works without anchor forensics - just skips anchor drift."""
        d = self._make_detector_without_premium()
        msg = {
            "text": "Hello world",
            "word_count": 2,
            "embedding": np.random.rand(384).tolist(),
            "sender": "agent1",
            "message_id": "m1",
        }
        history = {"agent1": {"gpt-4": [msg]}}
        anchor = {"text": "test", "embedding": np.random.rand(384).tolist()}

        # Should not raise, should return anomalies list
        anomalies = d.detect(msg, history, "agent1", "gpt-4", anchor=anchor)
        assert isinstance(anomalies, list)
        # No ANCHOR_DRIFT since function is None
        drift_types = [a.type for a in anomalies if a.type == "ANCHOR_DRIFT"]
        assert len(drift_types) == 0


# ============================================
# Test: Monitor without premium decipher
# ============================================

class TestMonitorWithoutPremiumDecipher:
    """Verify monitor.decipher() degrades gracefully."""

    def test_decipher_returns_premium_required(self):
        from insa_its.monitor import insAItsMonitor
        m = insAItsMonitor()
        # Simulate premium decipher not available
        m._decipher_engine = None
        result = m.decipher({"text": "test msg", "sender": "agent1"})
        assert "error" in result
        assert result.get("premium_required") is True
        assert result.get("original_text") == "test msg"

    def test_send_message_still_works_without_decipher(self):
        from insa_its.monitor import insAItsMonitor
        m = insAItsMonitor()
        m._decipher_engine = None
        result = m.send_message("Hello world", "agent1", llm_id="gpt-4")
        assert "anomalies" in result
        assert "message" in result

    def test_hallucination_detection_works_without_premium(self):
        """Hallucination detection is open-source and should work."""
        from insa_its.monitor import insAItsMonitor
        m = insAItsMonitor()
        m._decipher_engine = None
        m.detector._premium_detector = None

        result = m.send_message(
            "The capital of France is Paris",
            "agent1", llm_id="gpt-4"
        )
        assert "anomalies" in result

    def test_forensic_tracing_works_without_premium(self):
        """Forensic chain tracing is open-source."""
        from insa_its.monitor import insAItsMonitor
        m = insAItsMonitor()
        m._decipher_engine = None

        # Send some messages
        m.send_message("Hello", "agent1", receiver_id="agent2", llm_id="gpt-4")
        m.send_message("Hi back", "agent2", receiver_id="agent1", llm_id="gpt-4o")

        thread = m.get_conversation_thread("agent1", "agent2")
        assert len(thread) >= 1

    def test_stats_work_without_premium(self):
        from insa_its.monitor import insAItsMonitor
        m = insAItsMonitor()
        m._decipher_engine = None
        stats = m.get_stats()
        assert "session_id" in stats
        assert "tier" in stats

    def test_anchor_still_works_basic(self):
        """Basic anchor storage is open-source."""
        from insa_its.monitor import insAItsMonitor
        m = insAItsMonitor()
        anchor_result = m.set_anchor("What is AI?")
        assert anchor_result["anchor_set"] is True

        anchor = m.get_anchor()
        assert anchor is not None
        assert anchor["text"] == "What is AI?"

        clear = m.clear_anchor()
        assert clear["anchor_cleared"] is True
        assert m.get_anchor() is None

    def test_learn_from_session_without_premium_dict(self):
        """learn_from_session should work with basic jargon dict."""
        from insa_its.monitor import insAItsMonitor
        m = insAItsMonitor()
        m.detector._adaptive_dict = None

        # Send messages with repeated acronyms
        for i in range(4):
            m.send_message(
                f"The XYZZY protocol version {i}",
                "agent1", llm_id="gpt-4"
            )
        result = m.learn_from_session(min_occurrences=3)
        assert result["status"] == "success"

    def test_trend_analysis_without_premium(self):
        """Trend analysis is open-source."""
        from insa_its.monitor import insAItsMonitor
        m = insAItsMonitor()
        result = m.get_anomaly_trends()
        assert result["status"] == "no_anomalies"

    def test_conversation_reading_without_premium(self):
        """Conversation reading is open-source."""
        from insa_its.monitor import insAItsMonitor
        m = insAItsMonitor()
        m.send_message("Test message", "agent1", llm_id="gpt-4")
        convo = m.get_conversation(agent_id="agent1")
        assert len(convo) >= 1
        assert convo[0]["text"] == "Test message"


# ============================================
# Test: Config premium/open feature sets
# ============================================

class TestConfigFeatureSets:
    """Verify config.py has the premium/open feature classification."""

    def test_premium_features_set_exists(self):
        from insa_its.config import PREMIUM_FEATURES
        assert isinstance(PREMIUM_FEATURES, set)
        assert "shorthand_detection" in PREMIUM_FEATURES
        assert "decipher_full" in PREMIUM_FEATURES

    def test_open_features_set_exists(self):
        from insa_its.config import OPEN_FEATURES
        assert isinstance(OPEN_FEATURES, set)
        assert "anomaly_detection" in OPEN_FEATURES
        assert "hallucination_detection" in OPEN_FEATURES

    def test_is_premium_feature(self):
        from insa_its.config import is_premium_feature
        assert is_premium_feature("shorthand_detection") is True
        assert is_premium_feature("anomaly_detection") is False
        assert is_premium_feature("decipher_full") is True
        assert is_premium_feature("hallucination_detection") is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

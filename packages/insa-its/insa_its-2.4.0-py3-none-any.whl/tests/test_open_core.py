"""
InsAIts SDK - Open-Core Architecture Tests
============================================
Tests that premium features load and function correctly
when the premium package is available.

Run with: python -m pytest tests/test_open_core.py -v
"""

import sys
import os
import time

os.environ['INSAITS_DEV_MODE'] = 'true'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import numpy as np


# ============================================
# Test: Package-level exports
# ============================================

class TestPackageExports:
    """Verify that all expected symbols are exported from insa_its."""

    def test_version_is_2_4_0(self):
        import insa_its
        assert insa_its.__version__ == "2.4.0"

    def test_premium_available_flag_exists(self):
        import insa_its
        assert hasattr(insa_its, 'PREMIUM_AVAILABLE')
        assert isinstance(insa_its.PREMIUM_AVAILABLE, bool)

    def test_premium_available_is_true(self):
        """Premium package is present in dev environment."""
        import insa_its
        assert insa_its.PREMIUM_AVAILABLE is True

    def test_premium_feature_error_exported(self):
        from insa_its import PremiumFeatureError
        assert issubclass(PremiumFeatureError, Exception)

    def test_set_default_model_exported(self):
        from insa_its import set_default_model, get_default_model
        assert callable(set_default_model)
        assert callable(get_default_model)

    def test_dashboard_available_flag(self):
        import insa_its
        assert hasattr(insa_its, 'DASHBOARD_AVAILABLE')

    def test_all_exports_count(self):
        import insa_its
        assert len(insa_its.__all__) >= 25


# ============================================
# Test: Premium module loading
# ============================================

class TestPremiumModuleLoading:
    """Verify that premium submodules load correctly."""

    def test_premium_init_loads(self):
        from insa_its.premium import PREMIUM_AVAILABLE
        assert PREMIUM_AVAILABLE is True

    def test_advanced_detector_loads(self):
        from insa_its.premium import PremiumDetector
        assert PremiumDetector is not None

    def test_adaptive_dict_loads(self):
        from insa_its.premium import AdaptiveDictionary, DOMAIN_DICTIONARIES
        assert AdaptiveDictionary is not None
        assert isinstance(DOMAIN_DICTIONARIES, dict)
        assert len(DOMAIN_DICTIONARIES) >= 6

    def test_decipher_engine_loads(self):
        from insa_its.premium import DECIPHER_AVAILABLE
        assert DECIPHER_AVAILABLE is True
        from insa_its.premium import DecipherEngine
        assert DecipherEngine is not None

    def test_anchor_forensics_loads(self):
        from insa_its.premium import ANCHOR_AVAILABLE
        assert ANCHOR_AVAILABLE is True
        from insa_its.premium import detect_anchor_drift, suppress_anchor_aligned
        assert callable(detect_anchor_drift)
        assert callable(suppress_anchor_aligned)

    def test_detection_functions_exported(self):
        from insa_its.premium import (
            detect_shorthand_emergence,
            detect_context_loss,
            detect_cross_llm_shorthand,
            detect_cross_llm_jargon,
            confirm_shorthand_llm,
        )
        assert callable(detect_shorthand_emergence)
        assert callable(detect_context_loss)


# ============================================
# Test: AnomalyDetector with premium
# ============================================

class TestAnomalyDetectorPremium:
    """Verify AnomalyDetector initializes with premium features."""

    def test_premium_detector_loaded(self):
        from insa_its.detector import AnomalyDetector
        d = AnomalyDetector()
        assert d._premium_detector is not None

    def test_adaptive_dict_loaded(self):
        from insa_its.detector import AnomalyDetector
        d = AnomalyDetector()
        assert d._adaptive_dict is not None

    def test_anchor_drift_function_loaded(self):
        from insa_its.detector import AnomalyDetector
        d = AnomalyDetector()
        assert d._detect_anchor_drift is not None

    def test_anchor_suppress_function_loaded(self):
        from insa_its.detector import AnomalyDetector
        d = AnomalyDetector()
        assert d._suppress_anchor_aligned is not None

    def test_jargon_dict_has_premium_data(self):
        from insa_its.detector import AnomalyDetector
        d = AnomalyDetector()
        stats = d.get_jargon_stats()
        assert stats["known_terms"] >= 150
        assert "premium_required" not in stats

    def test_load_domain_returns_real_result(self):
        from insa_its.detector import AnomalyDetector
        d = AnomalyDetector()
        result = d.load_domain("finance")
        assert "error" not in result
        assert result.get("loaded") == "finance"

    def test_get_available_domains_returns_list(self):
        from insa_its.detector import AnomalyDetector
        d = AnomalyDetector()
        domains = d.get_available_domains()
        assert isinstance(domains, list)
        assert len(domains) >= 6
        assert "finance" in domains
        assert "healthcare" in domains

    def test_add_learned_term(self):
        from insa_its.detector import AnomalyDetector
        d = AnomalyDetector()
        d.add_learned_term("XYZZY", "test expansion")
        stats = d.get_jargon_stats()
        assert stats["learned_terms"] >= 1


# ============================================
# Test: insAItsMonitor with premium
# ============================================

class TestMonitorPremium:
    """Verify insAItsMonitor initializes with premium features."""

    def test_decipher_engine_loaded(self):
        from insa_its.monitor import insAItsMonitor
        m = insAItsMonitor()
        assert m._decipher_engine is not None

    def test_monitor_basic_flow(self):
        from insa_its.monitor import insAItsMonitor
        m = insAItsMonitor()
        result = m.send_message("Hello world", "agent1", llm_id="gpt-4")
        assert "anomalies" in result
        assert "message" in result

    def test_monitor_with_anchor(self):
        from insa_its.monitor import insAItsMonitor
        m = insAItsMonitor()
        anchor = m.set_anchor("What is machine learning?")
        assert anchor["anchor_set"] is True

        result = m.send_message(
            "Machine learning is a subset of AI",
            "agent1", llm_id="gpt-4"
        )
        assert "anomalies" in result

    def test_decipher_with_premium(self):
        """Decipher should not return premium_required error when premium is loaded."""
        from insa_its.monitor import insAItsMonitor
        m = insAItsMonitor()
        m.send_message("Hello from agent1", "agent1", llm_id="gpt-4")
        result = m.decipher({"text": "Test msg", "sender": "agent1"})
        # Should NOT have premium_required error (may have other errors like no Ollama)
        assert result.get("premium_required") is not True

    def test_learn_from_session(self):
        import random
        import string
        from insa_its.monitor import insAItsMonitor
        m = insAItsMonitor(api_key="test-free-100")
        # Generate unique ALL-CAPS LETTER term (regex requires [A-Z]{2,})
        suffix = ''.join(random.choices(string.ascii_uppercase, k=4))
        term = f"XQ{suffix}"
        for i in range(5):
            m.send_message(
                f"The {term} protocol enables faster message {i}",
                "agent1", llm_id="gpt-4"
            )
        result = m.learn_from_session(min_occurrences=3)
        assert result["status"] == "success"
        # Premium auto-learning may already know the term (via detect_premium candidate tracking),
        # so it counts as already_known. Either way, the flow succeeds.
        total_processed = result["terms_learned"] + result["already_known"]
        assert total_processed >= 1

    def test_domain_management_via_monitor(self):
        from insa_its.monitor import insAItsMonitor
        m = insAItsMonitor()
        domains = m.get_available_domains()
        assert len(domains) >= 6

        result = m.load_domain("kubernetes")
        assert result.get("loaded") == "kubernetes"


# ============================================
# Test: Ollama model selection
# ============================================

class TestOllamaModelSelection:
    """Verify Ollama model selection feature."""

    def test_default_model(self):
        from insa_its.local_llm import get_default_model
        model = get_default_model()
        assert isinstance(model, str)
        assert len(model) > 0

    def test_set_and_get_model(self):
        from insa_its.local_llm import set_default_model, get_default_model
        original = get_default_model()
        set_default_model("phi3")
        assert get_default_model() == "phi3"
        set_default_model(original)  # Reset

    def test_monitor_ollama_model_param(self):
        from insa_its.monitor import insAItsMonitor
        from insa_its.local_llm import get_default_model, set_default_model
        original = get_default_model()
        m = insAItsMonitor(ollama_model="mistral")
        assert get_default_model() == "mistral"
        set_default_model(original)  # Reset


# ============================================
# Test: Anchor forensics integration
# ============================================

class TestAnchorForensics:
    """Verify anchor drift detection via premium."""

    def test_detect_anchor_drift_function(self):
        from insa_its.premium.anchor_forensics import detect_anchor_drift
        from insa_its.detector import Anomaly

        msg = {"text": "Something completely unrelated to query", "message_id": "m1"}
        anchor = {"text": "What is quantum computing?", "embedding": None}
        result = detect_anchor_drift(
            current_msg=msg,
            llm_id="gpt-4",
            sender_id="agent1",
            anchor_similarity=0.15,
            anchor=anchor,
        )
        assert result is not None
        assert isinstance(result, Anomaly)
        assert result.type == "ANCHOR_DRIFT"
        assert result.severity == "high"

    def test_no_drift_when_aligned(self):
        from insa_its.premium.anchor_forensics import detect_anchor_drift

        msg = {"text": "Quantum computing uses qubits", "message_id": "m2"}
        anchor = {"text": "What is quantum computing?", "embedding": None}
        result = detect_anchor_drift(
            current_msg=msg,
            llm_id="gpt-4",
            sender_id="agent1",
            anchor_similarity=0.85,
            anchor=anchor,
        )
        assert result is None

    def test_suppress_anchor_aligned(self):
        from insa_its.premium.anchor_forensics import suppress_anchor_aligned
        from insa_its.detector import Anomaly

        anomalies = [
            Anomaly(
                type="CROSS_LLM_JARGON",
                severity="high",
                llm_id="gpt-4",
                agent_id="agent1",
                details={"new_terms": ["QUBIT"]},
                timestamp=time.time(),
            )
        ]
        anchor = {"text": "Explain quantum computing"}
        result = suppress_anchor_aligned(anomalies, anchor, 0.75)
        assert result[0].severity == "info"
        assert result[0].details.get("suppressed") is True

    def test_terms_relevant_to_anchor(self):
        from insa_its.premium.anchor_forensics import terms_relevant_to_anchor
        assert terms_relevant_to_anchor(["QUBIT", "QPU"], "quantum computing") is True
        assert terms_relevant_to_anchor(["K8S", "POD"], "kubernetes deployment") is True
        assert terms_relevant_to_anchor(["EBITDA"], "finance report") is True


# ============================================
# Test: Decipher engine
# ============================================

class TestDecipherEngine:
    """Verify DecipherEngine instantiation and context building."""

    def test_decipher_engine_init(self):
        from insa_its.premium.decipher_engine import DecipherEngine
        engine = DecipherEngine(api_key="test", tier="pro")
        assert engine.api_key == "test"
        assert engine.tier == "pro"

    def test_build_context_empty_history(self):
        from insa_its.premium.decipher_engine import DecipherEngine
        engine = DecipherEngine()
        context = engine.build_context({}, "agent1")
        assert isinstance(context, list)
        assert len(context) == 0

    def test_cloud_decipher_no_api_key(self):
        from insa_its.premium.decipher_engine import DecipherEngine
        engine = DecipherEngine(api_key=None, tier="anonymous")
        result = engine.decipher(
            {"text": "test", "sender": "agent1"},
            context=[],
            mode="cloud"
        )
        assert "error" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

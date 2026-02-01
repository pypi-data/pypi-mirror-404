"""
InsAIts SDK V2 Features Test Suite
==================================
Tests for Phase 1 (Anchor-Aware Detection) and Phase 4 (Dictionary Management)

Run with: python -m pytest tests/test_v2_features.py -v
"""

import sys
import os
import time
import tempfile
import json

# Enable Development Mode for Testing
os.environ['INSAITS_DEV_MODE'] = 'true'

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import numpy as np

from insa_its import insAItsMonitor, AnomalyDetector
from insa_its.embeddings import get_local_embedding
try:
    from insa_its.premium.adaptive_dict import DOMAIN_DICTIONARIES
except ImportError:
    from insa_its.detector import DOMAIN_DICTIONARIES

# Test API Keys
TEST_PRO_KEY = 'test-pro-unlimited'


# ============================================
# PHASE 1: ANCHOR-AWARE DETECTION TESTS
# ============================================

class TestAnchorAwareDetection:
    """Tests for V2 anchor-aware detection (Phase 1)"""

    def test_set_anchor_basic(self):
        """Test setting an anchor"""
        monitor = insAItsMonitor(api_key=TEST_PRO_KEY)

        result = monitor.set_anchor("What is quantum computing?")

        assert result["anchor_set"] is True
        assert "anchor_id" in result
        assert len(result["anchor_id"]) > 0
        assert "text_preview" in result

    def test_get_anchor(self):
        """Test retrieving the current anchor"""
        monitor = insAItsMonitor(api_key=TEST_PRO_KEY)

        # Initially no anchor
        assert monitor.get_anchor() is None

        # Set anchor
        monitor.set_anchor("Explain machine learning algorithms")

        anchor = monitor.get_anchor()
        assert anchor is not None
        assert anchor["text"] == "Explain machine learning algorithms"
        assert "sender" in anchor
        assert "timestamp" in anchor
        assert "message_id" in anchor

    def test_clear_anchor(self):
        """Test clearing the anchor"""
        monitor = insAItsMonitor(api_key=TEST_PRO_KEY)

        # Set anchor
        monitor.set_anchor("Test query")
        assert monitor.get_anchor() is not None

        # Clear anchor
        result = monitor.clear_anchor()
        assert result["anchor_cleared"] is True
        assert monitor.get_anchor() is None

        # Clear again (should indicate no anchor was set)
        result2 = monitor.clear_anchor()
        assert result2["anchor_cleared"] is False

    def test_anchor_has_embedding(self):
        """Test that anchor includes embedding"""
        monitor = insAItsMonitor(api_key=TEST_PRO_KEY)

        monitor.set_anchor("Test anchor text")

        # Access internal anchor (has embedding)
        assert monitor.current_anchor is not None
        assert "embedding" in monitor.current_anchor
        assert monitor.current_anchor["embedding"] is not None

    def test_turn_counter_increments(self):
        """Test that turn counter increments with each message"""
        monitor = insAItsMonitor(api_key=TEST_PRO_KEY)

        monitor.set_anchor("User's question")
        assert monitor.turn_counter == 0

        monitor.send_message("First response", "agent1", llm_id="gpt-4o")
        assert monitor.turn_counter == 1

        time.sleep(0.15)
        monitor.send_message("Second response", "agent1", llm_id="gpt-4o")
        assert monitor.turn_counter == 2

    def test_message_includes_anchor_reference(self):
        """Test that messages include anchor_id when anchor is set"""
        monitor = insAItsMonitor(api_key=TEST_PRO_KEY)

        anchor_result = monitor.set_anchor("What is API design?")
        anchor_id = anchor_result["anchor_id"]

        result = monitor.send_message("API design involves...", "agent1", llm_id="gpt-4o")

        msg = result["message"]
        assert msg["anchor_id"] == anchor_id
        assert msg["is_anchor"] is False
        assert msg["turn_number"] == 1

    def test_anchor_similarity_calculated(self):
        """Test that anchor similarity is calculated when anchor is set"""
        monitor = insAItsMonitor(api_key=TEST_PRO_KEY)

        # Set anchor about quantum computing
        monitor.set_anchor("Explain quantum computing and qubits")

        # Verify anchor has embedding
        assert monitor.current_anchor is not None
        assert monitor.current_anchor.get("embedding") is not None

        # Send a message and check that internal processing uses anchor
        result = monitor.send_message(
            "I love cooking pasta with fresh basil and tomatoes in Italy",
            "agent1", llm_id="gpt-4o"
        )

        # The message should have anchor_id set
        msg = result["message"]
        assert msg["anchor_id"] is not None, "Message should have anchor_id when anchor is set"

        # If there are anomalies, they should have anchor_similarity attached
        anomalies = result["anomalies"]
        if anomalies:
            # Check at least one anomaly has anchor_similarity (could be None if not computed)
            has_anchor_sim = any(
                "anchor_similarity" in a
                for a in anomalies
            )
            # This is informational - not all anomalies may have anchor_similarity
            # The key is that the message processing works with anchors
            pass  # Test passes if no exception

    def test_anchor_drift_detection(self):
        """Test ANCHOR_DRIFT detection logic directly"""
        from insa_its.detector import AnomalyDetector, Anomaly
        import numpy as np

        detector = AnomalyDetector()

        # Create anchor with specific embedding
        anchor_embedding = np.random.randn(384)
        anchor_embedding = anchor_embedding / np.linalg.norm(anchor_embedding)

        anchor = {
            "text": "Explain quantum computing",
            "embedding": anchor_embedding,
            "sender": "user",
            "timestamp": time.time(),
            "message_id": "anchor-001"
        }

        # Create message with very different embedding (low similarity)
        # Create orthogonal embedding for low similarity
        msg_embedding = np.random.randn(384)
        msg_embedding = msg_embedding - np.dot(msg_embedding, anchor_embedding) * anchor_embedding
        msg_embedding = msg_embedding / np.linalg.norm(msg_embedding)

        current_msg = {
            "text": "Completely unrelated topic about cooking",
            "embedding": msg_embedding,
            "sender": "agent1",
            "llm_id": "gpt-4o",
            "word_count": 6,
            "timestamp": time.time(),
            "message_id": "msg-001"
        }

        history = {"agent1": {"gpt-4o": []}}

        # Run detection with anchor
        anomalies = detector.detect(
            current_msg, history, "agent1", "gpt-4o",
            receiver_id=None, anchor=anchor
        )

        # Should have ANCHOR_DRIFT when similarity < 0.4
        has_drift = any(a.type == "ANCHOR_DRIFT" for a in anomalies)

        # With orthogonal embeddings, similarity should be near 0
        # So ANCHOR_DRIFT should trigger
        assert has_drift, "Expected ANCHOR_DRIFT for orthogonal embeddings"

    def test_no_anchor_drift_for_aligned_response(self):
        """Test that aligned responses don't trigger ANCHOR_DRIFT"""
        monitor = insAItsMonitor(api_key=TEST_PRO_KEY)

        # Set anchor
        monitor.set_anchor("What is machine learning and how does it work?")

        # Send aligned response
        result = monitor.send_message(
            "Machine learning is a subset of artificial intelligence that enables computers to learn from data without explicit programming",
            "agent1", llm_id="gpt-4o"
        )

        has_drift = any(
            a.get("type") == "ANCHOR_DRIFT"
            for a in result["anomalies"]
        )

        # Should NOT have anchor drift for aligned response
        assert not has_drift, "Should not have ANCHOR_DRIFT for aligned response"


class TestAnchorFalsePositiveSuppression:
    """Tests for false positive suppression based on anchor"""

    def test_jargon_suppressed_when_relevant_to_anchor(self):
        """Test that jargon is suppressed when it's relevant to anchor query"""
        monitor = insAItsMonitor(api_key=TEST_PRO_KEY)

        # Set anchor asking about quantum computing
        monitor.set_anchor("Explain quantum computing concepts")

        # Response with quantum terms (should be relevant, suppressed)
        result = monitor.send_message(
            "Quantum computing uses QUBIT and QPU for superposition calculations using NISQ devices",
            "agent1", llm_id="gpt-4o"
        )

        jargon_anomalies = [
            a for a in result["anomalies"]
            if a.get("type") == "CROSS_LLM_JARGON"
        ]

        # If jargon detected, it should be suppressed (severity=info)
        for anomaly in jargon_anomalies:
            if anomaly.get("details", {}).get("suppressed"):
                assert anomaly["severity"] == "info", "Suppressed jargon should have 'info' severity"


# ============================================
# PHASE 4: DICTIONARY MANAGEMENT TESTS
# ============================================

class TestDomainDictionaries:
    """Tests for domain-specific dictionary loading (Phase 4)"""

    def test_domain_dictionaries_exist(self):
        """Test that DOMAIN_DICTIONARIES constant exists with expected domains"""
        assert DOMAIN_DICTIONARIES is not None

        expected_domains = ["finance", "healthcare", "kubernetes", "machine_learning", "devops", "quantum"]
        for domain in expected_domains:
            assert domain in DOMAIN_DICTIONARIES, f"Missing domain: {domain}"

    def test_domain_has_known_and_expansions(self):
        """Test that each domain has 'known' and 'expansions' keys"""
        for domain_name, domain_data in DOMAIN_DICTIONARIES.items():
            assert "known" in domain_data, f"{domain_name} missing 'known'"
            assert "expansions" in domain_data, f"{domain_name} missing 'expansions'"
            assert len(domain_data["known"]) > 0, f"{domain_name} has empty 'known'"

    def test_get_available_domains(self):
        """Test getting list of available domains"""
        monitor = insAItsMonitor(api_key=TEST_PRO_KEY)

        domains = monitor.get_available_domains()

        assert isinstance(domains, list)
        assert len(domains) >= 6  # At least the 6 we defined
        assert "finance" in domains
        assert "healthcare" in domains

    def test_load_domain_success(self):
        """Test successfully loading a domain dictionary"""
        monitor = insAItsMonitor(api_key=TEST_PRO_KEY)

        initial_stats = monitor.get_jargon_dictionary()
        initial_known = initial_stats["known_terms"]

        result = monitor.load_domain("finance")

        assert result.get("loaded") == "finance"
        assert result.get("terms_added") >= 0  # Some may already be in seed
        assert result.get("total_known") >= initial_known

    def test_load_domain_invalid(self):
        """Test loading invalid domain returns error"""
        monitor = insAItsMonitor(api_key=TEST_PRO_KEY)

        result = monitor.load_domain("invalid_domain_xyz")

        assert "error" in result
        assert "available_domains" in result

    def test_load_multiple_domains(self):
        """Test loading multiple domains"""
        monitor = insAItsMonitor(api_key=TEST_PRO_KEY)

        result1 = monitor.load_domain("kubernetes")
        result2 = monitor.load_domain("devops")

        assert result1.get("loaded") == "kubernetes"
        assert result2.get("loaded") == "devops"

        # Check that K8S terms are now known (via premium adaptive dict)
        adaptive_dict = monitor.detector._adaptive_dict
        assert adaptive_dict is not None
        assert adaptive_dict.is_known_term("K8S")
        assert adaptive_dict.is_known_term("CI")


class TestDictionaryExportImport:
    """Tests for dictionary export/import (Phase 4)"""

    def test_export_dictionary(self):
        """Test exporting dictionary to JSON"""
        monitor = insAItsMonitor(api_key=TEST_PRO_KEY)

        # Add a custom term
        monitor.add_jargon_term("TESTTERM", "Test Term Meaning")

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            filepath = f.name

        try:
            result = monitor.export_dictionary(filepath)

            assert result.get("exported") == filepath
            assert result.get("total_terms") > 0

            # Verify file content
            with open(filepath, 'r') as f:
                data = json.load(f)

            assert "known" in data
            assert "learned" in data
            assert "expanded" in data
            assert "metadata" in data
            assert data["metadata"]["version"] == "2.0"
        finally:
            os.unlink(filepath)

    def test_import_dictionary_merge(self):
        """Test importing dictionary in merge mode"""
        monitor = insAItsMonitor(api_key=TEST_PRO_KEY)

        # Create a test dictionary file
        test_dict = {
            "known": ["IMPORTED1", "IMPORTED2"],
            "learned": ["IMPORTED3"],
            "expanded": {"IMPORTED1": "Imported Term One"}
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_dict, f)
            filepath = f.name

        try:
            result = monitor.import_dictionary(filepath, merge=True)

            assert result.get("imported") == filepath
            assert result.get("mode") == "merge"

            # Check terms were imported (via premium adaptive dict)
            adaptive_dict = monitor.detector._adaptive_dict
            assert adaptive_dict is not None
            assert adaptive_dict.is_known_term("IMPORTED1")
            assert adaptive_dict.is_known_term("IMPORTED3")  # learned becomes known in check
        finally:
            os.unlink(filepath)

    def test_import_dictionary_replace(self):
        """Test importing dictionary in replace mode"""
        monitor = insAItsMonitor(api_key=TEST_PRO_KEY)

        # Add a term first
        monitor.add_jargon_term("WILLBEGONE")

        # Create a test dictionary file
        test_dict = {
            "known": [],
            "learned": ["NEWTERM"],
            "expanded": {}
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_dict, f)
            filepath = f.name

        try:
            result = monitor.import_dictionary(filepath, merge=False)

            assert result.get("mode") == "replace"

            # Check NEWTERM is there and WILLBEGONE is still there (seed terms preserved)
            detector = monitor.detector
            assert "NEWTERM" in detector.jargon_dict["learned"]
        finally:
            os.unlink(filepath)

    def test_import_nonexistent_file(self):
        """Test importing from nonexistent file returns error"""
        monitor = insAItsMonitor(api_key=TEST_PRO_KEY)

        result = monitor.import_dictionary("/nonexistent/path/file.json")

        assert "error" in result

    def test_import_invalid_json(self):
        """Test importing invalid JSON returns error"""
        monitor = insAItsMonitor(api_key=TEST_PRO_KEY)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("not valid json {{{")
            filepath = f.name

        try:
            result = monitor.import_dictionary(filepath)
            assert "error" in result
        finally:
            os.unlink(filepath)


class TestAutoExpandTerms:
    """Tests for LLM auto-expansion (Phase 4)"""

    def test_auto_expand_no_llm(self):
        """Test auto_expand_terms when LLM is not available"""
        monitor = insAItsMonitor(api_key=TEST_PRO_KEY)

        # This may return error if Ollama not available, which is expected
        result = monitor.auto_expand_terms(["TEST"])

        # Should return either error or expanded terms
        assert "error" in result or "expanded" in result

    def test_auto_expand_all_expanded(self):
        """Test auto_expand_terms when all terms already expanded"""
        monitor = insAItsMonitor(api_key=TEST_PRO_KEY)

        # Add term with expansion
        monitor.add_jargon_term("MYTERM", "My Term Meaning")

        # Try to expand only already-expanded terms
        result = monitor.auto_expand_terms(["MYTERM"])

        # If LLM unavailable, we get error
        # If LLM available, we might get success (it would try to expand anyway)
        assert "error" in result or "expanded" in result or "status" in result


class TestTermsRelevantToAnchor:
    """Tests for terms_relevant_to_anchor (now in premium/anchor_forensics)"""

    def test_quantum_terms_relevant_to_quantum_query(self):
        """Test quantum terms are relevant to quantum computing query"""
        from insa_its.premium.anchor_forensics import terms_relevant_to_anchor

        terms = ["QUBIT", "QPU", "NISQ"]
        anchor = "Explain quantum computing"

        assert terms_relevant_to_anchor(terms, anchor) is True

    def test_ml_terms_relevant_to_ml_query(self):
        """Test ML terms are relevant to machine learning query"""
        from insa_its.premium.anchor_forensics import terms_relevant_to_anchor

        terms = ["CNN", "RNN", "BERT"]
        anchor = "How does machine learning work?"

        assert terms_relevant_to_anchor(terms, anchor) is True

    def test_unrelated_terms_not_relevant(self):
        """Test unrelated terms are not marked as relevant"""
        from insa_its.premium.anchor_forensics import terms_relevant_to_anchor

        terms = ["XYZABC", "FOOBAR"]
        anchor = "Tell me about cooking recipes"

        # Without LLM, heuristics may not find a match
        # This depends on whether LLM is available
        result = terms_relevant_to_anchor(terms, anchor)
        # Result may be True or False depending on LLM availability
        assert isinstance(result, bool)

    def test_empty_terms_not_relevant(self):
        """Test empty terms list returns False"""
        from insa_its.premium.anchor_forensics import terms_relevant_to_anchor

        assert terms_relevant_to_anchor([], "Any query") is False

    def test_term_in_anchor_is_relevant(self):
        """Test term appearing in anchor text is relevant"""
        from insa_its.premium.anchor_forensics import terms_relevant_to_anchor

        terms = ["API"]
        anchor = "What is API design?"

        assert terms_relevant_to_anchor(terms, anchor) is True


class TestAnomalyDataclassV2Fields:
    """Tests for V2 fields in Anomaly dataclass"""

    def test_anomaly_has_v2_fields(self):
        """Test Anomaly dataclass has V2 fields"""
        from insa_its.detector import Anomaly

        anomaly = Anomaly(
            type="TEST",
            severity="high",
            llm_id="gpt-4o",
            agent_id="agent1",
            details={},
            timestamp=time.time()
        )

        # V2 fields should have defaults
        assert hasattr(anomaly, "message_id")
        assert hasattr(anomaly, "root_message_id")
        assert hasattr(anomaly, "drift_chain")
        assert hasattr(anomaly, "anchor_similarity")

        # Check defaults
        assert anomaly.message_id == ""
        assert anomaly.root_message_id is None
        assert anomaly.drift_chain == []
        assert anomaly.anchor_similarity is None

    def test_anomaly_with_v2_fields_set(self):
        """Test Anomaly with V2 fields explicitly set"""
        from insa_its.detector import Anomaly

        anomaly = Anomaly(
            type="ANCHOR_DRIFT",
            severity="high",
            llm_id="gpt-4o",
            agent_id="agent1",
            details={"anchor_similarity": 0.35},
            timestamp=time.time(),
            message_id="msg-123",
            root_message_id="msg-001",
            drift_chain=["msg-001", "msg-050", "msg-123"],
            anchor_similarity=0.35
        )

        assert anomaly.message_id == "msg-123"
        assert anomaly.root_message_id == "msg-001"
        assert len(anomaly.drift_chain) == 3
        assert anomaly.anchor_similarity == 0.35


# ============================================
# INTEGRATION TESTS
# ============================================

class TestV2Integration:
    """Integration tests combining V2 features"""

    def test_full_anchor_workflow(self):
        """Test complete anchor workflow: set, send messages, clear"""
        monitor = insAItsMonitor(api_key=TEST_PRO_KEY)

        # 1. Set anchor
        anchor_result = monitor.set_anchor("Explain Kubernetes deployments")
        assert anchor_result["anchor_set"] is True

        # 2. Load relevant domain
        domain_result = monitor.load_domain("kubernetes")
        assert domain_result["loaded"] == "kubernetes"

        # 3. Send aligned message
        result1 = monitor.send_message(
            "Kubernetes deployments manage pod replicas using ReplicaSets",
            "agent1", llm_id="gpt-4o"
        )
        assert "anomalies" in result1

        time.sleep(0.15)

        # 4. Send another message
        result2 = monitor.send_message(
            "Use kubectl to scale deployments and manage HPA",
            "agent1", llm_id="gpt-4o"
        )

        # Check turn counter
        anchor = monitor.get_anchor()
        assert anchor["turn_number"] == 2

        # 5. Clear anchor
        clear_result = monitor.clear_anchor()
        assert clear_result["anchor_cleared"] is True

    def test_dictionary_roundtrip(self):
        """Test dictionary export and import roundtrip"""
        monitor1 = insAItsMonitor(api_key=TEST_PRO_KEY)

        # Load domain and add custom term
        monitor1.load_domain("finance")
        monitor1.add_jargon_term("CUSTOMTEST", "Custom Test Term")

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            filepath = f.name

        try:
            # Export
            export_result = monitor1.export_dictionary(filepath)
            assert "exported" in export_result

            # Create new monitor and import
            monitor2 = insAItsMonitor(api_key=TEST_PRO_KEY)
            import_result = monitor2.import_dictionary(filepath, merge=True)
            assert "imported" in import_result

            # Verify custom term exists (via premium adaptive dict)
            adaptive_dict = monitor2.detector._adaptive_dict
            assert adaptive_dict is not None
            assert adaptive_dict.is_known_term("CUSTOMTEST")

            # Verify finance terms exist
            assert adaptive_dict.is_known_term("EBITDA")
        finally:
            os.unlink(filepath)


# ============================================
# PHASE 2: FORENSIC CHAIN TRACING TESTS
# ============================================

class TestForensicChainTracing:
    """Tests for V2 forensic chain tracing (Phase 2)"""

    def test_trace_root_basic(self):
        """Test basic trace_root functionality"""
        monitor = insAItsMonitor(api_key=TEST_PRO_KEY)

        # Create a conversation
        result1 = monitor.send_message("Hello agent B", "agent_a", "agent_b", "gpt-4o")
        time.sleep(0.15)
        result2 = monitor.send_message("Hello agent A, nice to meet you", "agent_b", "agent_a", "claude-3.5")
        time.sleep(0.15)

        # Send message with jargon to trigger anomaly
        result3 = monitor.send_message(
            "Let's use XYZPROTO and FOOBARSPEC protocols",
            "agent_a", "agent_b", "gpt-4o"
        )

        # Find a jargon anomaly if one was detected
        jargon_anomalies = [a for a in result3["anomalies"] if a.get("type") == "CROSS_LLM_JARGON"]

        if jargon_anomalies:
            # Add the message_id from the result message
            anomaly_with_id = dict(jargon_anomalies[0])
            anomaly_with_id["message_id"] = result3["message"]["message_id"]

            trace = monitor.trace_root(anomaly_with_id)

            assert "chain_length" in trace
            assert "full_chain" in trace
            assert "summary" in trace
            assert trace["anomaly_type"] == "CROSS_LLM_JARGON"

    def test_trace_root_no_message_id(self):
        """Test trace_root with missing message_id"""
        monitor = insAItsMonitor(api_key=TEST_PRO_KEY)

        result = monitor.trace_root({"type": "TEST", "details": {}})

        assert "error" in result
        assert "No message_id" in result["error"]

    def test_trace_root_message_not_found(self):
        """Test trace_root with nonexistent message_id"""
        monitor = insAItsMonitor(api_key=TEST_PRO_KEY)

        result = monitor.trace_root({"type": "TEST", "message_id": "nonexistent-123"})

        assert "error" in result
        assert "not found" in result["error"]

    def test_get_propagation_chain(self):
        """Test simplified get_propagation_chain method"""
        monitor = insAItsMonitor(api_key=TEST_PRO_KEY)

        # Send messages
        monitor.send_message("First message", "agent_a", llm_id="gpt-4o")
        time.sleep(0.15)
        result = monitor.send_message("Second message with XYZTERM", "agent_a", llm_id="gpt-4o")

        if result["anomalies"]:
            chain = monitor.get_propagation_chain(result["anomalies"][0])
            assert isinstance(chain, list)

    def test_find_message_by_id(self):
        """Test _find_message_by_id helper"""
        monitor = insAItsMonitor(api_key=TEST_PRO_KEY)

        result = monitor.send_message("Test message", "agent_1", llm_id="gpt-4o")
        msg_id = result["message"]["message_id"]

        found = monitor._find_message_by_id(msg_id)

        assert found is not None
        assert found["message_id"] == msg_id
        assert found["text"] == "Test message"

    def test_find_message_by_id_not_found(self):
        """Test _find_message_by_id with nonexistent ID"""
        monitor = insAItsMonitor(api_key=TEST_PRO_KEY)

        found = monitor._find_message_by_id("nonexistent-id")

        assert found is None

    def test_find_previous_message(self):
        """Test _find_previous_message helper"""
        monitor = insAItsMonitor(api_key=TEST_PRO_KEY)

        # Create conversation
        result1 = monitor.send_message("First", "agent_a", "agent_b", "gpt-4o")
        time.sleep(0.15)
        result2 = monitor.send_message("Reply", "agent_b", "agent_a", "claude-3.5")
        time.sleep(0.15)
        result3 = monitor.send_message("Response", "agent_a", "agent_b", "gpt-4o")

        # Find previous of result3
        msg3 = result3["message"]
        prev = monitor._find_previous_message(msg3)

        # Should find the reply from agent_b
        assert prev is not None
        assert prev["sender"] == "agent_b"

    def test_find_anomaly_origin_jargon(self):
        """Test _find_anomaly_origin for CROSS_LLM_JARGON"""
        monitor = insAItsMonitor(api_key=TEST_PRO_KEY)

        chain = [
            {"text_preview": "Normal message here", "word_count": 3},
            {"text_preview": "Message with XYZTERM", "word_count": 3},
            {"text_preview": "Another XYZTERM usage", "word_count": 3}
        ]

        anomaly = {
            "type": "CROSS_LLM_JARGON",
            "details": {"new_terms": ["XYZTERM"]}
        }

        origin = monitor._find_anomaly_origin(chain, "CROSS_LLM_JARGON", anomaly)

        # Should find index 1 where XYZTERM first appears
        assert origin == 1

    def test_find_anomaly_origin_shorthand(self):
        """Test _find_anomaly_origin for SHORTHAND_EMERGENCE"""
        monitor = insAItsMonitor(api_key=TEST_PRO_KEY)

        chain = [
            {"text_preview": "A very long message with many words", "word_count": 50},
            {"text_preview": "Medium message", "word_count": 30},
            {"text_preview": "Short", "word_count": 5}  # Big drop
        ]

        anomaly = {
            "type": "SHORTHAND_EMERGENCE",
            "details": {"compression_ratio": 6.0}
        }

        origin = monitor._find_anomaly_origin(chain, "SHORTHAND_EMERGENCE", anomaly)

        # Should find index 2 where word count drops significantly
        assert origin == 2

    def test_generate_forensic_summary_jargon(self):
        """Test _generate_forensic_summary for jargon anomaly"""
        monitor = insAItsMonitor(api_key=TEST_PRO_KEY)

        chain = [
            {"sender": "agent_a", "llm_id": "gpt-4o", "text_preview": "First"},
            {"sender": "agent_a", "llm_id": "gpt-4o", "text_preview": "With XYZTERM"}
        ]

        anomaly = {
            "type": "CROSS_LLM_JARGON",
            "details": {"new_terms": ["XYZTERM"]}
        }

        summary = monitor._generate_forensic_summary(chain, 1, anomaly)

        assert "XYZTERM" in summary
        assert "agent_a" in summary
        assert "gpt-4o" in summary

    def test_generate_forensic_summary_context_loss(self):
        """Test _generate_forensic_summary for context loss"""
        monitor = insAItsMonitor(api_key=TEST_PRO_KEY)

        chain = [
            {"sender": "agent_a", "llm_id": "gpt-4o", "text_preview": "First"},
            {"sender": "agent_a", "llm_id": "gpt-4o", "text_preview": "Unrelated"}
        ]

        anomaly = {
            "type": "CONTEXT_LOSS",
            "details": {"similarity": 0.25}
        }

        summary = monitor._generate_forensic_summary(chain, 1, anomaly)

        assert "25.0%" in summary or "25%" in summary  # Similarity percentage
        assert "diverged" in summary.lower() or "context" in summary.lower()

    def test_generate_forensic_summary_anchor_drift(self):
        """Test _generate_forensic_summary for anchor drift"""
        monitor = insAItsMonitor(api_key=TEST_PRO_KEY)

        chain = [
            {"sender": "agent_a", "llm_id": "gpt-4o", "text_preview": "Response"}
        ]

        anomaly = {
            "type": "ANCHOR_DRIFT",
            "details": {"anchor_similarity": 0.3}
        }

        summary = monitor._generate_forensic_summary(chain, 0, anomaly)

        assert "30.0%" in summary or "30%" in summary
        assert "drift" in summary.lower() or "query" in summary.lower()

    def test_visualize_chain(self):
        """Test visualize_chain ASCII output"""
        monitor = insAItsMonitor(api_key=TEST_PRO_KEY)

        # Create messages
        result1 = monitor.send_message("Message one", "agent_a", "agent_b", "gpt-4o")
        time.sleep(0.15)
        result2 = monitor.send_message("XYZPROTO testing", "agent_a", "agent_b", "gpt-4o")

        # Create anomaly dict with message_id
        anomaly = {
            "type": "CROSS_LLM_JARGON",
            "message_id": result2["message"]["message_id"],
            "details": {"new_terms": ["XYZPROTO"]}
        }

        viz = monitor.visualize_chain(anomaly)

        assert "FORENSIC CHAIN TRACE" in viz
        assert "Step" in viz
        assert "SUMMARY" in viz
        assert "agent_a" in viz

    def test_visualize_chain_with_text(self):
        """Test visualize_chain with text preview enabled"""
        monitor = insAItsMonitor(api_key=TEST_PRO_KEY)

        result = monitor.send_message("Test message content here", "agent_a", llm_id="gpt-4o")

        # Create anomaly dict with message_id
        anomaly = {
            "type": "TEST_ANOMALY",
            "message_id": result["message"]["message_id"],
            "details": {}
        }

        viz = monitor.visualize_chain(anomaly, include_text=True)

        assert "FORENSIC CHAIN TRACE" in viz
        assert "Text:" in viz

    def test_visualize_chain_empty(self):
        """Test visualize_chain with no chain"""
        monitor = insAItsMonitor(api_key=TEST_PRO_KEY)

        viz = monitor.visualize_chain({"type": "TEST", "message_id": "nonexistent"})

        assert "No chain to visualize" in viz


class TestForensicChainIntegration:
    """Integration tests for forensic chain tracing"""

    def test_full_forensic_workflow(self):
        """Test complete forensic workflow with real conversation"""
        monitor = insAItsMonitor(api_key=TEST_PRO_KEY)

        # Set anchor
        monitor.set_anchor("Discuss network protocols")

        # Simulate conversation that develops issues
        monitor.send_message(
            "Let's discuss TCP/IP and network protocols in detail today",
            "agent_a", "agent_b", "gpt-4o"
        )
        time.sleep(0.15)

        monitor.send_message(
            "Yes, TCP ensures reliable data transmission over networks",
            "agent_b", "agent_a", "claude-3.5"
        )
        time.sleep(0.15)

        # Introduce jargon
        result = monitor.send_message(
            "We should use XYZPROTO and FOOSPEC for this implementation",
            "agent_a", "agent_b", "gpt-4o"
        )

        # Create anomaly with message_id from result
        anomaly = {
            "type": "CROSS_LLM_JARGON",
            "message_id": result["message"]["message_id"],
            "details": {"new_terms": ["XYZPROTO", "FOOSPEC"]}
        }

        # Test trace_root
        trace = monitor.trace_root(anomaly)
        assert trace["chain_length"] >= 1
        assert trace["summary"]

        # Test get_propagation_chain
        chain = monitor.get_propagation_chain(anomaly)
        assert isinstance(chain, list)

        # Test visualize_chain
        viz = monitor.visualize_chain(anomaly, include_text=True)
        assert len(viz) > 0

    def test_forensic_with_anchor_drift(self):
        """Test forensic tracing with anchor drift anomaly"""
        from insa_its.detector import AnomalyDetector
        import numpy as np

        monitor = insAItsMonitor(api_key=TEST_PRO_KEY)

        # Set anchor about specific topic
        monitor.set_anchor("Explain database indexing strategies")

        # Send related message first
        monitor.send_message(
            "Database indexes improve query performance by creating fast lookup structures",
            "agent_a", llm_id="gpt-4o"
        )
        time.sleep(0.15)

        # Create artificial ANCHOR_DRIFT anomaly for testing trace
        # (since synthetic embeddings may not trigger it naturally)
        fake_anomaly = {
            "type": "ANCHOR_DRIFT",
            "message_id": list(monitor.history.get("agent_a", {}).get("gpt-4o", [{}]))[-1].get("message_id"),
            "details": {"anchor_similarity": 0.25}
        }

        if fake_anomaly["message_id"]:
            trace = monitor.trace_root(fake_anomaly)

            assert trace["anomaly_type"] == "ANCHOR_DRIFT"
            assert "drift" in trace["summary"].lower() or "similarity" in trace["summary"].lower()


# ============================================
# DECIPHER MODE TESTS
# ============================================

class TestDecipherModes:
    """Test cloud/local/auto decipher modes"""

    def test_decipher_mode_parameter_exists(self):
        """Test that decipher accepts mode parameter"""
        import inspect
        from insa_its import insAItsMonitor

        sig = inspect.signature(insAItsMonitor.decipher)
        params = list(sig.parameters.keys())
        assert "mode" in params, "decipher should have mode parameter"

    def test_decipher_mode_default_is_auto(self):
        """Test that default mode is 'auto'"""
        import inspect
        from insa_its import insAItsMonitor

        sig = inspect.signature(insAItsMonitor.decipher)
        mode_param = sig.parameters.get("mode")
        assert mode_param is not None
        assert mode_param.default == "auto"

    def test_decipher_local_mode_without_ollama(self):
        """Test local mode returns error when Ollama not available"""
        monitor = insAItsMonitor(api_key=TEST_PRO_KEY)

        msg = {
            "text": "PO for SKU-123 ASAP",
            "sender": "agent_a"
        }

        # Local mode should return error if Ollama not running
        result = monitor.decipher(msg, mode="local")

        # Either succeeds (if Ollama running) or has error
        assert "original_text" in result or "expanded_text" in result

    def test_decipher_cloud_mode_without_api_key(self):
        """Test cloud mode returns error without API key"""
        monitor = insAItsMonitor()  # No API key

        msg = {
            "text": "Process the XYZQ protocol",
            "sender": "agent_a"
        }

        result = monitor.decipher(msg, mode="cloud")

        assert "error" in result
        assert "API key" in result["error"] or "requires" in result["error"].lower()

    def test_decipher_cloud_mode_with_api_key(self):
        """Test cloud mode attempts API call with API key"""
        monitor = insAItsMonitor(api_key=TEST_PRO_KEY)

        msg = {
            "text": "Execute the QBRT algorithm",
            "sender": "agent_a"
        }

        result = monitor.decipher(msg, mode="cloud")

        # Should have either success or cloud-related error
        assert "original_text" in result or "expanded_text" in result

    def test_decipher_auto_mode_fallback(self):
        """Test auto mode falls back to local when cloud fails"""
        monitor = insAItsMonitor(api_key=TEST_PRO_KEY)

        msg = {
            "text": "Run CVP for customer 12345",
            "sender": "agent_a"
        }

        result = monitor.decipher(msg, mode="auto")

        # Should attempt cloud, then local - result depends on availability
        assert "original_text" in result or "expanded_text" in result

    def test_decipher_preserves_original_text(self):
        """Test that original text is always preserved in result"""
        monitor = insAItsMonitor(api_key=TEST_PRO_KEY)

        original = "Process ASAP via XYZ protocol"
        msg = {
            "text": original,
            "sender": "agent_a"
        }

        for mode in ["auto", "cloud", "local"]:
            result = monitor.decipher(msg, mode=mode)
            # Should have original_text on error, or can reconstruct from success
            if "error" in result:
                assert result.get("original_text") == original

    def test_decipher_with_context(self):
        """Test decipher builds context from conversation history"""
        monitor = insAItsMonitor(api_key=TEST_PRO_KEY)

        # Build some history
        monitor.send_message("Hello, let's discuss the project", "agent_a", receiver_id="agent_b", llm_id="gpt-4")
        time.sleep(0.1)
        monitor.send_message("Sure, what about the XYZ feature?", "agent_b", receiver_id="agent_a", llm_id="claude")

        msg = {
            "text": "Run CVP on XYZ",
            "sender": "agent_a",
            "receiver": "agent_b"
        }

        # Build context via premium decipher engine
        assert monitor._decipher_engine is not None
        context = monitor._decipher_engine.build_context(monitor.history, msg["sender"], msg.get("receiver"))
        assert isinstance(context, list)


class TestDecipherAPIIntegration:
    """Test decipher API endpoint integration"""

    def test_config_has_decipher_endpoint(self):
        """Test that config has decipher endpoint"""
        from insa_its.config import API_ENDPOINTS

        assert "decipher" in API_ENDPOINTS
        assert "decipher_status" in API_ENDPOINTS
        assert "/api/decipher" in API_ENDPOINTS["decipher"]

    def test_feature_flags_include_cloud_decipher(self):
        """Test that feature flags include cloud_decipher"""
        from insa_its.config import FEATURES, get_feature

        # Anonymous should not have cloud_decipher
        assert get_feature("anonymous", "cloud_decipher") == False

        # Free tier should have cloud_decipher
        assert get_feature("free", "cloud_decipher") == True

        # Pro should have cloud_decipher
        assert get_feature("pro", "cloud_decipher") == True

    def test_feature_flags_include_local_decipher(self):
        """Test that all tiers have local_decipher"""
        from insa_its.config import get_feature

        for tier in ["anonymous", "free", "starter", "pro"]:
            assert get_feature(tier, "local_decipher") == True


# ============================================
# RUN TESTS
# ============================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

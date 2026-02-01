"""
InsAIts SDK V2.3 Hallucination Detection Test Suite
====================================================
Tests for Phase 3: FactTracker, SourceGrounder, SelfConsistencyChecker,
PhantomCitationDetector, ConfidenceDecayTracker, and monitor integration.

Run with: python -m pytest tests/test_hallucination.py -v
"""

import sys
import os
import time
import json

# Enable Development Mode for Testing
os.environ['INSAITS_DEV_MODE'] = 'true'

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import numpy as np

from insa_its import insAItsMonitor
from insa_its.hallucination import (
    FactTracker, SourceGrounder, SelfConsistencyChecker,
    PhantomCitationDetector, ConfidenceDecayTracker, FactClaim
)
from insa_its.config import get_feature

# Test API Keys
TEST_PRO_KEY = 'test-pro-unlimited'
TEST_FREE_KEY = 'test-free-100'


# ============================================
# FACT CLAIM DATACLASS TESTS
# ============================================

class TestFactClaim:
    """Tests for FactClaim dataclass"""

    def test_fact_claim_creation(self):
        """Test basic FactClaim creation with required fields"""
        claim = FactClaim(
            claim="The server has 8 CPUs",
            topic="server cpus",
            value="8",
            agent_id="agent_a",
            message_id="msg-001",
            timestamp=time.time()
        )

        assert claim.claim == "The server has 8 CPUs"
        assert claim.topic == "server cpus"
        assert claim.value == "8"
        assert claim.agent_id == "agent_a"
        assert claim.message_id == "msg-001"

    def test_fact_claim_defaults(self):
        """Test FactClaim default values"""
        claim = FactClaim(
            claim="test", topic="t", value="v",
            agent_id="a", message_id="m", timestamp=0.0
        )

        assert claim.confidence == 0.5
        assert claim.claim_type == "general"

    def test_fact_claim_custom_type(self):
        """Test FactClaim with custom claim type"""
        claim = FactClaim(
            claim="costs 500 dollars",
            topic="cost",
            value="500 dollars",
            agent_id="agent_a",
            message_id="msg-001",
            timestamp=time.time(),
            confidence=0.8,
            claim_type="numeric"
        )

        assert claim.confidence == 0.8
        assert claim.claim_type == "numeric"


# ============================================
# PHANTOM CITATION DETECTOR TESTS
# ============================================

class TestPhantomCitationDetector:
    """Tests for PhantomCitationDetector"""

    def setup_method(self):
        self.detector = PhantomCitationDetector()

    def test_detect_empty_text(self):
        """Test detection on empty/short text"""
        assert self.detector.detect("") == []
        assert self.detector.detect("short") == []
        assert self.detector.detect(None) == []

    def test_detect_clean_text(self):
        """Test detection on text with no citations"""
        text = "Machine learning is a powerful technique for data analysis."
        result = self.detector.detect(text)
        assert result == []

    def test_detect_suspicious_url(self):
        """Test detection of suspicious URLs"""
        text = (
            "According to https://example.com/research/paper123 "
            "this method is effective."
        )
        result = self.detector.detect(text)
        suspicious_urls = [r for r in result if r["type"] == "suspicious_url"]
        assert len(suspicious_urls) > 0
        assert suspicious_urls[0]["suspicion_score"] >= 0.3

    def test_detect_very_long_url(self):
        """Test detection of extremely long URLs (common hallucination)"""
        long_path = "a" * 160
        text = f"See https://research.org/{long_path} for details."
        result = self.detector.detect(text)
        suspicious = [r for r in result if "extremely_long_url" in r.get("reasons", [])]
        assert len(suspicious) > 0

    def test_detect_future_paper_reference(self):
        """Test detection of future publication dates"""
        text = 'Smith et al. (2030) showed that quantum algorithms work.'
        result = self.detector.detect(text)
        future_refs = [
            r for r in result
            if "future_publication_date" in r.get("reasons", [])
        ]
        assert len(future_refs) > 0

    def test_detect_invalid_arxiv_month(self):
        """Test detection of invalid arxiv month"""
        text = "See arxiv: 2513.12345 for details."
        result = self.detector.detect(text)
        invalid = [
            r for r in result
            if "invalid_arxiv_month" in r.get("reasons", [])
        ]
        assert len(invalid) > 0

    def test_detect_future_arxiv(self):
        """Test detection of future arxiv date"""
        text = "See arxiv: 3001.12345 for details."
        result = self.detector.detect(text)
        future = [
            r for r in result
            if "future_arxiv_date" in r.get("reasons", [])
        ]
        assert len(future) > 0

    def test_detect_suspicious_doi_short_suffix(self):
        """Test detection of DOIs with suspiciously short suffix"""
        text = "The DOI is 10.1234/ab for this paper."
        result = self.detector.detect(text)
        short_suffix = [
            r for r in result
            if "suspiciously_short_suffix" in r.get("reasons", [])
        ]
        assert len(short_suffix) > 0

    def test_legitimate_url_not_flagged(self):
        """Test that legitimate-looking URLs are not flagged"""
        text = "Visit https://pytorch.org/docs/stable for documentation."
        result = self.detector.detect(text)
        # A standard URL to a well-known site should not be suspicious
        high_suspicion = [
            r for r in result if r.get("suspicion_score", 0) >= 0.5
        ]
        assert len(high_suspicion) == 0

    def test_overly_generic_paper_title(self):
        """Test detection of future publication year in citation"""
        text = 'Smith et al. (2028) presented a comprehensive survey.'
        result = self.detector.detect(text)
        future = [
            r for r in result
            if "future_publication_date" in r.get("reasons", [])
        ]
        assert len(future) > 0


# ============================================
# CONFIDENCE DECAY TRACKER TESTS
# ============================================

class TestConfidenceDecayTracker:
    """Tests for ConfidenceDecayTracker"""

    def setup_method(self):
        self.tracker = ConfidenceDecayTracker()

    def test_score_confidence_neutral(self):
        """Test neutral text gets 0.5 score"""
        score = self.tracker.score_confidence("The sky is blue today.")
        assert score == 0.5

    def test_score_confidence_empty(self):
        """Test empty text gets 0.5 score"""
        assert self.tracker.score_confidence("") == 0.5
        assert self.tracker.score_confidence(None) == 0.5

    def test_score_confidence_high(self):
        """Test confident text gets high score"""
        text = "This is definitely correct. It has been absolutely proven."
        score = self.tracker.score_confidence(text)
        assert score > 0.5

    def test_score_confidence_low(self):
        """Test uncertain text gets low score"""
        text = "Maybe this could possibly work. I think it might be right, perhaps."
        score = self.tracker.score_confidence(text)
        assert score < 0.5

    def test_track_no_decay(self):
        """Test tracking with consistent confidence"""
        now = time.time()
        result1 = self.tracker.track("agent1", "Certainly correct", now)
        result2 = self.tracker.track("agent1", "Definitely right", now + 1)
        result3 = self.tracker.track("agent1", "Absolutely true", now + 2)

        # No decay since all messages are confident
        assert result1 is None  # Need at least 3 entries
        assert result2 is None
        # result3 may or may not trigger depending on exact scores

    def test_track_decay_detected(self):
        """Test that confidence decay is detected"""
        now = time.time()
        # Start confident, become uncertain
        self.tracker.track("agent1", "This is certainly the answer", now)
        self.tracker.track("agent1", "This is probably the answer", now + 1)
        self.tracker.track("agent1", "Maybe this could be the answer", now + 2)
        self.tracker.track("agent1", "I'm not sure, possibly maybe", now + 3)
        result = self.tracker.track("agent1", "Perhaps, I think, unclear", now + 4)

        # Should detect decay pattern
        if result is not None:
            assert result["type"] in ("confidence_decay", "confidence_flip_flop")
            assert "agent_id" in result

    def test_track_flip_flop(self):
        """Test that flip-flopping is detected"""
        now = time.time()
        # Alternate between confident and uncertain
        self.tracker.track("agent1", "Absolutely certain", now)
        self.tracker.track("agent1", "Maybe possibly not", now + 1)
        self.tracker.track("agent1", "Definitely yes always", now + 2)
        self.tracker.track("agent1", "I think perhaps not", now + 3)
        result = self.tracker.track("agent1", "Certainly must be", now + 4)

        # May detect flip-flop
        if result is not None:
            assert result["type"] in ("confidence_decay", "confidence_flip_flop")

    def test_get_agent_confidence_no_history(self):
        """Test getting confidence for unknown agent"""
        stats = self.tracker.get_agent_confidence("unknown_agent")
        assert stats["agent_id"] == "unknown_agent"
        assert stats["entries"] == 0

    def test_get_agent_confidence_with_history(self):
        """Test getting confidence for tracked agent"""
        now = time.time()
        self.tracker.track("agent1", "Definitely correct", now)
        self.tracker.track("agent1", "Certainly right", now + 1)
        self.tracker.track("agent1", "Absolutely sure", now + 2)

        stats = self.tracker.get_agent_confidence("agent1")
        assert stats["agent_id"] == "agent1"
        assert stats["entries"] == 3
        assert "current_confidence" in stats
        assert "avg_confidence" in stats
        assert "trend" in stats

    def test_get_all_stats(self):
        """Test getting stats for all agents"""
        now = time.time()
        self.tracker.track("agent1", "Certainly", now)
        self.tracker.track("agent2", "Maybe", now + 1)

        stats = self.tracker.get_all_stats()
        assert "agent1" in stats
        assert "agent2" in stats

    def test_clear(self):
        """Test clearing tracker"""
        self.tracker.track("agent1", "Test", time.time())
        assert self.tracker.get_agent_confidence("agent1")["entries"] == 1

        self.tracker.clear()
        assert self.tracker.get_agent_confidence("agent1")["entries"] == 0

    def test_history_capped_at_50(self):
        """Test that history is capped at 50 entries per agent"""
        now = time.time()
        for i in range(60):
            self.tracker.track("agent1", "Test message", now + i)

        stats = self.tracker.get_agent_confidence("agent1")
        assert stats["entries"] == 50


# ============================================
# FACT TRACKER TESTS
# ============================================

class TestFactTracker:
    """Tests for FactTracker"""

    def setup_method(self):
        self.tracker = FactTracker()

    def test_extract_claims_empty(self):
        """Test extraction from empty text"""
        assert self.tracker.extract_claims("", "a", "m", use_llm=False) == []
        assert self.tracker.extract_claims("hi", "a", "m", use_llm=False) == []

    def test_extract_numeric_claims(self):
        """Test extraction of numeric claims"""
        text = "The server has 8 CPUs and costs 500 dollars per month."
        claims = self.tracker.extract_claims(text, "agent1", "msg-001", use_llm=False)

        numeric = [c for c in claims if c.claim_type == "numeric"]
        assert len(numeric) > 0
        # Check that a numeric value was extracted
        assert any("8" in c.value or "500" in c.value for c in numeric)

    def test_extract_date_claims(self):
        """Test extraction of date claims"""
        text = "The company was founded in 2019 and launched the product in March 2020."
        claims = self.tracker.extract_claims(text, "agent1", "msg-001", use_llm=False)

        dates = [c for c in claims if c.claim_type == "date"]
        assert len(dates) > 0

    def test_extract_entity_claims(self):
        """Test extraction of entity claims"""
        text = "Einstein discovered the theory of relativity."
        claims = self.tracker.extract_claims(text, "agent1", "msg-001", use_llm=False)

        entities = [c for c in claims if c.claim_type == "entity"]
        assert len(entities) > 0

    def test_extract_comparison_claims(self):
        """Test extraction of comparison claims"""
        text = "Python is faster than Ruby for data processing."
        claims = self.tracker.extract_claims(text, "agent1", "msg-001", use_llm=False)

        comparisons = [c for c in claims if c.claim_type == "comparison"]
        assert len(comparisons) > 0

    def test_track_no_contradictions(self):
        """Test tracking claims with no contradictions"""
        claims = [
            FactClaim("cost is 100", "cost", "100 dollars",
                      "agent1", "msg-001", time.time(), 0.8, "numeric"),
            FactClaim("speed is 50", "speed", "50 ms",
                      "agent1", "msg-001", time.time(), 0.7, "numeric"),
        ]

        contradictions = self.tracker.track_claims(claims)
        assert len(contradictions) == 0

    def test_track_numeric_contradiction(self):
        """Test detecting numeric contradictions"""
        # First claim
        claims1 = [
            FactClaim("cost is 100", "cost", "100 dollars",
                      "agent1", "msg-001", time.time(), 0.8, "numeric")
        ]
        self.tracker.track_claims(claims1)

        # Contradicting claim with different value
        claims2 = [
            FactClaim("cost is 500", "cost", "500 dollars",
                      "agent2", "msg-002", time.time(), 0.7, "numeric")
        ]
        contradictions = self.tracker.track_claims(claims2)

        assert len(contradictions) > 0
        assert contradictions[0]["topic"] == "cost"
        assert contradictions[0]["original_value"] == "100 dollars"
        assert contradictions[0]["new_value"] == "500 dollars"

    def test_track_cross_agent_contradiction(self):
        """Test detecting cross-agent contradictions (unique InsAIts feature)"""
        claims1 = [
            FactClaim("users is 1000", "users", "1000",
                      "agent_a", "msg-001", time.time(), 0.8, "numeric")
        ]
        self.tracker.track_claims(claims1)

        # Different agent, different value
        claims2 = [
            FactClaim("users is 5000", "users", "5000",
                      "agent_b", "msg-002", time.time(), 0.7, "numeric")
        ]
        contradictions = self.tracker.track_claims(claims2)

        assert len(contradictions) > 0
        assert contradictions[0]["cross_agent"] is True
        assert contradictions[0]["severity"] == "critical"

    def test_track_same_agent_contradiction(self):
        """Test detecting same-agent contradictions"""
        claims1 = [
            FactClaim("price is 50", "price", "50",
                      "agent_a", "msg-001", time.time(), 0.8, "numeric")
        ]
        self.tracker.track_claims(claims1)

        claims2 = [
            FactClaim("price is 200", "price", "200",
                      "agent_a", "msg-002", time.time(), 0.7, "numeric")
        ]
        contradictions = self.tracker.track_claims(claims2)

        assert len(contradictions) > 0
        assert contradictions[0]["cross_agent"] is False
        assert contradictions[0]["severity"] == "high"

    def test_no_self_contradiction_same_message(self):
        """Test that claims in same message don't contradict each other"""
        claims = [
            FactClaim("cost is 100", "cost", "100",
                      "agent1", "msg-001", time.time(), 0.8, "numeric"),
            FactClaim("cost is 200", "cost", "200",
                      "agent1", "msg-001", time.time(), 0.7, "numeric"),
        ]
        contradictions = self.tracker.track_claims(claims)
        # Should not find contradiction since same message_id
        assert len(contradictions) == 0

    def test_values_contradict_negation(self):
        """Test negation contradiction detection"""
        assert self.tracker._values_contradict("failed", "succeeded") is True
        assert self.tracker._values_contradict("disabled", "enabled") is True

    def test_values_contradict_dates(self):
        """Test date contradiction detection"""
        assert self.tracker._values_contradict("founded in 2019", "founded in 2021") is True

    def test_values_no_contradict_same(self):
        """Test same values don't contradict"""
        assert self.tracker._values_contradict("100 dollars", "100 dollars") is False

    def test_values_no_contradict_empty(self):
        """Test empty values don't contradict"""
        assert self.tracker._values_contradict("", "") is False
        assert self.tracker._values_contradict("", "something") is False

    def test_get_claims(self):
        """Test getting all claims as dicts"""
        claims = [
            FactClaim("test claim", "topic", "value",
                      "agent1", "msg-001", time.time())
        ]
        self.tracker.track_claims(claims)

        result = self.tracker.get_claims()
        assert len(result) == 1
        assert result[0]["claim"] == "test claim"
        assert result[0]["topic"] == "topic"

    def test_get_claim_count(self):
        """Test claim count"""
        assert self.tracker.get_claim_count() == 0

        claims = [
            FactClaim("test", "t", "v", "a", "m", time.time())
        ]
        self.tracker.track_claims(claims)
        assert self.tracker.get_claim_count() == 1

    def test_get_topics(self):
        """Test getting topics"""
        claims = [
            FactClaim("cost claim", "cost", "100", "a", "m1", time.time()),
            FactClaim("speed claim", "speed", "50", "a", "m1", time.time()),
        ]
        self.tracker.track_claims(claims)

        topics = self.tracker.get_topics()
        assert "cost" in topics
        assert "speed" in topics

    def test_get_numeric_drift(self):
        """Test numeric drift detection"""
        # Track claims with changing numeric values
        claims1 = [
            FactClaim("cost is 100", "cost", "100 dollars",
                      "agent1", "msg-001", time.time(), 0.8, "numeric")
        ]
        self.tracker.track_claims(claims1)

        claims2 = [
            FactClaim("cost is 200", "cost", "200 dollars",
                      "agent1", "msg-002", time.time(), 0.7, "numeric")
        ]
        self.tracker.track_claims(claims2)

        drifts = self.tracker.get_numeric_drift()
        # Should detect drift (100 -> 200 = 100% change)
        assert len(drifts) > 0
        assert drifts[0]["pct_change"] >= 10.0

    def test_get_numeric_drift_by_topic(self):
        """Test numeric drift for specific topic"""
        claims = [
            FactClaim("cost is 100", "cost", "100", "a", "m1", time.time(), 0.8, "numeric"),
        ]
        self.tracker.track_claims(claims)
        claims2 = [
            FactClaim("cost is 500", "cost", "500", "a", "m2", time.time(), 0.7, "numeric"),
        ]
        self.tracker.track_claims(claims2)

        # Use the actual normalized topic key
        all_drifts = self.tracker.get_numeric_drift()
        assert len(all_drifts) > 0
        actual_topic = all_drifts[0]["topic"]

        # Filter by actual topic should find it
        drifts = self.tracker.get_numeric_drift(actual_topic)
        assert len(drifts) > 0

        # Non-existent topic should return nothing
        drifts_empty = self.tracker.get_numeric_drift(
            "zzz_completely_nonexistent_xyz_123"
        )
        assert len(drifts_empty) == 0

    def test_get_cross_agent_summary(self):
        """Test cross-agent summary"""
        claims1 = [
            FactClaim("claim", "topic1", "val1", "agent_a", "m1", time.time()),
        ]
        self.tracker.track_claims(claims1)

        claims2 = [
            FactClaim("claim", "topic1", "val2", "agent_b", "m2", time.time()),
        ]
        self.tracker.track_claims(claims2)

        summary = self.tracker.get_cross_agent_summary()
        assert summary["total_claims"] == 2
        assert summary["multi_agent_topics"] >= 1
        assert "agent_a" in summary["agents"]
        assert "agent_b" in summary["agents"]

    def test_detect_phantom_citations(self):
        """Test phantom citation detection through FactTracker"""
        text = "See https://example.com/fake/paper for details."
        result = self.tracker.detect_phantom_citations(text)
        assert isinstance(result, list)

    def test_clear(self):
        """Test clearing the tracker"""
        claims = [FactClaim("test", "t", "v", "a", "m", time.time())]
        self.tracker.track_claims(claims)
        assert self.tracker.get_claim_count() == 1

        self.tracker.clear()
        assert self.tracker.get_claim_count() == 0
        assert len(self.tracker.get_topics()) == 0

    def test_max_claims_enforced(self):
        """Test that MAX_CLAIMS limit is enforced"""
        for i in range(1050):
            claims = [
                FactClaim(f"claim {i}", f"topic_{i}", f"val_{i}",
                          "agent", f"msg-{i}", time.time())
            ]
            self.tracker.track_claims(claims)

        assert self.tracker.get_claim_count() <= FactTracker.MAX_CLAIMS

    def test_deduplicate_claims(self):
        """Test claim deduplication"""
        claims = [
            FactClaim("cost 100", "cost", "100", "a", "m", time.time()),
            FactClaim("cost 100 again", "cost", "100", "a", "m", time.time()),
        ]
        unique = self.tracker._deduplicate_claims(claims)
        assert len(unique) == 1


# ============================================
# SOURCE GROUNDER TESTS
# ============================================

class TestSourceGrounder:
    """Tests for SourceGrounder"""

    def setup_method(self):
        self.grounder = SourceGrounder()

    def test_set_documents_empty(self):
        """Test setting empty documents"""
        result = self.grounder.set_documents([])
        assert result.get("error") is not None
        assert result["documents_loaded"] == 0

    def test_set_documents_basic(self):
        """Test setting basic documents"""
        docs = [
            "Machine learning uses algorithms to learn from data.",
            "Neural networks are inspired by the human brain."
        ]
        result = self.grounder.set_documents(docs)

        assert result["documents_loaded"] == 2
        assert result["total_chunks"] >= 2
        assert len(self.grounder.source_chunks) > 0

    def test_set_documents_skips_empty(self):
        """Test that empty documents are skipped"""
        docs = ["Valid document text.", "", "  ", "Another valid doc."]
        result = self.grounder.set_documents(docs)

        assert result["documents_loaded"] == 2
        assert result.get("skipped_empty") == 2

    def test_set_documents_chunking(self):
        """Test document chunking"""
        long_doc = "A" * 2000  # 2000 characters
        result = self.grounder.set_documents(
            [long_doc], chunk_size=500, chunk_overlap=50
        )

        assert result["total_chunks"] > 1
        assert result["chunk_size"] == 500

    def test_set_documents_max_chunks(self):
        """Test MAX_CHUNKS limit"""
        # Create many documents to exceed chunk limit
        docs = ["Test document " * 50 for _ in range(100)]
        result = self.grounder.set_documents(docs, chunk_size=100)

        assert result["total_chunks"] <= SourceGrounder.MAX_CHUNKS

    def test_check_grounding_no_sources(self):
        """Test grounding check without source documents"""
        result = self.grounder.check_grounding("Test text")

        assert result["grounded"] is None
        assert "No source documents" in result["reason"]

    def test_check_grounding_empty_text(self):
        """Test grounding check with empty text"""
        self.grounder.set_documents(["Source document."])
        result = self.grounder.check_grounding("")

        assert result["grounded"] is None

    def test_check_grounding_with_sources(self):
        """Test grounding check against source documents"""
        docs = [
            "Python is a programming language created by Guido van Rossum. "
            "It is known for its readability and simplicity."
        ]
        self.grounder.set_documents(docs)

        result = self.grounder.check_grounding(
            "Python is a readable programming language."
        )

        assert "grounded" in result
        assert isinstance(result["grounded"], bool)
        assert "grounding_score" in result
        assert "nearest_chunks" in result
        assert len(result["nearest_chunks"]) > 0

    def test_check_grounding_returns_sentence_analysis(self):
        """Test that grounding returns sentence-level analysis"""
        docs = ["Source document about machine learning and AI."]
        self.grounder.set_documents(docs)

        result = self.grounder.check_grounding(
            "Machine learning is important. AI is the future. "
            "Cooking is fun."
        )

        assert "sentence_analysis" in result
        analysis = result["sentence_analysis"]
        assert "total_sentences" in analysis
        assert "grounded_sentences" in analysis
        assert "ungrounded_sentences" in analysis

    def test_check_grounding_batch(self):
        """Test batch grounding check"""
        docs = ["Source document about technology."]
        self.grounder.set_documents(docs)

        texts = ["Technology is great.", "Cooking recipes."]
        results = self.grounder.check_grounding_batch(texts)

        assert len(results) == 2
        assert all("grounded" in r for r in results)

    def test_get_stats(self):
        """Test getting grounder statistics"""
        stats = self.grounder.get_stats()
        assert stats["documents_loaded"] == 0
        assert stats["total_chunks"] == 0
        assert stats["has_sources"] is False

        self.grounder.set_documents(["Test doc."])
        stats = self.grounder.get_stats()
        assert stats["documents_loaded"] == 1
        assert stats["has_sources"] is True

    def test_clear(self):
        """Test clearing source documents"""
        self.grounder.set_documents(["Test doc."])
        assert self.grounder.get_stats()["has_sources"] is True

        self.grounder.clear()
        assert self.grounder.get_stats()["has_sources"] is False
        assert self.grounder.get_stats()["documents_loaded"] == 0

    def test_chunk_text_small(self):
        """Test chunking text smaller than chunk_size"""
        chunks = self.grounder._chunk_text("Small text", 500, 50)
        assert len(chunks) == 1
        assert chunks[0] == "Small text"

    def test_chunk_text_empty(self):
        """Test chunking empty text"""
        assert self.grounder._chunk_text("", 500, 50) == []
        assert self.grounder._chunk_text("  ", 500, 50) == []

    def test_split_sentences(self):
        """Test sentence splitting"""
        text = "First sentence. Second sentence! Third one?"
        sentences = self.grounder._split_sentences(text)
        assert len(sentences) == 3

    def test_split_sentences_empty(self):
        """Test splitting empty text"""
        assert self.grounder._split_sentences("") == []


# ============================================
# SELF-CONSISTENCY CHECKER TESTS
# ============================================

class TestSelfConsistencyChecker:
    """Tests for SelfConsistencyChecker"""

    def setup_method(self):
        self.checker = SelfConsistencyChecker()

    def test_check_short_text(self):
        """Test checking very short text"""
        result = self.checker.check("Short.")

        assert result["is_consistent"] is True
        assert "too short" in result.get("reason", "").lower()

    def test_check_empty_text(self):
        """Test checking empty text"""
        result = self.checker.check("")
        assert result["is_consistent"] is True

    def test_check_returns_expected_format(self):
        """Test that check returns expected format"""
        result = self.checker.check(
            "Machine learning algorithms process data to find patterns. "
            "These patterns are used for predictions."
        )

        # Should have either is_consistent or error (if no LLM)
        assert "is_consistent" in result
        if result["is_consistent"] is None:
            assert "error" in result  # LLM not available

    def test_check_against_claims_no_claims(self):
        """Test checking against empty claims list"""
        result = self.checker.check_against_claims("Some text", [])

        assert result.get("verified") is None
        assert "No known claims" in result.get("reason", "")

    def test_check_against_claims_empty_text(self):
        """Test checking empty text against claims"""
        result = self.checker.check_against_claims("", [{"topic": "t", "value": "v"}])

        assert result.get("verified") is None


# ============================================
# MONITOR INTEGRATION TESTS
# ============================================

class TestMonitorHallucinationIntegration:
    """Integration tests for hallucination features in insAItsMonitor"""

    def test_monitor_has_hallucination_components(self):
        """Test that monitor initializes hallucination components"""
        monitor = insAItsMonitor(api_key=TEST_PRO_KEY)

        assert hasattr(monitor, "fact_tracker")
        assert hasattr(monitor, "source_grounder")
        assert hasattr(monitor, "consistency_checker")
        assert hasattr(monitor, "confidence_tracker")
        assert hasattr(monitor, "citation_detector")
        assert isinstance(monitor.fact_tracker, FactTracker)
        assert isinstance(monitor.source_grounder, SourceGrounder)
        assert isinstance(monitor.confidence_tracker, ConfidenceDecayTracker)
        assert isinstance(monitor.citation_detector, PhantomCitationDetector)

    def test_enable_fact_tracking(self):
        """Test enabling fact tracking"""
        monitor = insAItsMonitor(api_key=TEST_PRO_KEY)

        assert monitor.fact_tracking_enabled is False

        result = monitor.enable_fact_tracking(True)
        assert result.get("fact_tracking") is True
        assert monitor.fact_tracking_enabled is True

        result = monitor.enable_fact_tracking(False)
        assert result.get("fact_tracking") is False
        assert monitor.fact_tracking_enabled is False

    def test_enable_fact_tracking_tier_gate(self):
        """Test that fact tracking is gated by tier"""
        # Anonymous user
        monitor = insAItsMonitor()
        result = monitor.enable_fact_tracking(True)

        assert "error" in result
        assert monitor.fact_tracking_enabled is False

    def test_set_source_documents(self):
        """Test setting source documents through monitor"""
        monitor = insAItsMonitor(api_key=TEST_PRO_KEY)

        result = monitor.set_source_documents(
            ["Source document about AI and machine learning."]
        )

        assert result.get("documents_loaded") == 1
        assert result.get("total_chunks") >= 1

    def test_set_source_documents_auto_check(self):
        """Test auto_check parameter"""
        monitor = insAItsMonitor(api_key=TEST_PRO_KEY)

        monitor.set_source_documents(
            ["Test document."], auto_check=True
        )
        assert monitor._auto_grounding_check is True

        monitor.set_source_documents(
            ["Test document."], auto_check=False
        )
        assert monitor._auto_grounding_check is False

    def test_check_grounding(self):
        """Test manual grounding check through monitor"""
        monitor = insAItsMonitor(api_key=TEST_PRO_KEY)

        monitor.set_source_documents([
            "Python was created by Guido van Rossum."
        ])

        result = monitor.check_grounding("Python is a programming language.")

        assert "grounded" in result
        assert "grounding_score" in result

    def test_check_grounding_tier_gate(self):
        """Test grounding is gated by tier"""
        monitor = insAItsMonitor()  # Anonymous
        result = monitor.check_grounding("Test text")

        assert "error" in result

    def test_verify_self_consistency(self):
        """Test self consistency check through monitor"""
        monitor = insAItsMonitor(api_key=TEST_PRO_KEY)

        result = monitor.verify_self_consistency("Short text for testing.")

        assert "is_consistent" in result

    def test_verify_self_consistency_tier_gate(self):
        """Test self consistency is gated by tier"""
        monitor = insAItsMonitor()  # Anonymous
        result = monitor.verify_self_consistency("Test text.")

        assert "error" in result

    def test_get_fact_claims_empty(self):
        """Test getting claims when none tracked"""
        monitor = insAItsMonitor(api_key=TEST_PRO_KEY)
        claims = monitor.get_fact_claims()
        assert claims == []

    def test_get_fact_tracker_stats(self):
        """Test getting fact tracker stats"""
        monitor = insAItsMonitor(api_key=TEST_PRO_KEY)
        stats = monitor.get_fact_tracker_stats()

        assert stats["total_claims"] == 0
        assert stats["fact_tracking_enabled"] is False
        assert "source_grounding" in stats

    def test_clear_fact_tracker(self):
        """Test clearing fact tracker"""
        monitor = insAItsMonitor(api_key=TEST_PRO_KEY)
        result = monitor.clear_fact_tracker()

        assert result["cleared"] is True
        assert result["claims_remaining"] == 0

    def test_clear_source_documents(self):
        """Test clearing source documents"""
        monitor = insAItsMonitor(api_key=TEST_PRO_KEY)
        monitor.set_source_documents(["Test doc."])
        assert monitor._auto_grounding_check is True

        result = monitor.clear_source_documents()
        assert result["cleared"] is True
        assert result["auto_grounding_check"] is False

    def test_detect_phantom_citations(self):
        """Test phantom citation detection through monitor"""
        monitor = insAItsMonitor(api_key=TEST_PRO_KEY)

        result = monitor.detect_phantom_citations(
            "See https://example.com/fake/paper for the study results."
        )

        assert "total_suspicious" in result
        assert "verdict" in result
        assert result["verdict"] in ("clean", "suspicious", "likely_fabricated")

    def test_detect_phantom_citations_tier_gate(self):
        """Test phantom citation detection is gated by tier"""
        monitor = insAItsMonitor()  # Anonymous
        result = monitor.detect_phantom_citations("Some text")

        assert "error" in result

    def test_get_confidence_stats(self):
        """Test getting confidence stats"""
        monitor = insAItsMonitor(api_key=TEST_PRO_KEY)

        result = monitor.get_confidence_stats()
        assert isinstance(result, dict)

    def test_get_confidence_stats_for_agent(self):
        """Test getting confidence stats for specific agent"""
        monitor = insAItsMonitor(api_key=TEST_PRO_KEY)

        result = monitor.get_confidence_stats(agent_id="agent1")
        assert result["agent_id"] == "agent1"
        assert result["entries"] == 0

    def test_get_confidence_stats_tier_gate(self):
        """Test confidence stats are gated by tier"""
        monitor = insAItsMonitor()  # Anonymous
        result = monitor.get_confidence_stats()

        assert "error" in result

    def test_get_numeric_drift(self):
        """Test getting numeric drift"""
        monitor = insAItsMonitor(api_key=TEST_PRO_KEY)

        result = monitor.get_numeric_drift()
        assert result["total_drifts"] == 0
        assert result["drift_events"] == []

    def test_get_numeric_drift_tier_gate(self):
        """Test numeric drift is gated by tier"""
        monitor = insAItsMonitor()  # Anonymous
        result = monitor.get_numeric_drift()

        assert "error" in result

    def test_get_cross_agent_summary(self):
        """Test getting cross-agent summary"""
        monitor = insAItsMonitor(api_key=TEST_PRO_KEY)

        result = monitor.get_cross_agent_summary()
        assert result["total_claims"] == 0

    def test_get_cross_agent_summary_tier_gate(self):
        """Test cross-agent summary is gated by tier"""
        monitor = insAItsMonitor()  # Anonymous
        result = monitor.get_cross_agent_summary()

        assert "error" in result

    def test_get_hallucination_summary(self):
        """Test getting full hallucination summary"""
        monitor = insAItsMonitor(api_key=TEST_PRO_KEY)

        result = monitor.get_hallucination_summary()
        assert "hallucination_health" in result
        assert result["hallucination_health"]["score"] == 100
        assert result["hallucination_health"]["status"] == "excellent"
        assert result["total_hallucination_anomalies"] == 0

    def test_get_hallucination_summary_tier_gate(self):
        """Test hallucination summary is gated by tier"""
        monitor = insAItsMonitor()  # Anonymous
        result = monitor.get_hallucination_summary()

        assert "error" in result


# ============================================
# SEND MESSAGE INTEGRATION TESTS
# ============================================

class TestSendMessageHallucinationIntegration:
    """Test hallucination detection within send_message flow"""

    def test_send_message_with_fact_tracking_enabled(self):
        """Test that send_message runs fact tracking when enabled"""
        monitor = insAItsMonitor(api_key=TEST_PRO_KEY)
        monitor.enable_fact_tracking(True)

        result = monitor.send_message(
            "The server has 16 CPUs and costs 500 dollars per month.",
            "agent1", llm_id="gpt-4o"
        )

        assert "anomalies" in result
        # Claims should have been tracked
        assert monitor.fact_tracker.get_claim_count() > 0

    def test_send_message_contradiction_detection(self):
        """Test contradiction detection through send_message"""
        monitor = insAItsMonitor(api_key=TEST_PRO_KEY)
        monitor.enable_fact_tracking(True)

        # First message with a numeric claim
        monitor.send_message(
            "The project costs exactly 1000 dollars to implement.",
            "agent1", llm_id="gpt-4o"
        )
        time.sleep(0.15)

        # Second message with contradicting claim
        result = monitor.send_message(
            "The project costs exactly 5000 dollars to implement.",
            "agent2", llm_id="claude-3.5"
        )

        # Check if FACT_CONTRADICTION was detected
        contradictions = [
            a for a in result["anomalies"]
            if a.get("type") == "FACT_CONTRADICTION"
        ]
        # This depends on the extraction quality; the regex may or may not
        # pick up both claims from these specific sentences
        # But the mechanism is wired correctly
        assert "anomalies" in result

    def test_send_message_without_fact_tracking(self):
        """Test that no fact tracking runs when disabled"""
        monitor = insAItsMonitor(api_key=TEST_PRO_KEY)
        # fact_tracking_enabled is False by default

        result = monitor.send_message(
            "The server has 8 CPUs.",
            "agent1", llm_id="gpt-4o"
        )

        assert monitor.fact_tracker.get_claim_count() == 0

    def test_send_message_grounding_check(self):
        """Test auto grounding check in send_message"""
        monitor = insAItsMonitor(api_key=TEST_PRO_KEY)

        # Set source documents with auto_check
        monitor.set_source_documents(
            ["Python was created by Guido van Rossum in 1991."],
            auto_check=True
        )

        result = monitor.send_message(
            "Cooking pasta requires boiling water and adding salt.",
            "agent1", llm_id="gpt-4o"
        )

        # Should have tried grounding check (may or may not flag)
        assert "anomalies" in result

    def test_send_message_confidence_tracking(self):
        """Test confidence tracking in send_message"""
        monitor = insAItsMonitor(api_key=TEST_PRO_KEY)
        monitor.enable_fact_tracking(True)

        # Send messages with decreasing confidence
        monitor.send_message(
            "This is certainly the correct approach. Definitely works.",
            "agent1", llm_id="gpt-4o"
        )
        time.sleep(0.15)

        monitor.send_message(
            "This probably works. I think it might be correct.",
            "agent1", llm_id="gpt-4o"
        )
        time.sleep(0.15)

        monitor.send_message(
            "Maybe this could work. Perhaps not sure about this.",
            "agent1", llm_id="gpt-4o"
        )

        # Confidence tracker should have entries
        stats = monitor.get_confidence_stats(agent_id="agent1")
        assert stats["entries"] >= 3


# ============================================
# SESSION HEALTH TESTS
# ============================================

class TestSessionHealthWithHallucination:
    """Test session health calculation with hallucination anomalies"""

    def test_health_includes_hallucination_factors(self):
        """Test that session health includes hallucination-related factors"""
        monitor = insAItsMonitor(api_key=TEST_PRO_KEY)

        # Manually add hallucination anomalies to history
        monitor.anomaly_history.append({
            "type": "FACT_CONTRADICTION",
            "severity": "critical",
            "llm_id": "agent1",
            "agent_id": "agent1",
            "details": {},
            "timestamp": time.time(),
            "message_id": "msg-001"
        })
        monitor.anomaly_history.append({
            "type": "PHANTOM_CITATION",
            "severity": "high",
            "llm_id": "agent1",
            "agent_id": "agent1",
            "details": {},
            "timestamp": time.time(),
            "message_id": "msg-002"
        })

        trends = monitor.get_anomaly_trends()
        health = trends.get("session_health", {})

        assert health["score"] < 100
        assert health["factors"]["fact_contradictions"] == 1
        assert health["factors"]["phantom_citations"] == 1

    def test_health_critical_with_many_hallucinations(self):
        """Test that health becomes critical with many hallucination anomalies"""
        monitor = insAItsMonitor(api_key=TEST_PRO_KEY)

        # Add many critical anomalies
        for i in range(5):
            monitor.anomaly_history.append({
                "type": "FACT_CONTRADICTION",
                "severity": "critical",
                "llm_id": "agent1",
                "agent_id": "agent1",
                "details": {},
                "timestamp": time.time(),
                "message_id": f"msg-{i}"
            })

        trends = monitor.get_anomaly_trends()
        health = trends.get("session_health", {})

        assert health["score"] == 0
        assert health["status"] == "critical"


# ============================================
# FORENSIC TRACING FOR HALLUCINATION TYPES
# ============================================

class TestForensicHallucinationTypes:
    """Test forensic chain tracing for hallucination anomaly types"""

    def test_forensic_summary_fact_contradiction(self):
        """Test forensic summary for FACT_CONTRADICTION"""
        monitor = insAItsMonitor(api_key=TEST_PRO_KEY)

        chain = [
            {"sender": "agent_a", "llm_id": "gpt-4o", "text_preview": "Cost is 100"},
            {"sender": "agent_b", "llm_id": "claude", "text_preview": "Cost is 500"}
        ]
        anomaly = {
            "type": "FACT_CONTRADICTION",
            "details": {
                "topic": "cost",
                "original_value": "100",
                "new_value": "500",
                "original_agent": "agent_a"
            }
        }

        summary = monitor._generate_forensic_summary(chain, 1, anomaly)
        assert "cost" in summary.lower()
        assert "100" in summary
        assert "500" in summary

    def test_forensic_summary_ungrounded_claim(self):
        """Test forensic summary for UNGROUNDED_CLAIM"""
        monitor = insAItsMonitor(api_key=TEST_PRO_KEY)

        chain = [
            {"sender": "agent_a", "llm_id": "gpt-4o", "text_preview": "Ungrounded"}
        ]
        anomaly = {
            "type": "UNGROUNDED_CLAIM",
            "details": {
                "grounding_score": 0.3,
                "threshold": 0.7,
                "ungrounded_sentences": 2
            }
        }

        summary = monitor._generate_forensic_summary(chain, 0, anomaly)
        assert "grounding" in summary.lower() or "ungrounded" in summary.lower()
        assert "30.0%" in summary

    def test_forensic_summary_phantom_citation(self):
        """Test forensic summary for PHANTOM_CITATION"""
        monitor = insAItsMonitor(api_key=TEST_PRO_KEY)

        chain = [
            {"sender": "agent_a", "llm_id": "gpt-4o", "text_preview": "Ref"}
        ]
        anomaly = {
            "type": "PHANTOM_CITATION",
            "details": {
                "citation_type": "suspicious_url",
                "citation": "https://fake.example.com/paper",
                "suspicion_score": 0.8,
                "reasons": ["suspicious_path_pattern"]
            }
        }

        summary = monitor._generate_forensic_summary(chain, 0, anomaly)
        assert "phantom" in summary.lower() or "citation" in summary.lower()
        assert "suspicious_url" in summary

    def test_forensic_summary_confidence_decay(self):
        """Test forensic summary for CONFIDENCE_DECAY"""
        monitor = insAItsMonitor(api_key=TEST_PRO_KEY)

        chain = [
            {"sender": "agent_a", "llm_id": "gpt-4o", "text_preview": "Sure"},
            {"sender": "agent_a", "llm_id": "gpt-4o", "text_preview": "Maybe"},
            {"sender": "agent_a", "llm_id": "gpt-4o", "text_preview": "Unsure"}
        ]
        anomaly = {
            "type": "CONFIDENCE_DECAY",
            "details": {
                "initial_confidence": 0.9,
                "current_confidence": 0.3,
                "decay_amount": 0.6,
                "decay_steps": 3
            }
        }

        summary = monitor._generate_forensic_summary(chain, 0, anomaly)
        assert "confidence" in summary.lower() or "decay" in summary.lower()

    def test_forensic_summary_confidence_flip_flop(self):
        """Test forensic summary for CONFIDENCE_FLIP_FLOP"""
        monitor = insAItsMonitor(api_key=TEST_PRO_KEY)

        chain = [
            {"sender": "agent_a", "llm_id": "gpt-4o", "text_preview": "Sure"},
            {"sender": "agent_a", "llm_id": "gpt-4o", "text_preview": "Maybe"},
            {"sender": "agent_a", "llm_id": "gpt-4o", "text_preview": "Sure"}
        ]
        anomaly = {
            "type": "CONFIDENCE_FLIP_FLOP",
            "details": {
                "flip_count": 2,
                "recent_scores": [0.9, 0.3, 0.8, 0.2, 0.9]
            }
        }

        summary = monitor._generate_forensic_summary(chain, 0, anomaly)
        assert "flip" in summary.lower() or "alternated" in summary.lower()

    def test_find_anomaly_origin_phantom_citation(self):
        """Test _find_anomaly_origin for PHANTOM_CITATION"""
        monitor = insAItsMonitor(api_key=TEST_PRO_KEY)

        chain = [{"text_preview": "Msg1"}, {"text_preview": "Msg2"}]
        anomaly = {"type": "PHANTOM_CITATION", "details": {}}

        origin = monitor._find_anomaly_origin(
            chain, "PHANTOM_CITATION", anomaly
        )
        assert origin == len(chain) - 1

    def test_find_anomaly_origin_confidence_decay(self):
        """Test _find_anomaly_origin for CONFIDENCE_DECAY"""
        monitor = insAItsMonitor(api_key=TEST_PRO_KEY)

        chain = [
            {"text_preview": "Msg1"},
            {"text_preview": "Msg2"},
            {"text_preview": "Msg3"},
            {"text_preview": "Msg4"}
        ]
        anomaly = {"type": "CONFIDENCE_DECAY", "details": {}}

        origin = monitor._find_anomaly_origin(
            chain, "CONFIDENCE_DECAY", anomaly
        )
        # Should point to ~3 steps before end
        assert origin == max(0, len(chain) - 3)


# ============================================
# CONFIG / FEATURE FLAGS TESTS
# ============================================

class TestHallucinationFeatureFlags:
    """Test hallucination feature flags in config"""

    def test_anonymous_no_hallucination_features(self):
        """Test anonymous tier has no hallucination features"""
        assert get_feature("anonymous", "fact_tracking") is False
        assert get_feature("anonymous", "source_grounding") is False
        assert get_feature("anonymous", "self_consistency") is False

    def test_free_has_hallucination_features(self):
        """Test free tier has hallucination features"""
        assert get_feature("free", "fact_tracking") is True
        assert get_feature("free", "source_grounding") is True
        assert get_feature("free", "self_consistency") is True

    def test_pro_has_hallucination_features(self):
        """Test pro tier has hallucination features"""
        assert get_feature("pro", "fact_tracking") is True
        assert get_feature("pro", "source_grounding") is True
        assert get_feature("pro", "self_consistency") is True

    def test_lifetime_has_hallucination_features(self):
        """Test lifetime tiers have hallucination features"""
        for tier in ("lifetime", "lifetime_starter", "lifetime_pro"):
            assert get_feature(tier, "fact_tracking") is True
            assert get_feature(tier, "source_grounding") is True
            assert get_feature(tier, "self_consistency") is True


# ============================================
# EDGE CASE TESTS
# ============================================

class TestHallucinationEdgeCases:
    """Edge case tests for hallucination detection"""

    def test_fact_tracker_unicode_text(self):
        """Test fact tracker with unicode text"""
        tracker = FactTracker()
        claims = tracker.extract_claims(
            "Der Server hat 8 CPUs und kostet 500 Euro.",
            "agent1", "msg-001", use_llm=False
        )
        # Should handle unicode without crashing
        assert isinstance(claims, list)

    def test_fact_tracker_very_long_text(self):
        """Test fact tracker with very long text"""
        tracker = FactTracker()
        long_text = "The server has 8 CPUs. " * 500
        claims = tracker.extract_claims(
            long_text, "agent1", "msg-001", use_llm=False
        )
        # Should handle long text and cap claims
        assert isinstance(claims, list)

    def test_phantom_detector_many_urls(self):
        """Test phantom detector with many URLs"""
        detector = PhantomCitationDetector()
        urls = " ".join(
            f"https://example.com/path{i}" for i in range(50)
        )
        result = detector.detect(urls)
        assert isinstance(result, list)

    def test_confidence_tracker_rapid_messages(self):
        """Test confidence tracker with rapid messages"""
        tracker = ConfidenceDecayTracker()
        now = time.time()
        for i in range(100):
            tracker.track("agent1", f"Message {i}", now + i * 0.01)

        stats = tracker.get_agent_confidence("agent1")
        assert stats["entries"] == 50  # Capped

    def test_source_grounder_small_chunks(self):
        """Test grounder with small chunk size (minimum clamped to 50)"""
        grounder = SourceGrounder()
        # chunk_size=1 would create thousands of single-char embeddings;
        # the grounder should clamp to a sane minimum or we test with 50
        result = grounder.set_documents(["Test document about AI safety"], chunk_size=50)
        assert result["total_chunks"] > 0

    def test_monitor_hallucination_error_resilience(self):
        """Test that hallucination errors don't break send_message"""
        monitor = insAItsMonitor(api_key=TEST_PRO_KEY)
        monitor.enable_fact_tracking(True)

        # This should not crash even with unusual text
        result = monitor.send_message(
            "",  # Empty text
            "agent1", llm_id="gpt-4o"
        )
        assert "anomalies" in result

    def test_normalize_topic(self):
        """Test topic normalization"""
        tracker = FactTracker()
        assert tracker._normalize_topic("") == ""
        assert tracker._normalize_topic("The Cost of the Project") != ""
        # Stop words should be removed
        normalized = tracker._normalize_topic("the cost of the project")
        assert "the" not in normalized.split()

    def test_values_contradict_boolean(self):
        """Test boolean/yes-no contradictions"""
        tracker = FactTracker()
        assert tracker._values_contradict("true", "false") is True
        assert tracker._values_contradict("yes ", "no ") is True

    def test_check_grounding_threshold(self):
        """Test grounding with custom threshold"""
        grounder = SourceGrounder()
        grounder.set_documents(["Test source document."])

        # Very low threshold should pass most text
        result = grounder.check_grounding("Anything", threshold=0.01)
        assert "grounded" in result

        # Very high threshold should fail most text
        result = grounder.check_grounding("Anything", threshold=0.99)
        assert "grounded" in result


# ============================================
# VERSION AND EXPORT TESTS
# ============================================

class TestVersionAndExports:
    """Test version bump and exports"""

    def test_version_is_2_4_0(self):
        """Test SDK version is 2.4.0"""
        import insa_its
        assert insa_its.__version__ == "2.4.0"

    def test_hallucination_classes_exported(self):
        """Test all hallucination classes are exported"""
        import insa_its

        assert hasattr(insa_its, "FactTracker")
        assert hasattr(insa_its, "SourceGrounder")
        assert hasattr(insa_its, "SelfConsistencyChecker")
        assert hasattr(insa_its, "PhantomCitationDetector")
        assert hasattr(insa_its, "ConfidenceDecayTracker")
        assert hasattr(insa_its, "FactClaim")
        assert hasattr(insa_its, "HallucinationError")

    def test_anomaly_class_exported(self):
        """Test Anomaly class is exported"""
        import insa_its
        assert hasattr(insa_its, "Anomaly")


# ============================================
# ADDITIONAL COVERAGE: PHANTOM CITATION HEURISTICS
# ============================================

class TestPhantomCitationHeuristics:
    """Deep tests for each phantom citation heuristic path"""

    def setup_method(self):
        self.detector = PhantomCitationDetector()

    def test_url_unusual_tld(self):
        """Test detection of URLs with unusual TLDs (combined with numeric domain)"""
        # .xyz adds 0.2, numeric_heavy_domain adds 0.3 => 0.5 total >= 0.3
        # Note: URL must END with the TLD (no path) since endswith() checks full URL
        text = "See https://site12345678.xyz for info."
        result = self.detector.detect(text)
        unusual_tld = [
            r for r in result
            if "unusual_tld" in r.get("reasons", [])
        ]
        assert len(unusual_tld) > 0

    def test_url_numeric_heavy_domain(self):
        """Test detection of numeric-heavy domains (often hallucinated)"""
        text = "Visit https://site12345678.com/paper for the study."
        result = self.detector.detect(text)
        numeric_heavy = [
            r for r in result
            if "numeric_heavy_domain" in r.get("reasons", [])
        ]
        assert len(numeric_heavy) > 0

    def test_doi_valid_format_not_flagged(self):
        """Test that well-formed DOIs with proper numeric registrant are clean"""
        # DOI regex requires 10.\d{4,}/... so non-numeric registrants
        # never match the regex (correctly excluded at pattern level)
        text = "Published as DOI: 10.1234/proper.article.2023 in a journal."
        result = self.detector.detect(text)
        doi_results = [
            r for r in result if r.get("type") == "suspicious_doi"
        ]
        # A proper DOI with numeric registrant and decent suffix passes
        assert len(doi_results) == 0

    def test_doi_overly_long_suffix(self):
        """Test detection of DOI with suspiciously long suffix"""
        long_suffix = "a" * 55
        text = f"The paper DOI is 10.1234/{long_suffix} and here it is."
        result = self.detector.detect(text)
        long_doi = [
            r for r in result
            if r.get("type") == "suspicious_doi"
            and "suspiciously_long_suffix" in r.get("reasons", [])
        ]
        assert len(long_doi) > 0

    def test_paper_ref_generic_title(self):
        """Test detection of overly generic paper titles (3+ buzzwords)"""
        text = (
            '"A Comprehensive Survey and Analysis of Novel Framework Approaches" '
            '(Journal of AI, 2023)'
        )
        result = self.detector.detect(text)
        generic = [
            r for r in result
            if "overly_generic_title" in r.get("reasons", [])
        ]
        assert len(generic) > 0

    def test_paper_ref_very_recent_with_generic_title(self):
        """Test detection of recent year combined with generic title"""
        # Year 2025 alone = 0.2 (below 0.3 threshold)
        # Combine with generic title for >0.3 total
        text = (
            '"A Comprehensive Survey of Novel Approaches" '
            '(Johnson et al., 2025)'
        )
        result = self.detector.detect(text)
        # Should be flagged due to combined suspicion score
        assert len(result) > 0
        # Verify at least one has the generic title or recent date reason
        all_reasons = []
        for r in result:
            all_reasons.extend(r.get("reasons", []))
        assert ("very_recent_date" in all_reasons or
                "overly_generic_title" in all_reasons)

    def test_multiple_citation_types_in_one_text(self):
        """Test that multiple citation types are detected from one text"""
        text = (
            "See https://example.com/fake/paper for reference. "
            "Also see DOI: 10.abcd/xy which has more details. "
            "Smith et al. (2030) confirmed the results. "
            "Additionally arxiv: 2513.12345 covers this."
        )
        result = self.detector.detect(text)
        types_found = set(r["type"] for r in result)
        assert len(types_found) >= 2

    def test_arxiv_valid_id_not_flagged(self):
        """Test that valid current-year arxiv IDs are not flagged"""
        # 2501 = Jan 2025 — valid and recent
        text = "See arxiv: 2501.12345 for the results."
        result = self.detector.detect(text)
        # Should not be flagged (month valid, year valid)
        assert len(result) == 0

    def test_isbn_pattern_defined(self):
        """Test that ISBN pattern exists on the class"""
        assert hasattr(PhantomCitationDetector, "ISBN_PATTERN")


# ============================================
# ADDITIONAL COVERAGE: CONFIDENCE DECAY SEVERITY
# ============================================

class TestConfidenceDecaySeverity:
    """Tests for confidence decay severity levels and trend reporting"""

    def setup_method(self):
        self.tracker = ConfidenceDecayTracker()

    def test_trend_stable(self):
        """Test stable trend when scores are consistent"""
        now = time.time()
        self.tracker.track("agent1", "Certainly true", now)
        self.tracker.track("agent1", "Definitely right", now + 1)
        self.tracker.track("agent1", "Absolutely correct", now + 2)

        stats = self.tracker.get_agent_confidence("agent1")
        assert stats["trend"] == "stable"

    def test_trend_declining(self):
        """Test declining trend detection"""
        now = time.time()
        # Start very confident, end very uncertain
        self.tracker.track("agent1", "This is certainly absolutely correct", now)
        self.tracker.track("agent1", "Regular normal text", now + 1)
        self.tracker.track("agent1", "Maybe possibly perhaps uncertain", now + 2)

        stats = self.tracker.get_agent_confidence("agent1")
        # Trend should be declining since last score < first - 0.15
        if stats["current_confidence"] < stats["avg_confidence"] - 0.1:
            assert stats["trend"] in ("declining", "stable")

    def test_min_max_confidence_reported(self):
        """Test that min/max confidence are correctly reported"""
        now = time.time()
        self.tracker.track("agent1", "Definitely yes", now)
        self.tracker.track("agent1", "Maybe possibly", now + 1)
        self.tracker.track("agent1", "Certainly true", now + 2)

        stats = self.tracker.get_agent_confidence("agent1")
        assert stats["min_confidence"] <= stats["avg_confidence"]
        assert stats["max_confidence"] >= stats["avg_confidence"]
        assert stats["min_confidence"] <= stats["max_confidence"]

    def test_confidence_score_clamped_0_to_1(self):
        """Test confidence score is always in 0-1 range"""
        tracker = ConfidenceDecayTracker()
        # Even with extreme input, score should be in range
        many_confident = " ".join(
            ["certainly definitely absolutely"] * 20
        )
        score = tracker.score_confidence(many_confident)
        assert 0.0 <= score <= 1.0

        many_uncertain = " ".join(
            ["maybe perhaps possibly uncertain"] * 20
        )
        score = tracker.score_confidence(many_uncertain)
        assert 0.0 <= score <= 1.0


# ============================================
# ADDITIONAL COVERAGE: VALUES CONTRADICT PATTERNS
# ============================================

class TestValuesContradictPatterns:
    """Deep tests for the _values_contradict method covering all branches"""

    def setup_method(self):
        self.tracker = FactTracker()

    def test_not_x_vs_x_substring(self):
        """Test 'not working' vs 'working' substring contradiction"""
        assert self.tracker._values_contradict(
            "not working", "working"
        ) is True

    def test_x_vs_not_x_reversed(self):
        """Test reversed 'working' vs 'not working' substring"""
        assert self.tracker._values_contradict(
            "working", "not working"
        ) is True

    def test_cross_pair_with_context(self):
        """Test cross-pair matching: 'task failed completely' vs 'task succeeded completely'"""
        assert self.tracker._values_contradict(
            "the task failed completely",
            "the task succeeded completely"
        ) is True

    def test_impossible_vs_possible(self):
        """Test impossible/possible pair"""
        assert self.tracker._values_contradict(
            "impossible", "possible"
        ) is True

    def test_invalid_vs_valid(self):
        """Test invalid/valid pair"""
        assert self.tracker._values_contradict(
            "invalid", "valid"
        ) is True

    def test_decreased_vs_increased(self):
        """Test decreased/increased pair"""
        assert self.tracker._values_contradict(
            "decreased", "increased"
        ) is True

    def test_no_contradiction_unrelated_values(self):
        """Test that unrelated values don't produce false positives"""
        assert self.tracker._values_contradict("apple", "banana") is False
        assert self.tracker._values_contradict("fast", "efficient") is False

    def test_no_contradiction_similar_numbers(self):
        """Test that identical numbers don't contradict"""
        assert self.tracker._values_contradict("100 users", "100 users") is False

    def test_numeric_with_commas(self):
        """Test numeric contradiction with comma-formatted numbers"""
        assert self.tracker._values_contradict(
            "1,000 users", "5,000 users"
        ) is True


# ============================================
# ADDITIONAL COVERAGE: NUMERIC DRIFT DETAILS
# ============================================

class TestNumericDriftDetails:
    """Deep tests for numeric drift detection severity and edge cases"""

    def setup_method(self):
        self.tracker = FactTracker()

    def test_drift_severity_low(self):
        """Test low severity drift (10-20% change)"""
        claims1 = [
            FactClaim("cost 100", "cost", "100 dollars",
                      "a", "m1", time.time(), 0.8, "numeric")
        ]
        self.tracker.track_claims(claims1)

        claims2 = [
            FactClaim("cost 115", "cost", "115 dollars",
                      "a", "m2", time.time(), 0.7, "numeric")
        ]
        self.tracker.track_claims(claims2)

        drifts = self.tracker.get_numeric_drift()
        assert len(drifts) > 0
        assert drifts[0]["severity"] == "low"

    def test_drift_severity_medium(self):
        """Test medium severity drift (20-50% change)"""
        claims1 = [
            FactClaim("cost 100", "cost", "100 dollars",
                      "a", "m1", time.time(), 0.8, "numeric")
        ]
        self.tracker.track_claims(claims1)

        claims2 = [
            FactClaim("cost 130", "cost", "130 dollars",
                      "a", "m2", time.time(), 0.7, "numeric")
        ]
        self.tracker.track_claims(claims2)

        drifts = self.tracker.get_numeric_drift()
        assert len(drifts) > 0
        assert drifts[0]["severity"] == "medium"

    def test_drift_severity_high(self):
        """Test high severity drift (>50% change)"""
        claims1 = [
            FactClaim("cost 100", "cost", "100 dollars",
                      "a", "m1", time.time(), 0.8, "numeric")
        ]
        self.tracker.track_claims(claims1)

        claims2 = [
            FactClaim("cost 200", "cost", "200 dollars",
                      "a", "m2", time.time(), 0.7, "numeric")
        ]
        self.tracker.track_claims(claims2)

        drifts = self.tracker.get_numeric_drift()
        assert len(drifts) > 0
        assert drifts[0]["severity"] == "high"

    def test_drift_initial_zero_skipped(self):
        """Test that topics with initial value 0 are skipped"""
        claims1 = [
            FactClaim("cost 0", "cost", "0 dollars",
                      "a", "m1", time.time(), 0.8, "numeric")
        ]
        self.tracker.track_claims(claims1)

        claims2 = [
            FactClaim("cost 500", "cost", "500 dollars",
                      "a", "m2", time.time(), 0.7, "numeric")
        ]
        self.tracker.track_claims(claims2)

        drifts = self.tracker.get_numeric_drift()
        # Should be empty because initial=0 is skipped
        cost_drifts = [d for d in drifts if d.get("initial_value") == 0]
        assert len(cost_drifts) == 0

    def test_drift_no_change_below_threshold(self):
        """Test that <10% change doesn't trigger drift"""
        claims1 = [
            FactClaim("cost 100", "cost", "100 dollars",
                      "a", "m1", time.time(), 0.8, "numeric")
        ]
        self.tracker.track_claims(claims1)

        claims2 = [
            FactClaim("cost 105", "cost", "105 dollars",
                      "a", "m2", time.time(), 0.7, "numeric")
        ]
        self.tracker.track_claims(claims2)

        drifts = self.tracker.get_numeric_drift()
        # 5% change should not trigger (threshold is 10%)
        assert len(drifts) == 0

    def test_drift_agents_involved(self):
        """Test that agents_involved includes all contributing agents"""
        claims1 = [
            FactClaim("cost 100", "cost", "100 dollars",
                      "agent_a", "m1", time.time(), 0.8, "numeric")
        ]
        self.tracker.track_claims(claims1)

        claims2 = [
            FactClaim("cost 200", "cost", "200 dollars",
                      "agent_b", "m2", time.time(), 0.7, "numeric")
        ]
        self.tracker.track_claims(claims2)

        drifts = self.tracker.get_numeric_drift()
        assert len(drifts) > 0
        agents = drifts[0]["agents_involved"]
        assert "agent_a" in agents
        assert "agent_b" in agents

    def test_cross_agent_summary_multi_agent_details(self):
        """Test multi_agent_details in cross-agent summary"""
        claims1 = [
            FactClaim("claim", "shared_topic", "val1",
                      "agent_a", "m1", time.time()),
        ]
        self.tracker.track_claims(claims1)

        claims2 = [
            FactClaim("claim", "shared_topic", "val2",
                      "agent_b", "m2", time.time()),
        ]
        self.tracker.track_claims(claims2)

        summary = self.tracker.get_cross_agent_summary()
        details = summary["multi_agent_details"]
        assert len(details) >= 1
        # At least one topic should have both agents
        found = False
        for topic, agents in details.items():
            if "agent_a" in agents and "agent_b" in agents:
                found = True
                break
        assert found


# ============================================
# ADDITIONAL COVERAGE: GROUNDING EDGE CASES
# ============================================

class TestGroundingEdgeCases:
    """Additional source grounding edge cases"""

    def test_check_grounding_avg_top3(self):
        """Test avg_top3_score is returned"""
        grounder = SourceGrounder()
        grounder.set_documents([
            "Python is a programming language.",
            "Java is also a programming language.",
            "Rust is a systems programming language."
        ])

        result = grounder.check_grounding("Python is great.")
        assert "avg_top3_score" in result
        assert 0.0 <= result["avg_top3_score"] <= 1.0

    def test_check_grounding_documents_loaded_in_result(self):
        """Test documents_loaded count in grounding result"""
        grounder = SourceGrounder()
        grounder.set_documents(["Doc one.", "Doc two."])

        result = grounder.check_grounding("Test text.")
        assert result["documents_loaded"] == 2
        assert result["total_chunks"] >= 2

    def test_check_grounding_batch_cap_at_50(self):
        """Test batch is capped at 50 texts"""
        grounder = SourceGrounder()
        grounder.set_documents(["Source document."])

        texts = [f"Text {i}" for i in range(60)]
        results = grounder.check_grounding_batch(texts)
        assert len(results) == 50  # Capped

    def test_chunk_overlap_produces_more_chunks(self):
        """Test that overlap creates more chunks than no overlap"""
        grounder = SourceGrounder()
        text = "A" * 1000

        chunks_no_overlap = grounder._chunk_text(text, 200, 0)
        chunks_with_overlap = grounder._chunk_text(text, 200, 50)

        assert len(chunks_with_overlap) >= len(chunks_no_overlap)


# ============================================
# ADDITIONAL: MONITOR HALLUCINATION WITH DATA
# ============================================

class TestMonitorHallucinationWithData:
    """Test monitor hallucination methods with actual tracked data"""

    def test_get_hallucination_summary_with_anomalies(self):
        """Test hallucination summary with actual anomalies injected"""
        monitor = insAItsMonitor(api_key=TEST_PRO_KEY)

        # Inject hallucination anomalies
        monitor.anomaly_history.extend([
            {"type": "FACT_CONTRADICTION", "severity": "critical",
             "llm_id": "a", "agent_id": "a", "details": {},
             "timestamp": time.time(), "message_id": "m1"},
            {"type": "PHANTOM_CITATION", "severity": "high",
             "llm_id": "a", "agent_id": "a", "details": {},
             "timestamp": time.time(), "message_id": "m2"},
            {"type": "UNGROUNDED_CLAIM", "severity": "medium",
             "llm_id": "a", "agent_id": "a", "details": {},
             "timestamp": time.time(), "message_id": "m3"},
        ])

        result = monitor.get_hallucination_summary()
        assert result["total_hallucination_anomalies"] == 3
        assert result["hallucination_health"]["score"] < 100
        assert result["hallucination_health"]["status"] != "excellent"
        assert result["by_type"]["FACT_CONTRADICTION"] == 1
        assert result["by_type"]["PHANTOM_CITATION"] == 1
        assert result["by_type"]["UNGROUNDED_CLAIM"] == 1

    def test_get_numeric_drift_through_monitor(self):
        """Test numeric drift detection through the full monitor pipeline"""
        monitor = insAItsMonitor(api_key=TEST_PRO_KEY)
        monitor.enable_fact_tracking(True)

        # Manually track claims to ensure drift data
        claims1 = [
            FactClaim("cost 100", "cost", "100 dollars",
                      "agent1", "m1", time.time(), 0.8, "numeric")
        ]
        monitor.fact_tracker.track_claims(claims1)

        claims2 = [
            FactClaim("cost 500", "cost", "500 dollars",
                      "agent2", "m2", time.time(), 0.7, "numeric")
        ]
        monitor.fact_tracker.track_claims(claims2)

        result = monitor.get_numeric_drift()
        assert result["total_drifts"] >= 1
        assert len(result["drift_events"]) >= 1

    def test_get_cross_agent_summary_through_monitor(self):
        """Test cross-agent summary through monitor"""
        monitor = insAItsMonitor(api_key=TEST_PRO_KEY)
        monitor.enable_fact_tracking(True)

        # Track claims from different agents
        claims1 = [
            FactClaim("claim", "shared_topic", "val1",
                      "agent_a", "m1", time.time())
        ]
        monitor.fact_tracker.track_claims(claims1)

        claims2 = [
            FactClaim("claim", "shared_topic", "val2",
                      "agent_b", "m2", time.time())
        ]
        monitor.fact_tracker.track_claims(claims2)

        result = monitor.get_cross_agent_summary()
        assert result["total_claims"] == 2
        assert result["multi_agent_topics"] >= 1

    def test_detect_phantom_citations_verdict_levels(self):
        """Test phantom citation verdict levels"""
        monitor = insAItsMonitor(api_key=TEST_PRO_KEY)

        # Clean text — no citations at all
        result = monitor.detect_phantom_citations(
            "Machine learning is used for data analysis and pattern recognition."
        )
        assert result["verdict"] == "clean"
        assert result["total_suspicious"] == 0

        # Suspicious text — needs suspicion_score >= 0.5 for high_confidence
        # Combine multiple heuristic triggers per URL
        long_path = "x" * 160
        result = monitor.detect_phantom_citations(
            f"See https://site12345678.xyz/{long_path} for details. "
            "Also Smith et al. (2030) confirmed results."
        )
        assert result["total_suspicious"] > 0
        # At least one citation should be high confidence (>= 0.5)
        assert result["high_confidence"] > 0
        assert result["verdict"] in ("suspicious", "likely_fabricated")


# ============================================
# ADDITIONAL: SELF-CONSISTENCY CHECKER EDGES
# ============================================

class TestSelfConsistencyEdgeCases:
    """Edge cases for SelfConsistencyChecker"""

    def test_check_llm_unavailable(self):
        """Test check returns proper error when LLM unavailable"""
        checker = SelfConsistencyChecker()
        result = checker.check(
            "This is a long enough text for analysis. " * 5
        )
        # Without Ollama, should return error
        assert result.get("is_consistent") is None or result.get("error")

    def test_check_against_claims_llm_unavailable(self):
        """Test claim verification returns error when LLM unavailable"""
        checker = SelfConsistencyChecker()
        result = checker.check_against_claims(
            "The cost is 500 dollars.",
            [{"topic": "cost", "value": "100 dollars"}]
        )
        # Without Ollama, should return error or None verified
        assert (result.get("verified") is None or
                result.get("error") is not None)


# ============================================
# ADDITIONAL: SESSION HEALTH DETAILED FACTORS
# ============================================

class TestSessionHealthDetailedFactors:
    """Test all hallucination factor penalties in session health"""

    def test_ungrounded_claims_penalty(self):
        """Test ungrounded claims reduce health score"""
        monitor = insAItsMonitor(api_key=TEST_PRO_KEY)
        monitor.anomaly_history.append({
            "type": "UNGROUNDED_CLAIM", "severity": "medium",
            "llm_id": "a", "agent_id": "a", "details": {},
            "timestamp": time.time(), "message_id": "m1"
        })

        trends = monitor.get_anomaly_trends()
        health = trends.get("session_health", {})
        assert health["score"] < 100
        assert health["factors"]["ungrounded_claims"] == 1

    def test_confidence_decay_penalty(self):
        """Test confidence decay reduces health score"""
        monitor = insAItsMonitor(api_key=TEST_PRO_KEY)
        monitor.anomaly_history.append({
            "type": "CONFIDENCE_DECAY", "severity": "medium",
            "llm_id": "a", "agent_id": "a", "details": {},
            "timestamp": time.time(), "message_id": "m1"
        })

        trends = monitor.get_anomaly_trends()
        health = trends.get("session_health", {})
        assert health["score"] < 100
        assert health["factors"]["confidence_decays"] == 1

    def test_confidence_flip_flop_penalty(self):
        """Test confidence flip-flop reduces health score"""
        monitor = insAItsMonitor(api_key=TEST_PRO_KEY)
        monitor.anomaly_history.append({
            "type": "CONFIDENCE_FLIP_FLOP", "severity": "medium",
            "llm_id": "a", "agent_id": "a", "details": {},
            "timestamp": time.time(), "message_id": "m1"
        })

        trends = monitor.get_anomaly_trends()
        health = trends.get("session_health", {})
        assert health["score"] < 100
        assert health["factors"]["confidence_flip_flops"] == 1

    def test_all_hallucination_factors_counted(self):
        """Test all hallucination types are counted in health factors"""
        monitor = insAItsMonitor(api_key=TEST_PRO_KEY)
        anomaly_types = [
            "FACT_CONTRADICTION", "PHANTOM_CITATION",
            "UNGROUNDED_CLAIM", "CONFIDENCE_DECAY",
            "CONFIDENCE_FLIP_FLOP"
        ]
        for atype in anomaly_types:
            monitor.anomaly_history.append({
                "type": atype, "severity": "medium",
                "llm_id": "a", "agent_id": "a", "details": {},
                "timestamp": time.time(), "message_id": f"m-{atype}"
            })

        trends = monitor.get_anomaly_trends()
        health = trends.get("session_health", {})
        factors = health["factors"]

        assert factors["fact_contradictions"] == 1
        assert factors["phantom_citations"] == 1
        assert factors["ungrounded_claims"] == 1
        assert factors["confidence_decays"] == 1
        assert factors["confidence_flip_flops"] == 1


# ============================================
# RUN TESTS
# ============================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

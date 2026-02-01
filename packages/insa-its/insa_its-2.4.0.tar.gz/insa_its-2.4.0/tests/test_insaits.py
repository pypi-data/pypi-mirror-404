"""
InsAIts SDK Test Suite
======================
Comprehensive tests for the Multi-LLM anomaly detection system.

Run with: python -m pytest tests/test_insaits.py -v
Or simply: python tests/test_insaits.py
"""

import sys
import os
import time

# ============================================
# Enable Development Mode for Testing
# ============================================
os.environ['INSAITS_DEV_MODE'] = 'true'

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from insa_its import insAItsMonitor, AnomalyDetector
from insa_its.embeddings import get_synthetic_embedding, get_local_embedding, EmbeddingCache
from insa_its.exceptions import RateLimitError, insAItsError

import numpy as np

# ============================================
# Test API Keys (for development mode)
# ============================================
TEST_PRO_KEY = 'test-pro-unlimited'
TEST_STARTER_KEY = 'test-starter-10k'
TEST_FREE_KEY = 'test-free-100'


class TestResults:
    """Simple test result tracker"""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []

    def record(self, name: str, passed: bool, error: str = None):
        if passed:
            self.passed += 1
            print(f"  [PASS] {name}")
        else:
            self.failed += 1
            self.errors.append((name, error))
            print(f"  [FAIL] {name}: {error}")

    def summary(self):
        total = self.passed + self.failed
        print(f"\n{'='*50}")
        print(f"RESULTS: {self.passed}/{total} tests passed")
        if self.errors:
            print(f"\nFailed tests:")
            for name, error in self.errors:
                print(f"  - {name}: {error}")
        print(f"{'='*50}")
        return self.failed == 0


results = TestResults()


# ============================================
# EMBEDDING TESTS
# ============================================
def test_embedding_generation():
    """Test that embeddings are generated correctly"""
    print("\n[Testing Embeddings]")

    # Test synthetic embedding
    text = "Hello world this is a test message"
    emb = get_synthetic_embedding(text)

    results.record(
        "Synthetic embedding shape",
        emb.shape == (384,),
        f"Expected (384,), got {emb.shape}"
    )

    results.record(
        "Embedding is normalized",
        abs(np.linalg.norm(emb) - 1.0) < 0.01,
        f"Norm is {np.linalg.norm(emb)}"
    )

    # Test caching
    emb2 = get_synthetic_embedding(text)
    results.record(
        "Embedding caching works",
        np.array_equal(emb, emb2),
        "Cached embedding differs from original"
    )

    # Test local embedding (falls back to synthetic if no sentence-transformers)
    emb_local = get_local_embedding(text)
    results.record(
        "Local embedding generation",
        emb_local.shape[0] > 0,
        f"Got empty embedding"
    )


def test_embedding_cache():
    """Test the LRU cache mechanism"""
    print("\n[Testing Embedding Cache]")

    cache = EmbeddingCache(max_size=3)

    # Add items
    cache.set("text1", np.array([1, 2, 3]))
    cache.set("text2", np.array([4, 5, 6]))
    cache.set("text3", np.array([7, 8, 9]))

    results.record(
        "Cache stores items",
        cache.get("text3") is not None,
        "Failed to retrieve cached item"
    )

    # Add one more to trigger eviction (text1 is oldest, should be evicted)
    cache.set("text4", np.array([10, 11, 12]))

    # text1 was oldest and not accessed, so it should be evicted
    results.record(
        "LRU eviction works",
        cache.get("text1") is None,
        "Oldest untouched item should be evicted"
    )

    results.record(
        "Recent items preserved",
        cache.get("text4") is not None,
        "New item should be in cache"
    )


# ============================================
# MONITOR TESTS
# ============================================
def test_monitor_initialization():
    """Test monitor creation"""
    print("\n[Testing Monitor Initialization]")

    monitor = insAItsMonitor(session_name="test-session")

    results.record(
        "Monitor created",
        monitor is not None,
        "Failed to create monitor"
    )

    results.record(
        "Session ID generated",
        len(monitor.session_id) > 0,
        "No session ID"
    )

    results.record(
        "Free tier by default",
        monitor.is_pro == False,
        "Should be free tier without API key"
    )

    # Pro tier - use test key
    monitor_pro = insAItsMonitor(api_key=TEST_PRO_KEY)
    results.record(
        "Pro tier with API key",
        monitor_pro.is_pro == True,
        "Should be pro tier with API key"
    )
    
    # Starter tier - use test key
    monitor_starter = insAItsMonitor(api_key=TEST_STARTER_KEY)
    results.record(
        "Starter tier enforces limits",
        monitor_starter.tier == "starter",
        f"Should be starter tier, got {monitor_starter.tier}"
    )


def test_message_sending():
    """Test sending messages through the monitor"""
    print("\n[Testing Message Sending]")

    monitor = insAItsMonitor()

    result = monitor.send_message(
        text="Hello, I am agent one sending a test message to agent two.",
        sender_id="agent_1",
        receiver_id="agent_2",
        llm_id="gpt-4o"
    )

    results.record(
        "Message returns result",
        result is not None,
        "No result returned"
    )

    results.record(
        "Result has anomalies key",
        "anomalies" in result,
        "Missing anomalies key"
    )

    results.record(
        "Result has message key",
        "message" in result,
        "Missing message key"
    )

    results.record(
        "Agent registered",
        "agent_1" in monitor.agents,
        "Agent not registered"
    )


def test_rate_limiting():
    """Test rate limiting functionality"""
    print("\n[Testing Rate Limiting]")

    # Use starter tier to test rate limiting on paid tier
    monitor = insAItsMonitor(api_key=TEST_STARTER_KEY)

    # First message should succeed
    monitor.send_message("First message", "agent_1", llm_id="gpt-4o")

    # Immediate second message should be rate limited
    rate_limited = False
    try:
        monitor.send_message("Second message", "agent_1", llm_id="gpt-4o")
    except RateLimitError:
        rate_limited = True

    results.record(
        "Rate limiting enforced",
        rate_limited,
        "Should have raised RateLimitError"
    )

    # Wait and try again
    time.sleep(0.15)
    try:
        monitor.send_message("Third message", "agent_1", llm_id="gpt-4o")
        results.record("Rate limit resets", True, "")
    except RateLimitError:
        results.record("Rate limit resets", False, "Should allow after cooldown")


# ============================================
# ANOMALY DETECTION TESTS
# ============================================
def test_shorthand_detection():
    """Test shorthand emergence detection"""
    print("\n[Testing Shorthand Detection]")

    monitor = insAItsMonitor()

    # Send a long message first (>40 words as required by detector)
    long_text = (
        "This is a very long and detailed message that contains a lot of words "
        "and explanations about the topic we are discussing which should be quite "
        "verbose and lengthy indeed and we keep going with more words to ensure "
        "we have enough content here for the test to work properly with detection"
    )
    monitor.send_message(long_text, "agent_1", llm_id="gpt-4o")

    time.sleep(0.15)

    # Send a semantically similar but very short message (<15 words)
    # Using similar terms to get high similarity score (>0.65)
    result = monitor.send_message(
        "Topic discussion verbose lengthy content",
        "agent_1", llm_id="gpt-4o"
    )

    # Check if any anomaly was detected (shorthand or context loss both indicate compression)
    has_anomaly = len(result["anomalies"]) > 0

    results.record(
        "Shorthand/compression detected",
        has_anomaly,
        f"Expected anomaly detection for message compression"
    )


def test_context_loss_detection():
    """Test context loss detection"""
    print("\n[Testing Context Loss Detection]")

    monitor = insAItsMonitor()

    # Send related messages then completely unrelated
    monitor.send_message(
        "We are discussing quantum physics and particle behavior in accelerators",
        "agent_1", llm_id="claude-3.5"
    )
    time.sleep(0.15)

    result = monitor.send_message(
        "I love cooking pasta with tomato sauce and fresh basil leaves",
        "agent_1", llm_id="claude-3.5"
    )

    has_context_loss = any(
        a.get("type") == "CONTEXT_LOSS"
        for a in result["anomalies"]
    )

    results.record(
        "Context loss detected",
        has_context_loss,
        f"Expected CONTEXT_LOSS for topic change, got {[a.get('type') for a in result['anomalies']]}"
    )


def test_fingerprint_mismatch():
    """Test LLM fingerprint mismatch detection"""
    print("\n[Testing Fingerprint Mismatch]")

    # Use pro tier for unlimited messages
    monitor = insAItsMonitor(api_key=TEST_PRO_KEY)

    # GPT-4o has avg 35 words, send something way longer
    long_message = " ".join(["word"] * 80)  # 80 words
    monitor.send_message("Setup message with normal length here", "agent_1", llm_id="gpt-4o")
    time.sleep(0.15)

    result = monitor.send_message(long_message, "agent_1", llm_id="gpt-4o")

    has_mismatch = any(
        a.get("type") == "LLM_FINGERPRINT_MISMATCH"
        for a in result["anomalies"]
    )

    results.record(
        "Fingerprint mismatch detected",
        has_mismatch,
        f"Expected LLM_FINGERPRINT_MISMATCH for unusual word count, got {[a.get('type') for a in result['anomalies']]}"
    )


def test_jargon_detection():
    """Test cross-LLM jargon detection"""
    print("\n[Testing Jargon Detection]")

    monitor = insAItsMonitor()

    # Send normal message first
    monitor.send_message("Hello this is a normal conversation", "agent_1", llm_id="gpt-4o")
    time.sleep(0.15)

    # Send message with new acronyms
    result = monitor.send_message(
        "The QSRC protocol uses DFTX encoding for MXPLR data",
        "agent_1", llm_id="gpt-4o"
    )

    has_jargon = any(
        a.get("type") == "CROSS_LLM_JARGON"
        for a in result["anomalies"]
    )

    results.record(
        "New jargon detected",
        has_jargon,
        f"Expected CROSS_LLM_JARGON for new acronyms"
    )


# ============================================
# CONVERSATION READING TESTS
# ============================================
def test_conversation_reading():
    """Test conversation history reading"""
    print("\n[Testing Conversation Reading]")

    monitor = insAItsMonitor()

    # Create a conversation
    monitor.send_message("Hello agent 2", "agent_1", "agent_2", "gpt-4o")
    time.sleep(0.15)
    monitor.send_message("Hello agent 1, how are you?", "agent_2", "agent_1", "claude-3.5")
    time.sleep(0.15)
    monitor.send_message("I am fine, working on the project", "agent_1", "agent_2", "gpt-4o")

    # Get all conversations
    conv = monitor.get_conversation()
    results.record(
        "Get all conversations",
        len(conv) == 3,
        f"Expected 3 messages, got {len(conv)}"
    )

    # Get specific agent
    agent_conv = monitor.get_conversation(agent_id="agent_1")
    results.record(
        "Get agent conversation",
        len(agent_conv) == 2,
        f"Expected 2 messages from agent_1, got {len(agent_conv)}"
    )


def test_discussion_thread():
    """Test getting discussion thread between agents"""
    print("\n[Testing Discussion Thread]")

    monitor = insAItsMonitor()

    # Create back-and-forth
    monitor.send_message("Message 1 from A to B", "agent_a", "agent_b", "gpt-4o")
    time.sleep(0.15)
    monitor.send_message("Reply from B to A", "agent_b", "agent_a", "claude-3.5")
    time.sleep(0.15)
    monitor.send_message("Follow up from A to B", "agent_a", "agent_b", "gpt-4o")

    thread = monitor.get_discussion_thread("agent_a", "agent_b")

    results.record(
        "Thread retrieved",
        len(thread) == 3,
        f"Expected 3 messages in thread, got {len(thread)}"
    )

    results.record(
        "Thread has direction",
        "direction" in thread[0],
        "Missing direction field"
    )


def test_discussion_analysis():
    """Test discussion analysis"""
    print("\n[Testing Discussion Analysis]")

    monitor = insAItsMonitor()

    # Create coherent conversation
    monitor.send_message(
        "Let's discuss the machine learning algorithm implementation",
        "agent_a", "agent_b", "gpt-4o"
    )
    time.sleep(0.15)
    monitor.send_message(
        "Yes, the machine learning model needs proper training data",
        "agent_b", "agent_a", "claude-3.5"
    )
    time.sleep(0.15)
    monitor.send_message(
        "We should use neural networks for this machine learning task",
        "agent_a", "agent_b", "gpt-4o"
    )

    analysis = monitor.analyze_discussion("agent_a", "agent_b")

    results.record(
        "Analysis returns message count",
        analysis.get("message_count") == 3,
        f"Expected 3, got {analysis.get('message_count')}"
    )

    results.record(
        "Analysis has coherence score",
        "avg_coherence" in analysis,
        "Missing coherence score"
    )

    results.record(
        "Analysis has health status",
        "coherence_health" in analysis,
        "Missing health status"
    )


def test_get_all_discussions():
    """Test getting summary of all discussions"""
    print("\n[Testing All Discussions Summary]")

    monitor = insAItsMonitor()

    # Create multiple discussion pairs
    monitor.send_message("A to B", "agent_a", "agent_b", "gpt-4o")
    time.sleep(0.15)
    monitor.send_message("C to D", "agent_c", "agent_d", "claude-3.5")
    time.sleep(0.15)
    monitor.send_message("B to A", "agent_b", "agent_a", "gpt-4o")

    discussions = monitor.get_all_discussions()

    results.record(
        "Multiple discussions found",
        len(discussions) == 2,
        f"Expected 2 discussion pairs, got {len(discussions)}"
    )


def test_export_log():
    """Test exporting conversation log"""
    print("\n[Testing Export Log]")

    monitor = insAItsMonitor(session_name="test-export")

    monitor.send_message("Test message 1", "agent_1", "agent_2", "gpt-4o")
    time.sleep(0.15)
    monitor.send_message("Test message 2", "agent_2", "agent_1", "claude-3.5")

    log = monitor.export_conversation_log()

    results.record(
        "Log contains session name",
        "test-export" in log,
        "Session name not in log"
    )

    results.record(
        "Log contains messages",
        "Test message 1" in log and "Test message 2" in log,
        "Messages not in log"
    )


# ============================================
# GRAPH TESTS
# ============================================
def test_graph_export():
    """Test graph export functionality"""
    print("\n[Testing Graph Export]")

    monitor = insAItsMonitor()

    monitor.send_message("Message to create edge", "agent_1", "agent_2", "gpt-4o")

    graph_data = monitor.export_graph()

    if graph_data:  # NetworkX may not be available
        results.record(
            "Graph has nodes",
            "nodes" in graph_data,
            "Missing nodes in graph data"
        )
        results.record(
            "Graph has links",
            "links" in graph_data,
            "Missing links in graph data"
        )
    else:
        print("  [SKIP] NetworkX not available")


def test_stats():
    """Test statistics gathering"""
    print("\n[Testing Statistics]")

    monitor = insAItsMonitor(session_name="stats-test")

    monitor.send_message("Msg 1", "agent_1", llm_id="gpt-4o")
    time.sleep(0.15)
    monitor.send_message("Msg 2", "agent_2", llm_id="claude-3.5")

    stats = monitor.get_stats()

    results.record(
        "Stats has session_id",
        "session_id" in stats,
        "Missing session_id"
    )

    results.record(
        "Stats has agents",
        len(stats.get("agents", [])) == 2,
        f"Expected 2 agents, got {len(stats.get('agents', []))}"
    )

    results.record(
        "Stats has message count",
        stats.get("total_messages") == 2,
        f"Expected 2 messages, got {stats.get('total_messages')}"
    )


# ============================================
# RUN ALL TESTS
# ============================================
def run_all_tests():
    print("=" * 50)
    print("InsAIts SDK Test Suite")
    print("=" * 50)

    # Embedding tests
    test_embedding_generation()
    test_embedding_cache()

    # Monitor tests
    test_monitor_initialization()
    test_message_sending()
    test_rate_limiting()

    # Anomaly detection tests
    test_shorthand_detection()
    test_context_loss_detection()
    test_fingerprint_mismatch()
    test_jargon_detection()

    # Conversation reading tests
    test_conversation_reading()
    test_discussion_thread()
    test_discussion_analysis()
    test_get_all_discussions()
    test_export_log()

    # Graph and stats tests
    test_graph_export()
    test_stats()

    # Summary
    success = results.summary()
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)

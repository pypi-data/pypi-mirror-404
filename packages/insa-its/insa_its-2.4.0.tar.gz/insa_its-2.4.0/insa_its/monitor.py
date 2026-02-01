import uuid
import time
import threading
import logging
import json
import requests
import numpy as np
from typing import List, Dict, Optional, Any, Literal
from datetime import datetime

from .detector import AnomalyDetector, Anomaly
from .embeddings import get_synthetic_embedding, get_local_embedding, cache
from .exceptions import RateLimitError, insAItsError
from .license import LicenseManager
from .config import (
    ANONYMOUS_LIMITS,
    get_tier_limits,
    get_feature,
    PRICING_URL,
    REGISTER_URL,
    API_ENDPOINTS,
)
from .hallucination import (
    FactTracker, SourceGrounder, SelfConsistencyChecker,
    PhantomCitationDetector, ConfidenceDecayTracker, FactClaim
)

# New: LLM integration for decipher
try:
    from .local_llm import ollama_chat
    LLM_AVAILABLE = True
except Exception:
    LLM_AVAILABLE = False

try:
    import websocket
    WS_AVAILABLE = True
except ImportError:
    WS_AVAILABLE = False

try:
    import networkx as nx
    GRAPH_AVAILABLE = True
except ImportError:
    GRAPH_AVAILABLE = False

logger = logging.getLogger(__name__)

class insAItsMonitor:
    """Main SDK class - Multi-LLM deciphering + prevention"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        cloud_url: str = "wss://api.insa-its.com/ws",
        auto_prevent: bool = True,
        decipher_mode: bool = True,
        session_name: Optional[str] = None,
        use_cloud_embeddings: bool = False,  # Disabled by default - use local for speed
        cloud_timeout: int = 30,  # Timeout for cloud requests (seconds)
        cloud_retries: int = 2,  # Number of retries for cloud
        ollama_model: Optional[str] = None  # User-specified Ollama model
    ):
        self.api_key = api_key
        self.cloud_url = cloud_url
        self.session_id = str(uuid.uuid4())
        self.session_name = session_name or f"session-{datetime.now().isoformat()}"

        # Cloud embedding settings
        self.use_cloud_embeddings = use_cloud_embeddings
        self.cloud_timeout = cloud_timeout
        self.cloud_retries = cloud_retries

        # Ollama model selection
        if ollama_model:
            from .local_llm import set_default_model
            set_default_model(ollama_model)

        # License management - ALWAYS validate (even without key)
        self.license = LicenseManager(api_key)
        validation = self.license.validate()
        logger.info(f"License validation: {validation}")

        # Tier-based access
        self.tier = self.license.tier
        self._limits = get_tier_limits(self.tier)
        self.is_pro = self.tier in ("pro", "lifetime", "enterprise")
        self.is_paid = self.tier in ("starter", "pro", "lifetime", "enterprise")
        self.auto_prevent = auto_prevent and self.is_pro
        self.decipher_mode = decipher_mode and get_feature(self.tier, "integrations")

        # History: {agent_id: {llm_id: List[msg]}}
        self.history: Dict[str, Dict[str, List[Dict]]] = {}
        self.agents: List[str] = []

        # Rate limiting
        self.last_msg_time: Dict[str, float] = {}

        # Usage tracking
        self.session_message_count = 0
        self.max_messages = self._limits.get("session_messages", 5)

        # Components
        self.detector = AnomalyDetector()

        # Premium: Decipher engine (cloud + local message expansion)
        self._decipher_engine = None
        try:
            from .premium import DECIPHER_AVAILABLE
            if DECIPHER_AVAILABLE:
                from .premium.decipher_engine import DecipherEngine
                self._decipher_engine = DecipherEngine(
                    api_key=self.api_key,
                    tier=self.tier,
                    api_endpoints=API_ENDPOINTS,
                    get_feature_fn=get_feature,
                )
                logger.info("Premium decipher engine enabled")
        except ImportError:
            logger.debug("Premium decipher engine not available")

        # Anomaly tracking for trend analysis
        self.anomaly_history: List[Dict] = []

        # Graph - only for registered users
        if GRAPH_AVAILABLE and get_feature(self.tier, "graph"):
            self.graph = nx.DiGraph()
        else:
            self.graph = None

        # V2: Anchor-aware detection
        self.current_anchor: Optional[Dict] = None
        self.turn_counter: int = 0

        # V2.3: Hallucination detection (Phase 3)
        self.fact_tracker = FactTracker()
        self.source_grounder = SourceGrounder()
        self.consistency_checker = SelfConsistencyChecker()
        self.confidence_tracker = ConfidenceDecayTracker()
        self.citation_detector = PhantomCitationDetector()
        self.fact_tracking_enabled = False
        self._auto_grounding_check = False

        # Cloud
        self.ws = None
        self.ws_thread = None
        if self.is_pro and WS_AVAILABLE:
            threading.Thread(target=self._connect_with_retry, daemon=True).start()

    def _connect_with_retry(self):
        max_retries = 10
        for attempt in range(max_retries):
            try:
                def on_open(ws):
                    ws.send(json.dumps({
                        "type": "auth",
                        "session_id": self.session_id,
                        "api_key": self.api_key
                    }))

                def on_message(ws, msg):
                    data = json.loads(msg)
                    if data.get("anomalies"):
                        logger.info(f"Cloud anomalies: {data['anomalies']}")

                self.ws = websocket.WebSocketApp(
                    self.cloud_url,
                    on_open=on_open,
                    on_message=on_message
                )
                self.ws.run_forever(ping_interval=30)
            except Exception as e:
                logger.error(f"WS attempt {attempt+1} failed: {e}", exc_info=True)
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)

    def register_agent(self, agent_id: str, llm_id: str = "unknown"):
        if agent_id not in self.agents:
            self.agents.append(agent_id)
            self.history[agent_id] = {}
        if llm_id not in self.history[agent_id]:
            self.history[agent_id][llm_id] = []
        if self.graph:
            self.graph.add_node(f"{agent_id}:{llm_id}")

    # ============================================
    # V2: ANCHOR-AWARE DETECTION (Phase 1)
    # ============================================

    def set_anchor(
        self,
        text: str,
        sender_id: str = "user"
    ) -> Dict:
        """
        Set the anchor (user's original query) for context-aware detection.

        All subsequent AI messages will be compared against this anchor.
        If AI response is semantically aligned with anchor, anomaly severity
        is reduced or suppressed to prevent false positives.

        Args:
            text: The user's original query text
            sender_id: ID of the sender (default "user")

        Returns:
            Dict with anchor_set status and anchor_id
        """
        import uuid

        embedding = get_local_embedding(text)

        self.current_anchor = {
            "text": text,
            "embedding": embedding,
            "sender": sender_id,
            "timestamp": time.time(),
            "message_id": str(uuid.uuid4()),
            "is_anchor": True,
            "anchor_id": None,  # It IS the anchor
            "turn_number": 0
        }

        self.turn_counter = 0

        logger.info(f"Anchor set: '{text[:50]}...' from {sender_id}")

        return {
            "anchor_set": True,
            "anchor_id": self.current_anchor["message_id"],
            "text_preview": text[:100]
        }

    def get_anchor(self) -> Optional[Dict]:
        """
        Get the current anchor (user's original query).

        Returns:
            The current anchor dict, or None if no anchor is set
        """
        if self.current_anchor is None:
            return None

        # Return without embedding for readability
        return {
            "text": self.current_anchor["text"],
            "sender": self.current_anchor["sender"],
            "timestamp": self.current_anchor["timestamp"],
            "message_id": self.current_anchor["message_id"],
            "turn_number": self.turn_counter
        }

    def clear_anchor(self) -> Dict:
        """
        Clear the current anchor.

        Returns:
            Dict with status
        """
        had_anchor = self.current_anchor is not None
        self.current_anchor = None
        self.turn_counter = 0

        return {"anchor_cleared": had_anchor}

    def send_message(
        self,
        text: str,
        sender_id: str,
        receiver_id: Optional[str] = None,
        llm_id: str = "unknown"
    ) -> Dict[str, Any]:
        # Check usage quota based on tier
        if self.max_messages != -1:  # -1 = unlimited
            if self.session_message_count >= self.max_messages:
                if self.tier == "anonymous":
                    msg = f"Anonymous limit ({self.max_messages} messages) reached. Get FREE API key for 100 messages!"
                else:
                    msg = f"Message limit ({self.max_messages}) reached. Upgrade for more."
                return {
                    "error": "limit_reached",
                    "message": msg,
                    "upgrade_url": PRICING_URL,
                    "register_url": REGISTER_URL,
                    "anomalies": [],
                    "remaining": 0,
                    "tier": self.tier
                }

        # Rate limit
        now = time.time()
        if now - self.last_msg_time.get(sender_id, 0) < 0.1:
            raise RateLimitError("Rate limit: max 10 msg/sec per agent")
        self.last_msg_time[sender_id] = now

        self.register_agent(sender_id, llm_id)
        if receiver_id:
            self.register_agent(receiver_id, llm_id)

        # Track usage
        self.session_message_count += 1
        self.license.track_usage(message_count=1)

        # Embedding - try cloud if enabled and Pro, always fallback to local
        embedding = None
        if self.is_pro and self.use_cloud_embeddings:
            embedding = self.license.get_cloud_embedding(
                text,
                timeout=self.cloud_timeout,
                max_retries=self.cloud_retries
            )
        if embedding is None:
            # Local embeddings (sentence-transformers or synthetic fallback)
            embedding = get_local_embedding(text)

        # V2: Increment turn counter if anchor is set
        if self.current_anchor is not None:
            self.turn_counter += 1

        msg = {
            "text": text,
            "embedding": embedding,
            "sender": sender_id,
            "receiver": receiver_id,
            "llm_id": llm_id,
            "word_count": len(text.split()),
            "timestamp": now,
            "message_id": str(uuid.uuid4()),
            # V2 fields
            "is_anchor": False,
            "anchor_id": self.current_anchor["message_id"] if self.current_anchor else None,
            "turn_number": self.turn_counter
        }

        self.history[sender_id][llm_id].append(msg)
        if len(self.history[sender_id][llm_id]) > 100:
            self.history[sender_id][llm_id].pop(0)

        # V2: Pass anchor for context-aware detection
        anomalies = self.detector.detect(
            msg, self.history, sender_id, llm_id, receiver_id,
            anchor=self.current_anchor  # V2: anchor-aware detection
        )

        # V2.3: Hallucination detection (Phase 3)
        hallucination_anomalies = self._check_hallucination(
            text, sender_id, msg["message_id"], msg["timestamp"]
        )
        anomalies.extend(hallucination_anomalies)

        # Track anomalies for trend analysis
        for anomaly in anomalies:
            self.anomaly_history.append({
                "type": anomaly.type,
                "severity": anomaly.severity,
                "llm_id": anomaly.llm_id,
                "agent_id": anomaly.agent_id,
                "details": anomaly.details,
                "timestamp": anomaly.timestamp,
                "message_id": msg["message_id"]
            })

        # Calculate remaining messages
        if self.max_messages == -1:
            remaining = -1  # Unlimited
        else:
            remaining = max(0, self.max_messages - self.session_message_count)

        result = {
            "anomalies": [a.__dict__ for a in anomalies],
            "message": msg,
            "remaining": remaining,
            "tier": self.tier
        }

        # Show warning for anonymous users
        if self.tier == "anonymous" and remaining <= 2 and remaining > 0:
            print(f"\n[InsAIts] Warning: Only {remaining} messages left! Get FREE key: {REGISTER_URL}\n")

        if anomalies and self.decipher_mode:
            result["decipher_prompt"] = self._generate_decipher(anomalies)

        # Real graph similarity calculation
        if receiver_id and self.graph:
            similarity = self._calculate_edge_similarity(sender_id, receiver_id, llm_id, embedding)
            self.graph.add_edge(
                f"{sender_id}:{llm_id}",
                f"{receiver_id}:{llm_id}",
                similarity=round(similarity, 4),
                drift=round(1 - similarity, 4),
                last_update=now
            )

        return result

    def _calculate_edge_similarity(
        self,
        sender_id: str,
        receiver_id: str,
        llm_id: str,
        current_embedding: np.ndarray
    ) -> float:
        """Calculate real similarity between sender and receiver communication patterns"""
        recv_hist = self.history.get(receiver_id, {})

        # Get receiver's recent messages
        similarities = []
        for recv_llm, msgs in recv_hist.items():
            if msgs:
                for msg in msgs[-5:]:  # Last 5 messages
                    recv_emb = np.array(msg["embedding"])
                    sim = float(np.dot(current_embedding, recv_emb) /
                               (np.linalg.norm(current_embedding) * np.linalg.norm(recv_emb) + 1e-8))
                    similarities.append(sim)

        if similarities:
            return sum(similarities) / len(similarities)
        return 0.5  # Neutral if no history

    def _generate_decipher(self, anomalies: List[Anomaly]) -> str:
        lines = ["Clarify for cross-LLM understanding:"]
        for a in anomalies:
            if a.type == "CROSS_LLM_SHORTHAND":
                lines.append("- Expand shorthand across models")
            elif a.type == "CROSS_LLM_JARGON":
                lines.append(f"- Define: {', '.join(a.details.get('new_terms', []))}")
        return "\n".join(lines)

    def decipher(
        self,
        msg: Dict,
        target_llm_id: Optional[str] = None,
        model: str = "phi3",
        mode: Literal["auto", "cloud", "local"] = "auto"
    ) -> Dict[str, Any]:
        """
        The killer feature: expand shorthand, explain jargon, remove hedges,
        and rephrase for target LLM style.

        Args:
            msg: Message dict with 'text', 'sender', optionally 'receiver'
            target_llm_id: Target LLM style to optimize for
            model: Local Ollama model to use (default: phi3)
            mode: Decipher mode
                - "auto": Cloud first (if available), fallback to local
                - "cloud": Cloud only (requires API key with cloud_decipher feature)
                - "local": Local Ollama only

        Returns:
            Dict with expanded_text, explanations, rephrased_text, confidence_improved
        """
        if self._decipher_engine is None:
            return {
                "error": "Decipher requires InsAIts Premium",
                "premium_required": True,
                "original_text": msg.get("text", "")
            }

        # Build context from session history
        context = self._decipher_engine.build_context(
            self.history, msg["sender"], msg.get("receiver")
        )

        return self._decipher_engine.decipher(
            msg=msg, context=context,
            target_llm_id=target_llm_id, model=model, mode=mode
        )

    def get_conversation_thread(
        self,
        agent_a: str,
        agent_b: str,
        limit: int = 100
    ) -> List[Dict]:
        """
        Get the conversation thread between two specific agents.
        Returns messages in chronological order showing the back-and-forth.
        """
        thread = []

        # Collect messages from agent_a to agent_b
        for llm, msgs in self.history.get(agent_a, {}).items():
            for m in msgs:
                if m.get("receiver") == agent_b:
                    thread.append({**m, "_direction": f"{agent_a} → {agent_b}"})

        # Collect messages from agent_b to agent_a
        for llm, msgs in self.history.get(agent_b, {}).items():
            for m in msgs:
                if m.get("receiver") == agent_a:
                    thread.append({**m, "_direction": f"{agent_b} → {agent_a}"})

        # Sort chronologically
        thread = sorted(thread, key=lambda x: x["timestamp"])[-limit:]

        return thread

    def export_graph(self) -> Dict:
        if not self.graph:
            return {}
        data = nx.node_link_data(self.graph)
        for link in data["links"]:
            link["drift"] = 1 - link.get("similarity", 1)
        return data

    def get_stats(self) -> Dict:
        total_messages = sum(len(h) for a in self.history.values() for h in a.values())

        if self.is_pro:
            remaining = -1
        else:
            remaining = max(0, self.max_messages - self.session_message_count)

        return {
            "session_id": self.session_id,
            "session_name": self.session_name,
            "agents": self.agents,
            "total_messages": total_messages,
            "session_messages": self.session_message_count,
            "remaining": remaining,
            "limit": self.max_messages if not self.is_pro else -1,
            "tier": self.license.tier,
            "is_pro": self.is_pro,
            "license_status": self.license.get_status(),
            "llm_decipher_available": LLM_AVAILABLE
        }

    # ============================================
    # CONVERSATION READING & ANALYSIS
    # ============================================

    def get_conversation(
        self,
        agent_id: Optional[str] = None,
        llm_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict]:
        """
        Read conversation history.
        - If agent_id provided: get that agent's messages
        - If llm_id provided: filter by LLM
        - If neither: get all messages chronologically
        """
        messages = []

        if agent_id and agent_id in self.history:
            agent_hist = self.history[agent_id]
            if llm_id and llm_id in agent_hist:
                messages = agent_hist[llm_id][-limit:]
            else:
                for llm, msgs in agent_hist.items():
                    messages.extend(msgs)
        else:
            # All messages from all agents
            for aid, agent_hist in self.history.items():
                for llm, msgs in agent_hist.items():
                    messages.extend(msgs)

        # Sort by timestamp and limit
        messages = sorted(messages, key=lambda x: x["timestamp"])[-limit:]

        # Return readable format (without embeddings for readability)
        return [{
            "message_id": m.get("message_id", "N/A"),
            "text": m["text"],
            "sender": m["sender"],
            "receiver": m.get("receiver"),
            "llm_id": m["llm_id"],
            "word_count": m["word_count"],
            "timestamp": m["timestamp"],
            "time_formatted": datetime.fromtimestamp(m["timestamp"]).strftime("%H:%M:%S")
        } for m in messages]

    def get_discussion_thread(
        self,
        agent_a: str,
        agent_b: str,
        limit: int = 100
    ) -> List[Dict]:
        """
        Get the conversation thread between two specific agents.
        Returns messages in chronological order showing the back-and-forth.
        """
        thread = self.get_conversation_thread(agent_a, agent_b, limit)

        return [{
            "direction": m["_direction"],
            "text": m["text"],
            "llm_id": m["llm_id"],
            "word_count": m["word_count"],
            "time": datetime.fromtimestamp(m["timestamp"]).strftime("%H:%M:%S")
        } for m in thread]

    def analyze_discussion(
        self,
        agent_a: str,
        agent_b: str
    ) -> Dict:
        """
        Analyze the quality of discussion between two agents.
        Returns semantic coherence, drift patterns, and communication health.
        """
        thread = self.get_conversation_thread(agent_a, agent_b, limit=1000)

        if len(thread) < 2:
            return {"status": "insufficient_data", "message_count": len(thread)}

        # Calculate sequential similarity (coherence)
        similarities = []
        for i in range(1, len(thread)):
            emb_a = np.array(thread[i-1]["embedding"])
            emb_b = np.array(thread[i]["embedding"])
            sim = float(np.dot(emb_a, emb_b) /
                       (np.linalg.norm(emb_a) * np.linalg.norm(emb_b) + 1e-8))
            similarities.append(sim)

        avg_coherence = sum(similarities) / len(similarities) if similarities else 0

        # Detect drift (declining similarity over time)
        drift_detected = False
        if len(similarities) >= 4:
            first_half = sum(similarities[:len(similarities)//2]) / (len(similarities)//2)
            second_half = sum(similarities[len(similarities)//2:]) / (len(similarities) - len(similarities)//2)
            drift_detected = (first_half - second_half) > 0.15

        # Word count analysis (shorthand emergence)
        word_counts = [m["word_count"] for m in thread]
        avg_words_start = sum(word_counts[:3]) / min(3, len(word_counts))
        avg_words_end = sum(word_counts[-3:]) / min(3, len(word_counts))
        compression_trend = avg_words_start / max(avg_words_end, 1)

        return {
            "message_count": len(thread),
            "avg_coherence": round(avg_coherence, 3),
            "coherence_health": "good" if avg_coherence > 0.6 else "warning" if avg_coherence > 0.4 else "poor",
            "drift_detected": drift_detected,
            "compression_ratio": round(compression_trend, 2),
            "shorthand_risk": compression_trend > 2.0,
            "similarity_trend": similarities[-5:] if len(similarities) >= 5 else similarities
        }

    def get_all_discussions(self) -> List[Dict]:
        """
        Get summary of all agent-to-agent discussion pairs.
        """
        pairs = set()

        for agent_id, agent_hist in self.history.items():
            for llm, msgs in agent_hist.items():
                for m in msgs:
                    if m.get("receiver"):
                        pair = tuple(sorted([agent_id, m["receiver"]]))
                        pairs.add(pair)

        discussions = []
        for agent_a, agent_b in pairs:
            analysis = self.analyze_discussion(agent_a, agent_b)
            discussions.append({
                "agents": f"{agent_a} <-> {agent_b}",
                "message_count": analysis.get("message_count", 0),
                "health": analysis.get("coherence_health", "unknown"),
                "drift": analysis.get("drift_detected", False)
            })

        return sorted(discussions, key=lambda x: x["message_count"], reverse=True)

    def export_conversation_log(
        self,
        filepath: Optional[str] = None
    ) -> str:
        """
        Export full conversation log as formatted text.
        """
        lines = [
            f"=== InsAIts Session Log ===",
            f"Session: {self.session_name}",
            f"ID: {self.session_id}",
            f"Agents: {', '.join(self.agents)}",
            f"{'='*40}",
            ""
        ]

        all_msgs = []
        for agent_id, agent_hist in self.history.items():
            for llm, msgs in agent_hist.items():
                all_msgs.extend(msgs)

        all_msgs = sorted(all_msgs, key=lambda x: x["timestamp"])

        for m in all_msgs:
            time_str = datetime.fromtimestamp(m["timestamp"]).strftime("%H:%M:%S")
            receiver = f" → {m['receiver']}" if m.get("receiver") else ""
            lines.append(f"[{time_str}] {m['sender']}{receiver} ({m['llm_id']}):")
            lines.append(f"  {m['text']}")
            lines.append("")

        log_text = "\n".join(lines)

        if filepath:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(log_text)

        return log_text

    # ============================================
    # ADAPTIVE LEARNING & TREND ANALYSIS
    # ============================================

    def learn_from_session(
        self,
        min_occurrences: int = 3,
        auto_save: bool = True
    ) -> Dict:
        """
        Analyze session messages and learn new jargon terms.

        This method extracts acronyms/terms from all session messages,
        identifies frequently used ones, and adds them to the learned dictionary.

        Args:
            min_occurrences: Minimum times a term must appear to be learned
            auto_save: Whether to persist the dictionary after learning

        Returns:
            Dict with learning statistics
        """
        import re
        from collections import Counter

        # Collect all text from session
        all_text = []
        for agent_hist in self.history.values():
            for llm_msgs in agent_hist.values():
                for msg in llm_msgs:
                    all_text.append(msg["text"])

        if not all_text:
            return {
                "status": "no_data",
                "message": "No messages in session to learn from",
                "terms_learned": 0
            }

        # Extract all acronyms
        full_text = " ".join(all_text)
        acronyms = re.findall(r'\b[A-Z]{2,}\b', full_text)
        term_counts = Counter(acronyms)

        # Filter: only learn terms that appear frequently and aren't known
        new_terms = []
        skipped_known = []
        skipped_low_count = []

        # Check known terms via premium adaptive dict or basic seed dict
        known_terms = self.detector.jargon_dict.get("known", set())
        learned_terms = self.detector.jargon_dict.get("learned", set())
        all_known = known_terms | learned_terms

        for term, count in term_counts.items():
            if term.upper() in all_known or term in all_known:
                skipped_known.append(term)
            elif count < min_occurrences:
                skipped_low_count.append((term, count))
            else:
                # Learn this term
                self.detector.add_learned_term(term)
                new_terms.append((term, count))

        # Persist via premium adaptive dict if available
        if auto_save and new_terms and self.detector._adaptive_dict is not None:
            self.detector._adaptive_dict._save_dict()

        return {
            "status": "success",
            "terms_learned": len(new_terms),
            "learned_terms": new_terms,
            "already_known": len(skipped_known),
            "below_threshold": len(skipped_low_count),
            "jargon_stats": self.detector.get_jargon_stats()
        }

    def get_anomaly_trends(
        self,
        window_minutes: int = 5,
        include_details: bool = False
    ) -> Dict:
        """
        Analyze anomaly patterns over time.

        Provides insights into:
        - Anomaly frequency and distribution
        - Severity trends
        - Type breakdown
        - Time-based patterns

        Args:
            window_minutes: Time window for grouping anomalies
            include_details: Whether to include full anomaly details

        Returns:
            Dict with trend analysis
        """
        if not self.anomaly_history:
            return {
                "status": "no_anomalies",
                "message": "No anomalies detected in this session",
                "total_count": 0
            }

        from collections import Counter

        now = time.time()

        # Basic counts
        type_counts = Counter(a["type"] for a in self.anomaly_history)
        severity_counts = Counter(a["severity"] for a in self.anomaly_history)
        agent_counts = Counter(a["agent_id"] for a in self.anomaly_history)
        llm_counts = Counter(a["llm_id"] for a in self.anomaly_history)

        # Time-based analysis
        window_seconds = window_minutes * 60
        time_windows = {}

        for anomaly in self.anomaly_history:
            # Calculate which window this anomaly falls into
            age_seconds = now - anomaly["timestamp"]
            window_index = int(age_seconds // window_seconds)
            window_label = f"{window_index * window_minutes}-{(window_index + 1) * window_minutes}min ago"

            if window_label not in time_windows:
                time_windows[window_label] = []
            time_windows[window_label].append(anomaly["type"])

        # Calculate trend (increasing/decreasing)
        if len(self.anomaly_history) >= 4:
            mid = len(self.anomaly_history) // 2
            first_half_count = mid
            second_half_count = len(self.anomaly_history) - mid
            trend = "increasing" if second_half_count > first_half_count * 1.2 else \
                    "decreasing" if first_half_count > second_half_count * 1.2 else "stable"
        else:
            trend = "insufficient_data"

        # Build result
        result = {
            "status": "success",
            "total_count": len(self.anomaly_history),
            "by_type": dict(type_counts),
            "by_severity": dict(severity_counts),
            "by_agent": dict(agent_counts),
            "by_llm": dict(llm_counts),
            "trend": trend,
            "time_distribution": {
                k: {"count": len(v), "types": dict(Counter(v))}
                for k, v in sorted(time_windows.items())
            },
            "most_common_type": type_counts.most_common(1)[0] if type_counts else None,
            "high_severity_count": severity_counts.get("high", 0),
            "session_health": self._calculate_session_health(type_counts, severity_counts)
        }

        if include_details:
            result["anomaly_history"] = self.anomaly_history

        return result

    def _calculate_session_health(
        self,
        type_counts: 'Counter',
        severity_counts: 'Counter'
    ) -> Dict:
        """
        Calculate overall session health based on anomaly patterns.

        Returns health score (0-100) and status.
        """
        total = sum(type_counts.values())

        if total == 0:
            return {"score": 100, "status": "excellent", "message": "No anomalies detected"}

        # Deduct points based on severity
        high_penalty = severity_counts.get("high", 0) * 15
        medium_penalty = severity_counts.get("medium", 0) * 5
        low_penalty = severity_counts.get("low", 0) * 2
        critical_penalty = severity_counts.get("critical", 0) * 25

        # Extra penalty for certain anomaly types
        context_loss_penalty = type_counts.get("CONTEXT_LOSS", 0) * 10
        shorthand_penalty = type_counts.get("SHORTHAND_EMERGENCE", 0) * 5

        # V2.3: Hallucination-related penalties
        fact_contradiction_penalty = (
            type_counts.get("FACT_CONTRADICTION", 0) * 20
        )
        phantom_citation_penalty = (
            type_counts.get("PHANTOM_CITATION", 0) * 15
        )
        ungrounded_penalty = (
            type_counts.get("UNGROUNDED_CLAIM", 0) * 10
        )
        confidence_decay_penalty = (
            type_counts.get("CONFIDENCE_DECAY", 0) * 8
        )
        confidence_flip_penalty = (
            type_counts.get("CONFIDENCE_FLIP_FLOP", 0) * 5
        )

        total_penalty = min(
            100,
            critical_penalty + high_penalty + medium_penalty + low_penalty +
            context_loss_penalty + shorthand_penalty +
            fact_contradiction_penalty + phantom_citation_penalty +
            ungrounded_penalty + confidence_decay_penalty +
            confidence_flip_penalty
        )
        score = max(0, 100 - total_penalty)

        if score >= 80:
            status, message = "good", "Communication is healthy with minor issues"
        elif score >= 60:
            status, message = "warning", "Some communication issues detected"
        elif score >= 40:
            status, message = "concerning", "Significant communication issues"
        else:
            status, message = "critical", "Severe communication breakdown detected"

        return {
            "score": score,
            "status": status,
            "message": message,
            "factors": {
                "high_severity_anomalies": severity_counts.get("high", 0),
                "critical_severity_anomalies": severity_counts.get("critical", 0),
                "context_losses": type_counts.get("CONTEXT_LOSS", 0),
                "shorthand_emergences": type_counts.get("SHORTHAND_EMERGENCE", 0),
                "fact_contradictions": type_counts.get("FACT_CONTRADICTION", 0),
                "phantom_citations": type_counts.get("PHANTOM_CITATION", 0),
                "ungrounded_claims": type_counts.get("UNGROUNDED_CLAIM", 0),
                "confidence_decays": type_counts.get("CONFIDENCE_DECAY", 0),
                "confidence_flip_flops": type_counts.get("CONFIDENCE_FLIP_FLOP", 0)
            }
        }

    def get_jargon_dictionary(self) -> Dict:
        """
        Get the current state of the adaptive jargon dictionary.

        Returns statistics and the learned/candidate terms.
        """
        return self.detector.get_jargon_stats()

    def add_jargon_term(self, term: str, meaning: Optional[str] = None) -> None:
        """
        Manually add a term to the jargon dictionary.

        Args:
            term: The acronym/term to add (will be uppercased)
            meaning: Optional expanded meaning
        """
        self.detector.add_learned_term(term, meaning)
        logger.info(f"Manually added jargon term: {term.upper()}")

    # ============================================
    # V2: DOMAIN DICTIONARY MANAGEMENT (Phase 4)
    # ============================================

    def load_domain(self, domain: str) -> Dict:
        """
        Load a domain-specific dictionary to reduce false positives.

        Available domains: finance, healthcare, kubernetes, machine_learning, devops, quantum

        Args:
            domain: Domain name to load

        Returns:
            Dict with loaded domain info and terms added
        """
        return self.detector.load_domain(domain)

    def get_available_domains(self) -> List[str]:
        """
        Get list of available domain dictionaries.

        Returns:
            List of domain names
        """
        return self.detector.get_available_domains()

    def export_dictionary(self, filepath: str) -> Dict:
        """
        Export the current jargon dictionary to a JSON file.

        Args:
            filepath: Path to save the dictionary JSON file

        Returns:
            Dict with export status and statistics
        """
        return self.detector.export_dictionary(filepath)

    def import_dictionary(self, filepath: str, merge: bool = True) -> Dict:
        """
        Import a dictionary from a JSON file.

        Args:
            filepath: Path to the dictionary JSON file
            merge: If True, merge with existing. If False, replace.

        Returns:
            Dict with import status and statistics
        """
        return self.detector.import_dictionary(filepath, merge)

    def auto_expand_terms(
        self,
        terms: Optional[List[str]] = None,
        model: str = "phi3"
    ) -> Dict:
        """
        Use LLM to automatically expand undefined terms.

        Requires Ollama to be running locally.

        Args:
            terms: List of terms to expand. If None, expands all learned terms without expansions.
            model: Ollama model to use for expansion

        Returns:
            Dict with expanded terms and statistics
        """
        return self.detector.auto_expand_terms(terms, model)

    # ============================================
    # V2.3: HALLUCINATION DETECTION (Phase 3)
    # ============================================

    def enable_fact_tracking(self, enabled: bool = True) -> Dict:
        """
        Enable or disable automatic fact tracking in send_message.

        When enabled, factual claims are extracted from every message
        and checked against previous claims for contradictions.

        Args:
            enabled: Whether to enable fact tracking

        Returns:
            Dict with status
        """
        if not get_feature(self.tier, "fact_tracking"):
            return {
                "error": f"Fact tracking not available for {self.tier} tier",
                "upgrade_url": PRICING_URL
            }

        self.fact_tracking_enabled = enabled
        logger.info(f"Fact tracking {'enabled' if enabled else 'disabled'}")
        return {"fact_tracking": enabled, "tier": self.tier}

    def set_source_documents(
        self,
        documents: List[str],
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        auto_check: bool = True
    ) -> Dict:
        """
        Set source documents for grounding verification.

        When source documents are set, AI responses can be checked against
        them to detect ungrounded claims (hallucinations).

        Args:
            documents: List of source document texts
            chunk_size: Characters per chunk for splitting documents
            chunk_overlap: Overlap between consecutive chunks
            auto_check: If True, automatically check grounding in send_message

        Returns:
            Dict with document and chunk statistics
        """
        if not get_feature(self.tier, "source_grounding"):
            return {
                "error": f"Source grounding not available for {self.tier} tier",
                "upgrade_url": PRICING_URL
            }

        result = self.source_grounder.set_documents(
            documents, chunk_size, chunk_overlap
        )

        if "error" not in result:
            self._auto_grounding_check = auto_check
            if auto_check:
                logger.info("Auto grounding check enabled in send_message")

        return result

    def check_grounding(
        self,
        text: str,
        threshold: float = 0.7
    ) -> Dict:
        """
        Manually check if text is grounded in source documents.

        Requires set_source_documents() to be called first.

        Args:
            text: Text to check against source documents
            threshold: Minimum similarity for grounding (0-1)

        Returns:
            Dict with grounding assessment
        """
        if not get_feature(self.tier, "source_grounding"):
            return {
                "error": f"Source grounding not available for {self.tier} tier",
                "upgrade_url": PRICING_URL
            }

        return self.source_grounder.check_grounding(text, threshold)

    def verify_self_consistency(
        self,
        text: str,
        model: str = "phi3"
    ) -> Dict:
        """
        Use local LLM to verify response is internally consistent.

        Checks for contradictions, fabricated data, overconfidence,
        and logical inconsistencies.

        Requires Ollama running locally.

        Args:
            text: Text to verify
            model: Ollama model to use

        Returns:
            Dict with consistency assessment
        """
        if not get_feature(self.tier, "self_consistency"):
            return {
                "error": (
                    f"Self-consistency not available for {self.tier} tier"
                ),
                "upgrade_url": PRICING_URL
            }

        return self.consistency_checker.check(text, model)

    def get_fact_claims(self) -> List[Dict]:
        """Get all tracked factual claims from the session."""
        return self.fact_tracker.get_claims()

    def get_fact_tracker_stats(self) -> Dict:
        """Get fact tracker statistics."""
        return {
            "total_claims": self.fact_tracker.get_claim_count(),
            "topics": self.fact_tracker.get_topics(),
            "fact_tracking_enabled": self.fact_tracking_enabled,
            "source_grounding": self.source_grounder.get_stats(),
            "auto_grounding_check": self._auto_grounding_check
        }

    def clear_fact_tracker(self) -> Dict:
        """Reset the fact tracker and clear all tracked claims."""
        self.fact_tracker.clear()
        return {"cleared": True, "claims_remaining": 0}

    def clear_source_documents(self) -> Dict:
        """Clear source documents and disable auto grounding check."""
        self.source_grounder.clear()
        self._auto_grounding_check = False
        return {"cleared": True, "auto_grounding_check": False}

    def detect_phantom_citations(self, text: str) -> Dict:
        """
        Manually check text for fabricated citations.

        Detects suspicious URLs, DOIs, paper references, and arxiv IDs
        that AI models commonly hallucinate.

        Args:
            text: Text to analyze for phantom citations

        Returns:
            Dict with suspicious citations and summary
        """
        if not get_feature(self.tier, "fact_tracking"):
            return {
                "error": (
                    f"Phantom citation detection not available "
                    f"for {self.tier} tier"
                ),
                "upgrade_url": PRICING_URL
            }

        suspicious = self.citation_detector.detect(text)
        high_confidence = [
            c for c in suspicious if c.get("suspicion_score", 0) >= 0.5
        ]

        return {
            "total_suspicious": len(suspicious),
            "high_confidence": len(high_confidence),
            "citations": suspicious,
            "verdict": (
                "clean" if not high_confidence
                else "suspicious" if len(high_confidence) <= 2
                else "likely_fabricated"
            )
        }

    def get_confidence_stats(
        self,
        agent_id: Optional[str] = None
    ) -> Dict:
        """
        Get confidence tracking statistics.

        Shows confidence trajectory per agent, detecting patterns
        of certainty erosion or flip-flopping.

        Args:
            agent_id: Specific agent to get stats for, or None for all

        Returns:
            Dict with confidence statistics
        """
        if not get_feature(self.tier, "fact_tracking"):
            return {
                "error": (
                    f"Confidence tracking not available "
                    f"for {self.tier} tier"
                ),
                "upgrade_url": PRICING_URL
            }

        if agent_id:
            return self.confidence_tracker.get_agent_confidence(agent_id)
        return self.confidence_tracker.get_all_stats()

    def get_numeric_drift(self, topic: str = "") -> Dict:
        """
        Get numeric value drift for tracked topics.

        Detects when numeric facts change across messages
        (e.g., "costs $500" then "costs $450" then "costs $300").

        Args:
            topic: Specific topic to check, or empty for all

        Returns:
            Dict with drift events and summary
        """
        if not get_feature(self.tier, "fact_tracking"):
            return {
                "error": (
                    f"Numeric drift detection not available "
                    f"for {self.tier} tier"
                ),
                "upgrade_url": PRICING_URL
            }

        drifts = self.fact_tracker.get_numeric_drift(topic)
        return {
            "drift_events": drifts,
            "total_drifts": len(drifts),
            "high_severity": sum(
                1 for d in drifts if d.get("severity") == "high"
            ),
            "topics_affected": list(set(d["topic"] for d in drifts))
        }

    def get_cross_agent_summary(self) -> Dict:
        """
        Get summary of factual claims across all agents.

        Highlights topics where multiple agents have made claims,
        which is where cross-agent contradictions are most likely.
        This is the unique InsAIts differentiator - no single-agent
        tool can detect inter-agent factual inconsistencies.

        Returns:
            Dict with cross-agent analysis
        """
        if not get_feature(self.tier, "fact_tracking"):
            return {
                "error": (
                    f"Cross-agent analysis not available "
                    f"for {self.tier} tier"
                ),
                "upgrade_url": PRICING_URL
            }

        return self.fact_tracker.get_cross_agent_summary()

    def get_hallucination_summary(self) -> Dict:
        """
        Comprehensive summary of all hallucination detection results.

        Aggregates data from fact tracking, phantom citations,
        confidence decay, and source grounding into a single report.

        Returns:
            Dict with full hallucination assessment
        """
        if not get_feature(self.tier, "fact_tracking"):
            return {
                "error": (
                    f"Hallucination detection not available "
                    f"for {self.tier} tier"
                ),
                "upgrade_url": PRICING_URL
            }

        # Collect anomaly counts by type
        hallucination_types = {
            "FACT_CONTRADICTION", "UNGROUNDED_CLAIM",
            "PHANTOM_CITATION", "CONFIDENCE_DECAY",
            "CONFIDENCE_FLIP_FLOP"
        }
        hallucination_anomalies = [
            a for a in self.anomaly_history
            if a.get("type") in hallucination_types
        ]

        type_counts = {}
        for a in hallucination_anomalies:
            t = a["type"]
            type_counts[t] = type_counts.get(t, 0) + 1

        total = len(hallucination_anomalies)

        # Calculate hallucination health score (0-100)
        if total == 0:
            health_score = 100
            health_status = "excellent"
        else:
            penalty = (
                type_counts.get("FACT_CONTRADICTION", 0) * 20 +
                type_counts.get("PHANTOM_CITATION", 0) * 15 +
                type_counts.get("UNGROUNDED_CLAIM", 0) * 10 +
                type_counts.get("CONFIDENCE_DECAY", 0) * 8 +
                type_counts.get("CONFIDENCE_FLIP_FLOP", 0) * 5
            )
            health_score = max(0, 100 - min(100, penalty))
            if health_score >= 80:
                health_status = "good"
            elif health_score >= 60:
                health_status = "warning"
            elif health_score >= 40:
                health_status = "concerning"
            else:
                health_status = "critical"

        return {
            "hallucination_health": {
                "score": health_score,
                "status": health_status
            },
            "total_hallucination_anomalies": total,
            "by_type": type_counts,
            "fact_tracker": {
                "total_claims": self.fact_tracker.get_claim_count(),
                "topics": len(self.fact_tracker.get_topics()),
                "enabled": self.fact_tracking_enabled
            },
            "source_grounding": self.source_grounder.get_stats(),
            "confidence": self.confidence_tracker.get_all_stats(),
            "numeric_drifts": len(
                self.fact_tracker.get_numeric_drift()
            ),
            "cross_agent": (
                self.fact_tracker.get_cross_agent_summary()
            )
        }

    def _check_hallucination(
        self,
        text: str,
        sender_id: str,
        message_id: str,
        timestamp: float
    ) -> List[Anomaly]:
        """
        Internal method called by send_message to run hallucination checks.

        Runs (when enabled):
        1. Fact tracking - extract claims, detect cross-agent contradictions
        2. Phantom citation detection - find fabricated URLs, DOIs, papers
        3. Confidence decay tracking - monitor certainty erosion per agent
        4. Source grounding - verify response against source documents

        Returns list of Anomaly objects for any issues found.
        """
        hallucination_anomalies = []

        # 1. Fact tracking: extract claims and check for contradictions
        if self.fact_tracking_enabled:
            try:
                claims = self.fact_tracker.extract_claims(
                    text, sender_id, message_id, use_llm=False
                )
                contradictions = self.fact_tracker.track_claims(claims)

                for contradiction in contradictions:
                    hallucination_anomalies.append(Anomaly(
                        type="FACT_CONTRADICTION",
                        severity=(
                            "critical" if contradiction.get("cross_agent")
                            else "high"
                        ),
                        llm_id=sender_id,
                        agent_id=sender_id,
                        details={
                            "topic": contradiction["topic"],
                            "original_value": contradiction["original_value"],
                            "original_agent": contradiction["original_agent"],
                            "new_value": contradiction["new_value"],
                            "confidence": contradiction["confidence"],
                            "cross_agent": contradiction.get(
                                "cross_agent", False
                            )
                        },
                        timestamp=timestamp,
                        message_id=message_id
                    ))
            except Exception as e:
                logger.error(
                    f"Fact tracking error: {e}", exc_info=True
                )

        # 2. Phantom citation detection
        if self.fact_tracking_enabled:
            try:
                suspicious_citations = self.citation_detector.detect(text)
                for citation in suspicious_citations:
                    if citation.get("suspicion_score", 0) >= 0.5:
                        hallucination_anomalies.append(Anomaly(
                            type="PHANTOM_CITATION",
                            severity=(
                                "critical"
                                if citation["suspicion_score"] >= 0.8
                                else "high"
                            ),
                            llm_id=sender_id,
                            agent_id=sender_id,
                            details={
                                "citation_type": citation["type"],
                                "citation": citation["citation"],
                                "suspicion_score": citation[
                                    "suspicion_score"
                                ],
                                "reasons": citation.get("reasons", [])
                            },
                            timestamp=timestamp,
                            message_id=message_id
                        ))
            except Exception as e:
                logger.error(
                    f"Phantom citation detection error: {e}", exc_info=True
                )

        # 3. Confidence decay tracking
        if self.fact_tracking_enabled:
            try:
                decay_result = self.confidence_tracker.track(
                    sender_id, text, timestamp
                )
                if decay_result is not None:
                    decay_type = decay_result.get("type", "confidence_decay")
                    if decay_type == "confidence_flip_flop":
                        hallucination_anomalies.append(Anomaly(
                            type="CONFIDENCE_FLIP_FLOP",
                            severity="medium",
                            llm_id=sender_id,
                            agent_id=sender_id,
                            details={
                                "flip_count": decay_result["flip_count"],
                                "recent_scores": decay_result[
                                    "recent_scores"
                                ],
                                "avg_confidence": decay_result[
                                    "avg_confidence"
                                ]
                            },
                            timestamp=timestamp,
                            message_id=message_id
                        ))
                    else:
                        hallucination_anomalies.append(Anomaly(
                            type="CONFIDENCE_DECAY",
                            severity=decay_result.get("severity", "medium"),
                            llm_id=sender_id,
                            agent_id=sender_id,
                            details={
                                "initial_confidence": decay_result[
                                    "initial_confidence"
                                ],
                                "current_confidence": decay_result[
                                    "current_confidence"
                                ],
                                "decay_amount": decay_result["decay_amount"],
                                "decay_steps": decay_result["decay_steps"],
                                "avg_confidence": decay_result[
                                    "avg_confidence"
                                ]
                            },
                            timestamp=timestamp,
                            message_id=message_id
                        ))
            except Exception as e:
                logger.error(
                    f"Confidence tracking error: {e}", exc_info=True
                )

        # 4. Source grounding: check if response is grounded
        if self._auto_grounding_check and self.source_grounder.source_chunks:
            try:
                grounding = self.source_grounder.check_grounding(text)
                if grounding.get("grounded") is False:
                    ungrounded_count = grounding.get(
                        "sentence_analysis", {}
                    ).get("ungrounded_sentences", 0)
                    hallucination_anomalies.append(Anomaly(
                        type="UNGROUNDED_CLAIM",
                        severity="high",
                        llm_id=sender_id,
                        agent_id=sender_id,
                        details={
                            "grounding_score": grounding["grounding_score"],
                            "threshold": grounding["threshold"],
                            "nearest_chunk": (
                                grounding["nearest_chunks"][0][
                                    "chunk_preview"
                                ]
                                if grounding.get("nearest_chunks")
                                else "N/A"
                            ),
                            "ungrounded_sentences": ungrounded_count
                        },
                        timestamp=timestamp,
                        message_id=message_id
                    ))
            except Exception as e:
                logger.error(
                    f"Grounding check error: {e}", exc_info=True
                )

        return hallucination_anomalies

    # ============================================
    # V2: FORENSIC CHAIN TRACING (Phase 2)
    # ============================================

    def trace_root(
        self,
        anomaly: Dict,
        max_depth: int = 20
    ) -> Dict:
        """
        Trace an anomaly back to its root cause.

        Returns the chain of messages that led to this anomaly,
        identifying where the problem first appeared.

        Args:
            anomaly: The anomaly dict (from send_message result)
            max_depth: Maximum chain depth to trace

        Returns:
            Dict with chain analysis and forensic summary
        """
        # Get the message_id from anomaly
        target_msg_id = anomaly.get("message_id")
        if not target_msg_id:
            return {"error": "No message_id in anomaly", "chain": []}

        # Find the target message
        target_msg = self._find_message_by_id(target_msg_id)
        if not target_msg:
            return {"error": f"Message not found: {target_msg_id}", "chain": []}

        # Build backward chain
        chain = []
        current_msg = target_msg
        visited = set()

        for _ in range(max_depth):
            msg_id = current_msg.get("message_id")
            if not msg_id or msg_id in visited:
                break
            visited.add(msg_id)

            chain.append({
                "message_id": msg_id,
                "sender": current_msg.get("sender"),
                "receiver": current_msg.get("receiver"),
                "llm_id": current_msg.get("llm_id"),
                "text_preview": current_msg.get("text", "")[:100],
                "word_count": current_msg.get("word_count", 0),
                "timestamp": current_msg.get("timestamp"),
                "turn_number": current_msg.get("turn_number", 0)
            })

            # Find previous message in this conversation
            prev_msg = self._find_previous_message(current_msg)
            if not prev_msg:
                break
            current_msg = prev_msg

        # Reverse to show oldest first
        chain.reverse()

        # Identify the root (first message where issue appears)
        anomaly_type = anomaly.get("type", "UNKNOWN")
        root_index = self._find_anomaly_origin(chain, anomaly_type, anomaly)

        # Generate human-readable summary
        summary = self._generate_forensic_summary(chain, root_index, anomaly)

        return {
            "anomaly_type": anomaly_type,
            "chain_length": len(chain),
            "root_message": chain[root_index] if 0 <= root_index < len(chain) else None,
            "root_index": root_index,
            "full_chain": chain,
            "summary": summary,
            "anchor_id": target_msg.get("anchor_id")
        }

    def get_propagation_chain(
        self,
        anomaly: Dict
    ) -> List[Dict]:
        """
        Get the message propagation chain for an anomaly.

        Simplified version of trace_root that returns just the chain.

        Args:
            anomaly: The anomaly dict

        Returns:
            List of messages in the propagation chain
        """
        result = self.trace_root(anomaly)
        return result.get("full_chain", [])

    def _find_message_by_id(self, message_id: str) -> Optional[Dict]:
        """Find a message by its ID across all history."""
        for agent_id, agent_hist in self.history.items():
            for llm_id, messages in agent_hist.items():
                for msg in messages:
                    if msg.get("message_id") == message_id:
                        return msg
        return None

    def _find_previous_message(self, current_msg: Dict) -> Optional[Dict]:
        """
        Find the message that came before the current one in the conversation.

        Logic:
        1. If there's a receiver, look for messages from receiver to sender
        2. Otherwise, look for previous message from same sender
        """
        sender = current_msg.get("sender")
        receiver = current_msg.get("receiver")
        llm_id = current_msg.get("llm_id")
        timestamp = current_msg.get("timestamp", 0)

        candidates = []

        # Collect all messages before this timestamp
        for agent_id, agent_hist in self.history.items():
            for llm, messages in agent_hist.items():
                for msg in messages:
                    msg_ts = msg.get("timestamp", 0)
                    if msg_ts < timestamp:
                        # Prioritize: messages from receiver to sender (reply chain)
                        if receiver and msg.get("sender") == receiver and msg.get("receiver") == sender:
                            candidates.append((msg_ts, 2, msg))  # Priority 2 (highest)
                        # Same sender, same LLM (continuation)
                        elif msg.get("sender") == sender and msg.get("llm_id") == llm_id:
                            candidates.append((msg_ts, 1, msg))  # Priority 1
                        # Any message to this sender
                        elif msg.get("receiver") == sender:
                            candidates.append((msg_ts, 0, msg))  # Priority 0

        if not candidates:
            return None

        # Sort by priority (desc), then timestamp (desc) to get most recent high-priority
        candidates.sort(key=lambda x: (x[1], x[0]), reverse=True)
        return candidates[0][2]

    def _find_anomaly_origin(
        self,
        chain: List[Dict],
        anomaly_type: str,
        anomaly: Dict
    ) -> int:
        """
        Find where in the chain the anomaly first appears.

        Returns the index of the root message.
        """
        if not chain:
            return -1

        if anomaly_type == "CROSS_LLM_JARGON":
            # Find first message containing the unknown terms
            new_terms = anomaly.get("details", {}).get("new_terms", [])
            if new_terms:
                for i, msg in enumerate(chain):
                    text = msg.get("text_preview", "").upper()
                    if any(term.upper() in text for term in new_terms):
                        return i
            return 0

        elif anomaly_type == "CONTEXT_LOSS":
            # Find where similarity drops - this is the break point
            # Since we don't have similarities in chain, return the anomaly message
            return len(chain) - 1

        elif anomaly_type == "ANCHOR_DRIFT":
            # The drift starts from the message itself
            return len(chain) - 1

        elif anomaly_type == "SHORTHAND_EMERGENCE":
            # Find where word count first drops significantly
            for i in range(1, len(chain)):
                prev_words = chain[i-1].get("word_count", 0)
                curr_words = chain[i].get("word_count", 0)
                if prev_words > 0 and curr_words < prev_words * 0.5:
                    return i
            return len(chain) - 1

        elif anomaly_type == "FACT_CONTRADICTION":
            # The contradiction is in the latest message
            return len(chain) - 1

        elif anomaly_type == "UNGROUNDED_CLAIM":
            # The ungrounded claim is in the latest message
            return len(chain) - 1

        elif anomaly_type == "PHANTOM_CITATION":
            # The phantom citation is in the latest message
            return len(chain) - 1

        elif anomaly_type == "CONFIDENCE_DECAY":
            # Decay is gradual; find where confidence first started dropping
            # The most informative point is where the pattern became anomalous
            return max(0, len(chain) - 3)

        elif anomaly_type == "CONFIDENCE_FLIP_FLOP":
            # Flip-flop is a pattern across recent messages
            return max(0, len(chain) - 3)

        # Default: last message is the origin
        return len(chain) - 1

    def _generate_forensic_summary(
        self,
        chain: List[Dict],
        root_index: int,
        anomaly: Dict
    ) -> str:
        """Generate human-readable forensic report."""
        if not chain:
            return "No messages in chain to analyze."

        anomaly_type = anomaly.get("type", "UNKNOWN")
        root = chain[root_index] if 0 <= root_index < len(chain) else None

        if anomaly_type == "CROSS_LLM_JARGON":
            terms = anomaly.get("details", {}).get("new_terms", [])
            terms_str = ", ".join(terms[:3]) if terms else "unknown terms"
            if root:
                return (
                    f"Jargon '{terms_str}' first appeared in message from "
                    f"{root['sender']} ({root['llm_id']}) at step {root_index + 1} of {len(chain)}. "
                    f"Propagated through {len(chain) - root_index - 1} subsequent messages."
                )
            return f"Jargon '{terms_str}' detected but origin could not be determined."

        elif anomaly_type == "CONTEXT_LOSS":
            similarity = anomaly.get("details", {}).get("similarity", 0)
            if root:
                return (
                    f"Context loss detected at step {root_index + 1} of {len(chain)}. "
                    f"Similarity dropped to {similarity:.1%}. "
                    f"Message from {root['sender']} ({root['llm_id']}) "
                    f"diverged from previous topic."
                )
            return f"Context loss detected with {similarity:.1%} similarity."

        elif anomaly_type == "ANCHOR_DRIFT":
            anchor_sim = anomaly.get("details", {}).get("anchor_similarity", 0)
            if root:
                return (
                    f"Response drifted from original query at step {root_index + 1}. "
                    f"Anchor similarity: {anchor_sim:.1%}. "
                    f"Agent {root['sender']} ({root['llm_id']}) response "
                    f"no longer addresses the user's question."
                )
            return f"Anchor drift detected with {anchor_sim:.1%} similarity to original query."

        elif anomaly_type == "SHORTHAND_EMERGENCE":
            compression = anomaly.get("details", {}).get("compression_ratio", 0)
            if root:
                return (
                    f"Shorthand emerged at step {root_index + 1} of {len(chain)}. "
                    f"Compression ratio: {compression:.1f}x. "
                    f"Agent {root['sender']} began using abbreviated language."
                )
            return f"Shorthand emergence detected with {compression:.1f}x compression."

        elif anomaly_type == "LOW_CONFIDENCE":
            confidence = anomaly.get("details", {}).get("confidence", "Unknown")
            hedge_words = anomaly.get("details", {}).get("hedge_words", [])
            if root:
                return (
                    f"Low confidence language at step {root_index + 1}. "
                    f"Confidence level: {confidence}. "
                    f"Hedging words: {', '.join(hedge_words[:3]) if hedge_words else 'none detected'}. "
                    f"Agent {root['sender']} shows uncertainty."
                )
            return f"Low confidence detected: {confidence}."

        elif anomaly_type == "FACT_CONTRADICTION":
            topic = anomaly.get("details", {}).get("topic", "unknown")
            original = anomaly.get("details", {}).get("original_value", "?")
            new_val = anomaly.get("details", {}).get("new_value", "?")
            original_agent = anomaly.get("details", {}).get("original_agent", "?")
            if root:
                return (
                    f"Factual contradiction detected at step {root_index + 1} "
                    f"of {len(chain)}. "
                    f"Topic: '{topic}'. "
                    f"Original claim by {original_agent}: '{original}'. "
                    f"Contradicting claim by {root['sender']}: '{new_val}'."
                )
            return (
                f"Factual contradiction on topic '{topic}': "
                f"'{original}' vs '{new_val}'."
            )

        elif anomaly_type == "UNGROUNDED_CLAIM":
            score = anomaly.get("details", {}).get("grounding_score", 0)
            threshold = anomaly.get("details", {}).get("threshold", 0.7)
            ungrounded_count = anomaly.get("details", {}).get(
                "ungrounded_sentences", 0
            )
            if root:
                extra = ""
                if ungrounded_count > 0:
                    extra = (
                        f" {ungrounded_count} sentences could not be "
                        f"matched to any source document."
                    )
                return (
                    f"Ungrounded claim detected at step {root_index + 1} "
                    f"of {len(chain)}. "
                    f"Grounding score: {score:.1%} (threshold: {threshold:.1%}). "
                    f"Agent {root['sender']} response is not supported by "
                    f"provided source documents.{extra}"
                )
            return (
                f"Ungrounded claim detected with grounding score "
                f"{score:.1%} (threshold: {threshold:.1%})."
            )

        elif anomaly_type == "PHANTOM_CITATION":
            citation_type = anomaly.get("details", {}).get(
                "citation_type", "unknown"
            )
            citation = anomaly.get("details", {}).get("citation", "?")
            suspicion = anomaly.get("details", {}).get(
                "suspicion_score", 0
            )
            reasons = anomaly.get("details", {}).get("reasons", [])
            reasons_str = ", ".join(reasons[:3]) if reasons else "heuristic"
            if root:
                return (
                    f"Phantom citation detected at step {root_index + 1} "
                    f"of {len(chain)}. "
                    f"Type: {citation_type}. "
                    f"Citation: '{citation[:80]}'. "
                    f"Suspicion score: {suspicion:.0%} ({reasons_str}). "
                    f"Agent {root['sender']} may have fabricated this "
                    f"reference."
                )
            return (
                f"Phantom citation detected: '{citation[:80]}' "
                f"(suspicion: {suspicion:.0%})."
            )

        elif anomaly_type == "CONFIDENCE_DECAY":
            initial = anomaly.get("details", {}).get(
                "initial_confidence", 0
            )
            current = anomaly.get("details", {}).get(
                "current_confidence", 0
            )
            decay = anomaly.get("details", {}).get("decay_amount", 0)
            steps = anomaly.get("details", {}).get("decay_steps", 0)
            if root:
                return (
                    f"Confidence decay detected starting around step "
                    f"{root_index + 1} of {len(chain)}. "
                    f"Confidence dropped from {initial:.0%} to "
                    f"{current:.0%} ({decay:.0%} decay over {steps} steps). "
                    f"Agent {root['sender']} is becoming progressively "
                    f"less certain in its assertions."
                )
            return (
                f"Confidence decay: {initial:.0%} -> {current:.0%} "
                f"({decay:.0%} drop)."
            )

        elif anomaly_type == "CONFIDENCE_FLIP_FLOP":
            flips = anomaly.get("details", {}).get("flip_count", 0)
            scores = anomaly.get("details", {}).get("recent_scores", [])
            scores_str = " -> ".join(
                f"{s:.0%}" for s in scores
            ) if scores else "N/A"
            if root:
                return (
                    f"Confidence flip-flop detected starting around step "
                    f"{root_index + 1} of {len(chain)}. "
                    f"Agent {root['sender']} alternated between confident "
                    f"and uncertain language {flips} times. "
                    f"Recent confidence trajectory: {scores_str}."
                )
            return (
                f"Confidence flip-flop: {flips} alternations detected."
            )

        # Generic fallback
        if root:
            return (
                f"Anomaly '{anomaly_type}' originated at step {root_index + 1} of {len(chain)} "
                f"from agent {root['sender']} ({root['llm_id']})."
            )
        return f"Anomaly '{anomaly_type}' detected in the conversation chain."

    def visualize_chain(
        self,
        anomaly: Dict,
        include_text: bool = False
    ) -> str:
        """
        Create ASCII visualization of the message chain leading to an anomaly.

        Args:
            anomaly: The anomaly dict
            include_text: Whether to include message text previews

        Returns:
            ASCII art visualization of the chain
        """
        result = self.trace_root(anomaly)
        chain = result.get("full_chain", [])
        root_index = result.get("root_index", -1)
        anomaly_type = result.get("anomaly_type", "UNKNOWN")

        if not chain:
            return "No chain to visualize."

        lines = [
            "=" * 60,
            f"FORENSIC CHAIN TRACE: {anomaly_type}",
            "=" * 60,
            ""
        ]

        for i, msg in enumerate(chain):
            # Marker for root message
            marker = " >>> ROOT" if i == root_index else ""
            marker += " <<< ANOMALY" if i == len(chain) - 1 else ""

            sender = msg.get("sender", "?")
            receiver = msg.get("receiver", "")
            llm_id = msg.get("llm_id", "?")
            words = msg.get("word_count", 0)

            arrow = f" -> {receiver}" if receiver else ""

            lines.append(f"[Step {i + 1}]{marker}")
            lines.append(f"  {sender}{arrow} ({llm_id})")
            lines.append(f"  Words: {words}")

            if include_text:
                text = msg.get("text_preview", "")[:80]
                lines.append(f"  Text: \"{text}...\"")

            if i < len(chain) - 1:
                lines.append("     |")
                lines.append("     v")

        lines.append("")
        lines.append("-" * 60)
        lines.append("SUMMARY:")
        lines.append(result.get("summary", "No summary available."))
        lines.append("=" * 60)

        return "\n".join(lines)
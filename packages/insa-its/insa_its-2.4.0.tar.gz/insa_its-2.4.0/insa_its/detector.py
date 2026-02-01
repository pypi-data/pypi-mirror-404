"""
InsAIts SDK - Anomaly Detector
==============================
Multi-LLM statistical anomaly detection with optional premium features.

Open-source detection:
- LLM_FINGERPRINT_MISMATCH: Message length deviates from LLM's typical output
- LOW_CONFIDENCE: Hedging/uncertainty detected via local LLM

Premium detection (requires insa_its.premium):
- SHORTHAND_EMERGENCE: Verbose messages suddenly become terse
- CONTEXT_LOSS: Complete topic changes between consecutive messages
- CROSS_LLM_SHORTHAND: Short messages semantically similar to longer ones from different LLMs
- CROSS_LLM_JARGON: Undefined acronyms/jargon appearing suddenly
- ANCHOR_DRIFT: Response drifts from original user query
- Anchor-based false positive suppression
"""

import numpy as np
import json
import logging
from pathlib import Path
from typing import Any, List, Dict, Optional, Set
from dataclasses import dataclass, field
from collections import defaultdict
import time

logger = logging.getLogger(__name__)

# LLM integration
try:
    from .local_llm import ollama_chat
    LLM_AVAILABLE = True
except Exception:
    LLM_AVAILABLE = False

# Backward-compat: cache directory constants
INSAITS_CACHE_DIR = Path.home() / ".insaits"
JARGON_FILE = INSAITS_CACHE_DIR / "jargon.json"

# Backward-compat: Domain dictionaries stub
# Full version lives in premium/adaptive_dict.py (loaded at runtime, not import time,
# to avoid circular imports: detector -> premium/__init__ -> advanced_detector -> detector)
DOMAIN_DICTIONARIES: Dict[str, Dict[str, Any]] = {}


@dataclass
class Anomaly:
    type: str
    severity: str
    llm_id: str
    agent_id: str
    details: Dict
    timestamp: float
    # V2 fields for forensic tracing and anchor-aware detection
    message_id: str = ""
    root_message_id: Optional[str] = None
    drift_chain: List[str] = field(default_factory=list)
    anchor_similarity: Optional[float] = None


class AnomalyDetector:
    """Multi-LLM statistical anomaly detection with adaptive jargon learning."""

    # Promotion threshold: how many times a term must appear before auto-learning
    CANDIDATE_PROMOTION_THRESHOLD = 5
    # Maximum candidates to track (prevents memory bloat)
    MAX_CANDIDATES = 500

    def __init__(self, auto_learn: bool = True):
        """
        Initialize detector with optional premium features.

        Args:
            auto_learn: If True, automatically learn new terms from conversations
        """
        self.auto_learn = auto_learn

        # Premium: Advanced detection + adaptive dictionary
        self._premium_detector = None
        self._adaptive_dict = None
        self._detect_anchor_drift = None
        self._suppress_anchor_aligned = None
        try:
            from .premium import PREMIUM_AVAILABLE
            if PREMIUM_AVAILABLE:
                from .premium.adaptive_dict import AdaptiveDictionary
                from .premium.advanced_detector import PremiumDetector
                self._adaptive_dict = AdaptiveDictionary(
                    auto_learn=auto_learn,
                    seed_terms=self._get_seed_terms()
                )
                self._premium_detector = PremiumDetector(self._adaptive_dict)
                logger.info("Premium detection enabled")

            # Anchor forensics (optional premium module)
            from .premium import ANCHOR_AVAILABLE
            if ANCHOR_AVAILABLE:
                from .premium.anchor_forensics import (
                    detect_anchor_drift as _drift_fn,
                    suppress_anchor_aligned as _suppress_fn,
                )
                self._detect_anchor_drift = _drift_fn
                self._suppress_anchor_aligned = _suppress_fn
                logger.info("Premium anchor forensics enabled")
        except ImportError:
            logger.debug("Premium package not available, using open-source detection only")

        # Jargon dict: delegate to premium or use basic seed-only dict
        if self._adaptive_dict is not None:
            self.jargon_dict = self._adaptive_dict.jargon_dict
        else:
            self.jargon_dict = {
                "known": self._get_seed_terms(),
                "candidate": defaultdict(int),
                "learned": set(),
                "expanded": {}
            }

        # LLM fingerprint patterns - typical response characteristics
        self.llm_patterns = {
            # OpenAI models
            'gpt-4': {'avg_words': 40, 'jargon_heavy': False},
            'gpt-4o': {'avg_words': 35, 'jargon_heavy': False},
            'gpt-4o-mini': {'avg_words': 30, 'jargon_heavy': False},
            'gpt-3.5-turbo': {'avg_words': 25, 'jargon_heavy': False},
            # Anthropic models
            'claude-3': {'avg_words': 50, 'jargon_heavy': False},
            'claude-3.5': {'avg_words': 45, 'jargon_heavy': False},
            'claude-3-opus': {'avg_words': 60, 'jargon_heavy': False},
            'claude-3-sonnet': {'avg_words': 45, 'jargon_heavy': False},
            'claude-3-haiku': {'avg_words': 30, 'jargon_heavy': False},
            # Google models
            'gemini-2.0': {'avg_words': 40, 'jargon_heavy': True},
            'gemini-1.5-pro': {'avg_words': 45, 'jargon_heavy': True},
            'gemini-1.5-flash': {'avg_words': 30, 'jargon_heavy': True},
            # xAI
            'grok-2': {'avg_words': 35, 'jargon_heavy': False},
            # Open source
            'llama-3.1': {'avg_words': 35, 'jargon_heavy': True},
            'llama-3.2': {'avg_words': 30, 'jargon_heavy': True},
            'mistral': {'avg_words': 30, 'jargon_heavy': True},
            'phi3': {'avg_words': 25, 'jargon_heavy': False},
        }

    def _get_seed_terms(self) -> Set[str]:
        """Return the seed set of common acronyms to avoid false positives."""
        return {
            # AI/ML
            'AI', 'ML', 'NLP', 'LLM', 'GPT', 'CNN', 'RNN', 'GAN', 'RAG', 'AGI',
            'BERT', 'LSTM', 'DNN', 'SVM', 'KNN', 'PCA', 'RLHF', 'DPO', 'PPO',
            # Web/API
            'API', 'URL', 'HTTP', 'HTTPS', 'REST', 'JSON', 'XML', 'HTML', 'CSS',
            'JS', 'TS', 'SQL', 'DOM', 'CDN', 'SDK', 'CLI', 'GUI', 'URI', 'JWT',
            'GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS', 'CORS',
            # Infrastructure
            'AWS', 'GCP', 'CPU', 'GPU', 'RAM', 'SSD', 'VM', 'DNS', 'IP', 'SSL',
            'TLS', 'SSH', 'FTP', 'TCP', 'UDP', 'VPN', 'LAN', 'WAN', 'NAS', 'SAN',
            'K8S', 'EC2', 'S3', 'RDS', 'ECS', 'EKS', 'IAM', 'VPC', 'ALB', 'ELB',
            # Business/Common
            'ID', 'OK', 'ETA', 'FYI', 'TBD', 'FAQ', 'KPI', 'ROI', 'SLA', 'EOD',
            'ASAP', 'CEO', 'CTO', 'CFO', 'COO', 'HR', 'PR', 'QA', 'PM', 'UI', 'UX',
            'MVP', 'POC', 'RFP', 'RFQ', 'NDA', 'SOW', 'MOU', 'LOI',
            # E-commerce/Customer Service
            'SKU', 'RMA', 'PO', 'ERP', 'CRM', 'B2B', 'B2C', 'D2C', 'POS', 'WMS',
            # Marketing/Advertising
            'SEO', 'SEM', 'PPC', 'CTR', 'CVR', 'CPA', 'CPM', 'CPC', 'ROAS',
            'CAC', 'CLV', 'LTV', 'AOV', 'GMV', 'CRO', 'ABM', 'UGC', 'SMM',
            # Programming
            'OOP', 'CRUD', 'IDE', 'GIT', 'CI', 'CD', 'TDD', 'BDD', 'DRY', 'SOLID',
            'MVC', 'MVP', 'MVVM', 'ORM', 'DSL', 'AST', 'JIT', 'AOT', 'GC',
            # Data/Files
            'CSV', 'PDF', 'PNG', 'JPG', 'GIF', 'MP4', 'ZIP', 'TAR', 'YAML', 'TOML',
            # Metrics
            'NPS', 'CSAT', 'MRR', 'ARR', 'DAU', 'MAU', 'WAU', 'ARPU', 'ARPPU',
            # Finance
            'USD', 'EUR', 'GBP', 'JPY', 'BTC', 'ETH', 'IPO', 'ICO', 'VC', 'PE',
            'EBITDA', 'P&L', 'CFO', 'GAAP', 'IFRS', 'AML', 'KYC',
            # Healthcare
            'HIPAA', 'PHI', 'EHR', 'EMR', 'FDA', 'CDC', 'WHO', 'ICU', 'ER',
            # Legal
            'GDPR', 'CCPA', 'SOC', 'PCI', 'DSS', 'ISO', 'NIST', 'FERPA',
        }

    # ============================================
    # Detection
    # ============================================

    def detect(
        self,
        current_msg: Dict,
        history: Dict[str, Dict[str, List[Dict]]],
        sender_id: str,
        llm_id: str,
        receiver_id: Optional[str] = None,
        anchor: Optional[Dict] = None
    ) -> List[Anomaly]:
        anomalies = []
        agent_hist = history.get(sender_id, {})
        llm_hist = agent_hist.get(llm_id, [])

        # V2: Calculate anchor similarity (for drift detection and suppression)
        anchor_similarity = None
        if anchor and anchor.get("embedding") is not None:
            anchor_emb = np.array(anchor["embedding"])
            msg_emb = np.array(current_msg["embedding"])
            anchor_similarity = self._cosine(anchor_emb, msg_emb)

        # Open-source: fingerprint mismatch (always runs)
        mismatch = self._fingerprint_mismatch(current_msg, llm_id)
        if mismatch:
            anomalies.append(mismatch)

        # ANCHOR_DRIFT: response drifts from original query (premium)
        if anchor_similarity is not None and self._detect_anchor_drift is not None:
            drift_anomaly = self._detect_anchor_drift(
                current_msg=current_msg,
                llm_id=llm_id,
                sender_id=sender_id,
                anchor_similarity=anchor_similarity,
                anchor=anchor,
            )
            if drift_anomaly is not None:
                anomalies.append(drift_anomaly)

        # Calculate previous message similarity (if history available)
        prev_msg = None
        similarity = None
        if len(llm_hist) >= 2:
            prev_msg = llm_hist[-2]
            current_emb = np.array(current_msg["embedding"])
            prev_emb = np.array(prev_msg["embedding"])
            similarity = self._cosine(current_emb, prev_emb)

        # Premium detection: jargon, shorthand, context_loss, cross-LLM
        if self._premium_detector is not None:
            premium_anomalies = self._premium_detector.detect_premium(
                current_msg=current_msg,
                history=history,
                sender_id=sender_id,
                llm_id=llm_id,
                prev_msg=prev_msg,
                similarity=similarity,
                receiver_id=receiver_id,
                anchor=anchor,
                anchor_similarity=anchor_similarity,
            )
            anomalies.extend(premium_anomalies)

        # Open-source: LLM hedging/confidence detection
        if LLM_AVAILABLE:
            hedging = self._detect_hedging_llm(current_msg["text"])
            if hedging:
                if prev_msg is None:
                    # Early messages: only flag low confidence
                    if hedging.get("confidence") == "Low":
                        anomalies.append(Anomaly(
                            type="LOW_CONFIDENCE",
                            severity="high",
                            llm_id=llm_id,
                            agent_id=sender_id,
                            details=hedging,
                            timestamp=time.time(),
                            message_id=current_msg.get("message_id", ""),
                            anchor_similarity=anchor_similarity
                        ))
                else:
                    # With history: flag medium and low
                    if hedging.get("confidence") in ("Low", "Medium"):
                        severity = "high" if hedging["confidence"] == "Low" else "medium"
                        anomalies.append(Anomaly(
                            type="LOW_CONFIDENCE",
                            severity=severity,
                            llm_id=llm_id,
                            agent_id=sender_id,
                            details=hedging,
                            timestamp=time.time(),
                            message_id=current_msg.get("message_id", ""),
                            anchor_similarity=anchor_similarity
                        ))

        # Anchor-based false positive suppression (premium)
        if self._suppress_anchor_aligned is not None:
            anomalies = self._suppress_anchor_aligned(anomalies, anchor, anchor_similarity)

        return anomalies

    # ============================================
    # Open-source detection methods
    # ============================================

    def _cosine(self, a: np.ndarray, b: np.ndarray) -> float:
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-8))

    def _fingerprint_mismatch(self, msg: Dict, llm_id: str) -> Optional[Anomaly]:
        """Detect when message length significantly deviates from LLM's typical output."""
        pattern = self.llm_patterns.get(llm_id)
        if not pattern:
            return None

        expected = pattern["avg_words"]
        actual = msg["word_count"]
        deviation = abs(actual - expected)

        # Dynamic threshold: 50% of expected or minimum 20 words deviation
        threshold = max(expected * 0.5, 20)

        if deviation > threshold:
            return Anomaly(
                type="LLM_FINGERPRINT_MISMATCH",
                severity="medium" if deviation < threshold * 2 else "high",
                llm_id=llm_id,
                agent_id=msg["sender"],
                details={
                    "expected": expected,
                    "actual": actual,
                    "deviation": round(deviation, 1),
                    "threshold": round(threshold, 1)
                },
                timestamp=time.time()
            )
        return None

    def _detect_hedging_llm(self, text: str) -> Optional[Dict]:
        if not LLM_AVAILABLE:
            return None
        messages = [
            {"role": "system", "content": "You are an expert at detecting hedging/low confidence in AI responses."},
            {"role": "user", "content": f'''Analyze this response for confidence.

Response: "{text}"

Output ONLY valid JSON:
{{
  "confidence": "High" | "Medium" | "Low",
  "hedge_words": ["word1", "word2"] or [],
  "explanation": "brief reason"
}}'''}
        ]
        response = ollama_chat(messages, temperature=0.1)
        if response:
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                return {"raw_response": response}
        return None

    # ============================================
    # Backward-compatible wrapper methods
    # ============================================
    # These delegate to premium AdaptiveDictionary when available,
    # or return graceful error dicts when premium is not installed.

    def add_learned_term(self, term: str, expanded: Optional[str] = None) -> None:
        """Manually add a term to the learned dictionary."""
        if self._adaptive_dict is not None:
            self._adaptive_dict.add_learned_term(term, expanded)
        else:
            upper = term.upper()
            self.jargon_dict["learned"].add(upper)
            if expanded:
                self.jargon_dict["expanded"][upper] = expanded

    def get_jargon_stats(self) -> Dict:
        """Return statistics about the jargon dictionary."""
        if self._adaptive_dict is not None:
            return self._adaptive_dict.get_jargon_stats()
        return {
            "known_terms": len(self.jargon_dict["known"]),
            "learned_terms": 0,
            "candidate_terms": 0,
            "expanded_terms": 0,
            "premium_required": True,
        }

    def load_domain(self, domain: str) -> Dict:
        """Load a domain-specific dictionary to reduce false positives."""
        if self._adaptive_dict is not None:
            return self._adaptive_dict.load_domain(domain)
        return {"error": "Domain dictionaries require InsAIts Premium", "premium_required": True}

    def get_available_domains(self) -> List[str]:
        """Return list of available domain dictionaries."""
        if self._adaptive_dict is not None:
            return self._adaptive_dict.get_available_domains()
        return []

    def export_dictionary(self, filepath: str) -> Dict:
        """Export the current dictionary to a JSON file."""
        if self._adaptive_dict is not None:
            return self._adaptive_dict.export_dictionary(filepath)
        return {"error": "Dictionary export requires InsAIts Premium", "premium_required": True}

    def import_dictionary(self, filepath: str, merge: bool = True) -> Dict:
        """Import a dictionary from a JSON file."""
        if self._adaptive_dict is not None:
            return self._adaptive_dict.import_dictionary(filepath, merge)
        return {"error": "Dictionary import requires InsAIts Premium", "premium_required": True}

    def auto_expand_terms(
        self,
        terms: Optional[List[str]] = None,
        model: str = "phi3"
    ) -> Dict:
        """Use LLM to automatically expand undefined terms."""
        if self._adaptive_dict is not None:
            return self._adaptive_dict.auto_expand_terms(terms, model)
        return {"error": "Auto-expand requires InsAIts Premium", "premium_required": True}

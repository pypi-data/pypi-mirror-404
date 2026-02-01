"""
InsAIts SDK - Hallucination Detection (Phase 3)
================================================
Detect factual contradictions, ungrounded claims, phantom citations,
confidence decay, and self-inconsistency in AI-to-AI communications.

Features:
- FactTracker: Extract and track factual claims, detect contradictions
  across agents (cross-agent fact consistency)
- SourceGrounder: Verify responses against source documents
- SelfConsistencyChecker: Use LLM to check internal consistency
- PhantomCitationDetector: Detect fabricated URLs, DOIs, paper references
- ConfidenceDecayTracker: Track certainty erosion across conversation turns
- NumericalConsistencyTracker: Track numeric claims per topic across agents

Unique to InsAIts: Cross-agent hallucination detection leverages the
multi-agent monitoring pipeline to catch contradictions BETWEEN agents
that single-agent tools cannot detect.

Privacy-first: All processing is local. No content sent to cloud.
"""

import re
import time
import logging
import json
import numpy as np
from typing import List, Dict, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from collections import defaultdict

from .embeddings import get_local_embedding
from .exceptions import insAItsError

try:
    from .local_llm import ollama_chat
    LLM_AVAILABLE = True
except Exception:
    LLM_AVAILABLE = False

logger = logging.getLogger(__name__)


# ============================================
# DATA CLASSES
# ============================================

@dataclass
class FactClaim:
    """A factual claim extracted from text."""
    claim: str
    topic: str
    value: str
    agent_id: str
    message_id: str
    timestamp: float
    confidence: float = 0.5
    claim_type: str = "general"  # general, numeric, date, entity, comparison, citation


# ============================================
# PHANTOM CITATION DETECTOR
# ============================================

class PhantomCitationDetector:
    """
    Detect fabricated citations, URLs, DOIs, and paper references.

    AI models frequently hallucinate academic references, generating
    plausible-looking but non-existent paper titles, authors, DOIs, and
    URLs. This detector identifies patterns that suggest fabrication.

    Detection heuristics:
    - URLs with suspicious domain patterns (random chars, nonstandard TLDs)
    - DOIs that don't follow standard format
    - Paper references with implausible author/date combinations
    - Overly specific citations that lack verifiable details
    """

    # Patterns for citation detection
    URL_PATTERN = re.compile(
        r'https?://[^\s<>"\')\]]+',
        re.IGNORECASE
    )

    DOI_PATTERN = re.compile(
        r'(?:doi[:\s]*)?10\.\d{4,}/[^\s]+',
        re.IGNORECASE
    )

    PAPER_REF_PATTERN = re.compile(
        r'(?:'
        # "Author et al. (YYYY)" or "Author & Author (YYYY)"
        r'[A-Z][a-z]+(?:\s+(?:et\s+al\.?|&\s+[A-Z][a-z]+))?'
        r'\s*\(\d{4}\)'
        r'|'
        # "Title" (Journal, YYYY) or [N] Author, "Title", Journal
        r'"[^"]{10,200}"\s*(?:\([^)]+\d{4}\)|,\s*\d{4})'
        r')',
        re.MULTILINE
    )

    ARXIV_PATTERN = re.compile(
        r'arxiv[:\s]*\d{4}\.\d{4,5}',
        re.IGNORECASE
    )

    ISBN_PATTERN = re.compile(
        r'ISBN[:\s]*[\d-]{10,17}',
        re.IGNORECASE
    )

    # Known suspicious URL patterns (randomly generated-looking strings)
    SUSPICIOUS_PATH_PATTERN = re.compile(
        r'/[a-z0-9]{20,}|'  # Very long random paths
        r'/[A-Z]{10,}|'     # All-caps long paths
        r'example\.com|'    # Placeholder domains
        r'placeholder\.|'
        r'fake\.|'
        r'test\.test',
        re.IGNORECASE
    )

    def detect(self, text: str) -> List[Dict]:
        """
        Detect potentially fabricated citations in text.

        Args:
            text: Text to analyze for phantom citations

        Returns:
            List of suspicious citation dicts with type and confidence
        """
        if not text or len(text.strip()) < 20:
            return []

        suspicious = []

        suspicious.extend(self._check_urls(text))
        suspicious.extend(self._check_dois(text))
        suspicious.extend(self._check_paper_refs(text))
        suspicious.extend(self._check_arxiv_refs(text))

        return suspicious

    def _check_urls(self, text: str) -> List[Dict]:
        results = []
        for match in self.URL_PATTERN.finditer(text):
            url = match.group(0).rstrip('.,;:)')
            suspicion_score = 0.0
            reasons = []

            # Check for suspicious path patterns
            if self.SUSPICIOUS_PATH_PATTERN.search(url):
                suspicion_score += 0.4
                reasons.append("suspicious_path_pattern")

            # Check for very long URLs (often hallucinated)
            if len(url) > 150:
                suspicion_score += 0.3
                reasons.append("extremely_long_url")

            # Check for unusual TLDs
            unusual_tlds = [
                '.xyz', '.info', '.biz', '.tk', '.ml', '.ga', '.cf'
            ]
            if any(url.lower().endswith(tld) for tld in unusual_tlds):
                suspicion_score += 0.2
                reasons.append("unusual_tld")

            # Check for numeric-heavy domains (e.g., site123456.com)
            domain_part = url.split('/')[2] if '/' in url else url
            digit_ratio = sum(c.isdigit() for c in domain_part) / max(
                len(domain_part), 1
            )
            if digit_ratio > 0.4:
                suspicion_score += 0.3
                reasons.append("numeric_heavy_domain")

            if suspicion_score >= 0.3:
                results.append({
                    "type": "suspicious_url",
                    "citation": url[:200],
                    "suspicion_score": round(min(suspicion_score, 1.0), 2),
                    "reasons": reasons
                })

        return results

    def _check_dois(self, text: str) -> List[Dict]:
        results = []
        for match in self.DOI_PATTERN.finditer(text):
            doi = match.group(0)
            suspicion_score = 0.0
            reasons = []

            # DOIs with unusual registrant codes
            # Standard DOIs: 10.XXXX/... where XXXX is 4-5 digits
            doi_num = doi.split('10.')[1] if '10.' in doi else ""
            registrant = doi_num.split('/')[0] if '/' in doi_num else ""

            if registrant and not registrant.isdigit():
                suspicion_score += 0.3
                reasons.append("non_numeric_registrant")

            # Very short suffix (likely fabricated)
            suffix = doi_num.split('/', 1)[1] if '/' in doi_num else ""
            if suffix and len(suffix) < 3:
                suspicion_score += 0.4
                reasons.append("suspiciously_short_suffix")

            # Overly long suffix with random chars
            if suffix and len(suffix) > 50:
                suspicion_score += 0.3
                reasons.append("suspiciously_long_suffix")

            if suspicion_score >= 0.3:
                results.append({
                    "type": "suspicious_doi",
                    "citation": doi[:100],
                    "suspicion_score": round(min(suspicion_score, 1.0), 2),
                    "reasons": reasons
                })

        return results

    def _check_paper_refs(self, text: str) -> List[Dict]:
        results = []
        for match in self.PAPER_REF_PATTERN.finditer(text):
            ref = match.group(0)
            suspicion_score = 0.0
            reasons = []

            # Check for future dates
            year_matches = re.findall(r'\b(20\d{2}|19\d{2})\b', ref)
            for year_str in year_matches:
                year = int(year_str)
                if year > 2025:
                    suspicion_score += 0.6
                    reasons.append("future_publication_date")
                elif year > 2024:
                    suspicion_score += 0.2
                    reasons.append("very_recent_date")

            # Overly generic titles in quotes
            quoted = re.findall(r'"([^"]+)"', ref)
            for title in quoted:
                generic_words = [
                    'comprehensive', 'review', 'survey', 'analysis',
                    'study', 'investigation', 'approach', 'method',
                    'framework', 'novel', 'advanced', 'modern'
                ]
                generic_count = sum(
                    1 for w in generic_words if w in title.lower()
                )
                if generic_count >= 3:
                    suspicion_score += 0.3
                    reasons.append("overly_generic_title")

            if suspicion_score >= 0.3:
                results.append({
                    "type": "suspicious_paper_reference",
                    "citation": ref[:200],
                    "suspicion_score": round(min(suspicion_score, 1.0), 2),
                    "reasons": reasons
                })

        return results[:5]

    def _check_arxiv_refs(self, text: str) -> List[Dict]:
        results = []
        for match in self.ARXIV_PATTERN.finditer(text):
            arxiv_id = match.group(0)
            suspicion_score = 0.0
            reasons = []

            # Extract year/month from arxiv ID (format: YYMM.NNNNN)
            id_part = re.findall(r'(\d{4})\.\d+', arxiv_id)
            if id_part:
                yymm = id_part[0]
                year = int("20" + yymm[:2]) if int(yymm[:2]) < 50 else int(
                    "19" + yymm[:2]
                )
                month = int(yymm[2:])

                if year > 2025:
                    suspicion_score += 0.6
                    reasons.append("future_arxiv_date")
                if month > 12 or month < 1:
                    suspicion_score += 0.8
                    reasons.append("invalid_arxiv_month")

            if suspicion_score >= 0.3:
                results.append({
                    "type": "suspicious_arxiv",
                    "citation": arxiv_id[:50],
                    "suspicion_score": round(min(suspicion_score, 1.0), 2),
                    "reasons": reasons
                })

        return results


# ============================================
# CONFIDENCE DECAY TRACKER
# ============================================

class ConfidenceDecayTracker:
    """
    Track confidence/certainty erosion across conversation turns.

    When AI agents communicate, initial confident assertions can
    degrade into hedged, uncertain language. This tracker monitors
    the confidence trajectory per topic and per agent.

    Detects:
    - Confident claim followed by hedged restatement
    - Progressive weakening of assertions
    - Flip-flopping between confident and uncertain language
    """

    CONFIDENT_MARKERS = frozenset([
        "certainly", "definitely", "absolutely", "clearly", "obviously",
        "undoubtedly", "without doubt", "confirmed", "proven", "established",
        "guaranteed", "always", "never", "must", "will"
    ])

    UNCERTAIN_MARKERS = frozenset([
        "maybe", "perhaps", "possibly", "might", "could", "potentially",
        "uncertain", "unclear", "not sure", "i think", "probably",
        "it seems", "appears to", "likely", "unlikely", "roughly",
        "approximately", "around", "estimated", "debatable", "arguably"
    ])

    def __init__(self):
        # agent_id -> [(timestamp, confidence_score, topic_hint)]
        self._history: Dict[str, List[Tuple[float, float, str]]] = (
            defaultdict(list)
        )

    def score_confidence(self, text: str) -> float:
        """
        Score the confidence level of a text (0.0 = very uncertain, 1.0 = very confident).

        Uses marker counting with position weighting (markers at start
        of sentences carry more weight).
        """
        if not text:
            return 0.5

        text_lower = text.lower()
        words = text_lower.split()

        if not words:
            return 0.5

        confident_count = 0
        uncertain_count = 0

        for marker in self.CONFIDENT_MARKERS:
            occurrences = text_lower.count(marker)
            confident_count += occurrences
            # Bonus for markers in first sentence
            first_sentence = text_lower.split('.')[0] if '.' in text_lower else text_lower
            if marker in first_sentence:
                confident_count += 0.5

        for marker in self.UNCERTAIN_MARKERS:
            occurrences = text_lower.count(marker)
            uncertain_count += occurrences
            first_sentence = text_lower.split('.')[0] if '.' in text_lower else text_lower
            if marker in first_sentence:
                uncertain_count += 0.5

        total = confident_count + uncertain_count
        if total == 0:
            return 0.5  # Neutral

        # Normalize to 0-1 scale
        score = confident_count / total
        return round(max(0.0, min(1.0, score)), 3)

    def track(
        self,
        agent_id: str,
        text: str,
        timestamp: float,
        topic_hint: str = ""
    ) -> Optional[Dict]:
        """
        Track confidence for an agent and detect decay.

        Args:
            agent_id: ID of the agent
            text: Message text
            timestamp: Message timestamp
            topic_hint: Optional topic context

        Returns:
            Dict with decay info if detected, None otherwise
        """
        score = self.score_confidence(text)
        self._history[agent_id].append((timestamp, score, topic_hint))

        # Keep last 50 entries per agent
        if len(self._history[agent_id]) > 50:
            self._history[agent_id] = self._history[agent_id][-50:]

        history = self._history[agent_id]
        if len(history) < 3:
            return None

        # Check for decay pattern in last 5 messages
        recent = history[-5:]
        scores = [s for _, s, _ in recent]

        # Detect monotonic decay (each score lower than previous)
        decay_count = sum(
            1 for i in range(1, len(scores))
            if scores[i] < scores[i - 1] - 0.05  # 5% threshold
        )

        # Detect flip-flopping (alternating high/low)
        flips = 0
        for i in range(2, len(scores)):
            if ((scores[i] > scores[i - 1] + 0.15 and
                 scores[i - 1] < scores[i - 2] - 0.15) or
                (scores[i] < scores[i - 1] - 0.15 and
                 scores[i - 1] > scores[i - 2] + 0.15)):
                flips += 1

        # Significant decay: score dropped by 0.3+ from start to end
        total_decay = scores[0] - scores[-1] if scores else 0
        avg_score = sum(scores) / len(scores)

        if decay_count >= 3 or total_decay >= 0.3:
            return {
                "type": "confidence_decay",
                "agent_id": agent_id,
                "initial_confidence": round(scores[0], 3),
                "current_confidence": round(scores[-1], 3),
                "decay_amount": round(total_decay, 3),
                "decay_steps": decay_count,
                "avg_confidence": round(avg_score, 3),
                "severity": (
                    "high" if total_decay >= 0.5 else
                    "medium" if total_decay >= 0.3 else "low"
                )
            }

        if flips >= 2:
            return {
                "type": "confidence_flip_flop",
                "agent_id": agent_id,
                "flip_count": flips,
                "recent_scores": [round(s, 3) for s in scores],
                "avg_confidence": round(avg_score, 3),
                "severity": "medium"
            }

        return None

    def get_agent_confidence(self, agent_id: str) -> Dict:
        """Get confidence history for an agent."""
        history = self._history.get(agent_id, [])
        if not history:
            return {"agent_id": agent_id, "entries": 0}

        scores = [s for _, s, _ in history]
        return {
            "agent_id": agent_id,
            "entries": len(history),
            "current_confidence": round(scores[-1], 3),
            "avg_confidence": round(sum(scores) / len(scores), 3),
            "min_confidence": round(min(scores), 3),
            "max_confidence": round(max(scores), 3),
            "trend": (
                "declining" if len(scores) >= 3 and scores[-1] < scores[0] - 0.15
                else "improving" if len(scores) >= 3 and scores[-1] > scores[0] + 0.15
                else "stable"
            )
        }

    def get_all_stats(self) -> Dict:
        """Get confidence stats for all tracked agents."""
        return {
            agent_id: self.get_agent_confidence(agent_id)
            for agent_id in self._history
        }

    def clear(self) -> None:
        """Reset all confidence tracking."""
        self._history.clear()


# ============================================
# FACT TRACKER
# ============================================

class FactTracker:
    """
    Track factual claims across a conversation and detect contradictions.

    Claims are extracted using heuristic regex patterns (always available)
    and optionally enhanced with local LLM analysis (Ollama).

    Cross-agent detection: Because InsAIts monitors ALL agents in a session,
    this tracker catches contradictions BETWEEN agents - something that
    single-agent monitoring tools fundamentally cannot do.

    Heuristic patterns detect:
    - Numeric claims ("costs 500 dollars", "has 8 items")
    - Date claims ("founded in 2023", "published on March 5, 2024")
    - Entity assertions ("Einstein discovered relativity")
    - Comparative claims ("Python is faster than Ruby")
    - Phantom citations (fabricated URLs, DOIs, papers)
    """

    MAX_CLAIMS = 1000

    NUMERIC_CLAIM_PATTERN = re.compile(
        r'(?:(?:is|was|were|are|has|had|have|equals?|contains?|costs?|'
        r'approximately|about|around|exactly|totals?|reached|scored|'
        r'measured|weighed|counted|reported|estimated|calculated)\s+)'
        r'(\d[\d,]*\.?\d*)\s*'
        r'(%|percent|dollars?|euros?|pounds?|years?|months?|days?|hours?|'
        r'minutes?|seconds?|items?|users?|people|employees?|customers?|'
        r'records?|files?|bytes?|points?|tokens?|parameters?|'
        r'GB|MB|KB|TB|ms|kg|lbs?|meters?|miles?|km|cm|mm|'
        r'million|billion|trillion|thousand)?',
        re.IGNORECASE
    )

    DATE_CLAIM_PATTERN = re.compile(
        r'(?:in|on|since|from|until|by|before|after|during|founded|'
        r'created|published|released|launched|established|started|'
        r'began|ended|completed|announced|introduced|deployed)\s+'
        r'(\d{4}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|'
        r'(?:January|February|March|April|May|June|July|August|'
        r'September|October|November|December)'
        r'\s+\d{1,2},?\s*\d{4})',
        re.IGNORECASE
    )

    ENTITY_CLAIM_PATTERN = re.compile(
        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+'
        r'(?:is|was|were|are|has been|had been|will be|'
        r'founded|created|published|released|discovered|'
        r'invented|developed|designed|built|wrote|'
        r'announced|acquired|launched|deployed|introduced)\s+'
        r'(.+?)(?:\.|,|;|$)',
        re.MULTILINE
    )

    COMPARISON_PATTERN = re.compile(
        r'(\w+(?:\s+\w+){0,3})\s+'
        r'(?:is|are|was|were)\s+'
        r'(?:greater|larger|smaller|less|more|fewer|better|worse|'
        r'faster|slower|higher|lower|bigger|cheaper|'
        r'more expensive|older|newer|longer|shorter|'
        r'more accurate|less accurate|more efficient|less efficient)\s+'
        r'than\s+'
        r'(\w+(?:\s+\w+){0,3})',
        re.IGNORECASE
    )

    def __init__(self):
        self.claims: Dict[str, List[FactClaim]] = {}
        self._all_claims: List[FactClaim] = []
        self.citation_detector = PhantomCitationDetector()
        # Track numeric values per topic for drift detection
        self._numeric_history: Dict[str, List[Tuple[float, str, str]]] = (
            defaultdict(list)
        )

    def extract_claims(
        self,
        text: str,
        agent_id: str,
        message_id: str,
        use_llm: bool = True
    ) -> List[FactClaim]:
        """
        Extract factual claims from text.

        Uses heuristic patterns first, then optionally LLM for deeper extraction.

        Args:
            text: The text to extract claims from
            agent_id: ID of the agent that produced the text
            message_id: ID of the message containing the text
            use_llm: Whether to use LLM for enhanced extraction

        Returns:
            List of extracted FactClaim objects
        """
        if not text or len(text.strip()) < 5:
            return []

        claims = []
        timestamp = time.time()

        try:
            claims.extend(
                self._extract_numeric_claims(
                    text, agent_id, message_id, timestamp
                )
            )
        except Exception as e:
            logger.debug(f"Numeric claim extraction error: {e}")

        try:
            claims.extend(
                self._extract_date_claims(
                    text, agent_id, message_id, timestamp
                )
            )
        except Exception as e:
            logger.debug(f"Date claim extraction error: {e}")

        try:
            claims.extend(
                self._extract_entity_claims(
                    text, agent_id, message_id, timestamp
                )
            )
        except Exception as e:
            logger.debug(f"Entity claim extraction error: {e}")

        try:
            claims.extend(
                self._extract_comparison_claims(
                    text, agent_id, message_id, timestamp
                )
            )
        except Exception as e:
            logger.debug(f"Comparison claim extraction error: {e}")

        if use_llm and LLM_AVAILABLE:
            try:
                llm_claims = self._extract_claims_llm(
                    text, agent_id, message_id, timestamp
                )
                claims.extend(llm_claims)
            except Exception as e:
                logger.debug(f"LLM claim extraction error: {e}")

        return self._deduplicate_claims(claims)

    def detect_phantom_citations(self, text: str) -> List[Dict]:
        """
        Detect potentially fabricated citations in text.

        Args:
            text: Text to analyze

        Returns:
            List of suspicious citation dicts
        """
        return self.citation_detector.detect(text)

    def track_claims(self, claims: List[FactClaim]) -> List[Dict]:
        """
        Track new claims and check for contradictions with existing ones.

        Performs:
        1. Cross-agent contradiction detection
        2. Numeric drift detection (same topic, changing numbers)
        3. Temporal consistency (claims changing over time)

        Args:
            claims: List of new claims to track

        Returns:
            List of contradiction dicts (empty if no contradictions found)
        """
        contradictions = []

        for claim in claims:
            topic_key = claim.topic[:50]

            if topic_key in self.claims:
                for existing in self.claims[topic_key]:
                    # Skip self-comparisons (same message)
                    if existing.message_id == claim.message_id:
                        continue

                    if self._values_contradict(existing.value, claim.value):
                        is_cross_agent = (
                            existing.agent_id != claim.agent_id
                        )
                        contradictions.append({
                            "type": "FACT_CONTRADICTION",
                            "topic": claim.topic,
                            "original_value": existing.value,
                            "original_agent": existing.agent_id,
                            "original_message_id": existing.message_id,
                            "original_timestamp": existing.timestamp,
                            "new_value": claim.value,
                            "new_agent": claim.agent_id,
                            "new_message_id": claim.message_id,
                            "confidence": min(
                                existing.confidence, claim.confidence
                            ),
                            "cross_agent": is_cross_agent,
                            "severity": (
                                "critical" if is_cross_agent
                                else "high"
                            )
                        })

                self.claims[topic_key].append(claim)
            else:
                self.claims[topic_key] = [claim]

            self._all_claims.append(claim)

            # Track numeric history for drift detection
            if claim.claim_type == "numeric":
                nums = re.findall(r'-?\d+\.?\d*', claim.value)
                if nums:
                    try:
                        self._numeric_history[topic_key].append(
                            (float(nums[0]), claim.agent_id, claim.message_id)
                        )
                    except (ValueError, IndexError):
                        pass

        # Enforce max claims limit (remove oldest)
        if len(self._all_claims) > self.MAX_CLAIMS:
            excess = len(self._all_claims) - self.MAX_CLAIMS
            self._all_claims = self._all_claims[excess:]

        return contradictions

    def get_numeric_drift(self, topic: str = "") -> List[Dict]:
        """
        Get numeric value drift for tracked topics.

        Detects when the same numeric fact drifts across messages
        (e.g., "costs $500" then "costs $450" then "costs $300").

        Args:
            topic: Specific topic to check, or empty for all

        Returns:
            List of drift events
        """
        drifts = []
        if topic:
            if topic in self._numeric_history:
                topics = {topic: self._numeric_history[topic]}
            else:
                return []
        else:
            topics = self._numeric_history

        for topic_key, entries in topics.items():
            if len(entries) < 2:
                continue

            values = [v for v, _, _ in entries]
            initial = values[0]
            current = values[-1]

            if initial == 0:
                continue

            pct_change = abs(current - initial) / abs(initial)
            if pct_change >= 0.1:  # 10% drift threshold
                drifts.append({
                    "topic": topic_key,
                    "initial_value": initial,
                    "current_value": current,
                    "pct_change": round(pct_change * 100, 1),
                    "entries": len(entries),
                    "agents_involved": list(set(a for _, a, _ in entries)),
                    "severity": (
                        "high" if pct_change >= 0.5
                        else "medium" if pct_change >= 0.2
                        else "low"
                    )
                })

        return drifts

    def get_claims(self) -> List[Dict]:
        """Get all tracked claims as serializable dicts."""
        return [
            {
                "claim": c.claim,
                "topic": c.topic,
                "value": c.value,
                "agent_id": c.agent_id,
                "message_id": c.message_id,
                "timestamp": c.timestamp,
                "confidence": c.confidence,
                "claim_type": c.claim_type
            }
            for c in self._all_claims
        ]

    def get_claim_count(self) -> int:
        """Get total number of tracked claims."""
        return len(self._all_claims)

    def get_topics(self) -> List[str]:
        """Get all tracked claim topics."""
        return list(self.claims.keys())

    def get_cross_agent_summary(self) -> Dict:
        """
        Get summary of claims across agents.

        Highlights topics where multiple agents have made claims,
        which is where cross-agent contradictions are most likely.
        """
        topic_agents: Dict[str, Set[str]] = defaultdict(set)
        for claim in self._all_claims:
            topic_agents[claim.topic[:50]].add(claim.agent_id)

        multi_agent_topics = {
            topic: list(agents)
            for topic, agents in topic_agents.items()
            if len(agents) > 1
        }

        return {
            "total_claims": len(self._all_claims),
            "total_topics": len(self.claims),
            "multi_agent_topics": len(multi_agent_topics),
            "multi_agent_details": multi_agent_topics,
            "agents": list(set(c.agent_id for c in self._all_claims))
        }

    def clear(self) -> None:
        """Reset the fact tracker."""
        self.claims.clear()
        self._all_claims.clear()
        self._numeric_history.clear()

    # --- Private extraction methods ---

    def _extract_numeric_claims(self, text, agent_id, message_id, timestamp):
        claims = []
        for match in self.NUMERIC_CLAIM_PATTERN.finditer(text):
            value = match.group(1)
            unit = match.group(2) or ""
            start = max(0, match.start() - 60)
            end = min(len(text), match.end() + 20)
            context = text[start:end].strip()

            claims.append(FactClaim(
                claim=context,
                topic=self._normalize_topic(context),
                value=f"{value} {unit}".strip(),
                agent_id=agent_id,
                message_id=message_id,
                timestamp=timestamp,
                confidence=0.6,
                claim_type="numeric"
            ))
        return claims[:10]

    def _extract_date_claims(self, text, agent_id, message_id, timestamp):
        claims = []
        for match in self.DATE_CLAIM_PATTERN.finditer(text):
            date_value = match.group(1)
            start = max(0, match.start() - 60)
            end = min(len(text), match.end() + 20)
            context = text[start:end].strip()

            claims.append(FactClaim(
                claim=context,
                topic=self._normalize_topic(context),
                value=date_value,
                agent_id=agent_id,
                message_id=message_id,
                timestamp=timestamp,
                confidence=0.7,
                claim_type="date"
            ))
        return claims[:10]

    def _extract_entity_claims(self, text, agent_id, message_id, timestamp):
        claims = []
        for match in self.ENTITY_CLAIM_PATTERN.finditer(text):
            entity = match.group(1)
            assertion = match.group(2).strip()
            if len(assertion) > 200:
                assertion = assertion[:200]

            full_claim = match.group(0)[:250]

            claims.append(FactClaim(
                claim=full_claim,
                topic=entity.lower(),
                value=assertion,
                agent_id=agent_id,
                message_id=message_id,
                timestamp=timestamp,
                confidence=0.5,
                claim_type="entity"
            ))
        return claims[:5]

    def _extract_comparison_claims(self, text, agent_id, message_id, timestamp):
        claims = []
        for match in self.COMPARISON_PATTERN.finditer(text):
            subject = match.group(1)
            comparand = match.group(2)
            full_match = match.group(0)

            claims.append(FactClaim(
                claim=full_match,
                topic=f"{subject.lower()} vs {comparand.lower()}",
                value=full_match,
                agent_id=agent_id,
                message_id=message_id,
                timestamp=timestamp,
                confidence=0.6,
                claim_type="comparison"
            ))
        return claims[:3]

    def _extract_claims_llm(self, text, agent_id, message_id, timestamp):
        """Use local LLM to extract factual claims."""
        if not LLM_AVAILABLE:
            return []

        messages = [{
            "role": "system",
            "content": (
                "Extract factual claims from text. "
                "Output ONLY a valid JSON array."
            )
        }, {
            "role": "user",
            "content": (
                f'Extract specific, verifiable factual claims from:\n'
                f'"{text[:1000]}"\n\n'
                f'Output JSON array (max 5 claims):\n'
                f'[{{"topic": "subject", "value": "assertion", '
                f'"confidence": 0.0-1.0}}]'
            )
        }]

        try:
            response = ollama_chat(messages, temperature=0.1)
            if response:
                parsed = json.loads(response)
                if isinstance(parsed, list):
                    return [
                        FactClaim(
                            claim=(
                                f"{c.get('topic', '')}: "
                                f"{c.get('value', '')}"
                            ),
                            topic=c.get("topic", "").lower(),
                            value=str(c.get("value", "")),
                            agent_id=agent_id,
                            message_id=message_id,
                            timestamp=timestamp,
                            confidence=float(c.get("confidence", 0.5)),
                            claim_type="llm_extracted"
                        )
                        for c in parsed[:5]
                        if c.get("topic") and c.get("value")
                    ]
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            logger.debug(f"LLM claim extraction failed: {e}")

        return []

    def _normalize_topic(self, text: str) -> str:
        """Normalize a topic string for comparison."""
        if not text:
            return ""
        text = text.lower().strip()
        text = re.sub(
            r'\b(the|a|an|is|was|were|are|has|had|have|'
            r'that|this|it|of|to|in|for|on|with)\b',
            '', text
        )
        return re.sub(r'\s+', ' ', text).strip()[:100]

    def _deduplicate_claims(self, claims: List[FactClaim]) -> List[FactClaim]:
        """Remove duplicate claims based on topic similarity."""
        if len(claims) <= 1:
            return claims

        seen_topics = set()
        unique = []
        for claim in claims:
            key = claim.topic[:50]
            if key not in seen_topics:
                seen_topics.add(key)
                unique.append(claim)
        return unique

    def _values_contradict(self, value_a: str, value_b: str) -> bool:
        """
        Check if two values contradict each other.

        Handles:
        - Numeric contradictions (different numbers for same topic)
        - Boolean/negation contradictions (true vs false, yes vs no)
        - Date contradictions (different dates for same event)
        - Semantic opposites (failed vs succeeded, approved vs denied)
        """
        if not value_a or not value_b:
            return False

        a = value_a.strip().lower()
        b = value_b.strip().lower()

        if a == b:
            return False

        # --- Numeric contradiction ---
        nums_a = re.findall(r'-?\d[\d,]*\.?\d*', a)
        nums_b = re.findall(r'-?\d[\d,]*\.?\d*', b)

        if nums_a and nums_b:
            try:
                num_a = float(nums_a[0].replace(',', ''))
                num_b = float(nums_b[0].replace(',', ''))
                if num_a != num_b:
                    return True
            except ValueError:
                pass

        # --- Date contradiction ---
        years_a = re.findall(r'\b(19|20)\d{2}\b', a)
        years_b = re.findall(r'\b(19|20)\d{2}\b', b)
        if years_a and years_b and years_a[0] != years_b[0]:
            return True

        # --- Boolean/negation contradiction ---
        negation_pairs = [
            ("not ", ""), ("never ", "always "),
            ("false", "true"), ("no ", "yes "),
            ("incorrect", "correct"), ("wrong", "right"),
            ("failed", "succeeded"), ("denied", "approved"),
            ("rejected", "accepted"), ("disabled", "enabled"),
            ("decreased", "increased"), ("declined", "grew"),
            ("impossible", "possible"), ("invalid", "valid"),
        ]
        for neg_a, neg_b in negation_pairs:
            # Exact pair match: "failed" vs "succeeded"
            if neg_a and neg_b:
                a_stripped = a.strip()
                b_stripped = b.strip()
                if ((a_stripped == neg_a.strip() and
                        b_stripped == neg_b.strip()) or
                        (a_stripped == neg_b.strip() and
                         b_stripped == neg_a.strip())):
                    return True

            # Substring removal match: "not working" vs "working"
            if (neg_a in a and
                    a.replace(neg_a, "").strip() == b.strip()):
                return True
            if (neg_a in b and
                    b.replace(neg_a, "").strip() == a.strip()):
                return True

            # Cross-pair match: "task failed completely" vs
            # "task succeeded completely"
            if neg_a and neg_b:
                if ((neg_a in a and neg_b in b) or
                        (neg_b in a and neg_a in b)):
                    stripped_a = a.replace(neg_a, "").replace(
                        neg_b, ""
                    ).strip()
                    stripped_b = b.replace(neg_a, "").replace(
                        neg_b, ""
                    ).strip()
                    if stripped_a and stripped_b and (
                        stripped_a in stripped_b or
                        stripped_b in stripped_a
                    ):
                        return True

        return False


# ============================================
# SOURCE GROUNDER
# ============================================

class SourceGrounder:
    """
    Verify AI responses are grounded in provided source documents.

    Chunks source documents, embeds them, and compares response
    embeddings against source chunks to calculate grounding scores.

    Supports:
    - Sentence-level grounding (split response into sentences, check each)
    - Multi-document scoring (best match across all documents)
    - Chunk overlap for context preservation at boundaries

    All processing is local (privacy-first).
    """

    MAX_CHUNKS = 500

    def __init__(self):
        self.source_chunks: List[str] = []
        self.source_embeddings: List[np.ndarray] = []
        self._documents_loaded: int = 0

    def set_documents(
        self,
        documents: List[str],
        chunk_size: int = 500,
        chunk_overlap: int = 50
    ) -> Dict:
        """
        Set source documents for grounding verification.

        Args:
            documents: List of source document texts
            chunk_size: Characters per chunk
            chunk_overlap: Overlap between consecutive chunks

        Returns:
            Dict with document and chunk statistics
        """
        if not documents:
            return {
                "error": "No documents provided",
                "documents_loaded": 0,
                "total_chunks": 0
            }

        self.source_chunks = []
        self.source_embeddings = []

        total_chunks = 0
        skipped_empty = 0
        for doc in documents:
            if not doc or not doc.strip():
                skipped_empty += 1
                continue
            chunks = self._chunk_text(doc, chunk_size, chunk_overlap)
            for chunk in chunks:
                if total_chunks >= self.MAX_CHUNKS:
                    break
                self.source_chunks.append(chunk)
                self.source_embeddings.append(get_local_embedding(chunk))
                total_chunks += 1

            if total_chunks >= self.MAX_CHUNKS:
                logger.warning(
                    f"Source chunks capped at {self.MAX_CHUNKS}"
                )
                break

        self._documents_loaded = len(documents) - skipped_empty

        logger.info(
            f"Source grounding: {self._documents_loaded} docs, "
            f"{total_chunks} chunks"
        )

        result = {
            "documents_loaded": self._documents_loaded,
            "total_chunks": total_chunks,
            "chunk_size": chunk_size,
            "max_chunks": self.MAX_CHUNKS
        }

        if skipped_empty > 0:
            result["skipped_empty"] = skipped_empty

        return result

    def check_grounding(
        self,
        text: str,
        threshold: float = 0.7
    ) -> Dict:
        """
        Check if a response is grounded in source documents.

        Args:
            text: Response text to check
            threshold: Minimum similarity score for grounding (0-1)

        Returns:
            Dict with grounding assessment including score, nearest chunks,
            and whether the response passes the threshold
        """
        if not self.source_embeddings:
            return {
                "grounded": None,
                "reason": "No source documents loaded",
                "grounding_score": 0.0,
                "threshold": threshold
            }

        if not text or not text.strip():
            return {
                "grounded": None,
                "reason": "Empty text provided",
                "grounding_score": 0.0,
                "threshold": threshold
            }

        response_emb = get_local_embedding(text)

        similarities = []
        for i, source_emb in enumerate(self.source_embeddings):
            sim = float(
                np.dot(response_emb, source_emb) /
                (np.linalg.norm(response_emb) *
                 np.linalg.norm(source_emb) + 1e-8)
            )
            similarities.append((sim, i))

        similarities.sort(reverse=True, key=lambda x: x[0])
        top_sim = similarities[0][0] if similarities else 0.0

        # Average of top 3 for more robust scoring
        top_k = min(3, len(similarities))
        top_3_avg = (
            sum(s for s, _ in similarities[:top_k]) / top_k
        ) if similarities else 0.0

        # Sentence-level grounding check
        sentences = self._split_sentences(text)
        sentence_scores = []
        if len(sentences) > 1:
            for sentence in sentences[:10]:  # Max 10 sentences
                if len(sentence.strip()) < 10:
                    continue
                sent_emb = get_local_embedding(sentence)
                best_sim = max(
                    float(
                        np.dot(sent_emb, se) /
                        (np.linalg.norm(sent_emb) *
                         np.linalg.norm(se) + 1e-8)
                    )
                    for se in self.source_embeddings
                )
                sentence_scores.append({
                    "sentence": sentence[:100],
                    "grounding_score": round(best_sim, 4),
                    "grounded": best_sim >= threshold
                })

        ungrounded_sentences = [
            s for s in sentence_scores if not s["grounded"]
        ]

        return {
            "grounded": top_sim >= threshold,
            "grounding_score": round(top_sim, 4),
            "avg_top3_score": round(top_3_avg, 4),
            "threshold": threshold,
            "nearest_chunks": [
                {
                    "similarity": round(s, 4),
                    "chunk_preview": self.source_chunks[i][:200]
                }
                for s, i in similarities[:3]
            ],
            "sentence_analysis": {
                "total_sentences": len(sentence_scores),
                "grounded_sentences": len(sentence_scores) - len(
                    ungrounded_sentences
                ),
                "ungrounded_sentences": len(ungrounded_sentences),
                "weakest_sentences": sorted(
                    sentence_scores,
                    key=lambda x: x["grounding_score"]
                )[:3] if sentence_scores else []
            },
            "documents_loaded": self._documents_loaded,
            "total_chunks": len(self.source_chunks)
        }

    def check_grounding_batch(
        self,
        texts: List[str],
        threshold: float = 0.7
    ) -> List[Dict]:
        """
        Check grounding for multiple texts.

        Args:
            texts: List of texts to check
            threshold: Minimum similarity for grounding

        Returns:
            List of grounding results
        """
        return [
            self.check_grounding(text, threshold)
            for text in texts[:50]  # Max 50 texts
        ]

    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        if not text:
            return []
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]

    def _chunk_text(
        self,
        text: str,
        chunk_size: int,
        chunk_overlap: int
    ) -> List[str]:
        """Split text into overlapping chunks."""
        if not text or not text.strip():
            return []

        if len(text) <= chunk_size:
            return [text.strip()]

        chunks = []
        start = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            if end >= len(text):
                break
            start = end - chunk_overlap

        return chunks

    def get_stats(self) -> Dict:
        """Get source grounding statistics."""
        return {
            "documents_loaded": self._documents_loaded,
            "total_chunks": len(self.source_chunks),
            "has_sources": len(self.source_chunks) > 0
        }

    def clear(self) -> None:
        """Clear all source documents and embeddings."""
        self.source_chunks.clear()
        self.source_embeddings.clear()
        self._documents_loaded = 0


# ============================================
# SELF-CONSISTENCY CHECKER
# ============================================

class SelfConsistencyChecker:
    """
    Use local LLM to verify a response is internally consistent.

    Checks for:
    - Internal contradictions (says X then says not-X)
    - Made-up statistics or citations
    - Overconfident claims about uncertain things
    - Logical inconsistencies in reasoning chains
    - References to non-existent sources

    Requires Ollama running locally.
    """

    def check(
        self,
        text: str,
        model: str = "phi3"
    ) -> Dict:
        """
        Check response for self-consistency using local LLM.

        Args:
            text: Response text to verify
            model: Ollama model to use

        Returns:
            Dict with consistency assessment
        """
        if not LLM_AVAILABLE:
            return {
                "is_consistent": None,
                "error": (
                    "LLM not available. Self-consistency checks require "
                    "Ollama (ollama serve, then ollama pull phi3)"
                )
            }

        if not text or len(text.strip()) < 10:
            return {
                "is_consistent": True,
                "issues": [],
                "confidence": "low",
                "suspicious_claims": [],
                "reason": "Text too short for meaningful analysis"
            }

        messages = [{
            "role": "system",
            "content": (
                "You are an expert fact-checker and logical analyzer. "
                "Analyze responses for internal consistency and accuracy."
            )
        }, {
            "role": "user",
            "content": (
                f'Analyze this AI response for consistency and accuracy:\n\n'
                f'"{text[:2000]}"\n\n'
                f'Check for:\n'
                f'1. Internal contradictions (says X then not-X)\n'
                f'2. Fabricated statistics, citations, or references\n'
                f'3. Overconfident claims about uncertain topics\n'
                f'4. Logical inconsistencies in reasoning\n'
                f'5. Claims that contradict well-known facts\n\n'
                f'Output ONLY valid JSON:\n'
                f'{{\n'
                f'  "is_consistent": true|false,\n'
                f'  "issues": ["issue 1", "issue 2"] or [],\n'
                f'  "confidence": "high"|"medium"|"low",\n'
                f'  "suspicious_claims": ["claim 1"] or []\n'
                f'}}'
            )
        }]

        try:
            response = ollama_chat(messages, model=model, temperature=0.1)
            if response:
                result = json.loads(response)
                result["model"] = f"ollama/{model}"
                return result
        except json.JSONDecodeError:
            return {
                "is_consistent": None,
                "error": "LLM returned invalid JSON",
                "raw_response": (response[:500] if response else None)
            }
        except Exception as e:
            logger.error(
                f"Self-consistency check failed: {e}", exc_info=True
            )
            return {
                "is_consistent": None,
                "error": str(e)
            }

        return {
            "is_consistent": None,
            "error": "No response from LLM"
        }

    def check_against_claims(
        self,
        text: str,
        known_claims: List[Dict],
        model: str = "phi3"
    ) -> Dict:
        """
        Check response against known factual claims using LLM.

        Args:
            text: Response text to verify
            known_claims: List of known claim dicts to check against
            model: Ollama model to use

        Returns:
            Dict with verification result
        """
        if not LLM_AVAILABLE:
            return {
                "verified": None,
                "error": "LLM not available for claim verification"
            }

        if not known_claims:
            return {
                "verified": None,
                "reason": "No known claims to verify against"
            }

        if not text or not text.strip():
            return {
                "verified": None,
                "reason": "Empty text provided"
            }

        claims_text = "\n".join(
            f"- {c.get('topic', 'unknown')}: {c.get('value', 'unknown')}"
            for c in known_claims[:20]
        )

        messages = [{
            "role": "system",
            "content": (
                "You verify if new text contradicts known facts. "
                "Output ONLY valid JSON."
            )
        }, {
            "role": "user",
            "content": (
                f'Known facts:\n{claims_text}\n\n'
                f'New text:\n"{text[:1000]}"\n\n'
                f'Does the new text contradict any known facts?\n'
                f'Output JSON:\n'
                f'{{"contradicts": true|false, '
                f'"contradictions": ["fact: X but text says Y"] or []}}'
            )
        }]

        try:
            response = ollama_chat(messages, model=model, temperature=0.1)
            if response:
                result = json.loads(response)
                result["model"] = f"ollama/{model}"
                result["claims_checked"] = len(known_claims)
                return result
        except (json.JSONDecodeError, Exception) as e:
            logger.debug(f"Claim verification failed: {e}")

        return {
            "verified": None,
            "error": "Claim verification failed"
        }

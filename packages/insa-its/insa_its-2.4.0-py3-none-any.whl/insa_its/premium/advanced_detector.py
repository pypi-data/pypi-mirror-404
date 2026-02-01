# Copyright (c) 2024-2026 YuyAI / InsAIts Team. All rights reserved.
# Proprietary and confidential. See LICENSE.premium for terms.
"""
InsAIts Premium - Advanced Anomaly Detection
=============================================
Shorthand emergence, context loss, cross-LLM shorthand/jargon detection,
and LLM-based shorthand confirmation.
"""

import re
import json
import time
import logging
import numpy as np
from typing import Any, Dict, List, Optional

from ..detector import Anomaly

logger = logging.getLogger(__name__)

# Try to import LLM for confirmation
try:
    from ..local_llm import ollama_chat
    LLM_AVAILABLE = True
except Exception:
    LLM_AVAILABLE = False


# ============================================
# Standalone Detection Functions
# ============================================

def detect_shorthand_emergence(
    current_msg: Dict,
    prev_msg: Dict,
    llm_id: str,
    sender_id: str,
    similarity: float,
    anchor_similarity: Optional[float] = None,
) -> Optional[Anomaly]:
    """
    Detect when verbose messages suddenly become terse.

    Triggers when:
    - Previous message had >= 25 words, current <= 20, and similarity > 0.4
    - OR compression ratio >= 3.0 and current <= 15 words
    """
    current_words = current_msg["word_count"]
    prev_words = prev_msg["word_count"]
    compression_ratio = prev_words / max(current_words, 1)

    if (prev_words >= 25 and current_words <= 20 and similarity > 0.4) or \
       (compression_ratio >= 3.0 and current_words <= 15):
        return Anomaly(
            type="SHORTHAND_EMERGENCE",
            severity="high",
            llm_id=llm_id,
            agent_id=sender_id,
            details={
                "compression_ratio": round(compression_ratio, 1),
                "similarity": round(similarity, 3)
            },
            timestamp=time.time(),
            message_id=current_msg.get("message_id", ""),
            anchor_similarity=anchor_similarity
        )
    return None


def detect_context_loss(
    current_msg: Dict,
    prev_msg: Dict,
    llm_id: str,
    sender_id: str,
    similarity: float,
    anchor_similarity: Optional[float] = None,
) -> Optional[Anomaly]:
    """
    Detect complete topic changes between consecutive messages.

    Triggers when embedding similarity between consecutive messages < 0.5.
    """
    if similarity < 0.5:
        return Anomaly(
            type="CONTEXT_LOSS",
            severity="high",
            llm_id=llm_id,
            agent_id=sender_id,
            details={"similarity": round(similarity, 3)},
            timestamp=time.time(),
            message_id=current_msg.get("message_id", ""),
            anchor_similarity=anchor_similarity
        )
    return None


def detect_cross_llm_shorthand(
    msg: Dict,
    history: Dict,
    sender: str,
    sender_llm: str,
    receiver: str
) -> List[Anomaly]:
    """
    Detect when short messages are semantically similar to longer ones
    from different LLMs (cross-LLM shorthand compression).
    """
    anomalies = []
    recv_hist = history.get(receiver, {})
    msg_emb = np.array(msg["embedding"])
    msg_words = msg["word_count"]

    for recv_llm, msgs in recv_hist.items():
        if recv_llm != sender_llm and msgs:
            for prev in msgs[-5:]:
                prev_words = prev["word_count"]
                prev_emb = np.array(prev["embedding"])
                sim = float(
                    np.dot(msg_emb, prev_emb) /
                    (np.linalg.norm(msg_emb) * np.linalg.norm(prev_emb) + 1e-8)
                )

                if sim > 0.6 and msg_words < 25 and prev_words > msg_words * 1.5:
                    anomalies.append(Anomaly(
                        type="CROSS_LLM_SHORTHAND",
                        severity="high",
                        llm_id=f"{sender_llm}->{recv_llm}",
                        agent_id=f"{sender}->{receiver}",
                        details={
                            "similarity": round(sim, 3),
                            "current_words": msg_words,
                            "previous_words": prev_words
                        },
                        timestamp=time.time()
                    ))
                    break
    return anomalies


def detect_cross_llm_jargon(
    msg: Dict,
    history: Dict,
    adaptive_dict: 'AdaptiveDictionary'
) -> Optional[Anomaly]:
    """
    Detect undefined acronyms/jargon that appear suddenly in conversation.

    Uses the adaptive dictionary system:
    - Known terms (seed + learned) are ignored
    - Unknown terms are tracked as candidates
    - Candidates seen frequently get auto-promoted to learned
    """
    acronyms = re.findall(r'\b[A-Z]{2,}\b', msg["text"])

    unknown = [
        a for a in acronyms
        if not adaptive_dict.is_known_term(a) and len(a) >= 2
    ]

    promoted_terms = []
    for term in unknown:
        if adaptive_dict.track_candidate(term):
            promoted_terms.append(term)

    if promoted_terms:
        logger.debug(f"Terms auto-promoted to learned: {promoted_terms}")

    seen_in_history = False
    for agent_h in history.values():
        for llm_h in agent_h.values():
            for m in llm_h:
                if m.get("message_id") != msg.get("message_id"):
                    if any(a in m["text"] for a in unknown):
                        seen_in_history = True
                        break
            if seen_in_history:
                break
        if seen_in_history:
            break

    if unknown and not seen_in_history:
        return Anomaly(
            type="CROSS_LLM_JARGON",
            severity="high",
            llm_id=msg["llm_id"],
            agent_id=msg["sender"],
            details={
                "new_terms": unknown[:5],
                "candidate_count": len(adaptive_dict.jargon_dict["candidate"]),
                "learned_count": len(adaptive_dict.jargon_dict["learned"])
            },
            timestamp=time.time()
        )
    return None


def confirm_shorthand_llm(
    prev_text: str,
    curr_text: str
) -> Optional[Dict]:
    """Use LLM to confirm whether shorthand has occurred."""
    if not LLM_AVAILABLE:
        return None

    messages = [
        {
            "role": "system",
            "content": (
                "Determine if the current message is shorthand/abbreviated "
                "compared to the previous."
            )
        },
        {
            "role": "user",
            "content": f'''Previous message: {prev_text}

Current message: {curr_text}

Output ONLY valid JSON:
{{
  "is_shorthand": true | false,
  "explanation": "brief reason",
  "expanded": "full expanded version if shorthand, else null"
}}'''
        }
    ]

    response = ollama_chat(messages, temperature=0.2)
    if response:
        try:
            data = json.loads(response)
            return data if data.get("is_shorthand") else None
        except json.JSONDecodeError:
            pass
    return None


# ============================================
# Premium Detector Orchestrator
# ============================================

class PremiumDetector:
    """
    Premium detection orchestrator.

    Called from the open-source AnomalyDetector.detect() when premium is available.
    Runs all proprietary detection algorithms and returns detected anomalies.
    """

    def __init__(self, adaptive_dict: 'AdaptiveDictionary'):
        self.adaptive_dict = adaptive_dict

    def detect_premium(
        self,
        current_msg: Dict,
        history: Dict,
        sender_id: str,
        llm_id: str,
        prev_msg: Optional[Dict],
        similarity: Optional[float],
        receiver_id: Optional[str],
        anchor: Optional[Dict],
        anchor_similarity: Optional[float],
    ) -> List[Anomaly]:
        """
        Run all premium detections.

        Args:
            current_msg: Current message dict with text, embedding, word_count, etc.
            history: Full conversation history
            sender_id: Agent ID of the sender
            llm_id: LLM model ID
            prev_msg: Previous message from same agent/LLM (or None)
            similarity: Cosine similarity to previous message (or None)
            receiver_id: Optional receiver agent ID
            anchor: Optional anchor dict (user query)
            anchor_similarity: Optional cosine similarity to anchor

        Returns:
            List of detected Anomaly objects
        """
        anomalies = []

        # Jargon detection (always runs, doesn't need history)
        jargon = detect_cross_llm_jargon(
            current_msg, history, self.adaptive_dict
        )
        if jargon:
            anomalies.append(jargon)

        # History-based detections (need prev_msg)
        if prev_msg is not None and similarity is not None:
            # Shorthand emergence
            shorthand = detect_shorthand_emergence(
                current_msg, prev_msg, llm_id, sender_id,
                similarity, anchor_similarity
            )
            if shorthand:
                anomalies.append(shorthand)

            # Context loss
            ctx_loss = detect_context_loss(
                current_msg, prev_msg, llm_id, sender_id,
                similarity, anchor_similarity
            )
            if ctx_loss:
                anomalies.append(ctx_loss)

            # LLM confirmation for shorthand (if LLM available)
            if LLM_AVAILABLE:
                shorthand_anoms = [a for a in anomalies if a.type == "SHORTHAND_EMERGENCE"]
                if shorthand_anoms:
                    confirm = confirm_shorthand_llm(prev_msg["text"], current_msg["text"])
                    if confirm and confirm.get("is_shorthand"):
                        for a in shorthand_anoms:
                            a.details.update({
                                "llm_explanation": confirm.get("explanation"),
                                "llm_expanded": confirm.get("expanded")
                            })
                    else:
                        anomalies = [a for a in anomalies if a.type != "SHORTHAND_EMERGENCE"]

        # Cross-LLM shorthand detection
        if receiver_id and receiver_id in history:
            cross = detect_cross_llm_shorthand(
                current_msg, history, sender_id, llm_id, receiver_id
            )
            anomalies.extend(cross)

        return anomalies

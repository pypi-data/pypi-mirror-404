# Copyright (c) 2024-2026 YuyAI / InsAIts Team. All rights reserved.
# Proprietary and confidential. See LICENSE.premium for terms.
"""
InsAIts Premium - Anchor Forensics
====================================
Anchor drift detection and false-positive suppression.

When a user query (anchor) is set, this module:
- Detects when AI responses drift away from the original query (ANCHOR_DRIFT)
- Suppresses false positives when jargon terms are relevant to the anchor query
- Uses domain keywords and optional LLM to check term relevance
"""

import time
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# LLM integration for relevance checking
try:
    from ..local_llm import ollama_chat
    LLM_AVAILABLE = True
except Exception:
    LLM_AVAILABLE = False


def detect_anchor_drift(
    current_msg: Dict,
    llm_id: str,
    sender_id: str,
    anchor_similarity: float,
    anchor: Dict,
) -> Optional[Any]:
    """
    Detect when AI response drifts from the original user query.

    Triggers when anchor_similarity < 0.4.

    Args:
        current_msg: Current message dict
        llm_id: LLM model ID
        sender_id: Agent ID of the sender
        anchor_similarity: Cosine similarity to anchor
        anchor: Anchor dict with text, embedding

    Returns:
        Anomaly object if drift detected, None otherwise
    """
    from ..detector import Anomaly

    if anchor_similarity < 0.4:
        return Anomaly(
            type="ANCHOR_DRIFT",
            severity="high",
            llm_id=llm_id,
            agent_id=sender_id,
            details={
                "anchor_similarity": round(anchor_similarity, 3),
                "anchor_text_preview": anchor.get("text", "")[:100],
                "response_preview": current_msg["text"][:100]
            },
            timestamp=time.time(),
            message_id=current_msg.get("message_id", ""),
            anchor_similarity=anchor_similarity
        )
    return None


def suppress_anchor_aligned(
    anomalies: List[Any],
    anchor: Optional[Dict],
    anchor_similarity: Optional[float]
) -> List[Any]:
    """
    Suppress false positives when response is aligned with anchor query.

    If anchor_similarity > 0.6, new terms that are relevant to the query
    are downgraded to "info" severity instead of "high".

    Args:
        anomalies: List of Anomaly objects
        anchor: Anchor dict (or None)
        anchor_similarity: Cosine similarity to anchor (or None)

    Returns:
        Filtered/modified list of anomalies
    """
    if anchor is None or anchor_similarity is None:
        return anomalies

    if anchor_similarity <= 0.6:
        return anomalies

    anchor_text = anchor.get("text", "")
    if not anchor_text:
        return anomalies

    for anomaly in anomalies:
        if anomaly.type == "CROSS_LLM_JARGON":
            new_terms = anomaly.details.get("new_terms", [])
            if new_terms and terms_relevant_to_anchor(new_terms, anchor_text):
                anomaly.severity = "info"
                anomaly.details["suppressed"] = True
                anomaly.details["reason"] = "Terms relevant to user query"

        # Attach anchor_similarity to all anomalies
        anomaly.anchor_similarity = anchor_similarity

    return anomalies


def terms_relevant_to_anchor(
    terms: List[str],
    anchor_text: str
) -> bool:
    """
    Check if the new terms are likely relevant to the user's query.

    Uses domain keyword matching and optional LLM fallback.

    Example:
    - Query: "Explain quantum computing"
    - Terms: ["QUBITS", "QPU"]
    - Returns: True
    """
    if not terms:
        return False

    anchor_lower = anchor_text.lower()

    # Domain keywords that indicate technical queries
    domain_indicators = {
        "quantum": ["qubit", "qpu", "superposition", "entangle", "nisq", "qml"],
        "machine learning": ["ml", "nn", "cnn", "rnn", "llm", "gpu", "bert", "gpt", "lstm"],
        "kubernetes": ["k8s", "pod", "helm", "kubectl", "container", "docker"],
        "finance": ["ebitda", "roi", "wacc", "dcf", "npv", "irr", "capex"],
        "healthcare": ["hipaa", "phi", "ehr", "emr", "fhir", "hl7"],
        "devops": ["ci", "cd", "sre", "slo", "sli", "mttr", "rto"],
        "api": ["rest", "graphql", "endpoint", "oauth", "jwt", "http"],
        "database": ["sql", "nosql", "orm", "acid", "crud", "index"],
        "cloud": ["aws", "gcp", "azure", "ec2", "s3", "lambda", "serverless"],
    }

    for domain, keywords in domain_indicators.items():
        if domain in anchor_lower:
            for term in terms:
                if term.lower() in keywords:
                    return True

    # Check if terms appear directly in the anchor
    for term in terms:
        if term.lower() in anchor_lower:
            return True

    # Fallback: Use LLM to check relevance
    if LLM_AVAILABLE:
        return _llm_check_relevance(terms, anchor_text)

    return False


def _llm_check_relevance(
    terms: List[str],
    anchor_text: str
) -> bool:
    """Use LLM to determine if terms are relevant to the anchor query."""
    messages = [{
        "role": "user",
        "content": f'''Are the following terms relevant to this query?

Query: "{anchor_text}"
Terms: {", ".join(terms)}

Reply with ONLY "YES" or "NO".'''
    }]

    try:
        response = ollama_chat(messages, temperature=0.1)
        if response:
            return response.strip().upper() == "YES"
    except Exception:
        pass

    return False

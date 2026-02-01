# Copyright (c) 2024-2026 YuyAI / InsAIts Team. All rights reserved.
# Proprietary and confidential. See LICENSE.premium for terms.
"""
InsAIts Premium - Decipher Engine
=================================
AI-to-AI message deciphering: expand shorthand, explain jargon,
remove hedging, and rephrase for target LLM style.

Supports cloud (API) and local (Ollama) decipher modes.
"""

import json
import logging
import requests
from typing import Any, Dict, List, Literal, Optional

logger = logging.getLogger(__name__)

# LLM integration for local decipher
try:
    from ..local_llm import ollama_chat
    LLM_AVAILABLE = True
except Exception:
    LLM_AVAILABLE = False


class DecipherEngine:
    """
    Premium decipher engine.

    Expands shorthand, explains jargon, removes hedging,
    and rephrases messages for target LLM compatibility.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        tier: str = "anonymous",
        api_endpoints: Optional[Dict[str, str]] = None,
        get_feature_fn=None,
    ):
        """
        Initialize the decipher engine.

        Args:
            api_key: API key for cloud decipher
            tier: User's subscription tier
            api_endpoints: Dict with API endpoint URLs
            get_feature_fn: Function to check feature availability by tier
        """
        self.api_key = api_key
        self.tier = tier
        self.api_endpoints = api_endpoints or {}
        self._get_feature = get_feature_fn

    def decipher(
        self,
        msg: Dict,
        context: List[Dict],
        target_llm_id: Optional[str] = None,
        model: str = "phi3",
        mode: Literal["auto", "cloud", "local"] = "auto"
    ) -> Dict[str, Any]:
        """
        Expand shorthand, explain jargon, remove hedges,
        and rephrase for target LLM style.

        Args:
            msg: Message dict with 'text', 'sender', optionally 'receiver'
            context: Conversation context (list of message dicts)
            target_llm_id: Target LLM style to optimize for
            model: Local Ollama model to use (default: phi3)
            mode: Decipher mode
                - "auto": Cloud first (if available), fallback to local
                - "cloud": Cloud only (requires API key)
                - "local": Local Ollama only

        Returns:
            Dict with expanded_text, explanations, rephrased_text, confidence_improved
        """
        target_style = target_llm_id or "clear, detailed, and confident"

        if mode == "cloud":
            return self._decipher_cloud(msg["text"], context, target_style)
        elif mode == "local":
            return self._decipher_local(msg["text"], context, target_style, model)
        else:  # auto
            cloud_result = self._decipher_cloud(msg["text"], context, target_style)
            if "error" not in cloud_result:
                return cloud_result
            return self._decipher_local(msg["text"], context, target_style, model)

    def _decipher_cloud(
        self,
        text: str,
        context: List[Dict],
        target_style: str
    ) -> Dict[str, Any]:
        """Call cloud decipher API."""
        if not self.api_key:
            return {"error": "Cloud decipher requires API key", "original_text": text}

        if self._get_feature and not self._get_feature(self.tier, "cloud_decipher"):
            return {
                "error": f"Cloud decipher not available for {self.tier} tier",
                "original_text": text
            }

        decipher_url = self.api_endpoints.get("decipher")
        if not decipher_url:
            return {"error": "Decipher API endpoint not configured", "original_text": text}

        try:
            response = requests.post(
                decipher_url,
                json={
                    "api_key": self.api_key,
                    "text": text,
                    "context": context,
                    "target_style": target_style
                },
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                data["provider"] = data.get("provider", "cloud")
                data["mode"] = "cloud"
                return data
            elif response.status_code == 401:
                return {"error": "Invalid API key", "original_text": text}
            elif response.status_code == 403:
                return {"error": "Cloud decipher limit reached or not available", "original_text": text}
            else:
                return {"error": f"Cloud API error: {response.status_code}", "original_text": text}

        except requests.exceptions.Timeout:
            return {"error": "Cloud decipher timeout", "original_text": text}
        except requests.exceptions.RequestException as e:
            logger.debug(f"Cloud decipher failed: {e}")
            return {"error": "Cloud decipher unavailable", "original_text": text}

    def _decipher_local(
        self,
        text: str,
        context: List[Dict],
        target_style: str,
        model: str = "phi3"
    ) -> Dict[str, Any]:
        """Use local Ollama for decipher."""
        if not LLM_AVAILABLE:
            return {
                "error": "Local decipher requires Ollama (pip install ollama, then 'ollama serve')",
                "original_text": text
            }

        # Quick check if Ollama is reachable
        test_resp = ollama_chat([{"role": "user", "content": "ping"}], model=model)
        if test_resp is None:
            return {
                "error": f"Ollama not available (run 'ollama serve' and 'ollama pull {model}')",
                "original_text": text
            }

        # Build context string
        context_lines = []
        for m in context:
            direction = f"{m['sender']} \u2192 {m['receiver']}"
            context_lines.append(f"{direction} ({m['llm_id']}): {m['text']}")
        context_str = "\n".join(context_lines) if context_lines else "No prior context available."

        system_prompt = (
            "You are an AI-to-AI communication mediator. "
            "Expand shorthand, explain undefined jargon, remove hedging for higher confidence, "
            "and rephrase for compatibility with the target LLM style."
        )

        user_prompt = f"""Conversation context:
{context_str}

Latest message:
{text}

Target LLM style: {target_style}

Tasks:
- Expand any shorthand/abbreviations
- Explain any new or unclear acronyms/terms
- Increase confidence (remove hedges like 'maybe', 'perhaps')
- Rephrase if needed for the target style

Output ONLY valid JSON:
{{
  "expanded_text": "full clear version",
  "explanations": {{"TERM1": "meaning", "TERM2": "meaning"}} or {{}},
  "rephrased_text": "version optimized for target LLM (or same as expanded if no change)",
  "confidence_improved": true | false
}}
"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        response = ollama_chat(messages, model=model, temperature=0.4)
        if response:
            try:
                result = json.loads(response)
                result["provider"] = f"ollama/{model}"
                result["mode"] = "local"
                return result
            except json.JSONDecodeError:
                return {"raw_llm_response": response, "original_text": text, "mode": "local"}

        return {"error": "No response from local LLM", "original_text": text}

    @staticmethod
    def build_context(history: Dict, sender_id: str, receiver_id: Optional[str] = None, limit: int = 15) -> List[Dict]:
        """
        Build conversation context for decipher from history.

        Args:
            history: Full conversation history dict
            sender_id: ID of the message sender
            receiver_id: Optional receiver ID for thread context
            limit: Maximum context messages

        Returns:
            List of context message dicts
        """
        if receiver_id:
            # Get thread between sender and receiver
            thread = []
            for llm, msgs in history.get(sender_id, {}).items():
                for m in msgs:
                    if m.get("receiver") == receiver_id:
                        thread.append(m)
            for llm, msgs in history.get(receiver_id, {}).items():
                for m in msgs:
                    if m.get("receiver") == sender_id:
                        thread.append(m)
            thread = sorted(thread, key=lambda x: x["timestamp"])[-limit:]
        else:
            recent = []
            for llm_hist in history.get(sender_id, {}).values():
                recent.extend(llm_hist[-10:])
            thread = sorted(recent, key=lambda x: x["timestamp"])[-limit:]

        # Format for API (exclude last message which is the one being deciphered)
        context = []
        prior_thread = thread[:-1] if thread else []
        for m in prior_thread:
            context.append({
                "sender": m["sender"],
                "receiver": m.get("receiver", "unknown"),
                "llm_id": m.get("llm_id", "unknown"),
                "text": m["text"]
            })
        return context

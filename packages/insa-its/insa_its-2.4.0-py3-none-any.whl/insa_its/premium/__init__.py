# Copyright (c) 2024-2026 YuyAI / InsAIts Team. All rights reserved.
# Proprietary and confidential. See LICENSE.premium for terms.
"""
InsAIts SDK - Premium Features
==============================
Proprietary - All Rights Reserved.

This module is included in the paid PyPI package (pip install insa-its)
and excluded from the open-source GitHub repository.

Premium features:
- Real-time shorthand/jargon emergence detection
- Cross-agent context loss detection
- Anchor drift forensics with false-positive suppression
- Automated deciphering/expansion to human-readable
- Adaptive dictionaries with domain-specific knowledge
- Dictionary import/export/auto-expand
"""

import logging

logger = logging.getLogger(__name__)

# Core premium detection (required for PREMIUM_AVAILABLE)
PREMIUM_AVAILABLE = True

try:
    from .advanced_detector import (
        PremiumDetector,
        detect_shorthand_emergence,
        detect_context_loss,
        detect_cross_llm_shorthand,
        detect_cross_llm_jargon,
        confirm_shorthand_llm,
    )
except ImportError as e:
    logger.error(f"Premium advanced_detector failed to load: {e}")
    PREMIUM_AVAILABLE = False

try:
    from .adaptive_dict import (
        AdaptiveDictionary,
        DOMAIN_DICTIONARIES,
    )
except ImportError as e:
    logger.error(f"Premium adaptive_dict failed to load: {e}")
    PREMIUM_AVAILABLE = False

# Optional premium modules (loaded independently, don't block core premium)
DECIPHER_AVAILABLE = False
try:
    from .decipher_engine import (
        DecipherEngine,
    )
    DECIPHER_AVAILABLE = True
except ImportError:
    logger.debug("Premium decipher_engine not yet available")

ANCHOR_AVAILABLE = False
try:
    from .anchor_forensics import (
        detect_anchor_drift,
        suppress_anchor_aligned,
        terms_relevant_to_anchor,
    )
    ANCHOR_AVAILABLE = True
except ImportError:
    logger.debug("Premium anchor_forensics not yet available")

if PREMIUM_AVAILABLE:
    logger.debug("Core premium features loaded successfully")
    if DECIPHER_AVAILABLE:
        logger.debug("Premium decipher engine loaded")
    if ANCHOR_AVAILABLE:
        logger.debug("Premium anchor forensics loaded")
else:
    logger.debug("Core premium features unavailable - running in open-source mode")

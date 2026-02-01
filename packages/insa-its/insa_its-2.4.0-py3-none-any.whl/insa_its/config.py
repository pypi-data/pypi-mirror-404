"""
InsAIts SDK - Configuration
===========================
Centralized configuration for the SDK.
"""

import os

# ============================================
# Development/Testing Mode
# ============================================

# Enable development mode for testing with mock API keys
DEV_MODE = os.getenv("INSAITS_DEV_MODE", "").lower() == "true"

# Test API keys for development (use in tests)
DEV_API_KEYS = {
    "test-pro-unlimited": {"tier": "pro", "valid": True},
    "test-starter-10k": {"tier": "starter", "valid": True},
    "test-free-100": {"tier": "free", "valid": True},
}

# ============================================
# API Configuration
# ============================================

# Production API URL (Railway deployment)
API_BASE_URL = "https://insaitsapi-production.up.railway.app"
API_URL_DEV = "http://localhost:8000"

# Use dev URL if environment variable is set
if os.getenv("INSAITS_DEV_MODE"):
    API_BASE_URL = API_URL_DEV
# Allow custom API URL override
if os.getenv("INSAITS_API_URL"):
    API_BASE_URL = os.getenv("INSAITS_API_URL")

API_ENDPOINTS = {
    "validate": f"{API_BASE_URL}/api/keys/validate",
    "usage_check": f"{API_BASE_URL}/api/usage/check",
    "usage_track": f"{API_BASE_URL}/api/usage/track",
    "embeddings": f"{API_BASE_URL}/api/embeddings/generate",
    "decipher": f"{API_BASE_URL}/api/decipher/expand",
    "decipher_status": f"{API_BASE_URL}/api/decipher/status",
    "register": f"{API_BASE_URL}/api/keys/generate",
}


# ============================================
# Tier Limits
# ============================================

# Anonymous (no API key) - VERY limited, forces registration
ANONYMOUS_LIMITS = {
    "session_messages": 5,  # Only 5 messages without key!
    "daily_messages": 5,
    "history_size": 5,
    "cloud_embeddings": False,
    "export": False,
    "show_warning": True,  # Show "register for more" warning
}

# Free tier (registered, free API key)
FREE_TIER_LIMITS = {
    "daily_messages": 100,
    "session_messages": 100,
    "history_size": 100,
    "cloud_embeddings": False,
    "export": False,
    "show_warning": False,
}

# Starter tier ($49/mo or €99 lifetime)
STARTER_TIER_LIMITS = {
    "daily_messages": 10000,
    "session_messages": 10000,
    "history_size": 1000,
    "cloud_embeddings": True,
    "export": True,
    "show_warning": False,
}

# Pro tier ($79/mo or €299 lifetime)
PRO_TIER_LIMITS = {
    "daily_messages": -1,  # Unlimited
    "session_messages": -1,
    "history_size": 10000,
    "cloud_embeddings": True,
    "export": True,
    "show_warning": False,
}

TIER_LIMITS = {
    "anonymous": ANONYMOUS_LIMITS,
    "free": FREE_TIER_LIMITS,
    "starter": STARTER_TIER_LIMITS,
    "pro": PRO_TIER_LIMITS,
    "lifetime": PRO_TIER_LIMITS,  # Legacy, same as Pro
    "lifetime_starter": STARTER_TIER_LIMITS,  # €99 one-time
    "lifetime_pro": PRO_TIER_LIMITS,  # €299 one-time
    "enterprise": PRO_TIER_LIMITS,
}


# ============================================
# Cache Settings
# ============================================

LICENSE_CACHE_TTL = 3600  # 1 hour - how long to cache license validation
EMBEDDING_CACHE_SIZE = 2000
OFFLINE_GRACE_PERIOD = 86400  # 24 hours - allow cached validation if offline


# ============================================
# Feature Flags
# ============================================

FEATURES = {
    "anonymous": {
        "anomaly_detection": True,
        "local_embeddings": True,
        "synthetic_embeddings": True,
        "cloud_embeddings": False,
        "cloud_decipher": False,
        "local_decipher": True,
        "conversation_reading": True,
        "export": False,
        "graph": False,
        "cloud_sync": False,
        "dashboard": False,
        "integrations": False,
        # Phase 3: Hallucination Detection
        "fact_tracking": False,
        "source_grounding": False,
        "self_consistency": False,
    },
    "free": {
        "anomaly_detection": True,
        "local_embeddings": True,
        "synthetic_embeddings": True,
        "cloud_embeddings": False,
        "cloud_decipher": True,  # 20/day
        "local_decipher": True,
        "conversation_reading": True,
        "export": False,
        "graph": True,
        "cloud_sync": False,
        "dashboard": True,
        "integrations": True,
        # Phase 3: Hallucination Detection
        "fact_tracking": True,
        "source_grounding": True,
        "self_consistency": True,
    },
    "starter": {
        "anomaly_detection": True,
        "local_embeddings": True,
        "synthetic_embeddings": True,
        "cloud_embeddings": True,
        "cloud_decipher": True,  # 500/day
        "local_decipher": True,
        "conversation_reading": True,
        "export": True,
        "graph": True,
        "cloud_sync": True,
        "dashboard": True,
        "integrations": True,
        # Phase 3: Hallucination Detection
        "fact_tracking": True,
        "source_grounding": True,
        "self_consistency": True,
    },
    "pro": {
        "anomaly_detection": True,
        "local_embeddings": True,
        "synthetic_embeddings": True,
        "cloud_embeddings": True,
        "cloud_decipher": True,  # Unlimited
        "local_decipher": True,
        "conversation_reading": True,
        "export": True,
        "graph": True,
        "cloud_sync": True,
        "dashboard": True,
        "integrations": True,
        # Phase 3: Hallucination Detection
        "fact_tracking": True,
        "source_grounding": True,
        "self_consistency": True,
    },
    "lifetime": {
        "anomaly_detection": True,
        "local_embeddings": True,
        "synthetic_embeddings": True,
        "cloud_embeddings": True,
        "cloud_decipher": True,  # Unlimited
        "local_decipher": True,
        "conversation_reading": True,
        "export": True,
        "graph": True,
        "cloud_sync": True,
        "dashboard": True,
        "integrations": True,
        # Phase 3: Hallucination Detection
        "fact_tracking": True,
        "source_grounding": True,
        "self_consistency": True,
    },
    "lifetime_starter": {
        "anomaly_detection": True,
        "local_embeddings": True,
        "synthetic_embeddings": True,
        "cloud_embeddings": True,
        "cloud_decipher": True,  # 500/day
        "local_decipher": True,
        "conversation_reading": True,
        "export": True,
        "graph": True,
        "cloud_sync": True,
        "dashboard": True,
        "integrations": True,
        # Phase 3: Hallucination Detection
        "fact_tracking": True,
        "source_grounding": True,
        "self_consistency": True,
    },
    "lifetime_pro": {
        "anomaly_detection": True,
        "local_embeddings": True,
        "synthetic_embeddings": True,
        "cloud_embeddings": True,
        "cloud_decipher": True,  # Unlimited
        "local_decipher": True,
        "conversation_reading": True,
        "export": True,
        "graph": True,
        "cloud_sync": True,
        "dashboard": True,
        "integrations": True,
        # Phase 3: Hallucination Detection
        "fact_tracking": True,
        "source_grounding": True,
        "self_consistency": True,
    },
}


# ============================================
# Open-Core Feature Classification
# ============================================

# Features that require the premium package (proprietary)
PREMIUM_FEATURES = {
    "shorthand_detection",
    "context_loss_detection",
    "cross_llm_shorthand",
    "cross_llm_jargon",
    "anchor_drift",
    "anchor_suppression",
    "adaptive_dictionary",
    "domain_dictionaries",
    "dictionary_export_import",
    "auto_expand_terms",
    "decipher_full",
    "learn_from_session",
}

# Features available in open-source (no premium needed)
OPEN_FEATURES = {
    "anomaly_detection",
    "local_embeddings",
    "synthetic_embeddings",
    "conversation_reading",
    "forensic_chain_tracing",
    "hallucination_detection",
    "fact_tracking",
    "source_grounding",
    "self_consistency",
    "phantom_citation_detection",
    "confidence_decay_tracking",
    "dashboard",
    "integrations",
    "trend_analysis",
    "graph",
    "low_confidence_detection",
    "llm_fingerprint_mismatch",
}


def get_feature(tier: str, feature: str) -> bool:
    """Check if a feature is available for a tier."""
    tier_features = FEATURES.get(tier, FEATURES["anonymous"])
    return tier_features.get(feature, False)


def is_premium_feature(feature: str) -> bool:
    """Check if a feature requires the premium package."""
    return feature in PREMIUM_FEATURES


def is_open_feature(feature: str) -> bool:
    """Check if a feature is available in the open-source version."""
    return feature in OPEN_FEATURES


def get_tier_limits(tier: str) -> dict:
    """Get limits for a specific tier."""
    return TIER_LIMITS.get(tier, ANONYMOUS_LIMITS)


# ============================================
# Registration & Pricing URLs
# ============================================

REGISTER_URL = "https://github.com/Nomadu27/InsAIts.API"

# Stripe URLs
PRICING_URL = "https://buy.stripe.com/00w6oH87R77T32A96Eb3q00"
STRIPE_STARTER_LIFETIME = "https://buy.stripe.com/00w6oH87R77T32A56Eb3q00"
STRIPE_PRO_LIFETIME = "https://buy.stripe.com/3cI8wPfAjak5bz61Ecb3q04"

# Gumroad URLs (alternative payment)
GUMROAD_STARTER_LIFETIME = "https://steddy.gumroad.com/l/InsAItsStarter"
GUMROAD_PRO_LIFETIME = "https://steddy.gumroad.com/l/InsAItsPro100"

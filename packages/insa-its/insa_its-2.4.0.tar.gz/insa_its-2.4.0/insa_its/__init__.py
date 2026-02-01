"""
insAIts SDK - pip install insa-its
Multi-LLM Agent Communication Monitoring & Hallucination Detection

Open-core model: Apache 2.0 open-source core + proprietary premium features.

Open-source features (FREE):
- Real-time anomaly detection (fingerprint mismatch, low confidence)
- LLM fingerprint validation
- Hallucination detection (fact tracking, source grounding,
  phantom citation detection, confidence decay tracking)
- Cross-agent contradiction detection (unique to InsAIts)
- Forensic chain tracing (trace anomalies back to root cause)
- Anchor-aware context tracking
- Terminal dashboard for live monitoring
- LangChain, CrewAI, LangGraph, Slack integrations
- Local embeddings (sentence-transformers) + cloud embeddings
- Configurable Ollama model selection

Premium features (requires insa_its.premium):
- Advanced anomaly detection (shorthand emergence, jargon, context loss, cross-LLM)
- Decipher engine (translate AI-to-AI communication, cloud + local)
- Anchor drift detection + false-positive suppression
- Adaptive jargon dictionary with domain-specific knowledge
- Dictionary import/export/auto-expand
"""

from .monitor import insAItsMonitor
from .detector import AnomalyDetector, Anomaly
from .license import LicenseManager, get_license_manager
from .config import FREE_TIER_LIMITS, FEATURES, get_feature
from .exceptions import (
    insAItsError,
    RateLimitError,
    APIError,
    AuthenticationError,
    EmbeddingError,
    HallucinationError,
    PremiumFeatureError,
)
from .hallucination import (
    FactTracker,
    SourceGrounder,
    SelfConsistencyChecker,
    PhantomCitationDetector,
    ConfidenceDecayTracker,
    FactClaim,
)
from .local_llm import set_default_model, get_default_model

# Premium availability flag
PREMIUM_AVAILABLE = False
try:
    from .premium import PREMIUM_AVAILABLE
except ImportError:
    pass

# Dashboard (requires: pip install rich)
try:
    from .dashboard import LiveDashboard, SimpleDashboard, create_dashboard
    DASHBOARD_AVAILABLE = True
except ImportError:
    DASHBOARD_AVAILABLE = False
    LiveDashboard = None
    SimpleDashboard = None
    create_dashboard = None

__version__ = "2.4.0"
__all__ = [
    # Core
    "insAItsMonitor",
    "AnomalyDetector",
    "Anomaly",
    "LicenseManager",
    "get_license_manager",
    # Config
    "FREE_TIER_LIMITS",
    "FEATURES",
    "get_feature",
    # Exceptions
    "insAItsError",
    "RateLimitError",
    "APIError",
    "AuthenticationError",
    "EmbeddingError",
    "HallucinationError",
    "PremiumFeatureError",
    # Hallucination Detection
    "FactTracker",
    "SourceGrounder",
    "SelfConsistencyChecker",
    "PhantomCitationDetector",
    "ConfidenceDecayTracker",
    "FactClaim",
    # Local LLM
    "set_default_model",
    "get_default_model",
    # Premium
    "PREMIUM_AVAILABLE",
    # Dashboard
    "LiveDashboard",
    "SimpleDashboard",
    "create_dashboard",
    "DASHBOARD_AVAILABLE",
]
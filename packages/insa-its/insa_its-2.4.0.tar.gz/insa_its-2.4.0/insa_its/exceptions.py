class insAItsError(Exception):
    """Base exception for insAIts SDK"""
    pass


class RateLimitError(insAItsError):
    """Rate limit exceeded"""
    pass


class APIError(insAItsError):
    """API communication error"""
    pass


class AuthenticationError(insAItsError):
    """Authentication failed"""
    pass


class EmbeddingError(insAItsError):
    """Embedding generation failed"""
    pass


class HallucinationError(insAItsError):
    """Hallucination detection error"""
    pass


class PremiumFeatureError(insAItsError):
    """Feature requires premium package"""

    def __init__(self, feature_name: str = ""):
        message = f"Feature '{feature_name}' requires InsAIts Premium. "
        message += "Install the full package: pip install insa-its"
        super().__init__(message)
        self.feature_name = feature_name
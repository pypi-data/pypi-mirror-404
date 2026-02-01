"""
InsAIts SDK - License Management
================================
API key validation and usage tracking.
Requires valid API key for full functionality.
"""

import time
import logging
import os
import json
from typing import Optional, Dict, Any
from pathlib import Path

from .config import (
    API_ENDPOINTS,
    ANONYMOUS_LIMITS,
    LICENSE_CACHE_TTL,
    OFFLINE_GRACE_PERIOD,
    get_feature,
    get_tier_limits,
    REGISTER_URL,
    PRICING_URL,
    GUMROAD_STARTER_LIFETIME,
    GUMROAD_PRO_LIFETIME,
    DEV_MODE,
    DEV_API_KEYS,
)

logger = logging.getLogger(__name__)

# Try to import requests, fallback to offline mode
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    logger.warning("requests not installed - running in offline mode")


# Cache file for offline validation
CACHE_DIR = Path.home() / ".insaits"
CACHE_FILE = CACHE_DIR / "license_cache.json"


class LicenseManager:
    """
    Manages license validation and usage tracking.

    IMPORTANT: Without a valid API key, functionality is severely limited.
    Register for a FREE key at: https://github.com/Nomadu27/InsAIts.API
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.tier = "anonymous"  # Default to anonymous (very limited)
        self.is_validated = False
        self.validation_time = 0
        self.session_message_count = 0
        self.daily_message_count = 0
        self._cached_validation: Optional[Dict] = None
        self._limits = ANONYMOUS_LIMITS.copy()

        # Try to load cached validation
        self._load_cache()

    def _get_cache_path(self) -> Path:
        """Get the cache file path, creating directory if needed."""
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        return CACHE_FILE

    def _load_cache(self):
        """Load cached validation from disk."""
        try:
            cache_path = self._get_cache_path()
            if cache_path.exists():
                with open(cache_path, 'r') as f:
                    data = json.load(f)
                    # Check if cache is for the same API key
                    if data.get("api_key_hash") == self._hash_key(self.api_key):
                        cache_time = data.get("validation_time", 0)
                        # Allow cached validation within grace period
                        if time.time() - cache_time < OFFLINE_GRACE_PERIOD:
                            self._cached_validation = data
                            self.tier = data.get("tier", "anonymous")
                            self.is_validated = True
                            self.validation_time = cache_time
                            self._limits = get_tier_limits(self.tier)
                            logger.info(f"Loaded cached validation: {self.tier}")
        except Exception as e:
            logger.debug(f"Could not load cache: {e}")

    def _save_cache(self):
        """Save validation to disk for offline use."""
        try:
            cache_path = self._get_cache_path()
            data = {
                "api_key_hash": self._hash_key(self.api_key),
                "tier": self.tier,
                "is_validated": self.is_validated,
                "validation_time": self.validation_time,
            }
            with open(cache_path, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            logger.debug(f"Could not save cache: {e}")

    def _hash_key(self, key: Optional[str]) -> str:
        """Hash API key for cache comparison."""
        if not key:
            return "anonymous"
        import hashlib
        return hashlib.sha256(key.encode()).hexdigest()[:16]

    def validate(self) -> Dict[str, Any]:
        """
        Validate the API key with the server.
        Returns cached result if still valid.

        Without API key = anonymous tier (5 messages only!)
        """
        # No API key = anonymous tier (very limited)
        if not self.api_key:
            self.tier = "anonymous"
            self.is_validated = False
            self._limits = ANONYMOUS_LIMITS
            self._show_registration_warning()
            return {
                "valid": False,
                "tier": "anonymous",
                "cached": False,
                "message": "No API key provided. Limited to 5 messages. Get FREE key at: " + REGISTER_URL
            }

        # Check cache
        if self._cached_validation and self._is_cache_valid():
            return {**self._cached_validation, "cached": True}

        # Dev mode: use DEV_API_KEYS for local testing
        if DEV_MODE and self.api_key in DEV_API_KEYS:
            dev_data = DEV_API_KEYS[self.api_key]
            self.tier = dev_data["tier"]
            self.is_validated = dev_data["valid"]
            self.validation_time = time.time()
            self._limits = get_tier_limits(self.tier)
            self._cached_validation = {
                "valid": self.is_validated,
                "tier": self.tier,
                "message": "Dev mode validation"
            }
            logger.info(f"Dev mode: validated as {self.tier} tier")
            return {**self._cached_validation, "cached": False, "dev_mode": True}

        # Can't validate without requests library
        if not REQUESTS_AVAILABLE:
            logger.warning("Cannot validate license - requests not available")
            # Fall back to cached if available
            if self._cached_validation:
                return {**self._cached_validation, "cached": True, "offline": True}
            self.tier = "anonymous"
            self._limits = ANONYMOUS_LIMITS
            return {"valid": False, "tier": "anonymous", "error": "offline"}

        # Call API
        try:
            response = requests.post(
                API_ENDPOINTS["validate"],
                json={"api_key": self.api_key},
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                self.is_validated = data.get("valid", False)
                self.tier = data.get("tier", "free") if self.is_validated else "anonymous"
                self.validation_time = time.time()
                self._limits = get_tier_limits(self.tier)

                self._cached_validation = {
                    "valid": self.is_validated,
                    "tier": self.tier,
                    "message": data.get("message", "")
                }

                # Save to disk for offline use
                self._save_cache()

                if self.is_validated:
                    logger.info(f"License validated: {self.tier} tier")
                else:
                    logger.warning("Invalid API key")
                    self._show_registration_warning()

                return {**self._cached_validation, "cached": False}
            else:
                logger.error(f"License validation failed: {response.status_code}")
                self.tier = "anonymous"
                self._limits = ANONYMOUS_LIMITS
                return {"valid": False, "tier": "anonymous", "error": "api_error"}

        except requests.exceptions.RequestException as e:
            logger.error(f"License validation request failed: {e}", exc_info=True)
            # Fall back to cached if available
            if self._cached_validation:
                logger.info("Using cached validation (offline)")
                return {**self._cached_validation, "cached": True, "offline": True}
            self.tier = "anonymous"
            self._limits = ANONYMOUS_LIMITS
            return {"valid": False, "tier": "anonymous", "error": "network_error"}

    def _show_registration_warning(self):
        """Show warning about limited functionality."""
        print("\n" + "="*60)
        print("  InsAIts - API Key Required for Full Access")
        print("="*60)
        print(f"  Current: ANONYMOUS mode (limited to {ANONYMOUS_LIMITS['session_messages']} messages)")
        print("")
        print("  Get your FREE API key:")
        print(f"    {REGISTER_URL}")
        print("")
        print("  Or get LIFETIME access (first 100 per tier):")
        print(f"    Starter: {GUMROAD_STARTER_LIFETIME}")
        print(f"    Pro:     {GUMROAD_PRO_LIFETIME}")
        print("="*60 + "\n")

    def _is_cache_valid(self) -> bool:
        """Check if cached validation is still valid."""
        return (time.time() - self.validation_time) < LICENSE_CACHE_TTL

    def check_quota(self) -> Dict[str, Any]:
        """
        Check remaining quota based on tier.
        """
        limits = self._limits

        # Unlimited tiers
        if limits.get("session_messages", 0) == -1:
            return {
                "allowed": True,
                "remaining": -1,
                "limit": -1,
                "tier": self.tier
            }

        # Limited tiers
        limit = limits.get("session_messages", 5)
        remaining = max(0, limit - self.session_message_count)

        return {
            "allowed": remaining > 0,
            "remaining": remaining,
            "limit": limit,
            "tier": self.tier
        }

    def track_usage(self, message_count: int = 1, anomaly_count: int = 0) -> Dict[str, Any]:
        """
        Track usage locally and optionally report to server.
        """
        self.session_message_count += message_count

        # Check if allowed
        quota = self.check_quota()
        if not quota["allowed"]:
            tier_msg = "Register for FREE to get 100 messages!" if self.tier == "anonymous" else "Upgrade for more messages."
            return {
                "success": False,
                "remaining": 0,
                "message": f"Message limit reached. {tier_msg}",
                "upgrade_url": PRICING_URL
            }

        # Report to server if validated and online
        if self.is_validated and self.api_key and REQUESTS_AVAILABLE:
            try:
                requests.post(
                    API_ENDPOINTS["usage_track"],
                    json={
                        "api_key": self.api_key,
                        "message_count": message_count,
                        "anomaly_count": anomaly_count
                    },
                    timeout=2
                )
            except Exception as e:
                # Non-blocking - don't fail if tracking fails
                logger.debug(f"Usage tracking failed: {e}")

        return {
            "success": True,
            "remaining": quota["remaining"],
            "message": f"{quota['remaining']} messages remaining" if quota["remaining"] >= 0 else "Unlimited"
        }

    def is_feature_available(self, feature: str) -> bool:
        """Check if a feature is available for current tier."""
        return get_feature(self.tier, feature)

    def get_cloud_embedding(
        self,
        text: str,
        timeout: int = 30,
        max_retries: int = 2
    ) -> Optional[list]:
        """
        Get cloud embedding from API (Starter+ only).
        Returns None if not available or fails after retries.
        """
        if not self.is_feature_available("cloud_embeddings"):
            return None

        if not self.api_key or not REQUESTS_AVAILABLE:
            return None

        for attempt in range(max_retries + 1):
            try:
                response = requests.post(
                    API_ENDPOINTS["embeddings"],
                    json={
                        "api_key": self.api_key,
                        "text": text
                    },
                    timeout=timeout
                )

                if response.status_code == 200:
                    data = response.json()
                    return data.get("embedding")

            except requests.exceptions.Timeout:
                if attempt < max_retries:
                    logger.warning(f"Cloud embedding timeout, retrying ({attempt + 1}/{max_retries})...")
                else:
                    logger.warning("Cloud embedding timed out - using local embeddings")
            except Exception as e:
                logger.warning(f"Cloud embedding failed: {e}")
                break  # Don't retry on other errors

        return None

    def get_status(self) -> Dict[str, Any]:
        """Get current license status."""
        quota = self.check_quota()
        return {
            "tier": self.tier,
            "is_validated": self.is_validated,
            "api_key_set": bool(self.api_key),
            "session_messages": self.session_message_count,
            "quota": quota,
            "limits": self._limits,
            "features": {
                "cloud_embeddings": self.is_feature_available("cloud_embeddings"),
                "export": self.is_feature_available("export"),
                "cloud_sync": self.is_feature_available("cloud_sync"),
                "dashboard": self.is_feature_available("dashboard"),
                "integrations": self.is_feature_available("integrations"),
            },
            "upgrade_url": PRICING_URL,
            "register_url": REGISTER_URL,
        }


# Global license manager instance (can be overridden)
_license_manager: Optional[LicenseManager] = None


def get_license_manager(api_key: Optional[str] = None) -> LicenseManager:
    """Get or create the global license manager."""
    global _license_manager
    if _license_manager is None or (api_key and api_key != _license_manager.api_key):
        _license_manager = LicenseManager(api_key)
        _license_manager.validate()
    return _license_manager

"""
InsAIts Slack Integration
=========================
Send anomaly alerts to Slack channels via webhooks.

Usage:
    from insa_its import insAItsMonitor
    from insa_its.integrations import SlackNotifier

    # Create monitor with Slack alerts
    monitor = insAItsMonitor(api_key="your-key")
    slack = SlackNotifier(
        webhook_url="https://hooks.slack.com/services/...",
        channel="#ai-monitoring",
        min_severity="medium"  # Only alert on medium+ severity
    )

    # Attach to monitor
    monitor.on_anomaly(slack.send_alert)

    # Or use the convenience wrapper
    from insa_its.integrations import slack_monitored
    monitor = slack_monitored(
        api_key="your-key",
        webhook_url="https://hooks.slack.com/..."
    )
"""

import logging
import requests
from typing import Optional, Dict, Any, List, Callable
from datetime import datetime

logger = logging.getLogger(__name__)


class SlackNotifier:
    """
    Send InsAIts anomaly alerts to Slack.

    Features:
    - Configurable severity thresholds
    - Rich message formatting with anomaly details
    - Rate limiting to prevent spam
    - Batch alerts for multiple anomalies
    - Custom message templates

    Example:
        slack = SlackNotifier(
            webhook_url="https://hooks.slack.com/services/...",
            min_severity="medium"
        )
        monitor.on_anomaly(slack.send_alert)
    """

    SEVERITY_LEVELS = {"low": 1, "medium": 2, "high": 3, "critical": 4}

    def __init__(
        self,
        webhook_url: str,
        channel: Optional[str] = None,
        username: str = "InsAIts Monitor",
        icon_emoji: str = ":robot_face:",
        min_severity: str = "medium",
        rate_limit_seconds: int = 60,
        batch_window_seconds: int = 5
    ):
        """
        Initialize Slack notifier.

        Args:
            webhook_url: Slack incoming webhook URL
            channel: Override channel (optional, uses webhook default)
            username: Bot username shown in Slack
            icon_emoji: Bot emoji icon
            min_severity: Minimum severity to alert ("low", "medium", "high", "critical")
            rate_limit_seconds: Minimum seconds between alerts per anomaly type
            batch_window_seconds: Window to batch multiple anomalies together
        """
        self.webhook_url = webhook_url
        self.channel = channel
        self.username = username
        self.icon_emoji = icon_emoji
        self.min_severity = min_severity.lower()
        self.rate_limit_seconds = rate_limit_seconds
        self.batch_window_seconds = batch_window_seconds

        self._last_alert_times: Dict[str, float] = {}
        self._pending_alerts: List[Dict] = []
        self._last_batch_time: float = 0

    def should_alert(self, anomaly: Dict) -> bool:
        """Check if anomaly meets severity threshold."""
        severity = anomaly.get("severity", "medium").lower()
        min_level = self.SEVERITY_LEVELS.get(self.min_severity, 2)
        anomaly_level = self.SEVERITY_LEVELS.get(severity, 2)
        return anomaly_level >= min_level

    def is_rate_limited(self, anomaly_type: str) -> bool:
        """Check if we've alerted on this type recently."""
        import time
        last_time = self._last_alert_times.get(anomaly_type, 0)
        return (time.time() - last_time) < self.rate_limit_seconds

    def send_alert(self, anomaly: Dict, context: Optional[Dict] = None) -> bool:
        """
        Send anomaly alert to Slack.

        Args:
            anomaly: Anomaly dict from InsAIts
            context: Optional additional context (message, session info)

        Returns:
            True if alert was sent, False if filtered/rate-limited
        """
        if not self.should_alert(anomaly):
            return False

        anomaly_type = anomaly.get("type", "UNKNOWN")
        if self.is_rate_limited(anomaly_type):
            logger.debug(f"Rate limited: {anomaly_type}")
            return False

        # Build Slack message
        message = self._build_message(anomaly, context)

        try:
            response = requests.post(
                self.webhook_url,
                json=message,
                timeout=10
            )

            if response.status_code == 200:
                import time
                self._last_alert_times[anomaly_type] = time.time()
                logger.info(f"Slack alert sent: {anomaly_type}")
                return True
            else:
                logger.error(f"Slack webhook failed: {response.status_code}")
                return False

        except requests.exceptions.RequestException as e:
            logger.error(f"Slack alert failed: {e}")
            return False

    def _build_message(self, anomaly: Dict, context: Optional[Dict] = None) -> Dict:
        """Build Slack message payload."""
        anomaly_type = anomaly.get("type", "UNKNOWN")
        severity = anomaly.get("severity", "medium").upper()
        details = anomaly.get("details", {})

        # Color based on severity
        color_map = {
            "LOW": "#36a64f",      # Green
            "MEDIUM": "#ff9800",   # Orange
            "HIGH": "#f44336",     # Red
            "CRITICAL": "#9c27b0"  # Purple
        }
        color = color_map.get(severity, "#ff9800")

        # Build fields
        fields = [
            {
                "title": "Type",
                "value": anomaly_type.replace("_", " ").title(),
                "short": True
            },
            {
                "title": "Severity",
                "value": f":{self._severity_emoji(severity)}: {severity}",
                "short": True
            }
        ]

        # Add agent info if available
        if "agent_id" in anomaly:
            fields.append({
                "title": "Agent",
                "value": anomaly["agent_id"],
                "short": True
            })

        if "llm_id" in anomaly:
            fields.append({
                "title": "LLM",
                "value": anomaly["llm_id"],
                "short": True
            })

        # Add specific details based on anomaly type
        if anomaly_type == "CROSS_LLM_JARGON" and "new_terms" in details:
            fields.append({
                "title": "Unknown Terms",
                "value": ", ".join(details["new_terms"][:5]),
                "short": False
            })

        if anomaly_type == "SHORTHAND_EMERGENCE" and "compression_ratio" in details:
            fields.append({
                "title": "Compression Ratio",
                "value": f"{details['compression_ratio']:.1%}",
                "short": True
            })

        if anomaly_type == "ANCHOR_DRIFT" and "anchor_similarity" in details:
            fields.append({
                "title": "Anchor Similarity",
                "value": f"{details['anchor_similarity']:.1%}",
                "short": True
            })

        # Add context text if available
        text_preview = ""
        if context and "text" in context:
            text_preview = context["text"][:200]
            if len(context["text"]) > 200:
                text_preview += "..."

        attachment = {
            "color": color,
            "title": f"AI Anomaly Detected: {anomaly_type}",
            "fields": fields,
            "footer": "InsAIts Monitor",
            "ts": int(datetime.now().timestamp())
        }

        if text_preview:
            attachment["text"] = f"```{text_preview}```"

        message = {
            "username": self.username,
            "icon_emoji": self.icon_emoji,
            "attachments": [attachment]
        }

        if self.channel:
            message["channel"] = self.channel

        return message

    def _severity_emoji(self, severity: str) -> str:
        """Get emoji for severity level."""
        emoji_map = {
            "LOW": "large_green_circle",
            "MEDIUM": "large_orange_circle",
            "HIGH": "red_circle",
            "CRITICAL": "rotating_light"
        }
        return emoji_map.get(severity.upper(), "warning")

    def send_batch_alert(self, anomalies: List[Dict], context: Optional[Dict] = None) -> bool:
        """
        Send batch alert for multiple anomalies.

        Args:
            anomalies: List of anomaly dicts
            context: Optional shared context

        Returns:
            True if alert sent
        """
        if not anomalies:
            return False

        # Filter by severity
        filtered = [a for a in anomalies if self.should_alert(a)]
        if not filtered:
            return False

        # Group by type
        by_type: Dict[str, List[Dict]] = {}
        for a in filtered:
            atype = a.get("type", "UNKNOWN")
            if atype not in by_type:
                by_type[atype] = []
            by_type[atype].append(a)

        # Build summary message
        fields = []
        for atype, items in by_type.items():
            severities = [i.get("severity", "medium").upper() for i in items]
            max_severity = max(severities, key=lambda s: self.SEVERITY_LEVELS.get(s.lower(), 2))
            fields.append({
                "title": atype.replace("_", " ").title(),
                "value": f"{len(items)} occurrences (max: {max_severity})",
                "short": True
            })

        message = {
            "username": self.username,
            "icon_emoji": self.icon_emoji,
            "attachments": [{
                "color": "#f44336",
                "title": f"AI Anomaly Summary: {len(filtered)} Issues Detected",
                "fields": fields,
                "footer": "InsAIts Monitor",
                "ts": int(datetime.now().timestamp())
            }]
        }

        if self.channel:
            message["channel"] = self.channel

        try:
            response = requests.post(self.webhook_url, json=message, timeout=10)
            return response.status_code == 200
        except requests.exceptions.RequestException as e:
            logger.error(f"Batch alert failed: {e}")
            return False

    def send_health_report(self, health: Dict) -> bool:
        """
        Send health report summary to Slack.

        Args:
            health: Health dict from monitor.get_stats() or analyze_crew_health()

        Returns:
            True if sent successfully
        """
        overall = health.get("overall_health", "unknown")
        anomaly_count = health.get("anomaly_count", 0)
        total_messages = health.get("total_messages", 0)

        color_map = {
            "good": "#36a64f",
            "warning": "#ff9800",
            "poor": "#f44336"
        }
        color = color_map.get(overall, "#9e9e9e")

        emoji_map = {
            "good": ":white_check_mark:",
            "warning": ":warning:",
            "poor": ":x:"
        }
        emoji = emoji_map.get(overall, ":question:")

        fields = [
            {"title": "Status", "value": f"{emoji} {overall.upper()}", "short": True},
            {"title": "Messages", "value": str(total_messages), "short": True},
            {"title": "Anomalies", "value": str(anomaly_count), "short": True},
        ]

        if "anomaly_rate" in health:
            fields.append({
                "title": "Anomaly Rate",
                "value": f"{health['anomaly_rate']:.1%}",
                "short": True
            })

        recommendations = health.get("recommendations", [])
        if recommendations:
            fields.append({
                "title": "Recommendations",
                "value": "\n".join(f"• {r}" for r in recommendations[:3]),
                "short": False
            })

        message = {
            "username": self.username,
            "icon_emoji": self.icon_emoji,
            "attachments": [{
                "color": color,
                "title": "AI Agent Health Report",
                "fields": fields,
                "footer": "InsAIts Monitor",
                "ts": int(datetime.now().timestamp())
            }]
        }

        if self.channel:
            message["channel"] = self.channel

        try:
            response = requests.post(self.webhook_url, json=message, timeout=10)
            return response.status_code == 200
        except requests.exceptions.RequestException as e:
            logger.error(f"Health report failed: {e}")
            return False


def slack_monitored(
    api_key: Optional[str] = None,
    webhook_url: str = "",
    channel: Optional[str] = None,
    min_severity: str = "medium",
    **monitor_kwargs
):
    """
    Create an InsAIts monitor with Slack alerts enabled.

    Args:
        api_key: InsAIts API key
        webhook_url: Slack webhook URL
        channel: Slack channel override
        min_severity: Minimum severity to alert
        **monitor_kwargs: Additional args for insAItsMonitor

    Returns:
        Tuple of (monitor, slack_notifier)

    Example:
        monitor, slack = slack_monitored(
            api_key="your-key",
            webhook_url="https://hooks.slack.com/...",
            min_severity="high"
        )

        # Monitor will auto-alert on anomalies
        result = monitor.send_message("Process order", "agent1", llm_id="gpt-4")
    """
    from ..monitor import insAItsMonitor

    monitor = insAItsMonitor(api_key=api_key, **monitor_kwargs)
    slack = SlackNotifier(
        webhook_url=webhook_url,
        channel=channel,
        min_severity=min_severity
    )

    # Store original send_message
    original_send = monitor.send_message

    def monitored_send(*args, **kwargs):
        result = original_send(*args, **kwargs)

        # Alert on anomalies
        if result.get("anomalies"):
            for anomaly in result["anomalies"]:
                slack.send_alert(anomaly, context=result.get("message"))

        return result

    monitor.send_message = monitored_send
    monitor._slack_notifier = slack

    return monitor, slack

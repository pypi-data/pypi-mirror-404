"""
InsAIts Export Integrations
===========================
Export anomalies and conversation logs to external services.

Supported exports:
- Notion: Create pages in a database
- Airtable: Add records to a base
- Webhook: Send to any HTTP endpoint
- CSV/JSON: Local file exports

Usage:
    from insa_its.integrations import NotionExporter, AirtableExporter

    # Export to Notion
    notion = NotionExporter(token="secret_...", database_id="...")
    notion.export_anomalies(monitor.get_stats()["anomalies"])

    # Export to Airtable
    airtable = AirtableExporter(api_key="pat...", base_id="app...", table_name="Anomalies")
    airtable.export_anomalies(anomalies)
"""

import logging
import requests
import json
import csv
from typing import Optional, Dict, Any, List
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class NotionExporter:
    """
    Export InsAIts data to Notion databases.

    Creates pages in a Notion database for:
    - Individual anomalies
    - Session summaries
    - Health reports

    Setup:
    1. Create a Notion integration at https://www.notion.so/my-integrations
    2. Share your database with the integration
    3. Get the database ID from the database URL

    Example:
        notion = NotionExporter(
            token="secret_xxx",
            database_id="abc123..."
        )
        notion.export_anomaly(anomaly)
    """

    API_URL = "https://api.notion.com/v1"
    API_VERSION = "2022-06-28"

    def __init__(
        self,
        token: str,
        database_id: str,
        page_icon: str = "🤖"
    ):
        """
        Initialize Notion exporter.

        Args:
            token: Notion integration token (secret_xxx)
            database_id: Target database ID
            page_icon: Default emoji icon for pages
        """
        self.token = token
        self.database_id = database_id
        self.page_icon = page_icon

        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Notion-Version": self.API_VERSION
        }

    def export_anomaly(self, anomaly: Dict, context: Optional[Dict] = None) -> Optional[str]:
        """
        Export single anomaly to Notion.

        Args:
            anomaly: Anomaly dict from InsAIts
            context: Optional additional context

        Returns:
            Page ID if successful, None otherwise
        """
        anomaly_type = anomaly.get("type", "UNKNOWN")
        severity = anomaly.get("severity", "medium").upper()
        agent_id = anomaly.get("agent_id", "unknown")
        llm_id = anomaly.get("llm_id", "unknown")
        details = anomaly.get("details", {})

        # Build properties based on your database schema
        properties = {
            "Name": {
                "title": [{"text": {"content": f"{anomaly_type} - {agent_id}"}}]
            },
            "Type": {
                "select": {"name": anomaly_type}
            },
            "Severity": {
                "select": {"name": severity}
            },
            "Agent": {
                "rich_text": [{"text": {"content": agent_id}}]
            },
            "LLM": {
                "rich_text": [{"text": {"content": llm_id}}]
            },
            "Timestamp": {
                "date": {"start": datetime.now().isoformat()}
            }
        }

        # Build page content
        children = [
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"text": {"content": "Anomaly Details"}}]
                }
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"text": {"content": f"Type: {anomaly_type}"}}]
                }
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"text": {"content": f"Severity: {severity}"}}]
                }
            }
        ]

        # Add details as code block
        if details:
            children.append({
                "object": "block",
                "type": "code",
                "code": {
                    "rich_text": [{"text": {"content": json.dumps(details, indent=2)}}],
                    "language": "json"
                }
            })

        # Add context if available
        if context and "text" in context:
            children.extend([
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"text": {"content": "Message Context"}}]
                    }
                },
                {
                    "object": "block",
                    "type": "quote",
                    "quote": {
                        "rich_text": [{"text": {"content": context["text"][:2000]}}]
                    }
                }
            ])

        payload = {
            "parent": {"database_id": self.database_id},
            "icon": {"type": "emoji", "emoji": self._severity_emoji(severity)},
            "properties": properties,
            "children": children
        }

        try:
            response = requests.post(
                f"{self.API_URL}/pages",
                headers=self.headers,
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                page_id = response.json().get("id")
                logger.info(f"Notion page created: {page_id}")
                return page_id
            else:
                logger.error(f"Notion export failed: {response.status_code} - {response.text}")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"Notion export error: {e}")
            return None

    def export_anomalies(self, anomalies: List[Dict]) -> List[str]:
        """
        Export multiple anomalies to Notion.

        Args:
            anomalies: List of anomaly dicts

        Returns:
            List of created page IDs
        """
        page_ids = []
        for anomaly in anomalies:
            page_id = self.export_anomaly(anomaly)
            if page_id:
                page_ids.append(page_id)
        return page_ids

    def export_session_summary(self, stats: Dict, session_name: str = "Session") -> Optional[str]:
        """
        Export session summary to Notion.

        Args:
            stats: Stats dict from monitor.get_stats()
            session_name: Name for the session

        Returns:
            Page ID if successful
        """
        total_messages = stats.get("total_messages", 0)
        anomaly_count = len(stats.get("anomalies", []))
        health = "Good" if anomaly_count < 5 else "Warning" if anomaly_count < 20 else "Poor"

        properties = {
            "Name": {
                "title": [{"text": {"content": f"{session_name} - {datetime.now().strftime('%Y-%m-%d %H:%M')}"}}]
            },
            "Type": {
                "select": {"name": "SESSION_SUMMARY"}
            },
            "Severity": {
                "select": {"name": health.upper()}
            }
        }

        children = [
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"text": {"content": "Session Statistics"}}]
                }
            },
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{"text": {"content": f"Total Messages: {total_messages}"}}]
                }
            },
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{"text": {"content": f"Anomalies Detected: {anomaly_count}"}}]
                }
            },
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{"text": {"content": f"Health Status: {health}"}}]
                }
            }
        ]

        payload = {
            "parent": {"database_id": self.database_id},
            "icon": {"type": "emoji", "emoji": self.page_icon},
            "properties": properties,
            "children": children
        }

        try:
            response = requests.post(
                f"{self.API_URL}/pages",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            if response.status_code == 200:
                return response.json().get("id")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Notion session export error: {e}")
            return None

    def _severity_emoji(self, severity: str) -> str:
        """Get emoji for severity."""
        emoji_map = {
            "LOW": "🟢",
            "MEDIUM": "🟡",
            "HIGH": "🔴",
            "CRITICAL": "🚨"
        }
        return emoji_map.get(severity.upper(), "⚠️")


class AirtableExporter:
    """
    Export InsAIts data to Airtable bases.

    Creates records in an Airtable table for anomalies and session data.

    Setup:
    1. Create a Personal Access Token at https://airtable.com/create/tokens
    2. Create a base with a table for anomalies
    3. Get base ID from the URL (starts with 'app')

    Example:
        airtable = AirtableExporter(
            api_key="patXXX",
            base_id="appXXX",
            table_name="Anomalies"
        )
        airtable.export_anomaly(anomaly)
    """

    API_URL = "https://api.airtable.com/v0"

    def __init__(
        self,
        api_key: str,
        base_id: str,
        table_name: str = "Anomalies"
    ):
        """
        Initialize Airtable exporter.

        Args:
            api_key: Airtable Personal Access Token
            base_id: Airtable base ID (appXXX)
            table_name: Target table name
        """
        self.api_key = api_key
        self.base_id = base_id
        self.table_name = table_name

        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    def export_anomaly(self, anomaly: Dict, context: Optional[Dict] = None) -> Optional[str]:
        """
        Export single anomaly to Airtable.

        Args:
            anomaly: Anomaly dict from InsAIts
            context: Optional additional context

        Returns:
            Record ID if successful
        """
        fields = {
            "Type": anomaly.get("type", "UNKNOWN"),
            "Severity": anomaly.get("severity", "medium").upper(),
            "Agent": anomaly.get("agent_id", "unknown"),
            "LLM": anomaly.get("llm_id", "unknown"),
            "Timestamp": datetime.now().isoformat(),
            "Details": json.dumps(anomaly.get("details", {}))
        }

        if context and "text" in context:
            fields["Message"] = context["text"][:10000]  # Airtable limit

        payload = {"fields": fields}

        try:
            response = requests.post(
                f"{self.API_URL}/{self.base_id}/{self.table_name}",
                headers=self.headers,
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                record_id = response.json().get("id")
                logger.info(f"Airtable record created: {record_id}")
                return record_id
            else:
                logger.error(f"Airtable export failed: {response.status_code} - {response.text}")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"Airtable export error: {e}")
            return None

    def export_anomalies(self, anomalies: List[Dict]) -> List[str]:
        """
        Export multiple anomalies to Airtable.

        Airtable allows batch creation of up to 10 records at once.

        Args:
            anomalies: List of anomaly dicts

        Returns:
            List of created record IDs
        """
        record_ids = []

        # Batch in groups of 10
        for i in range(0, len(anomalies), 10):
            batch = anomalies[i:i + 10]
            records = []

            for anomaly in batch:
                records.append({
                    "fields": {
                        "Type": anomaly.get("type", "UNKNOWN"),
                        "Severity": anomaly.get("severity", "medium").upper(),
                        "Agent": anomaly.get("agent_id", "unknown"),
                        "LLM": anomaly.get("llm_id", "unknown"),
                        "Timestamp": datetime.now().isoformat(),
                        "Details": json.dumps(anomaly.get("details", {}))
                    }
                })

            payload = {"records": records}

            try:
                response = requests.post(
                    f"{self.API_URL}/{self.base_id}/{self.table_name}",
                    headers=self.headers,
                    json=payload,
                    timeout=30
                )

                if response.status_code == 200:
                    for record in response.json().get("records", []):
                        record_ids.append(record.get("id"))

            except requests.exceptions.RequestException as e:
                logger.error(f"Airtable batch export error: {e}")

        return record_ids


class WebhookExporter:
    """
    Export InsAIts data to any HTTP webhook endpoint.

    Generic webhook exporter that can send anomalies and stats
    to any service that accepts JSON POST requests.

    Example:
        webhook = WebhookExporter(
            url="https://your-api.com/anomalies",
            headers={"X-API-Key": "your-key"}
        )
        webhook.export_anomaly(anomaly)
    """

    def __init__(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        method: str = "POST",
        timeout: int = 30
    ):
        """
        Initialize webhook exporter.

        Args:
            url: Webhook endpoint URL
            headers: Optional custom headers
            method: HTTP method (POST, PUT)
            timeout: Request timeout in seconds
        """
        self.url = url
        self.headers = headers or {}
        self.headers.setdefault("Content-Type", "application/json")
        self.method = method.upper()
        self.timeout = timeout

    def export_anomaly(self, anomaly: Dict, context: Optional[Dict] = None) -> bool:
        """
        Export anomaly to webhook.

        Args:
            anomaly: Anomaly dict
            context: Optional context

        Returns:
            True if successful
        """
        payload = {
            "event": "anomaly_detected",
            "timestamp": datetime.now().isoformat(),
            "anomaly": anomaly,
            "context": context
        }

        return self._send(payload)

    def export_stats(self, stats: Dict) -> bool:
        """Export stats to webhook."""
        payload = {
            "event": "stats_update",
            "timestamp": datetime.now().isoformat(),
            "stats": stats
        }
        return self._send(payload)

    def _send(self, payload: Dict) -> bool:
        """Send payload to webhook."""
        try:
            if self.method == "POST":
                response = requests.post(
                    self.url,
                    headers=self.headers,
                    json=payload,
                    timeout=self.timeout
                )
            else:
                response = requests.put(
                    self.url,
                    headers=self.headers,
                    json=payload,
                    timeout=self.timeout
                )

            return response.status_code in (200, 201, 202, 204)

        except requests.exceptions.RequestException as e:
            logger.error(f"Webhook export error: {e}")
            return False


class FileExporter:
    """
    Export InsAIts data to local files.

    Supports CSV and JSON formats for anomalies and conversation logs.

    Example:
        exporter = FileExporter(output_dir="./logs")
        exporter.export_anomalies_csv(anomalies, "anomalies.csv")
        exporter.export_conversation_json(messages, "conversation.json")
    """

    def __init__(self, output_dir: str = "."):
        """
        Initialize file exporter.

        Args:
            output_dir: Directory for output files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export_anomalies_csv(self, anomalies: List[Dict], filename: str = "anomalies.csv") -> str:
        """
        Export anomalies to CSV.

        Args:
            anomalies: List of anomaly dicts
            filename: Output filename

        Returns:
            Full path to created file
        """
        filepath = self.output_dir / filename

        fieldnames = ["timestamp", "type", "severity", "agent_id", "llm_id", "details"]

        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for anomaly in anomalies:
                writer.writerow({
                    "timestamp": anomaly.get("timestamp", datetime.now().isoformat()),
                    "type": anomaly.get("type", ""),
                    "severity": anomaly.get("severity", ""),
                    "agent_id": anomaly.get("agent_id", ""),
                    "llm_id": anomaly.get("llm_id", ""),
                    "details": json.dumps(anomaly.get("details", {}))
                })

        logger.info(f"Exported {len(anomalies)} anomalies to {filepath}")
        return str(filepath)

    def export_anomalies_json(self, anomalies: List[Dict], filename: str = "anomalies.json") -> str:
        """
        Export anomalies to JSON.

        Args:
            anomalies: List of anomaly dicts
            filename: Output filename

        Returns:
            Full path to created file
        """
        filepath = self.output_dir / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump({
                "exported_at": datetime.now().isoformat(),
                "count": len(anomalies),
                "anomalies": anomalies
            }, f, indent=2, default=str)

        logger.info(f"Exported {len(anomalies)} anomalies to {filepath}")
        return str(filepath)

    def export_conversation_json(self, messages: List[Dict], filename: str = "conversation.json") -> str:
        """
        Export conversation history to JSON.

        Args:
            messages: List of message dicts
            filename: Output filename

        Returns:
            Full path to created file
        """
        filepath = self.output_dir / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump({
                "exported_at": datetime.now().isoformat(),
                "message_count": len(messages),
                "messages": messages
            }, f, indent=2, default=str)

        logger.info(f"Exported {len(messages)} messages to {filepath}")
        return str(filepath)

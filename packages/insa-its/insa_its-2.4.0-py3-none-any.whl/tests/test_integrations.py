"""
Tests for InsAIts Integrations
==============================
Tests for Slack, Notion, Airtable, LangGraph, and enhanced CrewAI integrations.
"""

import pytest
import json
import os
import time
from unittest.mock import Mock, patch, MagicMock

# Test with dev mode
os.environ["INSAITS_DEV_MODE"] = "true"

# Import integrations
from insa_its.integrations import (
    SlackNotifier,
    slack_monitored,
    NotionExporter,
    AirtableExporter,
    WebhookExporter,
    FileExporter,
)
from insa_its import insAItsMonitor


# ============================================
# SLACK NOTIFIER TESTS
# ============================================

class TestSlackNotifier:
    """Tests for Slack integration"""

    def test_slack_notifier_init(self):
        """Test SlackNotifier initialization"""
        slack = SlackNotifier(
            webhook_url="https://hooks.slack.com/test",
            channel="#test",
            min_severity="high"
        )
        assert slack.webhook_url == "https://hooks.slack.com/test"
        assert slack.channel == "#test"
        assert slack.min_severity == "high"

    def test_should_alert_severity_filtering(self):
        """Test severity threshold filtering"""
        slack = SlackNotifier(
            webhook_url="https://test.com",
            min_severity="high"
        )

        # Low severity should not alert
        assert slack.should_alert({"severity": "low"}) == False
        assert slack.should_alert({"severity": "medium"}) == False

        # High+ should alert
        assert slack.should_alert({"severity": "high"}) == True
        assert slack.should_alert({"severity": "critical"}) == True

    def test_should_alert_medium_threshold(self):
        """Test medium severity threshold"""
        slack = SlackNotifier(
            webhook_url="https://test.com",
            min_severity="medium"
        )

        assert slack.should_alert({"severity": "low"}) == False
        assert slack.should_alert({"severity": "medium"}) == True
        assert slack.should_alert({"severity": "high"}) == True

    def test_rate_limiting(self):
        """Test rate limiting logic"""
        slack = SlackNotifier(
            webhook_url="https://test.com",
            rate_limit_seconds=60
        )

        # Initially not rate limited
        assert slack.is_rate_limited("JARGON") == False

        # Simulate alert sent
        slack._last_alert_times["JARGON"] = time.time()

        # Should now be rate limited
        assert slack.is_rate_limited("JARGON") == True

        # Different type not rate limited
        assert slack.is_rate_limited("SHORTHAND") == False

    def test_build_message_structure(self):
        """Test Slack message building"""
        slack = SlackNotifier(
            webhook_url="https://test.com",
            channel="#alerts"
        )

        anomaly = {
            "type": "CROSS_LLM_JARGON",
            "severity": "high",
            "agent_id": "test_agent",
            "llm_id": "gpt-4",
            "details": {"new_terms": ["XYZQ", "ABCD"]}
        }

        message = slack._build_message(anomaly)

        assert message["channel"] == "#alerts"
        assert message["username"] == "InsAIts Monitor"
        assert "attachments" in message
        assert len(message["attachments"]) == 1

    @patch('requests.post')
    def test_send_alert_success(self, mock_post):
        """Test successful alert sending"""
        mock_post.return_value = Mock(status_code=200)

        slack = SlackNotifier(webhook_url="https://test.com")
        anomaly = {"type": "JARGON", "severity": "high"}

        result = slack.send_alert(anomaly)

        assert result == True
        mock_post.assert_called_once()

    @patch('requests.post')
    def test_send_alert_filtered_by_severity(self, mock_post):
        """Test alert filtered by severity"""
        slack = SlackNotifier(
            webhook_url="https://test.com",
            min_severity="high"
        )
        anomaly = {"type": "JARGON", "severity": "low"}

        result = slack.send_alert(anomaly)

        assert result == False
        mock_post.assert_not_called()

    @patch('requests.post')
    def test_send_health_report(self, mock_post):
        """Test health report sending"""
        mock_post.return_value = Mock(status_code=200)

        slack = SlackNotifier(webhook_url="https://test.com")
        health = {
            "overall_health": "warning",
            "anomaly_count": 5,
            "total_messages": 100,
            "anomaly_rate": 0.05,
            "recommendations": ["Check agent prompts"]
        }

        result = slack.send_health_report(health)

        assert result == True
        mock_post.assert_called_once()


class TestSlackMonitored:
    """Tests for slack_monitored convenience function"""

    @patch('requests.post')
    def test_slack_monitored_creates_monitor(self, mock_post):
        """Test slack_monitored creates monitor with alerts"""
        monitor, slack = slack_monitored(
            api_key="test-key",
            webhook_url="https://test.com",
            min_severity="medium"
        )

        assert monitor is not None
        assert slack is not None
        assert hasattr(monitor, '_slack_notifier')


# ============================================
# NOTION EXPORTER TESTS
# ============================================

class TestNotionExporter:
    """Tests for Notion export integration"""

    def test_notion_exporter_init(self):
        """Test NotionExporter initialization"""
        notion = NotionExporter(
            token="secret_xxx",
            database_id="db_123"
        )
        assert notion.token == "secret_xxx"
        assert notion.database_id == "db_123"
        assert "Authorization" in notion.headers

    def test_severity_emoji_mapping(self):
        """Test severity to emoji mapping"""
        notion = NotionExporter(token="x", database_id="y")

        assert notion._severity_emoji("LOW") == "🟢"
        assert notion._severity_emoji("MEDIUM") == "🟡"
        assert notion._severity_emoji("HIGH") == "🔴"
        assert notion._severity_emoji("CRITICAL") == "🚨"

    @patch('requests.post')
    def test_export_anomaly_success(self, mock_post):
        """Test successful anomaly export"""
        mock_post.return_value = Mock(
            status_code=200,
            json=lambda: {"id": "page_123"}
        )

        notion = NotionExporter(token="secret_x", database_id="db_y")
        anomaly = {
            "type": "JARGON",
            "severity": "high",
            "agent_id": "test",
            "llm_id": "gpt-4",
            "details": {"new_terms": ["X"]}
        }

        page_id = notion.export_anomaly(anomaly)

        assert page_id == "page_123"
        mock_post.assert_called_once()

    @patch('requests.post')
    def test_export_anomalies_batch(self, mock_post):
        """Test batch anomaly export"""
        mock_post.return_value = Mock(
            status_code=200,
            json=lambda: {"id": "page_x"}
        )

        notion = NotionExporter(token="x", database_id="y")
        anomalies = [
            {"type": "A", "severity": "high"},
            {"type": "B", "severity": "medium"}
        ]

        page_ids = notion.export_anomalies(anomalies)

        assert len(page_ids) == 2
        assert mock_post.call_count == 2


# ============================================
# AIRTABLE EXPORTER TESTS
# ============================================

class TestAirtableExporter:
    """Tests for Airtable export integration"""

    def test_airtable_exporter_init(self):
        """Test AirtableExporter initialization"""
        airtable = AirtableExporter(
            api_key="patXXX",
            base_id="appXXX",
            table_name="Anomalies"
        )
        assert airtable.api_key == "patXXX"
        assert airtable.base_id == "appXXX"
        assert airtable.table_name == "Anomalies"

    @patch('requests.post')
    def test_export_anomaly_success(self, mock_post):
        """Test successful anomaly export to Airtable"""
        mock_post.return_value = Mock(
            status_code=200,
            json=lambda: {"id": "rec123"}
        )

        airtable = AirtableExporter(
            api_key="pat",
            base_id="app",
            table_name="Test"
        )
        anomaly = {
            "type": "JARGON",
            "severity": "high",
            "agent_id": "test",
            "llm_id": "gpt-4"
        }

        record_id = airtable.export_anomaly(anomaly)

        assert record_id == "rec123"
        mock_post.assert_called_once()


# ============================================
# WEBHOOK EXPORTER TESTS
# ============================================

class TestWebhookExporter:
    """Tests for generic webhook export"""

    def test_webhook_exporter_init(self):
        """Test WebhookExporter initialization"""
        webhook = WebhookExporter(
            url="https://api.example.com/webhook",
            headers={"X-API-Key": "secret"}
        )
        assert webhook.url == "https://api.example.com/webhook"
        assert "X-API-Key" in webhook.headers

    @patch('requests.post')
    def test_export_anomaly(self, mock_post):
        """Test anomaly export via webhook"""
        mock_post.return_value = Mock(status_code=200)

        webhook = WebhookExporter(url="https://test.com")
        anomaly = {"type": "TEST", "severity": "high"}

        result = webhook.export_anomaly(anomaly)

        assert result == True
        call_args = mock_post.call_args
        payload = call_args.kwargs.get('json') or call_args[1].get('json')
        assert payload["event"] == "anomaly_detected"
        assert payload["anomaly"] == anomaly


# ============================================
# FILE EXPORTER TESTS
# ============================================

class TestFileExporter:
    """Tests for file export integration"""

    def test_file_exporter_init(self, tmp_path):
        """Test FileExporter initialization"""
        exporter = FileExporter(output_dir=str(tmp_path))
        assert exporter.output_dir.exists()

    def test_export_anomalies_csv(self, tmp_path):
        """Test CSV export"""
        exporter = FileExporter(output_dir=str(tmp_path))
        anomalies = [
            {"type": "A", "severity": "high", "agent_id": "x", "llm_id": "y", "details": {}},
            {"type": "B", "severity": "low", "agent_id": "z", "llm_id": "w", "details": {}}
        ]

        filepath = exporter.export_anomalies_csv(anomalies)

        assert os.path.exists(filepath)
        with open(filepath, 'r') as f:
            content = f.read()
            assert "type" in content
            assert "A" in content
            assert "B" in content

    def test_export_anomalies_json(self, tmp_path):
        """Test JSON export"""
        exporter = FileExporter(output_dir=str(tmp_path))
        anomalies = [{"type": "TEST", "severity": "high"}]

        filepath = exporter.export_anomalies_json(anomalies)

        assert os.path.exists(filepath)
        with open(filepath, 'r') as f:
            data = json.load(f)
            assert data["count"] == 1
            assert data["anomalies"][0]["type"] == "TEST"

    def test_export_conversation_json(self, tmp_path):
        """Test conversation export"""
        exporter = FileExporter(output_dir=str(tmp_path))
        messages = [
            {"sender": "a", "text": "hello"},
            {"sender": "b", "text": "world"}
        ]

        filepath = exporter.export_conversation_json(messages)

        assert os.path.exists(filepath)
        with open(filepath, 'r') as f:
            data = json.load(f)
            assert data["message_count"] == 2


# ============================================
# CREWAI CALLBACK TESTS
# ============================================

class TestCrewAICallbacks:
    """Tests for enhanced CrewAI callbacks"""

    def test_crewai_imports(self):
        """Test CrewAI monitor can be imported"""
        from insa_its.integrations import CrewAIMonitor
        assert CrewAIMonitor is not None

    def test_callback_registration(self):
        """Test callback registration methods exist"""
        from insa_its.integrations.crewai import CrewAIMonitor, CREWAI_AVAILABLE

        if not CREWAI_AVAILABLE:
            pytest.skip("CrewAI not installed")

        # Check the class has the callback methods
        import inspect
        members = dict(inspect.getmembers(CrewAIMonitor))
        assert 'on_anomaly' in members
        assert 'on_task_complete' in members


# ============================================
# LANGGRAPH INTEGRATION TESTS
# ============================================

class TestLangGraphIntegration:
    """Tests for LangGraph integration"""

    def test_langgraph_imports(self):
        """Test LangGraph monitor can be imported"""
        from insa_its.integrations import LANGGRAPH_AVAILABLE
        # Should be importable regardless of whether langgraph is installed
        assert LANGGRAPH_AVAILABLE in (True, False)

    def test_langgraph_monitor_class_exists(self):
        """Test LangGraphMonitor class exists"""
        from insa_its.integrations import LangGraphMonitor
        # May be None if langgraph not installed
        if LangGraphMonitor is not None:
            assert hasattr(LangGraphMonitor, 'wrap_graph')
            assert hasattr(LangGraphMonitor, 'get_anomalies')
            assert hasattr(LangGraphMonitor, 'get_node_stats')


# ============================================
# INTEGRATION IMPORTS TEST
# ============================================

class TestIntegrationImports:
    """Test all integrations can be imported"""

    def test_all_exports_importable(self):
        """Test all exports from integrations module"""
        from insa_its.integrations import (
            LangChainMonitor,
            monitor_langchain_chain,
            CrewAIMonitor,
            monitor_crew,
            SlackNotifier,
            slack_monitored,
            NotionExporter,
            AirtableExporter,
            WebhookExporter,
            FileExporter,
        )

        # All should be non-None classes/functions
        assert LangChainMonitor is not None
        assert monitor_langchain_chain is not None
        assert CrewAIMonitor is not None
        assert monitor_crew is not None
        assert SlackNotifier is not None
        assert slack_monitored is not None
        assert NotionExporter is not None
        assert AirtableExporter is not None
        assert WebhookExporter is not None
        assert FileExporter is not None


# ============================================
# RUN TESTS
# ============================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

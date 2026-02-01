"""
InsAIts Integrations
====================
Native integrations for popular AI frameworks and services.

Framework Integrations:
- LangChain: LangChainMonitor, monitor_langchain_chain
- LangGraph: LangGraphMonitor, monitor_langgraph
- CrewAI: CrewAIMonitor, monitor_crew

Notification Integrations:
- Slack: SlackNotifier, slack_monitored

Export Integrations:
- Notion: NotionExporter
- Airtable: AirtableExporter
- Webhook: WebhookExporter
- File: FileExporter

Usage:
    from insa_its.integrations import LangChainMonitor, SlackNotifier, NotionExporter
"""

# Framework integrations
from .langchain import LangChainMonitor, monitor_langchain_chain
from .crewai import CrewAIMonitor, monitor_crew

# LangGraph (optional - requires langgraph package)
try:
    from .langgraph import LangGraphMonitor, monitor_langgraph
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    LangGraphMonitor = None
    monitor_langgraph = None

# Notification integrations
from .slack import SlackNotifier, slack_monitored

# Export integrations
from .exports import (
    NotionExporter,
    AirtableExporter,
    WebhookExporter,
    FileExporter,
)

__all__ = [
    # LangChain
    'LangChainMonitor',
    'monitor_langchain_chain',
    # LangGraph
    'LangGraphMonitor',
    'monitor_langgraph',
    'LANGGRAPH_AVAILABLE',
    # CrewAI
    'CrewAIMonitor',
    'monitor_crew',
    # Slack
    'SlackNotifier',
    'slack_monitored',
    # Exports
    'NotionExporter',
    'AirtableExporter',
    'WebhookExporter',
    'FileExporter',
]

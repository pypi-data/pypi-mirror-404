# InsAIts - Making Multi-Agent AI Trustworthy

**Monitor what your AI agents are saying to each other.**

[![PyPI version](https://badge.fury.io/py/insa-its.svg)](https://pypi.org/project/insa-its/)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

---

## The Problem

When AI agents communicate with each other, strange things happen:
- **Shorthand emergence** - "Verify customer identity" becomes "Run CVP"
- **Context loss** - Agents suddenly switch topics mid-conversation
- **Jargon creation** - Made-up acronyms that mean nothing to humans
- **Hallucination chains** - One agent's error propagates through the system
- **Anchor drift** - Responses diverge from the user's original question

**In AI-to-human communication, we notice. In AI-to-AI? It's invisible.**

---

## The Solution

InsAIts is a lightweight Python SDK that monitors AI-to-AI communication in real-time.

```python
from insa_its import insAItsMonitor

monitor = insAItsMonitor()

# V2: Set anchor for context-aware detection
monitor.set_anchor("What is quantum computing?")

# Monitor any AI-to-AI message
result = monitor.send_message(
    text=agent_response,
    sender_id="OrderBot",
    receiver_id="InventoryBot",
    llm_id="gpt-4"
)

if result["anomalies"]:
    # V2: Trace the root cause
    for anomaly in result["anomalies"]:
        trace = monitor.trace_root(anomaly)
        print(trace["summary"])
```

**3 lines of code. Full visibility.**

---

## Open-Core Model (V2.4)

InsAIts uses an **open-core model**: the core SDK is **Apache 2.0 open source**, while premium features ship with `pip install insa-its`.

| Feature | License | Status |
|---------|---------|--------|
| Anomaly detection (fingerprint mismatch, low confidence) | Apache 2.0 | Open |
| Hallucination detection (all 5 subsystems) | Apache 2.0 | Open |
| Forensic chain tracing + visualization | Apache 2.0 | Open |
| Terminal dashboard | Apache 2.0 | Open |
| All integrations (LangChain, CrewAI, LangGraph, Slack, Notion, Airtable) | Apache 2.0 | Open |
| Local embeddings + cloud embeddings | Apache 2.0 | Open |
| Ollama integration + model selection | Apache 2.0 | Open |
| Trend analysis + session health scoring | Apache 2.0 | Open |
| Adaptive jargon dictionaries + domain dictionaries | Proprietary | Premium |
| Advanced shorthand/context-loss detection | Proprietary | Premium |
| Automated decipher engine (cloud + local) | Proprietary | Premium |
| Anchor drift forensics + false-positive suppression | Proprietary | Premium |

**Both open-source and premium features are included when you `pip install insa-its`.**
The public GitHub repo contains the Apache 2.0 open-source core only.

---

## What's New in V2.4

### Open-Core Architecture -- NEW
Apache 2.0 open-source core with proprietary premium features. See the table above for what's open vs premium.

### Ollama Model Selection -- NEW
Choose your preferred local LLM model:

```python
from insa_its import insAItsMonitor

# Use any Ollama model
monitor = insAItsMonitor(ollama_model="phi3")  # or "mistral", "llama3.2", etc.

# Or set globally
from insa_its import set_default_model
set_default_model("mistral")
```

### Hallucination Detection (Phase 3)

Detect when AI agents fabricate facts, contradict each other, or invent citations:

```python
monitor = insAItsMonitor(api_key="your-key")

# Enable cross-agent fact tracking
monitor.enable_fact_tracking(True)

# Agent A says one thing...
monitor.send_message("The project costs 1000 dollars.", "agent_a", llm_id="gpt-4o")

# Agent B contradicts it --> FACT_CONTRADICTION detected
result = monitor.send_message("The project costs 5000 dollars.", "agent_b", llm_id="claude-3.5")
# result["anomalies"] = [{"type": "FACT_CONTRADICTION", "severity": "critical", ...}]

# Detect fabricated citations
citations = monitor.detect_phantom_citations(
    "According to Smith et al. (2030), see https://fake-journal.xyz/paper"
)
# citations["verdict"] = "likely_fabricated"

# Source grounding -- verify responses against known documents
monitor.set_source_documents(["Your reference docs..."], auto_check=True)
result = monitor.check_grounding("AI response to verify")
# result["grounded"] = True/False, result["grounding_score"] = 0.85

# Confidence decay tracking
stats = monitor.get_confidence_stats(agent_id="agent_a")
# Detects when an agent goes from "certainly" to "maybe" to "I'm not sure"

# Full hallucination health report
summary = monitor.get_hallucination_summary()
# {"hallucination_health": {"score": 85, "status": "good"}, "by_type": {...}}
```

**Five hallucination detection subsystems:**
| Subsystem | What It Catches |
|-----------|----------------|
| **Fact Tracking** | Cross-agent contradictions, numeric drift |
| **Phantom Citation Detection** | Fabricated URLs, DOIs, arxiv IDs, paper references |
| **Source Grounding** | Responses that diverge from reference documents |
| **Confidence Decay** | Agents losing certainty over a conversation |
| **Self-Consistency** | Internal contradictions within a single response |

### Anchor-Aware Detection (Phase 1)
Stop false positives by setting the user's query as an anchor:

```python
# Set user's question as anchor
monitor.set_anchor("Explain quantum computing")

# Responses using "QUBIT", "QPU" won't trigger jargon alerts
# because they're relevant to the query
result = monitor.send_message("Quantum computers use qubits...", "agent1", llm_id="gpt-4o")
```

### Forensic Chain Tracing (Phase 2)
Trace any anomaly back to its root cause:

```python
trace = monitor.trace_root(anomaly)
print(trace["summary"])
# "Jargon 'XYZTERM' first appeared in message from agent_a (gpt-4o)
#  at step 3 of 7. Propagated through 4 subsequent messages."

# ASCII visualization
print(monitor.visualize_chain(anomaly, include_text=True))
```

### Domain Dictionaries (Phase 4)
Load domain-specific terms to reduce false positives:

```python
# Load finance terms (EBITDA, WACC, DCF, etc.)
monitor.load_domain("finance")

# Available domains: finance, healthcare, kubernetes, machine_learning, devops, quantum

# Import/export custom dictionaries
monitor.export_dictionary("my_team_terms.json")
monitor.import_dictionary("shared_terms.json", merge=True)

# Auto-expand unknown terms with LLM
monitor.auto_expand_terms()  # Requires Ollama
```

---

## What It Detects

| Anomaly Type | What It Catches | Severity |
|--------------|-----------------|----------|
| **SHORTHAND_EMERGENCE** | "Process order" -> "PO now" | High |
| **CONTEXT_LOSS** | Marketing meeting -> Recipe discussion | High |
| **CROSS_LLM_JARGON** | Undefined acronyms like "QXRT" | High |
| **ANCHOR_DRIFT** | Response diverges from user's question | High |
| **FACT_CONTRADICTION** | Agent A says 1000, Agent B says 5000 | Critical |
| **PHANTOM_CITATION** | Fabricated URLs, DOIs, arxiv IDs | High |
| **UNGROUNDED_CLAIM** | Response doesn't match source documents | Medium |
| **CONFIDENCE_DECAY** | Agent certainty erodes over conversation | Medium |
| **CONFIDENCE_FLIP_FLOP** | Agent alternates certain/uncertain | Medium |
| **LLM_FINGERPRINT_MISMATCH** | GPT-4 response that looks like GPT-3.5 | Medium |
| **LOW_CONFIDENCE** | Hedging: "maybe", "I think", "perhaps" | Medium |

---

## Quick Start

### Install

```bash
pip install insa-its
```

For local embeddings (recommended):
```bash
pip install insa-its[full]
```

Or from GitHub:
```bash
pip install git+https://github.com/Nomadu27/InsAIts.git
```

### Use

```python
from insa_its import insAItsMonitor

monitor = insAItsMonitor(session_name="my-agents")

# V2: Set anchor for smarter detection
monitor.set_anchor("Process customer refund request")

# Monitor your agent conversations
result = monitor.send_message(
    text="Process the customer order for SKU-12345",
    sender_id="OrderBot",
    receiver_id="InventoryBot",
    llm_id="gpt-4o-mini"
)

# Check for issues
if result["anomalies"]:
    for anomaly in result["anomalies"]:
        print(f"[{anomaly['severity']}] {anomaly['type']}")
        # V2: Get forensic trace
        trace = monitor.trace_root(anomaly)
        print(f"Root cause: {trace['summary']}")

# Get session health
print(monitor.get_stats())
```

---

## Features

### Real-Time Terminal Dashboard

```python
from insa_its.dashboard import LiveDashboard

dashboard = LiveDashboard(monitor)
dashboard.start()
# Live visualization of all agent communication
```

### LangChain Integration

```python
from insa_its.integrations import LangChainMonitor

monitor = LangChainMonitor()
monitored_chain = monitor.wrap_chain(your_chain, "MyAgent")
```

### CrewAI Integration

```python
from insa_its.integrations import CrewAIMonitor

monitor = CrewAIMonitor()
monitored_crew = monitor.wrap_crew(your_crew)
```

### Decipher Mode (V2.1: Cloud + Local)

Translate AI-to-AI jargon for human review. Choose your mode:

```python
# Auto mode (default): Cloud first, fallback to local
deciphered = monitor.decipher(message)

# Cloud mode: Use cloud LLM (requires API key)
deciphered = monitor.decipher(message, mode="cloud")

# Local mode: Use Ollama only (privacy-first)
deciphered = monitor.decipher(message, mode="local")

print(deciphered["expanded_text"])  # Human-readable version
print(deciphered["mode"])  # "cloud" or "local"
```

**Modes:**
| Mode | Description | Requirements |
|------|-------------|--------------|
| `auto` | Cloud first, fallback to local | API key (optional) |
| `cloud` | Cloud LLM only | API key + Free tier or above |
| `local` | Local Ollama only | Ollama running locally |

**Cloud Decipher Limits:**
- Free: 20/day
- Starter: 500/day
- Pro: Unlimited

### V2: Domain Dictionaries

```python
# See available domains
print(monitor.get_available_domains())
# ['finance', 'healthcare', 'kubernetes', 'machine_learning', 'devops', 'quantum']

# Load one or more
monitor.load_domain("kubernetes")
monitor.load_domain("devops")

# Terms like K8S, HPA, CI/CD won't trigger false positives
```

### V2: Forensic Chain Visualization

```python
# Get ASCII visualization of anomaly chain
viz = monitor.visualize_chain(anomaly, include_text=True)
print(viz)

# Output:
# ============================================================
# FORENSIC CHAIN TRACE: CROSS_LLM_JARGON
# ============================================================
#
# [Step 1]
#   agent_a -> agent_b (gpt-4o)
#   Words: 15
#   Text: "Let's discuss the implementation..."
#      |
#      v
# [Step 2]
#   agent_b -> agent_a (claude-3.5)
#   Words: 20
#      |
#      v
# [Step 3] >>> ROOT <<< ANOMALY
#   agent_a -> agent_b (gpt-4o)
#   Words: 8
#   Text: "Use XYZPROTO for this..."
#
# ------------------------------------------------------------
# SUMMARY:
# Jargon 'XYZPROTO' first appeared in message from agent_a (gpt-4o)
# at step 3 of 3. Propagated through 0 subsequent messages.
# ============================================================
```

### V2.2: Ecosystem Integrations

**Slack Alerts:**
```python
from insa_its.integrations import SlackNotifier, slack_monitored

# Option 1: Auto-alerting monitor
monitor, slack = slack_monitored(
    api_key="your-key",
    webhook_url="https://hooks.slack.com/services/...",
    min_severity="high"  # Only alert on high+ severity
)

# Option 2: Manual integration
slack = SlackNotifier(webhook_url="https://hooks.slack.com/...")
slack.send_alert(anomaly)
slack.send_health_report(monitor.get_stats())
```

**Export to Notion/Airtable:**
```python
from insa_its.integrations import NotionExporter, AirtableExporter

# Notion
notion = NotionExporter(token="secret_xxx", database_id="db_123")
notion.export_anomalies(anomalies)

# Airtable
airtable = AirtableExporter(api_key="patXXX", base_id="appXXX", table_name="Anomalies")
airtable.export_anomalies(anomalies)
```

**LangGraph Integration:**
```python
from insa_its.integrations import LangGraphMonitor

monitor = LangGraphMonitor(api_key="your-key")
monitored_graph = monitor.wrap_graph(your_graph)
app = monitored_graph.compile()

result = app.invoke(initial_state)
print(monitor.get_node_stats())
print(monitor.analyze_graph_health())
```

**CrewAI Callbacks:**
```python
from insa_its.integrations import CrewAIMonitor

def on_anomaly(anomaly, context):
    slack.send_alert(anomaly, context)

monitor = CrewAIMonitor(api_key="your-key", on_anomaly=on_anomaly)
crew = monitor.wrap_crew(your_crew)
```

---

## Pricing

### Lifetime Deals - First 100 Users Only!

| Plan | Price | What You Get |
|------|-------|--------------|
| **LIFETIME STARTER** | **EUR99 one-time** | 10K msgs/day forever |
| **LIFETIME PRO** | **EUR299 one-time** | Unlimited forever + priority support |

**Buy Lifetime (Gumroad):**
- [**Lifetime Starter (EUR99)**](https://steddy.gumroad.com/l/InsAItsStarter)
- [**Lifetime Pro (EUR299)**](https://steddy.gumroad.com/l/InsAItsPro100)

**Buy Lifetime (Stripe):**
- [**Lifetime Starter (EUR99)**](https://buy.stripe.com/00w6oH87R77T32A56Eb3q00)
- [**Lifetime Pro (EUR299)**](https://buy.stripe.com/3cI8wPfAjak5bz61Ecb3q04)

---

### Monthly Plans

| Tier | Messages/Day | Price | Best For |
|------|-------------|-------|----------|
| **Free** | 100 | $0 | Testing & evaluation |
| **Starter** | 10,000 | **$49/mo** | Indie devs & small teams |
| **Pro** | Unlimited | **$79/mo** | Production workloads |

**Buy Monthly (Gumroad):**
- [**Monthly Starter ($49/mo)**](https://steddy.gumroad.com/l/InsAItsStarterTier)
- [**Monthly Pro ($79/mo)**](https://steddy.gumroad.com/l/InsAItsProTier)

> **Free tier works without an API key!** Just `pip install insa-its` and start monitoring.

---

## Use Cases

| Industry | Problem Solved |
|----------|----------------|
| **E-Commerce** | Order bots losing context mid-transaction |
| **Customer Service** | Support agents developing incomprehensible shorthand |
| **Finance** | Analysis pipelines hallucinating metrics |
| **Healthcare** | Critical multi-agent systems where errors matter |
| **Research** | Ensuring scientific integrity in AI experiments |

---

## Demo

Try it yourself:

```bash
git clone https://github.com/Nomadu27/InsAIts.git
cd InsAIts
pip install -e .[full] rich

# Run the dashboard demo
python demo_dashboard.py

# Run marketing team simulation
python demo_marketing_team.py
```

---

## Architecture

```
Your Multi-Agent System           InsAIts V2.4 (Apache 2.0)
         |                              |
         |-- user query --------------> |-- set_anchor()
         |-- source docs -------------> |-- set_source_documents()
         |                              |
         |-- message -----------------> |
         |                              |-- Anchor similarity check
         |                              |-- Semantic embedding (local)
         |                              |-- Pattern analysis
         |                              |-- Fact tracking + contradiction detection
         |                              |-- Phantom citation detection
         |                              |-- Source grounding check
         |                              |-- Confidence decay tracking
         |                              |-- Anomaly detection
         |                              |
         |<-- anomalies, health --------|
         |                              |
         |-- trace_root() ------------> |-- Forensic chain tracing
         |<-- summary, visualization ---|
         |                              |
         |-- get_hallucination_summary() |
         |<-- full health report -------|
```

**Privacy First:**
- All hallucination detection runs locally (nothing leaves your machine)
- Local embeddings for source grounding
- No raw messages stored in cloud
- API keys hashed before storage
- GDPR-ready

---

## Documentation

| Resource | Link |
|----------|------|
| Installation Guide | [installation_guide.md](installation_guide.md) |
| API Reference | [insaitsapi-production.up.railway.app/docs](https://insaitsapi-production.up.railway.app/docs) |
| Privacy Policy | [PRIVACY_POLICY.md](PRIVACY_POLICY.md) |
| Terms of Service | [TERMS_OF_SERVICE.md](TERMS_OF_SERVICE.md) |

---

## Support

- **Email:** info@yuyai.pro
- **GitHub Issues:** [Report a bug](https://github.com/Nomadu27/InsAIts/issues)
- **API Status:** [insaitsapi-production.up.railway.app](https://insaitsapi-production.up.railway.app)

---

## License

**Open-Core Model:**
- Core SDK: [Apache License 2.0](LICENSE) - free to use, modify, and distribute
- Premium features (`insa_its/premium/`): [Proprietary](LICENSE.premium) - included via `pip install insa-its`

Free tier available for evaluation (100 msgs/day, no API key needed).

---

<p align="center">
<strong>InsAIts V2.4 - Making AI Collaboration Trustworthy</strong><br>
<em>Open-source core (Apache 2.0). Hallucination Detection, Cross-Agent Contradiction Tracking, Phantom Citation Detection, Anchor-Aware Monitoring, Forensic Chain Tracing, and Domain Dictionaries.</em>
</p>

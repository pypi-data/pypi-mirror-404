"""
InsAIts LangGraph Integration
=============================
Monitor LangGraph graphs and stateful agent workflows.

LangGraph is LangChain's framework for building stateful, multi-actor
applications with cyclic computational capabilities.

Usage:
    from langgraph.graph import StateGraph
    from insa_its.integrations import LangGraphMonitor

    # Create your graph
    graph = StateGraph(MyState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node)
    ...

    # Wrap with InsAIts monitoring
    monitor = LangGraphMonitor(api_key="your-key")
    monitored_graph = monitor.wrap_graph(graph)

    # Compile and run
    app = monitored_graph.compile()
    result = app.invoke({"messages": [HumanMessage(content="Hello")]})

    # Check for anomalies
    print(monitor.get_anomalies())
    print(monitor.get_node_stats())
"""

import logging
from typing import Optional, Dict, Any, List, Callable, TypeVar
from functools import wraps
import time

logger = logging.getLogger(__name__)

# Try importing LangGraph
try:
    from langgraph.graph import StateGraph, END
    from langgraph.graph.state import CompiledStateGraph
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    StateGraph = None
    END = None


class LangGraphMonitor:
    """
    Monitor LangGraph graphs and agent workflows.

    Features:
    - Node execution monitoring
    - State transition tracking
    - Cycle detection
    - Inter-node communication analysis
    - Anomaly detection across the graph

    Example:
        monitor = LangGraphMonitor(api_key="your-key")
        monitored = monitor.wrap_graph(graph)
        app = monitored.compile()
        result = app.invoke(initial_state)
        print(monitor.get_anomalies())
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        session_name: Optional[str] = None,
        auto_prevent: bool = True,
        track_state: bool = True,
        **kwargs
    ):
        """
        Initialize LangGraph monitor.

        Args:
            api_key: InsAIts API key (optional, enables Pro features)
            session_name: Name for this monitoring session
            auto_prevent: Auto-prevent anomalies (Pro feature)
            track_state: Track full state at each node (may increase memory)
            **kwargs: Additional args passed to insAItsMonitor
        """
        if not LANGGRAPH_AVAILABLE:
            raise ImportError(
                "LangGraph not installed. Install with: pip install langgraph"
            )

        from ..monitor import insAItsMonitor

        self.insaits = insAItsMonitor(
            api_key=api_key,
            session_name=session_name or "langgraph_session",
            auto_prevent=auto_prevent,
            **kwargs
        )
        self.track_state = track_state
        self._anomalies: List[Dict] = []
        self._node_stats: Dict[str, Dict] = {}
        self._transitions: List[Dict] = []
        self._cycle_count: int = 0
        self._wrapped_graphs: List[Any] = []

    def wrap_graph(self, graph: Any) -> Any:
        """
        Wrap a LangGraph StateGraph with InsAIts monitoring.

        This patches node functions to capture inputs/outputs and
        track state transitions.

        Args:
            graph: LangGraph StateGraph instance

        Returns:
            The same graph with monitoring enabled
        """
        if not LANGGRAPH_AVAILABLE:
            raise ImportError("LangGraph not available")

        # Get all nodes
        nodes = getattr(graph, '_nodes', {}) or getattr(graph, 'nodes', {})

        for node_name, node_func in list(nodes.items()):
            if node_name in ("__start__", "__end__"):
                continue

            # Register node as agent
            self.insaits.register_agent(node_name, "langgraph_node")

            # Initialize stats
            self._node_stats[node_name] = {
                "executions": 0,
                "total_time": 0,
                "anomalies": 0,
                "last_output": None
            }

            # Wrap the node function
            monitored_func = self._create_monitored_node(node_name, node_func)

            # Replace in graph
            if hasattr(graph, '_nodes'):
                graph._nodes[node_name] = monitored_func
            elif hasattr(graph, 'nodes'):
                graph.nodes[node_name] = monitored_func

        self._wrapped_graphs.append(graph)
        return graph

    def _create_monitored_node(self, node_name: str, original_func: Callable) -> Callable:
        """Create a monitored wrapper for a node function."""
        monitor = self

        @wraps(original_func)
        def monitored_node(state: Any, *args, **kwargs):
            start_time = time.time()

            # Log node entry
            state_summary = monitor._summarize_state(state)
            monitor.insaits.send_message(
                text=f"[Node Entry] State: {state_summary}",
                sender_id="graph_controller",
                receiver_id=node_name,
                llm_id="langgraph"
            )

            # Execute node
            try:
                result = original_func(state, *args, **kwargs)
            except Exception as e:
                # Log error
                monitor.insaits.send_message(
                    text=f"[Node Error] {type(e).__name__}: {str(e)[:200]}",
                    sender_id=node_name,
                    receiver_id="graph_controller",
                    llm_id="langgraph"
                )
                raise

            elapsed = time.time() - start_time

            # Log node output
            output_text = monitor._extract_output_text(result)
            msg_result = monitor.insaits.send_message(
                text=output_text,
                sender_id=node_name,
                receiver_id="graph_controller",
                llm_id="langgraph"
            )

            # Track anomalies
            if msg_result.get("anomalies"):
                monitor._anomalies.extend(msg_result["anomalies"])
                monitor._node_stats[node_name]["anomalies"] += len(msg_result["anomalies"])

            # Update stats
            monitor._node_stats[node_name]["executions"] += 1
            monitor._node_stats[node_name]["total_time"] += elapsed
            monitor._node_stats[node_name]["last_output"] = output_text[:200]

            return result

        return monitored_node

    def _summarize_state(self, state: Any) -> str:
        """Create a summary of the state for logging."""
        if not self.track_state:
            return "[state tracking disabled]"

        try:
            if isinstance(state, dict):
                # Handle common LangGraph state patterns
                if "messages" in state:
                    msgs = state["messages"]
                    if msgs:
                        last_msg = msgs[-1]
                        content = getattr(last_msg, "content", str(last_msg))
                        return f"{len(msgs)} messages, last: {content[:100]}..."
                    return "0 messages"

                # Generic dict summary
                keys = list(state.keys())[:5]
                return f"keys: {keys}"

            return str(state)[:200]

        except Exception:
            return "[state summary error]"

    def _extract_output_text(self, result: Any) -> str:
        """Extract text content from node output."""
        try:
            if isinstance(result, dict):
                # Check for messages
                if "messages" in result:
                    msgs = result["messages"]
                    if msgs:
                        last_msg = msgs[-1] if isinstance(msgs, list) else msgs
                        content = getattr(last_msg, "content", str(last_msg))
                        return content[:500]

                # Check for common output keys
                for key in ["output", "response", "result", "content", "text"]:
                    if key in result:
                        return str(result[key])[:500]

                return str(result)[:500]

            if hasattr(result, "content"):
                return result.content[:500]

            return str(result)[:500]

        except Exception:
            return "[output extraction error]"

    def track_transition(self, from_node: str, to_node: str, condition: Optional[str] = None):
        """
        Manually track a state transition.

        Args:
            from_node: Source node name
            to_node: Target node name
            condition: Optional condition that triggered the transition
        """
        transition = {
            "from": from_node,
            "to": to_node,
            "condition": condition,
            "timestamp": time.time()
        }
        self._transitions.append(transition)

        # Detect cycles
        if self._detect_cycle(from_node, to_node):
            self._cycle_count += 1
            logger.warning(f"Cycle detected: {from_node} -> {to_node}")

    def _detect_cycle(self, from_node: str, to_node: str) -> bool:
        """Simple cycle detection based on recent transitions."""
        recent = self._transitions[-10:]
        path = [t["to"] for t in recent if t["from"] == to_node]
        return from_node in path

    def get_anomalies(self) -> List[Dict]:
        """Get all anomalies detected during graph execution."""
        return self._anomalies.copy()

    def get_node_stats(self) -> Dict[str, Dict]:
        """
        Get statistics for each node.

        Returns:
            Dict mapping node names to their stats (executions, time, anomalies)
        """
        stats = {}
        for node, data in self._node_stats.items():
            avg_time = data["total_time"] / max(data["executions"], 1)
            stats[node] = {
                "executions": data["executions"],
                "avg_time_seconds": round(avg_time, 3),
                "total_time_seconds": round(data["total_time"], 3),
                "anomalies": data["anomalies"],
                "last_output_preview": data.get("last_output", "")
            }
        return stats

    def get_transitions(self) -> List[Dict]:
        """Get all recorded state transitions."""
        return self._transitions.copy()

    def get_stats(self) -> Dict:
        """Get overall monitoring statistics."""
        base_stats = self.insaits.get_stats()
        return {
            **base_stats,
            "langgraph": {
                "node_count": len(self._node_stats),
                "total_node_executions": sum(n["executions"] for n in self._node_stats.values()),
                "transition_count": len(self._transitions),
                "cycle_count": self._cycle_count,
                "nodes": self.get_node_stats()
            }
        }

    def get_conversation(self, limit: int = 100) -> List[Dict]:
        """Get full conversation history."""
        return self.insaits.get_conversation(limit=limit)

    def analyze_graph_health(self) -> Dict:
        """
        Analyze overall health of graph execution.

        Returns:
            Health analysis with metrics and recommendations
        """
        total_anomalies = len(self._anomalies)
        total_executions = sum(n["executions"] for n in self._node_stats.values())
        anomaly_rate = total_anomalies / max(total_executions, 1)

        # Determine health
        if anomaly_rate < 0.1 and self._cycle_count < 3:
            health = "good"
        elif anomaly_rate < 0.3 and self._cycle_count < 10:
            health = "warning"
        else:
            health = "poor"

        # Find problematic nodes
        problematic_nodes = []
        for node, stats in self._node_stats.items():
            if stats["anomalies"] > 2:
                problematic_nodes.append({
                    "node": node,
                    "anomalies": stats["anomalies"],
                    "executions": stats["executions"]
                })

        # Generate recommendations
        recommendations = []
        if self._cycle_count > 5:
            recommendations.append("High cycle count - consider adding better termination conditions")
        if problematic_nodes:
            nodes = ", ".join(n["node"] for n in problematic_nodes[:3])
            recommendations.append(f"Nodes with high anomaly rates: {nodes}")

        return {
            "overall_health": health,
            "anomaly_count": total_anomalies,
            "anomaly_rate": round(anomaly_rate, 3),
            "total_executions": total_executions,
            "cycle_count": self._cycle_count,
            "problematic_nodes": problematic_nodes,
            "recommendations": recommendations
        }

    def export_log(self, filepath: str) -> str:
        """Export conversation log to file."""
        return self.insaits.export_conversation_log(filepath)

    def visualize_graph_flow(self) -> str:
        """
        Create ASCII visualization of graph flow based on transitions.

        Returns:
            ASCII art showing node connections
        """
        if not self._transitions:
            return "No transitions recorded yet."

        lines = ["Graph Flow Visualization", "=" * 40, ""]

        # Group transitions
        edges: Dict[str, List[str]] = {}
        for t in self._transitions:
            from_node = t["from"]
            to_node = t["to"]
            if from_node not in edges:
                edges[from_node] = []
            if to_node not in edges[from_node]:
                edges[from_node].append(to_node)

        # Build visualization
        for from_node, to_nodes in edges.items():
            stats = self._node_stats.get(from_node, {})
            exec_count = stats.get("executions", 0)
            anomaly_count = stats.get("anomalies", 0)

            status = "OK" if anomaly_count == 0 else f"!{anomaly_count}"
            lines.append(f"[{from_node}] ({exec_count}x) [{status}]")

            for i, to_node in enumerate(to_nodes):
                is_last = i == len(to_nodes) - 1
                connector = "└──>" if is_last else "├──>"
                lines.append(f"  {connector} {to_node}")

            lines.append("")

        return "\n".join(lines)


def monitor_langgraph(
    graph: Any,
    api_key: Optional[str] = None,
    session_name: Optional[str] = None
) -> tuple:
    """
    Convenience function to quickly monitor a LangGraph graph.

    Args:
        graph: LangGraph StateGraph to monitor
        api_key: Optional InsAIts API key
        session_name: Optional session name

    Returns:
        Tuple of (monitored_graph, monitor_instance)

    Example:
        graph, monitor = monitor_langgraph(my_graph, session_name="agent_workflow")
        app = graph.compile()
        result = app.invoke(initial_state)
        print(monitor.analyze_graph_health())
    """
    monitor = LangGraphMonitor(api_key=api_key, session_name=session_name)
    monitored = monitor.wrap_graph(graph)
    return monitored, monitor

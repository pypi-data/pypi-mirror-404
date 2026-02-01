"""
InsAIts LangChain Integration
=============================
Monitor LangChain chains, agents, and conversations automatically.

Usage:
    from langchain.chat_models import ChatOpenAI
    from langchain.chains import LLMChain
    from insa_its.integrations import LangChainMonitor

    # Create your chain
    llm = ChatOpenAI(model="gpt-4")
    chain = LLMChain(llm=llm, prompt=your_prompt)

    # Wrap with InsAIts monitoring
    monitor = LangChainMonitor(api_key="your-key")
    monitored_chain = monitor.wrap_chain(chain, agent_id="MyAgent")

    # Use normally - all messages are automatically monitored
    result = monitored_chain.run("input")

    # Check for anomalies
    print(monitor.get_anomalies())
"""

import logging
from typing import Optional, Dict, Any, List, Callable
from functools import wraps

logger = logging.getLogger(__name__)

# Try importing LangChain
try:
    from langchain.callbacks.base import BaseCallbackHandler
    from langchain.schema import LLMResult, BaseMessage, HumanMessage, AIMessage
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    BaseCallbackHandler = object  # Fallback for type hints


class InsAItsCallbackHandler(BaseCallbackHandler if LANGCHAIN_AVAILABLE else object):
    """
    LangChain callback handler that sends messages to InsAIts monitor.
    Automatically captures all LLM inputs and outputs.
    """

    def __init__(
        self,
        insaits_monitor,
        agent_id: str = "langchain_agent",
        llm_id: str = "unknown"
    ):
        if LANGCHAIN_AVAILABLE:
            super().__init__()
        self.monitor = insaits_monitor
        self.agent_id = agent_id
        self.llm_id = llm_id
        self._current_prompt: Optional[str] = None
        self._anomalies: List[Dict] = []

    def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs):
        """Called when LLM starts processing."""
        # Extract LLM name from serialized data
        llm_name = serialized.get("name", serialized.get("id", ["unknown"]))[-1]
        if isinstance(llm_name, str):
            self.llm_id = llm_name.lower().replace("chat", "").replace("openai", "gpt-4")

        # Store prompt for context
        if prompts:
            self._current_prompt = prompts[0]

    def on_llm_end(self, response: Any, **kwargs):
        """Called when LLM finishes - capture the output."""
        if not LANGCHAIN_AVAILABLE:
            return

        try:
            # Extract text from response
            if hasattr(response, 'generations') and response.generations:
                for gen_list in response.generations:
                    for gen in gen_list:
                        text = gen.text if hasattr(gen, 'text') else str(gen)

                        # Send to InsAIts
                        result = self.monitor.send_message(
                            text=text,
                            sender_id=self.agent_id,
                            receiver_id=f"{self.agent_id}_output",
                            llm_id=self.llm_id
                        )

                        # Track anomalies
                        if result.get("anomalies"):
                            self._anomalies.extend(result["anomalies"])

        except Exception as e:
            logger.warning(f"InsAIts callback error: {e}")

    def on_chain_start(self, serialized: Dict[str, Any], inputs: Dict[str, Any], **kwargs):
        """Called when a chain starts."""
        chain_name = serialized.get("name", "chain")

        # Log input
        input_text = str(inputs.get("input", inputs.get("query", inputs)))
        if len(input_text) > 500:
            input_text = input_text[:500] + "..."

        self.monitor.send_message(
            text=f"[Chain Input] {input_text}",
            sender_id="user",
            receiver_id=self.agent_id,
            llm_id="human"
        )

    def on_agent_action(self, action: Any, **kwargs):
        """Called when an agent takes an action."""
        tool = getattr(action, 'tool', 'unknown_tool')
        tool_input = getattr(action, 'tool_input', '')

        self.monitor.send_message(
            text=f"[Tool: {tool}] {tool_input}",
            sender_id=self.agent_id,
            receiver_id=f"{tool}_tool",
            llm_id=self.llm_id
        )

    def on_tool_end(self, output: str, **kwargs):
        """Called when a tool finishes."""
        self.monitor.send_message(
            text=f"[Tool Output] {output[:500]}",
            sender_id="tool",
            receiver_id=self.agent_id,
            llm_id="tool"
        )

    def get_anomalies(self) -> List[Dict]:
        """Get all anomalies detected during this session."""
        return self._anomalies.copy()

    def clear_anomalies(self):
        """Clear the anomaly list."""
        self._anomalies.clear()


class LangChainMonitor:
    """
    Main class for monitoring LangChain chains and agents.

    Example:
        monitor = LangChainMonitor(api_key="your-key")

        # Wrap a chain
        monitored = monitor.wrap_chain(your_chain, "OrderBot")
        result = monitored.run("process order")

        # Check health
        print(monitor.get_stats())
        print(monitor.get_anomalies())
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        session_name: Optional[str] = None,
        auto_prevent: bool = True,
        **kwargs
    ):
        """
        Initialize LangChain monitor.

        Args:
            api_key: InsAIts API key (optional, enables Pro features)
            session_name: Name for this monitoring session
            auto_prevent: Auto-prevent anomalies (Pro feature)
            **kwargs: Additional args passed to insAItsMonitor
        """
        if not LANGCHAIN_AVAILABLE:
            raise ImportError(
                "LangChain not installed. Install with: pip install langchain"
            )

        # Import here to avoid circular imports
        from ..monitor import insAItsMonitor

        self.insaits = insAItsMonitor(
            api_key=api_key,
            session_name=session_name or "langchain_session",
            auto_prevent=auto_prevent,
            **kwargs
        )
        self._callbacks: List[InsAItsCallbackHandler] = []

    def create_callback(
        self,
        agent_id: str = "langchain_agent",
        llm_id: str = "auto"
    ) -> InsAItsCallbackHandler:
        """
        Create a callback handler to attach to LangChain components.

        Args:
            agent_id: Identifier for this agent
            llm_id: LLM model identifier (or "auto" to detect)

        Returns:
            InsAItsCallbackHandler to pass to LangChain
        """
        callback = InsAItsCallbackHandler(
            insaits_monitor=self.insaits,
            agent_id=agent_id,
            llm_id=llm_id
        )
        self._callbacks.append(callback)
        return callback

    def wrap_chain(self, chain: Any, agent_id: str = "chain_agent") -> Any:
        """
        Wrap a LangChain chain with InsAIts monitoring.

        Args:
            chain: LangChain chain to wrap
            agent_id: Identifier for this agent

        Returns:
            The same chain with monitoring callbacks attached
        """
        callback = self.create_callback(agent_id=agent_id)

        # Add callback to chain
        if hasattr(chain, 'callbacks'):
            if chain.callbacks is None:
                chain.callbacks = [callback]
            else:
                chain.callbacks.append(callback)
        else:
            logger.warning("Chain doesn't support callbacks, monitoring may be limited")

        return chain

    def wrap_llm(self, llm: Any, agent_id: str = "llm_agent") -> Any:
        """
        Wrap a LangChain LLM with InsAIts monitoring.

        Args:
            llm: LangChain LLM to wrap
            agent_id: Identifier for this agent

        Returns:
            The same LLM with monitoring callbacks attached
        """
        callback = self.create_callback(agent_id=agent_id)

        if hasattr(llm, 'callbacks'):
            if llm.callbacks is None:
                llm.callbacks = [callback]
            else:
                llm.callbacks.append(callback)

        return llm

    def get_anomalies(self) -> List[Dict]:
        """Get all anomalies from all monitored components."""
        all_anomalies = []
        for callback in self._callbacks:
            all_anomalies.extend(callback.get_anomalies())
        return all_anomalies

    def get_stats(self) -> Dict:
        """Get monitoring statistics."""
        return self.insaits.get_stats()

    def get_conversation(self, limit: int = 50) -> List[Dict]:
        """Get conversation history."""
        return self.insaits.get_conversation(limit=limit)

    def export_log(self, filepath: str) -> str:
        """Export conversation log to file."""
        return self.insaits.export_conversation_log(filepath)


def monitor_langchain_chain(
    chain: Any,
    agent_id: str = "monitored_chain",
    api_key: Optional[str] = None
) -> tuple:
    """
    Convenience function to quickly monitor a LangChain chain.

    Args:
        chain: LangChain chain to monitor
        agent_id: Identifier for the agent
        api_key: Optional InsAIts API key

    Returns:
        Tuple of (monitored_chain, monitor_instance)

    Example:
        chain, monitor = monitor_langchain_chain(my_chain, "OrderBot")
        result = chain.run("input")
        print(monitor.get_anomalies())
    """
    monitor = LangChainMonitor(api_key=api_key)
    monitored = monitor.wrap_chain(chain, agent_id)
    return monitored, monitor

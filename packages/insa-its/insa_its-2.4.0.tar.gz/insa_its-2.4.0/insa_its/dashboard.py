"""
InsAIts Terminal Dashboard
==========================
Real-time monitoring visualization using Rich library.

Usage:
    from insa_its import insAItsMonitor
    from insa_its.dashboard import LiveDashboard

    monitor = insAItsMonitor()
    dashboard = LiveDashboard(monitor)
    dashboard.start()

    # Your agent code here...
    monitor.send_message(...)

    dashboard.stop()
"""

import threading
import time
from typing import Optional, List, Dict
from datetime import datetime

# Try to import rich
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.layout import Layout
    from rich.live import Live
    from rich.text import Text
    from rich.style import Style
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


class LiveDashboard:
    """
    Real-time terminal dashboard for InsAIts monitoring.

    Features:
    - Live stats (agents, messages, anomalies, health)
    - Recent message feed
    - Anomaly alerts with highlighting
    - Conversation health indicators
    """

    def __init__(self, monitor, refresh_rate: float = 0.5):
        """
        Initialize the dashboard.

        Args:
            monitor: insAItsMonitor instance to visualize
            refresh_rate: How often to refresh display (seconds)
        """
        if not RICH_AVAILABLE:
            raise ImportError(
                "Rich library required for dashboard. Install with: pip install rich"
            )

        self.monitor = monitor
        self.refresh_rate = refresh_rate
        self.console = Console()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._recent_anomalies: List[Dict] = []
        self._max_anomalies = 10
        self._start_time = time.time()

    def _build_header(self) -> Panel:
        """Build the header panel with stats."""
        stats = self.monitor.get_stats()

        # Calculate runtime
        runtime = time.time() - self._start_time
        runtime_str = f"{int(runtime // 60)}m {int(runtime % 60)}s"

        # Calculate health
        all_discussions = self.monitor.get_all_discussions()
        if all_discussions:
            health_scores = [d.get('health', 'unknown') for d in all_discussions]
            good = health_scores.count('good')
            warning = health_scores.count('warning')
            poor = health_scores.count('poor')
            total = len(health_scores)
            health_pct = int((good * 100 + warning * 50) / max(total, 1))
            health_color = "green" if health_pct > 70 else "yellow" if health_pct > 40 else "red"
        else:
            health_pct = 100
            health_color = "green"

        # Build stats line
        agents = len(stats.get('agents', []))
        messages = stats.get('total_messages', 0)
        anomalies = len(self._recent_anomalies)
        tier = stats.get('tier', 'free').upper()

        header_text = Text()
        header_text.append("  AGENTS: ", style="bold")
        header_text.append(f"{agents}", style="cyan bold")
        header_text.append("  |  MESSAGES: ", style="bold")
        header_text.append(f"{messages}", style="cyan bold")
        header_text.append("  |  ANOMALIES: ", style="bold")
        header_text.append(f"{anomalies}", style="red bold" if anomalies > 0 else "green bold")
        header_text.append("  |  HEALTH: ", style="bold")
        header_text.append(f"{health_pct}%", style=f"{health_color} bold")
        header_text.append("  |  RUNTIME: ", style="bold")
        header_text.append(f"{runtime_str}", style="dim")
        header_text.append(f"  |  {tier}", style="magenta bold")

        return Panel(
            header_text,
            title="[bold blue]InsAIts Live Monitor[/bold blue]",
            border_style="blue",
            box=box.DOUBLE
        )

    def _build_messages_table(self) -> Table:
        """Build the recent messages table."""
        table = Table(
            title="Recent Messages",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold cyan"
        )

        table.add_column("Time", style="dim", width=8)
        table.add_column("From", style="green", width=15)
        table.add_column("To", style="yellow", width=15)
        table.add_column("LLM", style="magenta", width=12)
        table.add_column("Message", style="white", max_width=50)

        # Get recent messages
        messages = self.monitor.get_conversation(limit=8)

        for msg in messages[-8:]:
            time_str = msg.get('time_formatted', '??:??:??')
            sender = msg.get('sender', 'unknown')[:14]
            receiver = msg.get('receiver', '-')
            if receiver:
                receiver = receiver[:14]
            else:
                receiver = "-"
            llm = msg.get('llm_id', 'unknown')[:11]
            text = msg.get('text', '')[:48]
            if len(msg.get('text', '')) > 48:
                text += "..."

            table.add_row(time_str, sender, receiver, llm, text)

        return table

    def _build_anomalies_panel(self) -> Panel:
        """Build the anomalies alert panel."""
        if not self._recent_anomalies:
            content = Text("No anomalies detected", style="green")
        else:
            content = Text()
            for i, anomaly in enumerate(self._recent_anomalies[-5:]):
                anom_type = anomaly.get('type', 'UNKNOWN')
                severity = anomaly.get('severity', 'medium')
                agent = anomaly.get('agent_id', 'unknown')

                # Color by severity
                if severity == 'high':
                    style = "bold red"
                    icon = "[!]"
                elif severity == 'medium':
                    style = "yellow"
                    icon = "[~]"
                else:
                    style = "dim"
                    icon = "[.]"

                content.append(f"{icon} ", style=style)
                content.append(f"{anom_type}", style=style)
                content.append(f" - {agent}\n", style="dim")

        return Panel(
            content,
            title="[bold red]Anomaly Alerts[/bold red]",
            border_style="red" if self._recent_anomalies else "green",
            box=box.ROUNDED
        )

    def _build_agents_panel(self) -> Panel:
        """Build the agents status panel."""
        stats = self.monitor.get_stats()
        agents = stats.get('agents', [])

        content = Text()
        for agent in agents[:10]:
            # Get agent's message count
            agent_hist = self.monitor.history.get(agent, {})
            msg_count = sum(len(msgs) for msgs in agent_hist.values())

            content.append(f"  {agent}", style="cyan")
            content.append(f" ({msg_count} msgs)\n", style="dim")

        if not agents:
            content = Text("  No agents registered yet", style="dim")

        return Panel(
            content,
            title="[bold cyan]Active Agents[/bold cyan]",
            border_style="cyan",
            box=box.ROUNDED
        )

    def _build_layout(self) -> Layout:
        """Build the full dashboard layout."""
        layout = Layout()

        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body", ratio=1),
            Layout(name="footer", size=8)
        )

        layout["body"].split_row(
            Layout(name="messages", ratio=2),
            Layout(name="sidebar", ratio=1)
        )

        layout["sidebar"].split_column(
            Layout(name="agents", ratio=1),
            Layout(name="anomalies", ratio=1)
        )

        # Populate layout
        layout["header"].update(self._build_header())
        layout["messages"].update(self._build_messages_table())
        layout["agents"].update(self._build_agents_panel())
        layout["anomalies"].update(self._build_anomalies_panel())

        # Footer with instructions
        footer_text = Text()
        footer_text.append("  Press ", style="dim")
        footer_text.append("Ctrl+C", style="bold yellow")
        footer_text.append(" to stop monitoring  |  ", style="dim")
        footer_text.append("InsAIts", style="bold blue")
        footer_text.append(" - Making AI Collaboration Trustworthy", style="dim")

        layout["footer"].update(Panel(
            footer_text,
            border_style="dim",
            box=box.MINIMAL
        ))

        return layout

    def add_anomaly(self, anomaly: Dict):
        """Add an anomaly to the display."""
        self._recent_anomalies.append(anomaly)
        if len(self._recent_anomalies) > self._max_anomalies:
            self._recent_anomalies.pop(0)

    def start(self):
        """Start the live dashboard in background thread."""
        self._running = True
        self._start_time = time.time()
        self._thread = threading.Thread(target=self._run_live, daemon=True)
        self._thread.start()
        self.console.print("[green]Dashboard started. Monitoring...[/green]")

    def _run_live(self):
        """Run the live display loop."""
        with Live(
            self._build_layout(),
            console=self.console,
            refresh_per_second=1/self.refresh_rate,
            screen=True
        ) as live:
            while self._running:
                live.update(self._build_layout())
                time.sleep(self.refresh_rate)

    def stop(self):
        """Stop the dashboard."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
        self.console.print("\n[yellow]Dashboard stopped.[/yellow]")

    def run_blocking(self):
        """Run the dashboard in blocking mode (foreground)."""
        self._running = True
        self._start_time = time.time()

        try:
            with Live(
                self._build_layout(),
                console=self.console,
                refresh_per_second=1/self.refresh_rate,
                screen=True
            ) as live:
                while self._running:
                    live.update(self._build_layout())
                    time.sleep(self.refresh_rate)
        except KeyboardInterrupt:
            self._running = False
            self.console.print("\n[yellow]Dashboard stopped by user.[/yellow]")


class SimpleDashboard:
    """
    Simple non-live dashboard for environments without full terminal support.
    Prints status updates at intervals.
    """

    def __init__(self, monitor, interval: float = 5.0):
        self.monitor = monitor
        self.interval = interval
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def _print_status(self):
        """Print current status."""
        stats = self.monitor.get_stats()
        timestamp = datetime.now().strftime("%H:%M:%S")

        print(f"\n{'='*60}")
        print(f"[{timestamp}] InsAIts Status")
        print(f"{'='*60}")
        print(f"  Agents: {len(stats.get('agents', []))}")
        print(f"  Messages: {stats.get('total_messages', 0)}")
        print(f"  Tier: {stats.get('tier', 'free')}")

        # Recent messages
        messages = self.monitor.get_conversation(limit=3)
        if messages:
            print(f"\n  Recent messages:")
            for msg in messages:
                sender = msg.get('sender', '?')
                text = msg.get('text', '')[:40]
                print(f"    - {sender}: {text}...")

        print(f"{'='*60}")

    def start(self):
        """Start printing status updates."""
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def _run_loop(self):
        while self._running:
            self._print_status()
            time.sleep(self.interval)

    def stop(self):
        """Stop the simple dashboard."""
        self._running = False


def create_dashboard(monitor, live: bool = True, **kwargs):
    """
    Factory function to create appropriate dashboard.

    Args:
        monitor: insAItsMonitor instance
        live: If True, use LiveDashboard (requires rich). If False, use SimpleDashboard.
        **kwargs: Additional arguments for dashboard

    Returns:
        Dashboard instance
    """
    if live and RICH_AVAILABLE:
        return LiveDashboard(monitor, **kwargs)
    else:
        if live and not RICH_AVAILABLE:
            print("Warning: rich library not available, using simple dashboard")
        return SimpleDashboard(monitor, **kwargs)

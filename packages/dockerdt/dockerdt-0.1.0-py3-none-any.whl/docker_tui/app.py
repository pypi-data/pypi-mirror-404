"""Main TUI application for Docker TUI."""

import argparse
import sys

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import Header, Footer, Static, DataTable, Log, Button, Label, Input
from textual.binding import Binding
from textual.reactive import reactive
from textual import work
from rich.text import Text
from rich.console import Console
from rich.panel import Panel
from rich.table import Table as RichTable
from rich.columns import Columns
from rich import box

from docker_tui import __version__
from docker_tui.docker_client import DockerClient, ContainerInfo


class CustomHeader(Static):
    """Custom header with simple design."""

    def render(self) -> str:
        """Render the custom header."""
        return f"[bold white]🐳 Docker TUI[/bold white] [green]v{__version__}[/green] [dim]| Container Management Dashboard[/dim]"


class ContainerTable(DataTable):
    """Table showing containers."""

    BINDINGS = [
        Binding("enter", "select_container", "Select"),
    ]


class StatusBar(Static):
    """Status bar showing Docker connection status."""

    def __init__(self, connected: bool = False):
        super().__init__()
        self.connected = connected

    def compose(self) -> ComposeResult:
        if self.connected:
            yield Static("[bold green]● Docker Connected[/]", id="docker-status")
        else:
            yield Static("[bold red]● Docker Not Connected[/]", id="docker-status")


class DockerDashboard(App):
    """Docker TUI TUI Application."""

    CSS = """
    Screen {
        background: $surface;
    }

    CustomHeader {
        dock: top;
        height: 1;
        content-align: center middle;
        background: $panel;
    }

    #main-container {
        height: 100%;
        width: 100%;
    }

    #left-panel {
        width: 50%;
        height: 100%;
        border: solid $primary;
        padding: 0 1;
    }

    #right-panel {
        width: 50%;
        height: 100%;
        border: solid $secondary;
        padding: 0 1;
    }

    #container-table {
        height: 100%;
    }

    #logs-container {
        height: 100%;
    }

    #logs-title {
        height: 3;
        content-align: center middle;
        text-style: bold;
    }

    #logs-view {
        height: 1fr;
        border: solid $accent;
        padding: 0 1;
    }

    #action-bar {
        height: 3;
        dock: bottom;
        padding: 0 1;
        background: $panel;
    }

    .action-button {
        margin: 0 1;
        min-width: 12;
    }

    #status-bar {
        height: 1;
        dock: bottom;
        background: $panel;
        padding: 0 1;
    }

    #filter-input {
        width: 30;
        margin: 0 1;
    }

    .running {
        color: $success;
    }

    .stopped {
        color: $error;
    }

    .paused {
        color: $warning;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
        Binding("s", "start", "Start"),
        Binding("x", "stop", "Stop"),
        Binding("t", "restart", "Restart"),
        Binding("d", "delete", "Delete"),
        Binding("l", "logs", "Logs"),
        Binding("/", "filter", "Filter"),
        Binding("?", "help", "Help"),
    ]

    selected_container: reactive[str | None] = reactive(None)
    filter_text: reactive[str] = reactive("")

    def __init__(self):
        super().__init__()
        self.docker = DockerClient()
        self.containers: list[ContainerInfo] = []

    def compose(self) -> ComposeResult:
        yield CustomHeader()

        with Horizontal(id="main-container"):
            with Vertical(id="left-panel"):
                yield Label("[bold]Containers[/]", id="containers-title")
                yield ContainerTable(id="container-table")

            with Vertical(id="right-panel"):
                yield Label("[bold]Logs[/]", id="logs-title")
                yield Log(id="logs-view", highlight=True)

        with Horizontal(id="action-bar"):
            yield Button("Start [s]", id="btn-start", variant="success", classes="action-button")
            yield Button("Stop [x]", id="btn-stop", variant="error", classes="action-button")
            yield Button("Restart [t]", id="btn-restart", variant="warning", classes="action-button")
            yield Button("Delete [d]", id="btn-delete", variant="error", classes="action-button")
            yield Button("Refresh [r]", id="btn-refresh", variant="primary", classes="action-button")
            yield Input(placeholder="Filter...", id="filter-input")

        yield Footer()

    def on_mount(self) -> None:
        """Called when app is mounted."""

        table = self.query_one("#container-table", DataTable)
        table.add_columns("Name", "Image", "Status", "CPU", "Memory", "Ports")
        table.cursor_type = "row"

        self.refresh_containers()

    @work(thread=True)
    def refresh_containers(self) -> None:
        """Refresh container list."""
        self.containers = self.docker.list_containers(all=True)

        # Get stats for running containers
        for container in self.containers:
            if container.status == "running":
                stats = self.docker.get_container_stats(container.id)
                if stats:
                    container.cpu_percent = stats["cpu_percent"]
                    container.memory_usage = stats["memory_usage"]
                    container.memory_percent = stats["memory_percent"]

        self.call_from_thread(self.update_table)

    def update_table(self) -> None:
        """Update the container table."""
        table = self.query_one("#container-table", DataTable)
        table.clear()

        filter_text = self.filter_text.lower()

        for container in self.containers:
            # Apply filter
            if filter_text and filter_text not in container.name.lower():
                continue

            # Format status with color
            if container.status == "running":
                status = Text(f"● {container.status}", style="green")
            elif container.status == "exited":
                status = Text(f"○ {container.status}", style="red")
            else:
                status = Text(f"◐ {container.status}", style="yellow")

            # Format ports
            ports_str = self._format_ports(container.ports)

            # Format CPU/Memory
            if container.status == "running":
                cpu = f"{container.cpu_percent}%"
                mem = container.memory_usage
            else:
                cpu = "-"
                mem = "-"

            table.add_row(
                container.name,
                container.image[:30],
                status,
                cpu,
                mem,
                ports_str,
                key=container.id,
            )

    def _format_ports(self, ports: dict) -> str:
        """Format port mappings."""
        if not ports:
            return "-"

        port_list = []
        for container_port, host_bindings in ports.items():
            if host_bindings:
                for binding in host_bindings:
                    host_port = binding.get("HostPort", "")
                    port_list.append(f"{host_port}→{container_port.split('/')[0]}")

        return ", ".join(port_list[:2]) if port_list else "-"

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle row selection."""
        self.selected_container = event.row_key.value
        self.load_logs()

    @work(thread=True)
    def load_logs(self) -> None:
        """Load logs for selected container."""
        if not self.selected_container:
            return

        logs = self.docker.get_container_logs(self.selected_container, tail=100)
        self.call_from_thread(self.display_logs, logs)

    def display_logs(self, logs: str) -> None:
        """Display logs in the log view."""
        log_view = self.query_one("#logs-view", Log)
        log_view.clear()
        for line in logs.split("\n"):
            if line.strip():
                log_view.write_line(line)

    def action_refresh(self) -> None:
        """Refresh containers."""
        self.refresh_containers()
        self.notify("Refreshing containers...")

    def action_start(self) -> None:
        """Start selected container."""
        if not self.selected_container:
            self.notify("No container selected", severity="warning")
            return

        if self.docker.start_container(self.selected_container):
            self.notify("Container started successfully", severity="information")
            self.refresh_containers()
        else:
            self.notify("Container failed to start or exited immediately", severity="error")
            self.refresh_containers()

    def action_stop(self) -> None:
        """Stop selected container."""
        if not self.selected_container:
            self.notify("No container selected", severity="warning")
            return

        if self.docker.stop_container(self.selected_container):
            self.notify("Container stopped", severity="information")
            self.refresh_containers()
        else:
            self.notify("Failed to stop container", severity="error")

    def action_restart(self) -> None:
        """Restart selected container."""
        if not self.selected_container:
            self.notify("No container selected", severity="warning")
            return

        if self.docker.restart_container(self.selected_container):
            self.notify("Container restarted successfully", severity="information")
            self.refresh_containers()
        else:
            self.notify("Container failed to restart or exited immediately", severity="error")
            self.refresh_containers()

    def action_delete(self) -> None:
        """Delete selected container."""
        if not self.selected_container:
            self.notify("No container selected", severity="warning")
            return

        if self.docker.remove_container(self.selected_container, force=True):
            self.notify("Container deleted", severity="information")
            self.selected_container = None
            self.refresh_containers()
        else:
            self.notify("Failed to delete container", severity="error")

    def action_logs(self) -> None:
        """Show logs for selected container."""
        self.load_logs()

    def action_filter(self) -> None:
        """Focus filter input."""
        self.query_one("#filter-input", Input).focus()

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle filter input change."""
        if event.input.id == "filter-input":
            self.filter_text = event.value
            self.update_table()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        button_id = event.button.id

        if button_id == "btn-start":
            self.action_start()
        elif button_id == "btn-stop":
            self.action_stop()
        elif button_id == "btn-restart":
            self.action_restart()
        elif button_id == "btn-delete":
            self.action_delete()
        elif button_id == "btn-refresh":
            self.action_refresh()


def print_version():
    """Print version information with Rich formatting."""
    console = Console()

    version_panel = Panel(
        f"[bold white]🐳 Docker TUI[/bold white] [green]v{__version__}[/green]\n"
        f"[dim]A beautiful TUI for managing Docker containers[/dim]",
        border_style="cyan",
        box=box.DOUBLE,
        padding=(1, 2),
    )

    console.print()
    console.print(version_panel)
    console.print()


def print_help():
    """Print help information with Rich formatting."""
    console = Console()

    # Title
    console.print()
    console.print(Panel(
        "[bold white]🐳 Docker TUI[/bold white] [green]v{0}[/green]\n"
        "[dim]A beautiful TUI for managing Docker containers[/dim]".format(__version__),
        border_style="cyan",
        box=box.DOUBLE,
        padding=(1, 2),
    ))

    # Usage
    console.print("\n[bold yellow]USAGE[/bold yellow]")
    console.print("  [cyan]dt[/cyan] [dim]or[/dim] [cyan]docker-tui[/cyan]")

    # Options
    console.print("\n[bold yellow]OPTIONS[/bold yellow]")
    options_table = RichTable(show_header=False, box=None, padding=(0, 2))
    options_table.add_column(style="cyan", no_wrap=True)
    options_table.add_column(style="dim")
    options_table.add_row("-h, --help", "Show this help message")
    options_table.add_row("--version", "Show version information")
    console.print(options_table)

    # Keyboard shortcuts
    console.print("\n[bold yellow]KEYBOARD SHORTCUTS[/bold yellow]")
    shortcuts_table = RichTable(show_header=False, box=None, padding=(0, 2))
    shortcuts_table.add_column(style="green bold", no_wrap=True, width=8)
    shortcuts_table.add_column(style="white")

    shortcuts_table.add_row("r", "Refresh containers")
    shortcuts_table.add_row("s", "Start selected container")
    shortcuts_table.add_row("x", "Stop selected container")
    shortcuts_table.add_row("t", "Restart selected container")
    shortcuts_table.add_row("d", "Delete selected container")
    shortcuts_table.add_row("l", "Show logs for selected container")
    shortcuts_table.add_row("/", "Filter containers by name")
    shortcuts_table.add_row("q", "Quit application")
    shortcuts_table.add_row("?", "Show help overlay")

    console.print(shortcuts_table)

    # Features
    console.print("\n[bold yellow]FEATURES[/bold yellow]")
    features = [
        "View all containers (running/stopped)",
        "Real-time CPU and memory stats",
        "Container logs with live updates",
        "Start/Stop/Restart containers",
        "Delete containers",
        "Filter containers by name",
    ]
    for feature in features:
        console.print(f"  • {feature}")

    console.print()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        prog="docker-tui",
        description="A beautiful TUI for managing Docker containers",
        add_help=False,
    )
    parser.add_argument(
        "-h", "--help",
        action="store_true",
        help="Show help message"
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="Show version information"
    )

    args = parser.parse_args()

    if args.version:
        print_version()
        sys.exit(0)

    if args.help:
        print_help()
        sys.exit(0)

    app = DockerDashboard()
    app.run()


if __name__ == "__main__":
    main()

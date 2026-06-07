from textual.widgets import Static, Markdown, Button
from textual.containers import Vertical
from textual.app import ComposeResult
from rich.table import Table
from rich.text import Text
from PIL import Image
import io
import os

class AppLogo(Static):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
    def render(self) -> str:
        return (
            "[bold #0088ff]    _    [/bold #0088ff]\n"
            "[bold #0088ff]  /   \\  [/bold #0088ff]\n"
            "[bold #0088ff] |     | [/bold #0088ff]\n"
            "[bold #0088ff] _\\   /_ [/bold #0088ff]\n"
            " [b]OMEGA OS[/b]"
        )

class AgentStatusList(Static):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.agents = {
            "Action Engine": "Waiting",
            "Omega Creator": "Waiting",
            "Omega Think": "Waiting",
            "Vision Engine": "Waiting",
            "Memory DB": "Waiting"
        }
        self.border_title = "Agent Status"

    def render(self):
        table = Table(show_header=False, expand=True, box=None)
        table.add_column("Agent", style="cyan")
        table.add_column("Status", style="magenta", justify="right")
        
        for agent, status in self.agents.items():
            color = "green" if status == "Complete" else "yellow" if status == "Running" else "dim"
            table.add_row(agent, f"[{color}]{status}[/{color}]")
            
        return table

    def update_status(self, agent_name: str, status: str):
        if agent_name in self.agents:
            self.agents[agent_name] = status
            self.refresh()

class APIStatus(Static):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.border_title = "API Status"

    def render(self) -> str:
        return (
            "[b]Gemini Think API:[/b] [green]Online[/green]\n"
            "[b]HF Image API (SD3.5):[/b] [green]Online[/green]\n"
            "[b]HF Image API (Backup):[/b] [dim]Standby[/dim]\n"
            "[b]Vector DB:[/b] [green]Active[/green]\n"
        )

class VoiceCommandGuide(Static):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.border_title = "Voice Commands"

    def render(self) -> str:
        return (
            "- [cyan]'Omega create...'[/cyan] (e.g. mountains)\n"
            "- [cyan]'Omega think...'[/cyan] (e.g. what is life)\n"
            "- [cyan]'Omega open...'[/cyan] (e.g. notepad)\n"
            "- [cyan]'Omega type...'[/cyan] (e.g. hello world)\n"
        )

class GeminiResultBox(Vertical):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.border_title = "Omega Creation"
        self.current_content = ""

    def compose(self) -> ComposeResult:
        yield Static(self.current_content, id="gemini-markdown")
        yield Button("Download Creation", id="download-creation-btn", variant="success")

    def update_content(self, text: str):
        self.current_content = text
        md = self.query_one("#gemini-markdown", Static)
        md.update(Text.from_ansi(text))


"""Discord Plugin - Notifications for ADW.

Send task notifications to Discord channels via webhooks.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen
from urllib.error import URLError

import click

from adw.plugins.base import Plugin


class DiscordPlugin(Plugin):
    """Discord notifications plugin."""
    
    name = "discord"
    version = "0.1.0"
    description = "Discord notifications for task events"
    author = "StudiBudi"
    requires_external = []
    
    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__(config)
        self.webhook_url = self.config.get("webhook_url") or os.environ.get("ADW_DISCORD_WEBHOOK")
        self.notify_complete = self.config.get("notify_complete", True)
        self.notify_fail = self.config.get("notify_fail", True)
        self.username = self.config.get("username", "ADW Bot")
    
    def on_complete(self, task: str, result: dict[str, Any]) -> None:
        """Send notification on task completion."""
        if not self.notify_complete or not self.webhook_url:
            return
        
        commit = result.get("commit_hash", "")[:8] if result.get("commit_hash") else ""
        
        embed = {
            "title": "✅ Task Completed",
            "description": task[:200],
            "color": 0x00FF00,  # Green
        }
        
        if commit:
            embed["fields"] = [
                {"name": "Commit", "value": f"`{commit}`", "inline": True}
            ]
        
        self._send_webhook({"embeds": [embed]})
    
    def on_fail(self, task: str, error: str) -> None:
        """Send notification on task failure."""
        if not self.notify_fail or not self.webhook_url:
            return
        
        embed = {
            "title": "❌ Task Failed",
            "description": task[:200],
            "color": 0xFF0000,  # Red
            "fields": [
                {"name": "Error", "value": f"```{error[:500]}```", "inline": False}
            ]
        }
        
        self._send_webhook({"embeds": [embed]})
    
    def _send_webhook(self, message: dict) -> bool:
        """Send message to Discord webhook."""
        if not self.webhook_url:
            return False
        
        message["username"] = self.username
        
        try:
            data = json.dumps(message).encode("utf-8")
            request = Request(
                self.webhook_url,
                data=data,
                headers={"Content-Type": "application/json"},
            )
            with urlopen(request, timeout=10) as response:
                return response.status in (200, 204)
        except (URLError, Exception):
            return False
    
    def get_commands(self) -> list:
        """Return CLI commands."""
        return [create_discord_commands(self)]
    
    def status(self) -> dict[str, Any]:
        """Return plugin status."""
        base_status = super().status()
        base_status.update({
            "webhook_configured": bool(self.webhook_url),
            "notify_complete": self.notify_complete,
            "notify_fail": self.notify_fail,
        })
        return base_status


def create_discord_commands(plugin: DiscordPlugin):
    """Create the discord command group."""
    
    @click.group()
    def discord():
        """Discord notification commands."""
        pass
    
    @discord.command("test")
    @click.argument("message", default="Test notification from ADW")
    def discord_test(message: str):
        """Send a test notification."""
        from rich.console import Console
        console = Console()
        
        if not plugin.webhook_url:
            console.print("[red]✗ No webhook URL configured[/red]")
            console.print("[dim]Set ADW_DISCORD_WEBHOOK or configure in ~/.adw/config.toml[/dim]")
            return
        
        embed = {
            "title": "🔔 ADW Test",
            "description": message,
            "color": 0x5865F2,  # Discord blurple
        }
        
        if plugin._send_webhook({"embeds": [embed]}):
            console.print("[green]✓ Test notification sent[/green]")
        else:
            console.print("[red]✗ Failed to send notification[/red]")
    
    @discord.command("status")
    def discord_status():
        """Show Discord configuration status."""
        from rich.console import Console
        console = Console()
        
        if plugin.webhook_url:
            masked = plugin.webhook_url[:40] + "..." if len(plugin.webhook_url) > 45 else plugin.webhook_url
            console.print("[green]✓ Webhook configured[/green]")
            console.print(f"  URL: [dim]{masked}[/dim]")
        else:
            console.print("[yellow]○ No webhook configured[/yellow]")
            console.print("[dim]Set ADW_DISCORD_WEBHOOK environment variable[/dim]")
        
        console.print(f"  Notify on complete: {plugin.notify_complete}")
        console.print(f"  Notify on fail: {plugin.notify_fail}")
    
    return discord


# Export plugin class
plugin_class = DiscordPlugin

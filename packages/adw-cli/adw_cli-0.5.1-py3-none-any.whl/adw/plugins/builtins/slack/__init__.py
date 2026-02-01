"""Slack Plugin - Notifications for ADW.

Send task notifications to Slack channels.
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


class SlackPlugin(Plugin):
    """Slack notifications plugin."""
    
    name = "slack"
    version = "0.1.0"
    description = "Slack notifications for task events"
    author = "StudiBudi"
    requires_external = []
    
    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__(config)
        self.webhook_url = self.config.get("webhook_url") or os.environ.get("ADW_SLACK_WEBHOOK")
        self.notify_complete = self.config.get("notify_complete", True)
        self.notify_fail = self.config.get("notify_fail", True)
        self.channel = self.config.get("channel")
    
    def on_complete(self, task: str, result: dict[str, Any]) -> None:
        """Send notification on task completion."""
        if not self.notify_complete or not self.webhook_url:
            return
        
        commit = result.get("commit_hash", "")[:8] if result.get("commit_hash") else ""
        
        message = {
            "text": f"✅ Task completed: {task[:50]}",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*✅ Task Completed*\n{task}"
                    }
                }
            ]
        }
        
        if commit:
            message["blocks"].append({
                "type": "context",
                "elements": [
                    {"type": "mrkdwn", "text": f"Commit: `{commit}`"}
                ]
            })
        
        if self.channel:
            message["channel"] = self.channel
        
        self._send_webhook(message)
    
    def on_fail(self, task: str, error: str) -> None:
        """Send notification on task failure."""
        if not self.notify_fail or not self.webhook_url:
            return
        
        message = {
            "text": f"❌ Task failed: {task[:50]}",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*❌ Task Failed*\n{task}"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"```{error[:500]}```"
                    }
                }
            ]
        }
        
        if self.channel:
            message["channel"] = self.channel
        
        self._send_webhook(message)
    
    def _send_webhook(self, message: dict) -> bool:
        """Send message to Slack webhook."""
        if not self.webhook_url:
            return False
        
        try:
            data = json.dumps(message).encode("utf-8")
            request = Request(
                self.webhook_url,
                data=data,
                headers={"Content-Type": "application/json"},
            )
            with urlopen(request, timeout=10) as response:
                return response.status == 200
        except (URLError, Exception):
            return False
    
    def get_commands(self) -> list:
        """Return CLI commands."""
        return [create_slack_commands(self)]
    
    def status(self) -> dict[str, Any]:
        """Return plugin status."""
        base_status = super().status()
        base_status.update({
            "webhook_configured": bool(self.webhook_url),
            "notify_complete": self.notify_complete,
            "notify_fail": self.notify_fail,
        })
        return base_status


def create_slack_commands(plugin: SlackPlugin):
    """Create the slack command group."""
    
    @click.group()
    def slack():
        """Slack notification commands."""
        pass
    
    @slack.command("test")
    @click.argument("message", default="Test notification from ADW")
    def slack_test(message: str):
        """Send a test notification."""
        from rich.console import Console
        console = Console()
        
        if not plugin.webhook_url:
            console.print("[red]✗ No webhook URL configured[/red]")
            console.print("[dim]Set ADW_SLACK_WEBHOOK or configure in ~/.adw/config.toml[/dim]")
            return
        
        test_message = {
            "text": f"🔔 {message}",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*🔔 ADW Test*\n{message}"
                    }
                }
            ]
        }
        
        if plugin._send_webhook(test_message):
            console.print("[green]✓ Test notification sent[/green]")
        else:
            console.print("[red]✗ Failed to send notification[/red]")
    
    @slack.command("status")
    def slack_status():
        """Show Slack configuration status."""
        from rich.console import Console
        console = Console()
        
        if plugin.webhook_url:
            masked = plugin.webhook_url[:30] + "..." if len(plugin.webhook_url) > 35 else plugin.webhook_url
            console.print("[green]✓ Webhook configured[/green]")
            console.print(f"  URL: [dim]{masked}[/dim]")
        else:
            console.print("[yellow]○ No webhook configured[/yellow]")
            console.print("[dim]Set ADW_SLACK_WEBHOOK environment variable[/dim]")
        
        console.print(f"  Notify on complete: {plugin.notify_complete}")
        console.print(f"  Notify on fail: {plugin.notify_fail}")
    
    return slack


# Export plugin class
plugin_class = SlackPlugin

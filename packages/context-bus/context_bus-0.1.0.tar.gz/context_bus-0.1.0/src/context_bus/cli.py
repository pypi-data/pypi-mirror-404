#!/usr/bin/env python3
"""Context Bus CLI - Automatic model switching for AI coding agents."""

import os
import sys
import json
import shutil
import subprocess
from pathlib import Path

import click
import yaml

CONTEXT_BUS_DIR = Path.home() / ".context-bus"
CONFIG_DIR = Path.home() / ".config" / "context-bus"
PACKAGE_DIR = Path(__file__).parent


@click.group()
@click.version_option(version="0.1.0")
def main():
    """Context Bus - Automatic model switching with context preservation."""
    pass


@main.command()
@click.option("--workspace", "-w", default=".", help="Workspace directory")
@click.option("--force", "-f", is_flag=True, help="Overwrite existing files")
def init(workspace: str, force: bool):
    """Initialize Context Bus in a workspace."""
    workspace = Path(workspace).resolve()
    
    click.echo("🚀 Initializing Context Bus...")
    click.echo()
    
    # Create directories
    CONTEXT_BUS_DIR.mkdir(parents=True, exist_ok=True)
    (CONTEXT_BUS_DIR / "sessions").mkdir(exist_ok=True)
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    
    # Copy scripts
    scripts_src = PACKAGE_DIR / "scripts"
    if scripts_src.exists():
        for script in scripts_src.glob("*.sh"):
            dest = CONTEXT_BUS_DIR / script.name
            shutil.copy(script, dest)
            dest.chmod(0o755)
        click.echo(f"   ✅ Scripts installed to {CONTEXT_BUS_DIR}")
    
    # Create config
    config_file = CONFIG_DIR / "config.yaml"
    if not config_file.exists() or force:
        config_template = PACKAGE_DIR / "config.template.yaml"
        if config_template.exists():
            shutil.copy(config_template, config_file)
        click.echo(f"   ✅ Config created at {config_file}")
    else:
        click.echo(f"   ⏭️  Config already exists")
    
    # Initialize handoff.json
    handoff_file = CONTEXT_BUS_DIR / "handoff.json"
    if not handoff_file.exists() or force:
        handoff_data = {
            "version": 1,
            "timestamp": None,
            "task": {"id": None, "description": None, "status": "idle", "complexity": None},
            "model": {"current": "opus", "previous": None, "switch_reason": None, "usage_percent": None},
            "context_refs": ["AGENTS.md", "MEMORY.md"],
            "recent_actions": [],
            "blockers": [],
            "next_steps": [],
            "notes": {}
        }
        handoff_file.write_text(json.dumps(handoff_data, indent=2))
        click.echo(f"   ✅ Created handoff.json")
    
    # Augment workspace files (NEVER overwrite!)
    agents_file = workspace / "AGENTS.md"
    if not agents_file.exists():
        agents_template = PACKAGE_DIR / "templates" / "AGENTS.md"
        if agents_template.exists():
            shutil.copy(agents_template, agents_file)
            click.echo(f"   ✅ Created AGENTS.md")
    else:
        click.echo(f"   ⏭️  AGENTS.md already exists (not modified)")
    
    memory_file = workspace / "MEMORY.md"
    if not memory_file.exists():
        memory_template = PACKAGE_DIR / "templates" / "MEMORY.md"
        if memory_template.exists():
            shutil.copy(memory_template, memory_file)
            click.echo(f"   ✅ Created MEMORY.md")
    else:
        click.echo(f"   ⏭️  MEMORY.md already exists (not modified)")
    
    # Augment HEARTBEAT.md (add section if not present)
    heartbeat_file = workspace / "HEARTBEAT.md"
    if heartbeat_file.exists():
        content = heartbeat_file.read_text()
        if "Context Bus" not in content:
            heartbeat_addition = '''

## Context Bus Auto-Switch

Check usage via `session_status`. If >= 95%:
1. Run `~/.context-bus/context-handoff.sh opus codex auto_threshold`
2. Notify user: "🔄 Auto-switched to Codex"

If usage < 50% AND on codex AND tasks idle:
1. Run `~/.context-bus/model-router.sh --reset`
2. Notify user: "🔄 Switched back to Opus"
'''
            heartbeat_file.write_text(content + heartbeat_addition)
            click.echo(f"   ✅ Added Context Bus rules to HEARTBEAT.md")
        else:
            click.echo(f"   ⏭️  HEARTBEAT.md already has Context Bus rules")
    
    click.echo()
    click.echo("✅ Context Bus initialized!")
    click.echo()
    click.echo("Next: Edit ~/.config/context-bus/config.yaml to set Telegram chat ID")


@main.command()
def status():
    """Show current model and usage status."""
    handoff_file = CONTEXT_BUS_DIR / "handoff.json"
    
    if not handoff_file.exists():
        click.echo("❌ Context Bus not initialized. Run: context-bus init")
        return
    
    data = json.loads(handoff_file.read_text())
    
    model = data.get("model", {})
    task = data.get("task", {})
    
    click.echo("━" * 40)
    click.echo("🤖 Context Bus Status")
    click.echo("━" * 40)
    click.echo()
    click.echo(f"Model:   {model.get('current', 'unknown')}")
    click.echo(f"Usage:   {model.get('usage_percent', 'unknown')}%")
    click.echo(f"Task:    {task.get('description', 'None')}")
    click.echo(f"Status:  {task.get('status', 'idle')}")
    click.echo()


@main.command()
@click.argument("model", type=click.Choice(["opus", "codex", "gemini"]))
@click.option("--reason", "-r", default="manual", help="Reason for switch")
def switch(model: str, reason: str):
    """Switch to a different model."""
    script = CONTEXT_BUS_DIR / "context-handoff.sh"
    
    if not script.exists():
        click.echo("❌ Scripts not installed. Run: context-bus init")
        return
    
    # Get current model
    handoff_file = CONTEXT_BUS_DIR / "handoff.json"
    if handoff_file.exists():
        data = json.loads(handoff_file.read_text())
        current = data.get("model", {}).get("current", "opus")
    else:
        current = "opus"
    
    if current == model:
        click.echo(f"Already on {model}")
        return
    
    click.echo(f"🔄 Switching from {current} to {model}...")
    subprocess.run([str(script), current, model, reason], check=True)
    click.echo(f"✅ Switched to {model}")


@main.command()
@click.option("--show", is_flag=True, help="Show current config")
@click.option("--edit", is_flag=True, help="Open config in editor")
def config(show: bool, edit: bool):
    """View or edit configuration."""
    config_file = CONFIG_DIR / "config.yaml"
    
    if not config_file.exists():
        click.echo("❌ Config not found. Run: context-bus init")
        return
    
    if show:
        click.echo(config_file.read_text())
    elif edit:
        editor = os.environ.get("EDITOR", "vim")
        subprocess.run([editor, str(config_file)])
    else:
        click.echo(f"Config file: {config_file}")
        click.echo("Use --show to view or --edit to modify")


if __name__ == "__main__":
    main()

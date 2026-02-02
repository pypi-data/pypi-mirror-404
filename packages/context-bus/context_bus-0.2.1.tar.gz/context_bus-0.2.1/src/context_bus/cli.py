#!/usr/bin/env python3
"""Context Bus v3 CLI - Automatic model switching for AI coding agents."""

import os
import sys
import json
import shutil
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
import hashlib

import click
import yaml

VERSION = "0.2.0"

def get_workspace():
    """Detect the agent workspace."""
    # Check environment variable first
    if os.environ.get("CONTEXT_BUS_WORKSPACE"):
        return Path(os.environ["CONTEXT_BUS_WORKSPACE"])
    
    # Check current directory
    cwd = Path.cwd()
    if (cwd / "AGENTS.md").exists() or (cwd / "HEARTBEAT.md").exists():
        return cwd
    
    # Check common locations
    for path in ["~/clawd", "~/.clawd", "~/openclaw"]:
        p = Path(path).expanduser()
        if p.exists() and ((p / "AGENTS.md").exists() or (p / "HEARTBEAT.md").exists()):
            return p
    
    # Default to current directory
    return cwd


def get_context_dir(workspace=None):
    """Get the .context-bus directory."""
    ws = workspace or get_workspace()
    return ws / ".context-bus"


def get_config_dir():
    """Get the config directory."""
    return Path.home() / ".config" / "context-bus"


@click.group()
@click.version_option(version=VERSION)
def main():
    """Context Bus v3 - Automatic model switching with context preservation."""
    pass


@main.command()
@click.option("--workspace", "-w", default=None, help="Workspace directory")
def init(workspace: str):
    """Initialize Context Bus v3 in a workspace."""
    ws = Path(workspace).resolve() if workspace else get_workspace()
    context_dir = ws / ".context-bus"
    config_dir = get_config_dir()
    
    click.echo(f"🚀 Initializing Context Bus v3...")
    click.echo(f"   Workspace: {ws}")
    click.echo()
    
    # Create directories
    context_dir.mkdir(parents=True, exist_ok=True)
    config_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize handoff.json
    handoff_file = context_dir / "handoff.json"
    if not handoff_file.exists():
        now = datetime.now().astimezone().isoformat()
        expires = (datetime.now().astimezone() + timedelta(minutes=5)).isoformat()
        
        handoff = {
            "schema_version": 3,
            "sequence": 1,
            "timestamp": now,
            "handoff_ready": True,
            "handoff_expires": expires,
            "checksum": None,
            "author": "init",
            "model": {
                "current": "opus",
                "usage_percent": 0,
                "history": []
            },
            "task": {
                "description": None,
                "status": "idle",
                "project": None
            },
            "context": {
                "recent_actions": [],
                "decisions": [],
                "next_steps": [],
                "blockers": []
            },
            "files_touched": []
        }
        
        # Compute checksum
        content = json.dumps({k: v for k, v in handoff.items() if k != "checksum"}, sort_keys=True)
        checksum = hashlib.sha256(content.encode()).hexdigest()
        handoff["checksum"] = f"sha256:{checksum}"
        
        handoff_file.write_text(json.dumps(handoff, indent=2))
        click.echo(f"   ✅ Created handoff.json (v3 schema)")
    else:
        click.echo(f"   ⏭️  handoff.json already exists")
    
    # Copy scripts from package
    pkg_dir = Path(__file__).parent
    scripts_dir = pkg_dir / "scripts"
    
    if scripts_dir.exists():
        for script in ["handoff-utils.sh", "usage-monitor.sh", "generate-summary.sh"]:
            src = scripts_dir / script
            if src.exists():
                dst = context_dir / script
                shutil.copy(src, dst)
                dst.chmod(0o755)
        click.echo(f"   ✅ Installed scripts")
    
    # Create config
    config_file = config_dir / "config.yaml"
    if not config_file.exists():
        config = {
            "workspace": str(ws),
            "models": {
                "primary": "opus",
                "secondary": "codex",
                "tertiary": "gemini"
            },
            "thresholds": {
                "switch_to_secondary": 95,
                "switch_back": 50,
                "proactive_summary": 80
            },
            "safety": {
                "max_handoff_age_seconds": 300,
                "require_handoff_ready": True,
                "offline_abort_minutes": 30
            },
            "notifications": {
                "enabled": True,
                "channel": "telegram",
                "telegram": {"chat_id": ""}
            }
        }
        config_file.write_text(yaml.dump(config, default_flow_style=False))
        click.echo(f"   ✅ Created config.yaml")
    else:
        click.echo(f"   ⏭️  config.yaml already exists")
    
    # Augment HEARTBEAT.md
    heartbeat_file = ws / "HEARTBEAT.md"
    heartbeat_rules = '''

## Context Bus v3 — Usage Monitor & Handoff

### On Session Start

1. Read `.context-bus/handoff.json`
2. If `model.history` has entries → previous model switched
3. Read `.context-bus/rolling-summary.md` for context

### On Every Heartbeat

1. Run `session_status` → get usage %
2. Update handoff.json with current state:
   - model.usage_percent
   - task.description, task.status
   - context.recent_actions, context.next_steps
3. If usage >= 80%: Generate rolling-summary.md

### Switch-Back Rule

If model is "codex" AND usage < 50% AND task.status is "idle":
→ Switch back to Opus, notify user
'''
    
    if heartbeat_file.exists():
        content = heartbeat_file.read_text()
        if "Context Bus v3" not in content:
            heartbeat_file.write_text(content + heartbeat_rules)
            click.echo(f"   ✅ Added Context Bus v3 rules to HEARTBEAT.md")
        else:
            click.echo(f"   ⏭️  HEARTBEAT.md already has Context Bus v3 rules")
    else:
        heartbeat_file.write_text(f"# HEARTBEAT.md\n{heartbeat_rules}")
        click.echo(f"   ✅ Created HEARTBEAT.md")
    
    # Setup background monitor
    if sys.platform == "darwin":
        plist_path = Path.home() / "Library/LaunchAgents/com.contextbus.monitor.plist"
        plist_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.contextbus.monitor</string>
    <key>ProgramArguments</key>
    <array>
        <string>{context_dir}/usage-monitor.sh</string>
    </array>
    <key>EnvironmentVariables</key>
    <dict>
        <key>CONTEXT_BUS_WORKSPACE</key>
        <string>{ws}</string>
    </dict>
    <key>StartInterval</key>
    <integer>300</integer>
    <key>StandardOutPath</key>
    <string>{context_dir}/monitor.log</string>
    <key>StandardErrorPath</key>
    <string>{context_dir}/monitor.err</string>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>'''
        
        subprocess.run(["launchctl", "unload", str(plist_path)], capture_output=True)
        plist_path.write_text(plist_content)
        subprocess.run(["launchctl", "load", str(plist_path)], capture_output=True)
        click.echo(f"   ✅ LaunchAgent installed (runs every 5 min)")
    else:
        # Linux cron
        click.echo(f"   ℹ️  Add to crontab: */5 * * * * {context_dir}/usage-monitor.sh")
    
    click.echo()
    click.echo("✅ Context Bus v3 initialized!")
    click.echo()
    click.echo(f"📁 Files: {context_dir}")
    click.echo(f"⚙️  Config: {config_file}")


@main.command()
def status():
    """Show current model and usage status."""
    context_dir = get_context_dir()
    handoff_file = context_dir / "handoff.json"
    
    if not handoff_file.exists():
        click.echo("❌ Context Bus not initialized. Run: context-bus init")
        return
    
    data = json.loads(handoff_file.read_text())
    model = data.get("model", {})
    task = data.get("task", {})
    
    # Calculate age
    timestamp = data.get("timestamp", "")
    if timestamp:
        try:
            ts = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            age = datetime.now().astimezone() - ts
            age_str = f"{int(age.total_seconds() / 60)} min ago"
        except:
            age_str = "unknown"
    else:
        age_str = "unknown"
    
    click.echo("━" * 50)
    click.echo("🤖 Context Bus v3 Status")
    click.echo("━" * 50)
    click.echo()
    click.echo(f"Model:     {model.get('current', 'unknown')}")
    click.echo(f"Usage:     {model.get('usage_percent', 'unknown')}%")
    click.echo(f"Task:      {task.get('description', 'None') or 'None'}")
    click.echo(f"Status:    {task.get('status', 'idle')}")
    click.echo(f"Updated:   {age_str}")
    click.echo(f"Ready:     {data.get('handoff_ready', False)}")
    click.echo()
    
    # Show history
    history = model.get("history", [])
    if history:
        click.echo(f"Switches:  {len(history)}")
        for h in history[-3:]:
            click.echo(f"           {h.get('model')} → (reason: {h.get('reason')})")


@main.command()
@click.argument("model", type=click.Choice(["opus", "codex", "gemini"]))
@click.option("--reason", "-r", default="manual", help="Reason for switch")
def switch(model: str, reason: str):
    """Manually switch to a different model."""
    context_dir = get_context_dir()
    handoff_file = context_dir / "handoff.json"
    
    if not handoff_file.exists():
        click.echo("❌ Context Bus not initialized. Run: context-bus init")
        return
    
    data = json.loads(handoff_file.read_text())
    current = data.get("model", {}).get("current", "opus")
    
    if current == model:
        click.echo(f"Already on {model}")
        return
    
    # Update history
    history = data.get("model", {}).get("history", [])
    history.append({
        "model": current,
        "until": datetime.now().astimezone().isoformat(),
        "reason": reason
    })
    
    # Update model
    data["model"]["current"] = model
    data["model"]["history"] = history
    data["model"]["switch_reason"] = reason
    data["timestamp"] = datetime.now().astimezone().isoformat()
    data["sequence"] = data.get("sequence", 0) + 1
    
    handoff_file.write_text(json.dumps(data, indent=2))
    click.echo(f"✅ Switched {current} → {model}")


@main.command()
@click.argument("usage", type=int)
def update(usage: int):
    """Update current usage percentage."""
    context_dir = get_context_dir()
    handoff_file = context_dir / "handoff.json"
    
    if not handoff_file.exists():
        click.echo("❌ Context Bus not initialized. Run: context-bus init")
        return
    
    data = json.loads(handoff_file.read_text())
    data["model"]["usage_percent"] = usage
    data["timestamp"] = datetime.now().astimezone().isoformat()
    data["handoff_expires"] = (datetime.now().astimezone() + timedelta(minutes=5)).isoformat()
    data["handoff_ready"] = True
    data["sequence"] = data.get("sequence", 0) + 1
    
    handoff_file.write_text(json.dumps(data, indent=2))
    click.echo(f"✅ Updated usage to {usage}%")


@main.command()
@click.option("--show", is_flag=True, help="Show current config")
@click.option("--edit", is_flag=True, help="Open config in editor")
def config(show: bool, edit: bool):
    """View or edit configuration."""
    config_file = get_config_dir() / "config.yaml"
    
    if not config_file.exists():
        click.echo("❌ Config not found. Run: context-bus init")
        return
    
    if show:
        click.echo(config_file.read_text())
    elif edit:
        editor = os.environ.get("EDITOR", "vim")
        subprocess.run([editor, str(config_file)])
    else:
        click.echo(f"Config: {config_file}")
        click.echo("Use --show to view or --edit to modify")


if __name__ == "__main__":
    main()

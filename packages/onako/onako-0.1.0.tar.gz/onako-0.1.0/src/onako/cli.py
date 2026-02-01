import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

import click

ONAKO_DIR = Path.home() / ".onako"
LOG_DIR = ONAKO_DIR / "logs"


@click.group()
def main():
    """Onako — Dispatch and monitor Claude Code tasks from your phone."""
    pass


@main.command()
def version():
    """Print the version."""
    from onako import __version__
    click.echo(f"onako {__version__}")


@main.command()
@click.option("--host", default="127.0.0.1", help="Host to bind to.")
@click.option("--port", default=8000, type=int, help="Port to bind to.")
def serve(host, port):
    """Start the Onako server."""
    _check_prerequisites()

    from onako import __version__
    click.echo(f"Onako v{__version__}")
    click.echo(f"Starting server at http://{host}:{port}")
    click.echo(f"Dashboard: http://{host}:{port}")
    click.echo()

    import uvicorn
    from onako.server import app
    uvicorn.run(app, host=host, port=port)


@main.command()
@click.option("--host", default="127.0.0.1", help="Host to bind to.")
@click.option("--port", default=8000, type=int, help="Port to bind to.")
def install(host, port):
    """Install Onako as a background service (launchd on macOS, systemd on Linux)."""
    system = platform.system()
    onako_bin = shutil.which("onako")
    if not onako_bin:
        click.echo("Error: 'onako' command not found on PATH.", err=True)
        sys.exit(1)

    LOG_DIR.mkdir(parents=True, exist_ok=True)

    # Build PATH that includes dirs for tmux and claude
    path_dirs = set()
    for cmd in ["tmux", "claude"]:
        p = shutil.which(cmd)
        if p:
            path_dirs.add(str(Path(p).parent))
    path_dirs.update(["/usr/local/bin", "/usr/bin", "/bin"])
    path_value = ":".join(sorted(path_dirs))

    if system == "Darwin":
        _install_launchd(onako_bin, host, port, path_value)
    elif system == "Linux":
        _install_systemd(onako_bin, host, port, path_value)
    else:
        click.echo(f"Auto-start is not supported on {system}. Run 'onako serve' manually.", err=True)
        sys.exit(1)


def _install_launchd(onako_bin, host, port, path_value):
    from importlib.resources import files
    tpl = files("onako").joinpath("templates", "com.onako.server.plist.tpl").read_text()
    plist = tpl.format(
        onako_bin=onako_bin,
        host=host,
        port=port,
        log_dir=LOG_DIR,
        path_value=path_value,
    )
    plist_path = Path.home() / "Library" / "LaunchAgents" / "com.onako.server.plist"
    plist_path.parent.mkdir(parents=True, exist_ok=True)
    plist_path.write_text(plist)
    subprocess.run(["launchctl", "load", str(plist_path)], check=True)
    click.echo(f"Installed launchd service: {plist_path}")
    click.echo(f"Logs: {LOG_DIR}")
    click.echo(f"Onako is running at http://{host}:{port}")


def _install_systemd(onako_bin, host, port, path_value):
    from importlib.resources import files
    tpl = files("onako").joinpath("templates", "onako.service.tpl").read_text()
    unit = tpl.format(
        onako_bin=onako_bin,
        host=host,
        port=port,
        path_value=path_value,
    )
    unit_path = Path.home() / ".config" / "systemd" / "user" / "onako.service"
    unit_path.parent.mkdir(parents=True, exist_ok=True)
    unit_path.write_text(unit)
    subprocess.run(["systemctl", "--user", "daemon-reload"], check=True)
    subprocess.run(["systemctl", "--user", "enable", "--now", "onako"], check=True)
    click.echo(f"Installed systemd service: {unit_path}")
    click.echo(f"Onako is running at http://{host}:{port}")


@main.command()
def uninstall():
    """Remove the Onako background service."""
    system = platform.system()
    if system == "Darwin":
        plist_path = Path.home() / "Library" / "LaunchAgents" / "com.onako.server.plist"
        if plist_path.exists():
            subprocess.run(["launchctl", "unload", str(plist_path)])
            plist_path.unlink()
            click.echo("Onako service removed.")
        else:
            click.echo("Onako service is not installed.")
    elif system == "Linux":
        unit_path = Path.home() / ".config" / "systemd" / "user" / "onako.service"
        if unit_path.exists():
            subprocess.run(["systemctl", "--user", "disable", "--now", "onako"])
            unit_path.unlink()
            subprocess.run(["systemctl", "--user", "daemon-reload"])
            click.echo("Onako service removed.")
        else:
            click.echo("Onako service is not installed.")
    else:
        click.echo(f"Not supported on {system}.")


@main.command()
def status():
    """Check if Onako is running."""
    import urllib.request
    try:
        r = urllib.request.urlopen("http://127.0.0.1:8000/health", timeout=2)
        data = r.read().decode()
        if '"ok"' in data:
            click.echo("Onako server: running")
            click.echo("  URL: http://127.0.0.1:8000")
        else:
            click.echo("Onako server: not responding correctly")
    except Exception:
        click.echo("Onako server: not running")


def _check_prerequisites():
    """Check that tmux and claude are installed."""
    tmux_path = shutil.which("tmux")
    if not tmux_path:
        click.echo("Error: tmux is not installed.", err=True)
        click.echo("Install it with: brew install tmux (macOS) or apt install tmux (Linux)", err=True)
        sys.exit(1)
    click.echo(f"  tmux: {tmux_path}")

    claude_path = shutil.which("claude")
    if not claude_path:
        click.echo("Warning: claude CLI not found on PATH.", err=True)
        click.echo("Install Claude Code from: https://docs.anthropic.com/en/docs/claude-code", err=True)
    else:
        click.echo(f"  claude: {claude_path}")

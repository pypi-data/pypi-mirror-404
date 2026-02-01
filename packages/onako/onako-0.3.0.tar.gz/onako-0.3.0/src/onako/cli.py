import os
import platform
import socket
import shutil
import subprocess
import sys
from pathlib import Path

import click

ONAKO_DIR = Path.home() / ".onako"
LOG_DIR = ONAKO_DIR / "logs"
PID_FILE = ONAKO_DIR / "onako.pid"


@click.group(invoke_without_command=True)
@click.option("--host", default="0.0.0.0", help="Host to bind to.")
@click.option("--port", default=8787, type=int, help="Port to bind to.")
@click.option("--session", default="onako", help="tmux session name (auto-detected if inside tmux).")
@click.option("--dir", "working_dir", default=None, type=click.Path(exists=True), help="Working directory for tasks (default: current directory).")
@click.pass_context
def main(ctx, host, port, session, working_dir):
    """Onako — Dispatch and monitor Claude Code tasks from your phone."""
    if ctx.invoked_subcommand is not None:
        return

    _check_prerequisites()
    working_dir = str(Path(working_dir).resolve()) if working_dir else os.getcwd()

    # Auto-detect current tmux session if inside one
    if os.environ.get("TMUX"):
        try:
            result = subprocess.run(
                ["tmux", "display-message", "-p", "#S"],
                capture_output=True, text=True,
            )
            if result.returncode == 0 and result.stdout.strip():
                detected = result.stdout.strip()
                click.echo(f"Detected tmux session: {detected}")
                session = detected
        except FileNotFoundError:
            pass

    _start_server(host, port, session, working_dir)

    # If not inside tmux, ensure session exists and attach
    if not os.environ.get("TMUX"):
        result = subprocess.run(
            ["tmux", "has-session", "-t", session],
            capture_output=True,
        )
        if result.returncode != 0:
            subprocess.run(
                ["tmux", "new-session", "-d", "-s", session],
                check=True,
            )
        os.execvp("tmux", ["tmux", "attach-session", "-t", session])


@main.command()
def version():
    """Print the version."""
    from onako import __version__
    click.echo(f"onako {__version__}")


@main.command()
@click.option("--host", default="0.0.0.0", help="Host to bind to.")
@click.option("--port", default=8787, type=int, help="Port to bind to.")
@click.option("--session", default="onako", help="tmux session name.")
@click.option("--dir", "working_dir", default=None, type=click.Path(exists=True), help="Working directory for tasks (default: current directory).")
@click.option("--background", is_flag=True, help="Run as a background service (launchd/systemd).")
def serve(host, port, session, working_dir, background):
    """Start the Onako server."""
    working_dir = str(Path(working_dir).resolve()) if working_dir else os.getcwd()

    if background:
        _start_background(host, port, working_dir)
        return

    _check_prerequisites()

    os.environ["ONAKO_WORKING_DIR"] = working_dir
    os.environ["ONAKO_SESSION"] = session

    from onako import __version__
    click.echo(f"Onako v{__version__}")
    click.echo(f"Starting server at http://{host}:{port}")
    click.echo(f"Working directory: {working_dir}")
    click.echo(f"Session: {session}")
    click.echo()

    import uvicorn
    from onako.server import app
    uvicorn.run(app, host=host, port=port)


@main.command()
def stop():
    """Stop the background Onako service."""
    stopped = False

    # Try pid file first (from `onako start`)
    if PID_FILE.exists():
        try:
            pid = int(PID_FILE.read_text().strip())
            os.kill(pid, 15)  # SIGTERM
            click.echo(f"Onako server stopped (pid {pid}).")
            stopped = True
        except (ValueError, ProcessLookupError):
            click.echo("Stale pid file found, cleaning up.")
        PID_FILE.unlink(missing_ok=True)

    # Fall back to launchd/systemd
    if not stopped:
        system = platform.system()
        if system == "Darwin":
            plist_path = Path.home() / "Library" / "LaunchAgents" / "com.onako.server.plist"
            if plist_path.exists():
                uid = os.getuid()
                result = subprocess.run(
                    ["launchctl", "bootout", f"gui/{uid}", str(plist_path)],
                    capture_output=True,
                )
                if result.returncode != 0:
                    subprocess.run(["launchctl", "unload", str(plist_path)], capture_output=True)
                plist_path.unlink()
                click.echo("Onako service stopped and removed.")
                stopped = True
        elif system == "Linux":
            unit_path = Path.home() / ".config" / "systemd" / "user" / "onako.service"
            if unit_path.exists():
                subprocess.run(["systemctl", "--user", "disable", "--now", "onako"])
                unit_path.unlink()
                subprocess.run(["systemctl", "--user", "daemon-reload"])
                click.echo("Onako service stopped and removed.")
                stopped = True

    if not stopped:
        click.echo("Onako service is not running.")


@main.command()
def status():
    """Check if Onako is running."""
    import urllib.request
    try:
        r = urllib.request.urlopen("http://127.0.0.1:8787/health", timeout=2)
        data = r.read().decode()
        if '"ok"' in data:
            click.echo("Onako server: running")
            click.echo("  URL: http://127.0.0.1:8787")
        else:
            click.echo("Onako server: not responding correctly")
    except Exception:
        click.echo("Onako server: not running")


def _is_server_running():
    """Check if the onako server is already running via pid file."""
    if not PID_FILE.exists():
        return False
    try:
        pid = int(PID_FILE.read_text().strip())
        os.kill(pid, 0)  # signal 0 = check if process exists
        return True
    except (ValueError, ProcessLookupError, PermissionError):
        PID_FILE.unlink(missing_ok=True)
        return False


def _start_server(host, port, session, working_dir):
    """Start the Onako server in the background if not already running.

    Returns True if the server was started or is already running.
    """
    if _is_server_running():
        click.echo(f"Onako server already running (pid {PID_FILE.read_text().strip()})")
        return True

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    onako_bin = shutil.which("onako")
    if not onako_bin:
        click.echo("Error: 'onako' command not found on PATH.", err=True)
        sys.exit(1)

    log_out = LOG_DIR / "onako.log"

    with open(log_out, "a") as log_fh:
        proc = subprocess.Popen(
            [onako_bin, "serve", "--host", host, "--port", str(port), "--session", session, "--dir", working_dir],
            stdout=log_fh,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    PID_FILE.parent.mkdir(parents=True, exist_ok=True)
    PID_FILE.write_text(str(proc.pid))

    local_ip = _get_local_ip()
    banner = [
        f"Onako server started (pid {proc.pid})",
        f"  Dashboard: http://{host}:{port}",
    ]
    if local_ip:
        banner.append(f"             http://{local_ip}:{port}")
    banner.append(f"  Session:   {session}")
    banner.append(f"  Logs:      {log_out}")
    for line in banner:
        click.echo(line)

    # Wait for server to be ready
    import urllib.request
    for _ in range(20):
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=1)
            break
        except Exception:
            import time
            time.sleep(0.25)

    return True



def _start_background(host, port, working_dir):
    """Install and start Onako as a background service."""
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
        _install_launchd(onako_bin, host, port, working_dir, path_value)
    elif system == "Linux":
        _install_systemd(onako_bin, host, port, working_dir, path_value)
    else:
        click.echo(f"Background mode is not supported on {system}. Run 'onako serve' manually.", err=True)
        sys.exit(1)


def _install_launchd(onako_bin, host, port, working_dir, path_value):
    from importlib.resources import files
    tpl = files("onako").joinpath("templates", "com.onako.server.plist.tpl").read_text()
    plist = tpl.format(
        onako_bin=onako_bin,
        host=host,
        port=port,
        working_dir=working_dir,
        log_dir=LOG_DIR,
        path_value=path_value,
    )
    plist_path = Path.home() / "Library" / "LaunchAgents" / "com.onako.server.plist"
    plist_path.parent.mkdir(parents=True, exist_ok=True)

    # Unload existing service if present
    uid = os.getuid()
    subprocess.run(
        ["launchctl", "bootout", f"gui/{uid}", str(plist_path)],
        capture_output=True,
    )

    plist_path.write_text(plist)

    # Register and start the service
    result = subprocess.run(
        ["launchctl", "bootstrap", f"gui/{uid}", str(plist_path)],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        subprocess.run(["launchctl", "load", str(plist_path)], check=True)

    # kickstart forces the service to run now (bootstrap alone may not start it)
    subprocess.run(
        ["launchctl", "kickstart", f"gui/{uid}/com.onako.server"],
        capture_output=True,
    )

    click.echo(f"Onako running in background at http://{host}:{port}")
    click.echo(f"  Working directory: {working_dir}")
    click.echo(f"  Logs: {LOG_DIR}")
    click.echo()
    click.echo("If macOS blocks this service, allow it in:")
    click.echo("  System Settings > General > Login Items & Extensions")


def _install_systemd(onako_bin, host, port, working_dir, path_value):
    from importlib.resources import files
    tpl = files("onako").joinpath("templates", "onako.service.tpl").read_text()
    unit = tpl.format(
        onako_bin=onako_bin,
        host=host,
        port=port,
        working_dir=working_dir,
        path_value=path_value,
    )
    unit_path = Path.home() / ".config" / "systemd" / "user" / "onako.service"
    unit_path.parent.mkdir(parents=True, exist_ok=True)
    unit_path.write_text(unit)
    subprocess.run(["systemctl", "--user", "daemon-reload"], check=True)
    subprocess.run(["systemctl", "--user", "enable", "--now", "onako"], check=True)
    click.echo(f"Onako running in background at http://{host}:{port}")
    click.echo(f"  Working directory: {working_dir}")


def _get_local_ip():
    """Get the machine's local network IP address."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return None


def _check_prerequisites():
    """Check that tmux and claude are installed."""
    if not shutil.which("tmux"):
        click.echo("Error: tmux is not installed.", err=True)
        click.echo("Install it with: brew install tmux (macOS) or apt install tmux (Linux)", err=True)
        sys.exit(1)

    if not shutil.which("claude"):
        click.echo("Warning: claude CLI not found on PATH.", err=True)
        click.echo("Install Claude Code from: https://docs.anthropic.com/en/docs/claude-code", err=True)

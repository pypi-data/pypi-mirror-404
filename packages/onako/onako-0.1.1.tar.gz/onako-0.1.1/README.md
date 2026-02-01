# Onako

Dispatch and monitor Claude Code tasks from your phone.

Onako is a lightweight server that runs on your machine. It spawns Claude Code sessions in tmux, and you monitor them through a mobile-friendly web dashboard. Fire off tasks from an iOS Shortcut or the dashboard, check in from anywhere.

## Install

```bash
pipx install onako
```

Requires [tmux](https://github.com/tmux/tmux) and [Claude Code](https://docs.anthropic.com/en/docs/claude-code).

## Usage

```bash
onako serve
```

Open http://localhost:8787 on your phone (same network) or set up [Tailscale](https://tailscale.com) for access from anywhere.

### Auto-start on boot

```bash
onako install
```

### Other commands

```bash
onako status      # Check if server is running
onako uninstall   # Remove auto-start service
onako version     # Print version
```

## How it works

Each task is a tmux window running an interactive Claude Code session. The web dashboard reads tmux output and lets you send messages to running sessions. Task state is persisted in SQLite so it survives server restarts.

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
onako                              # starts server, drops you into tmux
onako --session my-project         # custom session name
```

If you're already inside tmux, onako auto-detects your session and skips the attach. Open http://localhost:8787 on your phone (same network) or set up [Tailscale](https://tailscale.com) for access from anywhere.

```bash
onako stop                         # stop the background server
onako status                       # check if running
onako serve                        # foreground server (for development)
onako version                      # print version
```

## How it works

Onako monitors all tmux windows in the configured session. Windows it creates (via the dashboard) are "managed" tasks. Windows created by you or other tools are discovered automatically as "external" — both get full dashboard support: view output, send messages, kill.

Task state is persisted in SQLite so it survives server restarts.

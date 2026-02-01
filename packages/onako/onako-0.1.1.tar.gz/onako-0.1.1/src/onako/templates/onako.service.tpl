[Unit]
Description=Onako - Claude Code Task Orchestrator
After=network.target

[Service]
ExecStart={onako_bin} serve --host {host} --port {port}
Restart=on-failure
Environment=PATH={path_value}

[Install]
WantedBy=default.target

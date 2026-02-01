[Unit]
Description=Onako - Claude Code Task Orchestrator
After=network.target

[Service]
ExecStart={onako_bin} serve --host {host} --port {port} --dir {working_dir}
WorkingDirectory={working_dir}
Restart=on-failure
Environment=PATH={path_value}

[Install]
WantedBy=default.target

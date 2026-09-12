"""Exercise Block 3 browser behavior with normal, empty, and failed reads."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import threading

from sictra_block3_precision.precision_console_web import create_server, synthetic_workspace


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    empty_payload = synthetic_workspace()
    empty_payload["signals"] = []
    empty_payload["controls"] = []
    servers = [
        create_server(port=0),
        create_server(port=0, workspace_loader=lambda: empty_payload),
    ]
    threads = [
        threading.Thread(target=server.serve_forever, daemon=True)
        for server in servers
    ]
    for thread in threads:
        thread.start()
    try:
        node = os.environ.get("SICTRA_A11Y_NODE", "node")
        completed = subprocess.run(
            [
                node,
                str(root / "tools" / "block3_precision_console_probe.js"),
                f"http://127.0.0.1:{servers[0].server_port}/",
                f"http://127.0.0.1:{servers[1].server_port}/",
            ],
            cwd=root,
            env=os.environ.copy(),
            check=False,
            text=True,
        )
        raise SystemExit(completed.returncode)
    finally:
        for server in servers:
            server.shutdown()
            server.server_close()
        for thread in threads:
            thread.join(timeout=2)


if __name__ == "__main__":
    main()

"""Run the browser accessibility probe against an isolated local console.

The command creates only a temporary synthetic graph and does not publish a
design, mutate the workspace database, or claim manual assistive validation.
"""

from __future__ import annotations

from pathlib import Path
import os
import subprocess
import tempfile
import threading

from sictra_block2_design.design_console_web import bootstrap_demo, create_server


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    node = os.environ.get("SICTRA_A11Y_NODE", "node")
    with tempfile.TemporaryDirectory() as folder:
        database = Path(folder) / "console-a11y.sqlite3"
        bootstrap_demo(database)
        server = create_server(database, "PROJECT-DEMO", port=0)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            completed = subprocess.run(
                [node, str(root / "tools" / "block2_accessibility_probe.js"),
                 f"http://127.0.0.1:{server.server_port}/"],
                cwd=root, env=os.environ.copy(), check=False, text=True,
            )
            raise SystemExit(completed.returncode)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)


if __name__ == "__main__":
    main()

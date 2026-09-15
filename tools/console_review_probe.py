"""Run browser regression against isolated, synthetic console servers.

Requires Node and Playwright on NODE_PATH; no package download is performed.
Runtime data and screenshots stay inside .runtime/console-review.
"""
import os
from pathlib import Path
import subprocess
import tempfile
import threading

from sictra_block2_design.design_console_web import bootstrap_demo, create_server as design
from sictra_block1.lab_web import create_server as intelligence
from sictra_block3_precision.precision_console_web import create_server as precision
from sictra_block4_orchestrator.web import create_server as orchestrator
from sictra_block4_orchestrator.runtime import FederatedOrchestratorStore, build_controlled_block1_package


def main():
    root = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory() as directory:
        db = Path(directory) / 'design.sqlite'
        bootstrap_demo(db)
        key = os.urandom(32)
        store = FederatedOrchestratorStore(Path(directory) / 'journal.sqlite', integrity_key=key)
        store.ingest(build_controlled_block1_package(integrity_key=key))
        store.process_pending()
        store.ingest(build_controlled_block1_package(integrity_key=key, case_id='CASE-RETURN', certainty='CONTRADICTED'))
        servers = [design(db, 'PROJECT-DEMO', port=0), precision(port=0), orchestrator(store, port=0),
                   intelligence(port=0, intake_store_path=Path(directory) / 'intake.json')]
        threads = [threading.Thread(target=server.serve_forever, daemon=True) for server in servers]
        for thread in threads:
            thread.start()
        try:
            urls = [f'http://127.0.0.1:{server.server_port}' for server in servers]
            result = subprocess.run(['node', str(root / 'tools/console_review_probe.cjs'), *urls[:3]], cwd=root, check=False)
            if result.returncode:
                return result.returncode
            return subprocess.run(['node', str(root / 'tools/suite_navigation_probe.cjs'), urls[3], *urls[:3]], cwd=root, check=False).returncode
        finally:
            for server in servers:
                server.shutdown()
                server.server_close()
            for thread in threads:
                thread.join(timeout=2)


if __name__ == '__main__':
    raise SystemExit(main())

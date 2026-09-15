"""Fixed, same-origin visual assets shared by the four laboratory consoles."""
from pathlib import Path

_ROOT = Path(__file__).with_name("console_assets")
CONSOLE_ASSETS = {
    "/review.js": (_ROOT / "review.js", "text/javascript; charset=utf-8"),
    "/suite.css": (_ROOT / "suite.css", "text/css; charset=utf-8"),
    "/suite-icons.svg": (_ROOT / "suite-icons.svg", "image/svg+xml"),
    "/suite-hero.png": (_ROOT.parent.parent / "sictra_block1" / "web" / "assets" / "telecare-hero-port.png", "image/png"),
}

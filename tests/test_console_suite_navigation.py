from html.parser import HTMLParser
from pathlib import Path
import unittest

from sictra.console_assets import CONSOLE_ASSETS
from sictra_block1.lab_web import _STATIC_FILES as BLOCK1
from sictra_block2_design.design_console_web import _STATIC_FILES as BLOCK2
from sictra_block3_precision.precision_console_web import _STATIC as BLOCK3
from sictra_block4_orchestrator.web import STATIC as BLOCK4


class NavigationParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.styles = []
        self.icons = []

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == "a":
            self.links.append(values)
        if tag == "link" and values.get("rel") == "stylesheet":
            self.styles.append(values.get("href"))
        if tag == "use":
            self.icons.append(values.get("href"))


class ConsoleSuiteNavigationTests(unittest.TestCase):
    def test_block_links_stay_in_current_tab_and_have_line_icons(self):
        root = Path(__file__).parents[1] / "src"
        files = ("sictra_block1/web", "sictra_block2_design/design_console",
                 "sictra_block3_precision/precision_console", "sictra_block4_orchestrator/command_center")
        for folder in files:
            with self.subTest(folder=folder):
                parser = NavigationParser()
                parser.feed((root / folder / "index.html").read_text(encoding="utf-8"))
                links = [a for a in parser.links if a.get("href", "").startswith("http://127.0.0.1:876")]
                self.assertEqual(3, len(links))
                for link in links:
                    self.assertIn(link.get("target", "_self"), ("_self", ""))
                    self.assertNotIn("onclick", link)
                self.assertEqual("/suite.css", parser.styles[-1])
                self.assertGreaterEqual(len(parser.icons), 3)
                self.assertTrue(all(value.startswith("/suite-icons.svg#") for value in parser.icons))

    def test_assets_are_identical_allowlisted_and_present_for_every_server(self):
        for mapping in (BLOCK1, BLOCK2, BLOCK3, BLOCK4):
            for url, asset in CONSOLE_ASSETS.items():
                self.assertEqual(asset, mapping[url])
                self.assertTrue(asset[0].is_file())
            for forbidden in ("/suite/../AGENTS.md", "/suite-icons.svg/../runtime.py", "/suite-hero.png?path=keys"):
                self.assertNotIn(forbidden, mapping)


if __name__ == "__main__":
    unittest.main()

"""Integration test for the copyedit pipeline.

Applies all fix rules to tests/data/copyedit.tex and writes the corrected
output to tests/outputs/copyedit_corrected.tex.
"""

import unittest
from pathlib import Path

from lsst.dptwo.utils.copyedit import apply_rule, load_rules

RULES_FILE = Path(__file__).parent.parent / ".copyedit-rules.yaml"
INPUT_FILE = Path(__file__).parent / "data" / "copyedit.tex"
OUTPUT_DIR = Path(__file__).parent / "outputs"
OUTPUT_FILE = OUTPUT_DIR / "copyedit_corrected.tex"


class CopyeditIntegrationTestCase(unittest.TestCase):

    def test_produces_corrected_output(self) -> None:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        rules = [r for r in load_rules(RULES_FILE) if not r["audit_only"]]
        text = INPUT_FILE.read_text()

        for rule in rules:
            text, _ = apply_rule(text, rule)

        OUTPUT_FILE.write_text(text)

        self.assertTrue(OUTPUT_FILE.exists())
        self.assertNotEqual(INPUT_FILE.read_text(), OUTPUT_FILE.read_text())


if __name__ == "__main__":
    unittest.main()

"""Integration test for the copyedit.py pipeline.

Applies all fix rules to tests/data/copyedit.py.tex and writes the corrected
output to tests/outputs/copyedit_corrected.tex.
"""

import unittest
from pathlib import Path

from lsst.dptwo.utils.copyedit import apply_rule, find_matches, load_rules

RULES_FILE = Path(__file__).parent.parent / "copyedit.py-rules.yaml"
INPUT_FILE = Path(__file__).parent / "data" / "copyedit.py.tex"
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


class CopyeditRuleTestCase(unittest.TestCase):
    """Unit tests for individual copy-edit rules."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.rules = {r["name"]: r for r in load_rules(RULES_FILE)}

    def _apply(self, rule_name: str, text: str) -> str:
        result, _ = apply_rule(text, self.rules[rule_name])
        return result

    def _hits(self, rule_name: str, text: str) -> int:
        return len(find_matches(text, self.rules[rule_name]))

    def test_sq_deg_abbrev(self) -> None:
        self.assertEqual(
            self._apply("sq-deg", "covers 18000 sq. deg of sky"),
            r"covers 18000 deg$^{\rm 2}$ of sky",
        )

    def test_sq_deg_no_period(self) -> None:
        self.assertEqual(
            self._apply("sq-deg", "covers 18000 sq deg of sky"),
            r"covers 18000 deg$^{\rm 2}$ of sky",
        )

    def test_sq_deg_written_out(self) -> None:
        self.assertEqual(
            self._apply("sq-deg", "equivalent to 18000 square degrees"),
            r"equivalent to 18000 deg$^{\rm 2}$",
        )

    def test_sq_deg_singular(self) -> None:
        self.assertEqual(
            self._apply("sq-deg", "one square degree"),
            r"one deg$^{\rm 2}$",
        )

    def test_sim_thin_space(self) -> None:
        self.assertEqual(
            self._apply("sim-thin-space", r"depth of $\sim$~27\,mag"),
            r"depth of $\sim$\,~27\,mag",
        )

    def test_sim_thin_space_already_correct(self) -> None:
        self.assertEqual(self._hits("sim-thin-space", r"$\sim$\,~27"), 0)


if __name__ == "__main__":
    unittest.main()

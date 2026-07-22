"""Integration test for the copyedit pipeline.

Applies all fix rules to tests/data/copyedit.tex and writes the corrected
output to tests/outputs/copyedit_corrected.tex.
"""

import unittest
from pathlib import Path

from lsst.dptwo.utils.copyedit import apply_rule, find_matches, load_rules

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

    # --- dataset ---------------------------------------------------------

    def test_dataset(self) -> None:
        self.assertEqual(
            self._apply("dataset", "a data set of images"),
            "a dataset of images",
        )

    def test_dataset_already_correct(self) -> None:
        self.assertEqual(self._hits("dataset", "a dataset of images"), 0)

    # --- farcs-numeric ---------------------------------------------------

    def test_farcs_numeric_space(self) -> None:
        self.assertEqual(
            self._apply("farcs-numeric", "seeing of 0.7 arcsec"),
            r"seeing of 0\farcs7",
        )

    def test_farcs_numeric_nbsp(self) -> None:
        self.assertEqual(
            self._apply("farcs-numeric", "seeing of 1.2~arcsec"),
            r"seeing of 1\farcs2",
        )

    def test_farcs_numeric_arcseconds(self) -> None:
        self.assertEqual(
            self._apply("farcs-numeric", "12.345 arcseconds"),
            r"12\farcs345",
        )

    # --- arcseconds ------------------------------------------------------

    def test_arcseconds_bare(self) -> None:
        self.assertEqual(
            self._apply("arcseconds", "typical arcsec scale"),
            "typical arcseconds scale",
        )

    def test_arcseconds_numeric_preserved(self) -> None:
        self.assertEqual(self._hits("arcseconds", "0.7 arcsec"), 0)

    def test_arcseconds_macro_preserved(self) -> None:
        self.assertEqual(self._hits("arcseconds", r"\arcsec"), 0)

    # --- nonzero ---------------------------------------------------------

    def test_nonzero(self) -> None:
        self.assertEqual(
            self._apply("nonzero", "a non-zero residual"),
            "a nonzero residual",
        )

    # --- bit-mask --------------------------------------------------------

    def test_bit_mask_singular(self) -> None:
        self.assertEqual(
            self._apply("bit-mask", "the bitmask column"),
            "the bit mask column",
        )

    def test_bit_mask_plural(self) -> None:
        self.assertEqual(
            self._apply("bit-mask", "using bitmasks"),
            "using bit masks",
        )

    # --- coadd -----------------------------------------------------------

    def test_coadd_base(self) -> None:
        self.assertEqual(self._apply("coadd", "a co-add image"), "a coadd image")

    def test_coadd_ed(self) -> None:
        self.assertEqual(self._apply("coadd", "co-added frames"), "coadded frames")

    def test_coadd_ing(self) -> None:
        self.assertEqual(self._apply("coadd", "co-adding visits"), "coadding visits")

    def test_coadd_ition(self) -> None:
        self.assertEqual(self._apply("coadd", "a co-addition"), "a coaddition")

    # --- coworking -------------------------------------------------------

    def test_coworking(self) -> None:
        self.assertEqual(
            self._apply("coworking", "co-working with"),
            "coworking with",
        )

    def test_coworker(self) -> None:
        self.assertEqual(
            self._apply("coworking", "a co-worker"),
            "a coworker",
        )

    def test_coworking_capital(self) -> None:
        self.assertEqual(
            self._apply("coworking", "Co-workers are"),
            "Coworkers are",
        )

    # --- survey-property-maps --------------------------------------------

    def test_survey_property_maps_body(self) -> None:
        self.assertEqual(
            self._apply("survey-property-maps", "Survey Property Maps are available"),
            "Survey Property maps are available",
        )

    def test_survey_property_maps_skip_section(self) -> None:
        text = r"\section{Survey Property Maps}" + "\nSurvey Property Maps are useful."
        result = self._apply("survey-property-maps", text)
        self.assertIn(r"\section{Survey Property Maps}", result)
        self.assertIn("Survey Property maps are useful.", result)

    # --- per-pixel -------------------------------------------------------

    def test_per_pixel_space(self) -> None:
        self.assertEqual(
            self._apply("per-pixel", "0.2 per pixel"),
            r"0.2 pixel$^{-1}$",
        )

    def test_per_pixel_nbsp(self) -> None:
        self.assertEqual(
            self._apply("per-pixel", "5~per pixel"),
            r"5~pixel$^{-1}$",
        )

    def test_per_pixel_prose_not_matched(self) -> None:
        self.assertEqual(self._hits("per-pixel", "electrons per pixel"), 0)

    # --- raws-texttt / raws ---------------------------------------------

    def test_raws_texttt(self) -> None:
        self.assertEqual(
            self._apply("raws-texttt", r"\texttt{raws}"),
            r"\texttt{raw} images",
        )

    def test_raws_bare(self) -> None:
        self.assertEqual(
            self._apply("raws", "the raws were processed"),
            "the raw images were processed",
        )

    # --- deep-coadds-texttt / deep-coadds --------------------------------

    def test_deep_coadds_texttt(self) -> None:
        self.assertEqual(
            self._apply("deep-coadds-texttt", r"\texttt{deep\_coadds}"),
            r"\texttt{deep\_coadd} images",
        )

    def test_deep_coadds_bare(self) -> None:
        self.assertEqual(
            self._apply("deep-coadds", r"deep\_coadds"),
            r"deep\_coadd images",
        )

    # --- template-coadds-texttt / template-coadds ------------------------

    def test_template_coadds_texttt(self) -> None:
        self.assertEqual(
            self._apply("template-coadds-texttt", r"\texttt{template\_coadds}"),
            r"\texttt{template\_coadd} images",
        )

    def test_template_coadds_bare(self) -> None:
        self.assertEqual(
            self._apply("template-coadds", r"template\_coadds"),
            r"template\_coadd images",
        )

    # --- boolean-flags ---------------------------------------------------

    def test_boolean_flags_plural(self) -> None:
        self.assertEqual(
            self._apply("boolean-flags", "boolean flags"),
            "Boolean flags",
        )

    def test_boolean_flag_singular(self) -> None:
        self.assertEqual(
            self._apply("boolean-flags", "a boolean flag"),
            "a Boolean flag",
        )

    def test_boolean_alone_not_matched(self) -> None:
        self.assertEqual(self._hits("boolean-flags", "a boolean value"), 0)

    # --- right-ascension -------------------------------------------------

    def test_right_ascension(self) -> None:
        self.assertEqual(
            self._apply("right-ascension", "the right ascension of the source"),
            "the R.A. of the source",
        )

    def test_right_ascension_case_insensitive(self) -> None:
        self.assertEqual(
            self._apply("right-ascension", "Right Ascension and declination"),
            "R.A. and declination",
        )

    def test_right_ascension_skip_section(self) -> None:
        text = r"\section{Right Ascension}" + "\nThe right ascension was measured."
        result = self._apply("right-ascension", text)
        self.assertIn(r"\section{Right Ascension}", result)
        self.assertIn("The R.A. was measured.", result)

    # --- declination -----------------------------------------------------

    def test_declination_lowercase(self) -> None:
        self.assertEqual(
            self._apply("declination", "the declination of the star"),
            "the decl. of the star",
        )

    def test_declination_uppercase(self) -> None:
        self.assertEqual(
            self._apply("declination", "Declination was measured"),
            "Decl. was measured",
        )

    def test_declination_skip_section(self) -> None:
        text = r"\section{Declination}" + "\nThe declination was recorded."
        result = self._apply("declination", text)
        self.assertIn(r"\section{Declination}", result)
        self.assertIn("The decl. was recorded.", result)

    # --- dec-abbrev ------------------------------------------------------

    def test_dec_abbrev(self) -> None:
        self.assertEqual(
            self._apply("dec-abbrev", "the dec of the source"),
            "the decl. of the source",
        )

    def test_dec_abbrev_with_period(self) -> None:
        self.assertEqual(
            self._apply("dec-abbrev", "the dec. of the source"),
            "the decl. of the source",
        )

    def test_dec_abbrev_decay_not_matched(self) -> None:
        self.assertEqual(self._hits("dec-abbrev", "decay rate"), 0)

    def test_dec_abbrev_macro_not_matched(self) -> None:
        self.assertEqual(self._hits("dec-abbrev", r"\dec"), 0)

    # --- band-filter -----------------------------------------------------

    def test_band_filter_space(self) -> None:
        self.assertEqual(
            self._apply("band-filter", "g band observations"),
            "$g$ band observations",
        )

    def test_band_filter_hyphen(self) -> None:
        self.assertEqual(
            self._apply("band-filter", "r-band imaging"),
            "$r$-band imaging",
        )

    def test_band_filter_already_correct(self) -> None:
        self.assertEqual(self._hits("band-filter", "$g$ band"), 0)

    # --- multiepoch ------------------------------------------------------

    def test_multiepoch(self) -> None:
        self.assertEqual(
            self._apply("multiepoch", "multi-epoch photometry"),
            "multiepoch photometry",
        )

    def test_multiepoch_capital(self) -> None:
        self.assertEqual(
            self._apply("multiepoch", "Multi-epoch analysis"),
            "Multiepoch analysis",
        )

    # --- multiband -------------------------------------------------------

    def test_multiband(self) -> None:
        self.assertEqual(
            self._apply("multiband", "multi-band survey"),
            "multiband survey",
        )

    # --- multidimensional ------------------------------------------------

    def test_multidimensional(self) -> None:
        self.assertEqual(
            self._apply("multidimensional", "multi-dimensional fitting"),
            "multidimensional fitting",
        )

    def test_multidimensionality(self) -> None:
        self.assertEqual(
            self._apply("multidimensional", "multi-dimensionality"),
            "multidimensionality",
        )

    # --- citation-empty-options ------------------------------------------

    def test_citation_cite(self) -> None:
        self.assertEqual(
            self._apply("citation-empty-options", r"\cite{foo}"),
            r"\cite[][]{foo}",
        )

    def test_citation_citep(self) -> None:
        self.assertEqual(
            self._apply("citation-empty-options", r"\citep{foo2024}"),
            r"\citep[][]{foo2024}",
        )

    def test_citation_citet(self) -> None:
        self.assertEqual(
            self._apply("citation-empty-options", r"\citet{bar}"),
            r"\citet[][]{bar}",
        )

    def test_citation_already_has_options(self) -> None:
        self.assertEqual(self._hits("citation-empty-options", r"\cite[][]{foo}"), 0)

    # --- preinstalled ----------------------------------------------------

    def test_preinstalled(self) -> None:
        self.assertEqual(
            self._apply("preinstalled", "a pre-installed package"),
            "a preinstalled package",
        )

    def test_preinstallation(self) -> None:
        self.assertEqual(
            self._apply("preinstalled", "Pre-installation steps"),
            "Preinstallation steps",
        )

    # --- pregenerated ----------------------------------------------------

    def test_pregenerated(self) -> None:
        self.assertEqual(
            self._apply("pregenerated", "a pre-generated template"),
            "a pregenerated template",
        )

    def test_pregeneration(self) -> None:
        self.assertEqual(
            self._apply("pregenerated", "pre-generation of templates"),
            "pregeneration of templates",
        )

    # --- nonlinear -------------------------------------------------------

    def test_nonlinear(self) -> None:
        self.assertEqual(
            self._apply("nonlinear", "a non-linear model"),
            "a nonlinear model",
        )

    def test_nonlinearity(self) -> None:
        self.assertEqual(
            self._apply("nonlinear", "detector non-linearity"),
            "detector nonlinearity",
        )

    # --- crosstalk -------------------------------------------------------

    def test_crosstalk_body(self) -> None:
        self.assertEqual(
            self._apply("crosstalk", "crosstalk between amplifiers"),
            "cross talk between amplifiers",
        )

    def test_crosstalk_skip_section(self) -> None:
        text = r"\section{Crosstalk Correction}" + "\nThe crosstalk signal was removed."
        result = self._apply("crosstalk", text)
        self.assertIn(r"\section{Crosstalk Correction}", result)
        self.assertIn("The cross talk signal was removed.", result)

    def test_crosstalk_skip_includegraphics(self) -> None:
        text = r"\includegraphics{crosstalk_fig.pdf}"
        self.assertEqual(self._hits("crosstalk", text), 0)

    # --- crossmatch ------------------------------------------------------

    def test_crossmatch(self) -> None:
        self.assertEqual(
            self._apply("crossmatch", "a cross-match with Gaia"),
            "a crossmatch with Gaia",
        )

    def test_crossmatching(self) -> None:
        self.assertEqual(
            self._apply("crossmatch", "Cross-matching was performed"),
            "Crossmatching was performed",
        )

    def test_crossmatched(self) -> None:
        self.assertEqual(
            self._apply("crossmatch", "cross-matched sources"),
            "crossmatched sources",
        )

    # --- solar-system ----------------------------------------------------

    def test_solar_system_body(self) -> None:
        self.assertEqual(
            self._apply("solar-system", "The Solar System contains eight planets"),
            "The solar system contains eight planets",
        )

    def test_solar_system_proper_noun_preserved(self) -> None:
        self.assertEqual(self._hits("solar-system", "Solar System Objects"), 0)

    def test_solar_system_after_period_preserved(self) -> None:
        self.assertEqual(self._hits("solar-system", ". Solar System"), 0)

    def test_solar_system_skip_section(self) -> None:
        text = r"\section{Solar System Science}" + "\nThe Solar System was surveyed."
        result = self._apply("solar-system", text)
        self.assertIn(r"\section{Solar System Science}", result)
        self.assertIn("The solar system was surveyed.", result)

    # --- lsstcomcam ------------------------------------------------------

    def test_lsstcomcam(self) -> None:
        self.assertEqual(
            self._apply("lsstcomcam", "ComCam observations"),
            "LSSTComCam observations",
        )

    def test_lsstcomcam_already_correct(self) -> None:
        self.assertEqual(self._hits("lsstcomcam", "LSSTComCam"), 0)

    # --- data-release ----------------------------------------------------

    def test_data_release_singular(self) -> None:
        self.assertEqual(
            self._apply("data-release", "data release 1 products"),
            "Data Release 1 products",
        )

    def test_data_release_plural(self) -> None:
        self.assertEqual(
            self._apply("data-release", "future data releases"),
            "future Data Releases",
        )

    def test_data_release_already_correct(self) -> None:
        self.assertEqual(self._hits("data-release", "Data Release"), 0)

    # --- doi-macro-inline-braces -----------------------------------------

    def test_doi_macro_inline_adds_braces(self) -> None:
        self.assertEqual(
            self._apply("doi-macro-inline-braces", r"the DOI is \doidptwopaper and"),
            r"the DOI is \doidptwopaper{} and",
        )

    def test_doi_macro_at_end_of_line(self) -> None:
        self.assertEqual(
            self._apply("doi-macro-inline-braces", r"see \doidptwopaper" + "\n"),
            r"see \doidptwopaper{}" + "\n",
        )

    def test_doi_macro_already_correct(self) -> None:
        self.assertEqual(self._hits("doi-macro-inline-braces", r"\doidptwopaper{}"), 0)

    def test_doi_macro_argument_not_matched(self) -> None:
        self.assertEqual(self._hits("doi-macro-inline-braces", r"\doi{\doidptwopaper}"), 0)

    def test_doi_macro_other_name(self) -> None:
        self.assertEqual(
            self._apply("doi-macro-inline-braces", r"see \doidptwocat and"),
            r"see \doidptwocat{} and",
        )


if __name__ == "__main__":
    unittest.main()

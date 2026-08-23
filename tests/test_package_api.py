import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

import persuasion_index
from PI_score_generator import (
    _load_concreteness_dic,
    _load_liwc_dic,
    _load_mwe_concreteness_dic,
    _load_nrc_vad,
)


class PublicApiTests(unittest.TestCase):
    def _missing_resource_env(self) -> dict[str, str]:
        env = os.environ.copy()
        env["PI_DISABLE_SPACY"] = "1"
        for name in (
            "PI_LIWC_FILE",
            "PI_CONCRETENESS_FILE",
            "PI_MWE_CONCRETENESS_FILE",
            "PI_NRC_VAD_FILE",
        ):
            env.pop(name, None)
        return env

    def test_single_text_shape_and_range(self):
        scores = persuasion_index.score(
            "According to a recent study, this plan could reduce costs by 20%."
        )
        self.assertEqual(len(scores), 15)
        self.assertEqual(
            sum(len(values) - 1 for values in scores.values()),
            55,
        )
        for values in scores.values():
            for value in values.values():
                self.assertGreaterEqual(value, 0.0)
                self.assertLessEqual(value, 1.0)

    def test_batch_api(self):
        frame = pd.DataFrame(
            {"argument": ["This is urgent.", "The evidence is mixed."]}
        )
        subfeatures, dimensions = persuasion_index.score_batch(frame)
        self.assertEqual(subfeatures.shape, (2, 55))
        self.assertEqual(dimensions.shape, (2, 15))

    def test_weighted_report(self):
        raw, weighted = persuasion_index.get_report(
            "This proposal is practical and evidence-based."
        )
        self.assertEqual(len(raw), 15)
        self.assertIsNotNone(weighted)
        self.assertIn("sub_model", weighted["metadata"])
        self.assertIn("mean_model", weighted["metadata"])

    def test_cli_module_outputs_json(self):
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "persuasion_index.cli",
                "--compact",
                "This is urgent.",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        output = json.loads(result.stdout)
        self.assertEqual(len(output), 15)

    def test_optional_warning_quiet_mode(self):
        env = self._missing_resource_env()
        env["PI_QUIET_OPTIONAL_WARNINGS"] = "1"

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "persuasion_index.cli",
                "--compact",
                "This is urgent.",
            ],
            check=True,
            capture_output=True,
            text=True,
            env=env,
        )
        json.loads(result.stdout)
        self.assertEqual(result.stderr, "")

    def test_resource_doctor_json_reports_partial_configuration(self):
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "persuasion_index.cli",
                "doctor",
                "--json",
                "--strict",
            ],
            check=False,
            capture_output=True,
            text=True,
            env=self._missing_resource_env(),
        )
        output = json.loads(result.stdout)
        self.assertEqual(result.returncode, 1)
        self.assertFalse(output["complete"])
        self.assertIn("liwc", output["missing"])
        self.assertIn("nrc_vad", output["missing"])
        self.assertIn("Sentiment.anger", output["resources"]["liwc"]["features"])
        self.assertEqual(
            output["resources"]["nrc_vad"]["features"],
            [
                "Sentiment.valence",
                "Sentiment.arousal",
                "Sentiment.dominance",
            ],
        )

    def test_strict_resource_mode_stops_partial_scoring(self):
        with patch.dict(
            os.environ,
            self._missing_resource_env(),
            clear=True,
        ):
            with self.assertRaises(persuasion_index.ResourceUnavailableError):
                persuasion_index.score(
                    "This is urgent.",
                    strict_resources=True,
                )

    def test_nrc_vad_path_override(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            vad_file = Path(temp_dir) / "nrc-vad.tsv"
            vad_file.write_text(
                "term\tvalence\tarousal\tdominance\n"
                "example\t0.6\t0.4\t0.5\n",
                encoding="utf-8",
            )
            with patch.dict(
                os.environ,
                {"PI_NRC_VAD_FILE": str(vad_file)},
                clear=False,
            ):
                _load_nrc_vad.cache_clear()
                vad = _load_nrc_vad()
            _load_nrc_vad.cache_clear()
            self.assertEqual(vad["example"], (0.6, 0.4, 0.5))

    def test_standard_liwc_dictionary_override(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            liwc_file = Path(temp_dir) / "LIWC.dic"
            liwc_file.write_text(
                "%\n"
                "1 Ppron\n"
                "2 You\n"
                "%\n"
                "you 1 2\n"
                "your* 1 2\n",
                encoding="utf-8",
            )
            with patch.dict(
                os.environ,
                {"PI_LIWC_FILE": str(liwc_file)},
                clear=False,
            ):
                _load_liwc_dic.cache_clear()
                liwc = _load_liwc_dic()
            _load_liwc_dic.cache_clear()
            self.assertEqual(liwc["You"], ["you", "your*"])
            self.assertEqual(liwc["Ppron"], ["you", "your*"])

    def test_concreteness_path_overrides(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            single_file = Path(temp_dir) / "single.tsv"
            single_file.write_text(
                "Word\tConc.M\n"
                "tree\t4.8\n",
                encoding="utf-8",
            )
            mwe_file = Path(temp_dir) / "multiword.csv"
            mwe_file.write_text(
                "Expression,Mean_C\n"
                "washing machine,4.5\n",
                encoding="utf-8-sig",
            )
            with patch.dict(
                os.environ,
                {
                    "PI_CONCRETENESS_FILE": str(single_file),
                    "PI_MWE_CONCRETENESS_FILE": str(mwe_file),
                },
                clear=False,
            ):
                _load_concreteness_dic.cache_clear()
                _load_mwe_concreteness_dic.cache_clear()
                single = _load_concreteness_dic()
                multiword = _load_mwe_concreteness_dic()
            _load_concreteness_dic.cache_clear()
            _load_mwe_concreteness_dic.cache_clear()
            self.assertEqual(single["tree"], 4.8)
            self.assertEqual(multiword["washing machine"], 4.5)

    def test_resource_doctor_handles_invalid_excel_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            invalid_file = Path(temp_dir) / "invalid.xlsx"
            invalid_file.write_text("not an Excel workbook", encoding="utf-8")
            with patch.dict(
                os.environ,
                {"PI_CONCRETENESS_FILE": str(invalid_file)},
                clear=False,
            ):
                status = persuasion_index.check_resources()[
                    "single_word_concreteness"
                ]
            self.assertFalse(status["available"])
            self.assertTrue(
                status["detail"].startswith("Could not read Excel resource header:")
                or "openpyxl is not installed" in status["detail"]
            )

    def test_cli_version_matches_package_version(self):
        result = subprocess.run(
            [sys.executable, "-m", "persuasion_index.cli", "--version"],
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertIn(persuasion_index.__version__, result.stdout)


if __name__ == "__main__":
    unittest.main()

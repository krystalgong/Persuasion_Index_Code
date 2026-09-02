import json
import os
import subprocess
import sys
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

import pandas as pd

import persuasion_index
from PI_score_generator import (
    RE_PERCENT,
    _load_concreteness_dic,
    _load_liwc_dic,
    _load_lexicons,
    _load_mwe_concreteness_dic,
    _load_nrc_vad,
    score_all,
)
from persuasion_runner import run_expanded_lexicons


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

    def test_optional_warnings_link_resource_guide_once(self):
        env = self._missing_resource_env()
        env.pop("PI_QUIET_OPTIONAL_WARNINGS", None)

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
        resource_guide_url = (
            "https://github.com/krystalgong/Persuasion_Index_Code/"
            "blob/main/THIRD_PARTY_RESOURCES.md"
        )
        self.assertEqual(result.stderr.count(resource_guide_url), 1)

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

    def test_score_preserves_case_for_case_sensitive_features(self):
        seen_texts: list[str] = []

        class FakeDoc(list):
            ents: list = []

        def fake_nlp(text: str):
            seen_texts.append(text)
            return FakeDoc()

        with patch("PI_score_generator._get_nlp", return_value=fake_nlp):
            scores = score_all("Smith (2020) says the plan is GREAT.")

        self.assertTrue(seen_texts)
        self.assertTrue(
            all(
                text == "Smith (2020) says the plan is GREAT."
                for text in seen_texts
            )
        )
        self.assertEqual(scores["Evidence"]["attribution"], 1.0)

        cased = persuasion_index.score(
            "The plan is GREAT and the results are good."
        )
        lowered = persuasion_index.score(
            "the plan is great and the results are good."
        )
        self.assertGreater(
            cased["Sentiment"]["vader_compound"],
            lowered["Sentiment"]["vader_compound"],
        )

    def test_percent_regex_matches_normal_percent_expressions(self):
        for text in ("20%", "20% of adults", "fell 20%.", "3.5%", "20 percent"):
            with self.subTest(text=text):
                self.assertTrue(RE_PERCENT.search(text))

        for text in ("20%rate", "abc20%"):
            with self.subTest(text=text):
                self.assertIsNone(RE_PERCENT.search(text))

    def test_liwc_configuration_refreshes_after_first_score(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            liwc_file = Path(temp_dir) / "dynamic-liwc.dic"
            env = {
                "PI_LIWC_FILE": str(liwc_file),
                "PI_QUIET_OPTIONAL_WARNINGS": "1",
            }
            with patch.dict(os.environ, env, clear=False):
                before = persuasion_index.score("furious")
                self.assertEqual(before["Sentiment"]["anger"], 0.0)

                liwc_file.write_text("Anger: furious\n", encoding="utf-8")
                after = persuasion_index.score("furious")
                self.assertGreater(after["Sentiment"]["anger"], 0.0)

                liwc_file.write_text("Anger: calm\n", encoding="utf-8")
                replaced = persuasion_index.score("furious")
                self.assertEqual(replaced["Sentiment"]["anger"], 0.0)

    def test_doctor_rejects_unparseable_and_partial_liwc(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            liwc_file = Path(temp_dir) / "invalid-liwc.dic"
            liwc_file.write_text(
                "this is not a LIWC dictionary at all",
                encoding="utf-8",
            )
            with patch.dict(
                os.environ,
                {"PI_LIWC_FILE": str(liwc_file)},
                clear=False,
            ):
                invalid = persuasion_index.check_resources()["liwc"]
            self.assertFalse(invalid["available"])
            self.assertIn("could not be parsed", invalid["detail"])

            liwc_file.write_text("Anger: furious\n", encoding="utf-8")
            with patch.dict(
                os.environ,
                {"PI_LIWC_FILE": str(liwc_file)},
                clear=False,
            ):
                partial = persuasion_index.check_resources()["liwc"]
            self.assertFalse(partial["available"])
            self.assertIn("missing PI-used categories", partial["detail"])
            self.assertIn("You", partial["missing_categories"])

            liwc_file.write_text(
                "I: me\n"
                "You: you\n"
                "Anger: furious\n"
                "Sad: sad\n"
                "Anx: worried\n"
                "Posemo: happy\n"
                "Past: was\n"
                "See: see\n"
                "Ppron: they\n",
                encoding="utf-8",
            )
            with patch.dict(
                os.environ,
                {"PI_LIWC_FILE": str(liwc_file)},
                clear=False,
            ):
                valid = persuasion_index.check_resources()["liwc"]
            self.assertTrue(valid["available"])
            self.assertEqual(valid["missing_categories"], [])

    def test_public_api_honors_custom_lexicon_without_overwriting_env(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            lexicon_file = Path(temp_dir) / "custom.json"
            lexicon_file.write_text(
                json.dumps({"ARG_CLAIM": ["zorb"]}),
                encoding="utf-8",
            )
            with patch.dict(
                os.environ,
                {"PI_LEXICON_FILE": str(lexicon_file)},
                clear=False,
            ):
                custom = persuasion_index.score("zorb")
                explicit_bundled = persuasion_index.score(
                    "zorb",
                    lexicon="expanded",
                )
                self.assertEqual(
                    os.environ["PI_LEXICON_FILE"],
                    str(lexicon_file),
                )

            self.assertGreater(
                custom["Argumentation"]["conclusion_explicitness"],
                0.0,
            )
            self.assertEqual(
                explicit_bundled["Argumentation"]["conclusion_explicitness"],
                0.0,
            )

            cli = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "persuasion_index.cli",
                    "--compact",
                    "--lexicon-file",
                    str(lexicon_file),
                    "zorb",
                ],
                check=True,
                capture_output=True,
                text=True,
                env={**os.environ, "PI_QUIET_OPTIONAL_WARNINGS": "1"},
            )
            cli_scores = json.loads(cli.stdout)
            self.assertGreater(
                cli_scores["Argumentation"]["conclusion_explicitness"],
                0.0,
            )

    def test_concurrent_custom_lexicons_do_not_contaminate_each_other(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            matching = Path(temp_dir) / "matching.json"
            missing = Path(temp_dir) / "missing.json"
            matching.write_text(
                json.dumps({"ARG_CLAIM": ["alpha"]}),
                encoding="utf-8",
            )
            missing.write_text(
                json.dumps({"ARG_CLAIM": ["beta"]}),
                encoding="utf-8",
            )
            barrier = threading.Barrier(2)

            def score_repeatedly(path: Path) -> list[float]:
                barrier.wait()
                return [
                    persuasion_index.score(
                        "alpha",
                        lexicon_file=path,
                    )["Argumentation"]["conclusion_explicitness"]
                    for _ in range(50)
                ]

            with ThreadPoolExecutor(max_workers=2) as executor:
                matching_future = executor.submit(score_repeatedly, matching)
                missing_future = executor.submit(score_repeatedly, missing)
                matching_scores = matching_future.result()
                missing_scores = missing_future.result()

            self.assertTrue(all(value > 0.0 for value in matching_scores))
            self.assertTrue(all(value == 0.0 for value in missing_scores))

    def test_cli_version_matches_package_version(self):
        result = subprocess.run(
            [sys.executable, "-m", "persuasion_index.cli", "--version"],
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertIn(persuasion_index.__version__, result.stdout)

    def test_package_and_version_command_use_lightweight_imports(self):
        code = (
            "import sys; import persuasion_index; "
            "assert 'pandas' not in sys.modules; "
            "assert 'PI_score_generator' not in sys.modules; "
            "print(persuasion_index.__version__)"
        )
        package_result = subprocess.run(
            [sys.executable, "-c", code],
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertEqual(
            package_result.stdout.strip(),
            persuasion_index.__version__,
        )

        version_result = subprocess.run(
            [
                sys.executable,
                "-X",
                "importtime",
                "-m",
                "persuasion_index.cli",
                "--version",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertNotIn("pandas", version_result.stderr)
        self.assertNotIn("PI_score_generator", version_result.stderr)

    def test_expanded_lexicon_retains_every_seed_entry(self):
        try:
            run_expanded_lexicons(False)
            seeded = _load_lexicons()
            run_expanded_lexicons(True)
            expanded = _load_lexicons()

            self.assertLessEqual(set(seeded), set(expanded))
            for key, seeded_value in seeded.items():
                expanded_value = expanded[key]
                if isinstance(seeded_value, set):
                    self.assertLessEqual(seeded_value, expanded_value, key)
                elif isinstance(seeded_value, dict):
                    self.assertLessEqual(
                        set(seeded_value),
                        set(expanded_value),
                        key,
                    )
                    for nested_key, nested_seeded in seeded_value.items():
                        nested_expanded = expanded_value[nested_key]
                        if isinstance(nested_seeded, set):
                            self.assertLessEqual(
                                nested_seeded,
                                nested_expanded,
                                f"{key}.{nested_key}",
                            )
        finally:
            run_expanded_lexicons(True)

    def test_representative_cues_raise_expected_features(self):
        neutral = persuasion_index.score(
            "The committee discussed the proposal during its meeting."
        )
        evidence = persuasion_index.score(
            "According to a 2025 survey of 1,200 participants, "
            "the policy reduced costs by 20%."
        )
        urgency = persuasion_index.score(
            "Act now. Only three places remain, and this offer expires tonight."
        )
        opponent = persuasion_index.score(
            "On the other hand, the current approach has limitations. "
            "However, this alternative is better."
        )

        self.assertGreater(
            evidence["Evidence"]["mean"],
            neutral["Evidence"]["mean"],
        )
        self.assertGreater(
            urgency["Scarcity/Urgency"]["mean"],
            neutral["Scarcity/Urgency"]["mean"],
        )
        self.assertEqual(opponent["Opponent’s View"]["acknowledge"], 1.0)
        self.assertEqual(
            opponent["Opponent’s View"]["refutation_strength"],
            1.0,
        )

    def test_empty_and_nonlexical_inputs_return_zero_schema(self):
        reference = persuasion_index.score("A substantive sentence.")

        for text in ("", " ", ".", "😀😀😀"):
            result = persuasion_index.score(text)
            self.assertEqual(tuple(result), tuple(reference))
            self.assertEqual(len(result), 15)
            self.assertEqual(
                sum(len(values) - 1 for values in result.values()),
                55,
            )
            for dimension, values in result.items():
                self.assertEqual(
                    tuple(values),
                    tuple(reference[dimension]),
                )
                self.assertTrue(
                    all(value == 0.0 for value in values.values()),
                    (text, dimension, values),
                )

        numeric = persuasion_index.score("12345")
        self.assertGreater(numeric["Evidence"]["statistical"], 0.0)

    def test_composite_lexicon_matches_respect_word_boundaries(self):
        neutral = persuasion_index.score(
            "The committee discussed the proposal."
        )
        committed = persuasion_index.score(
            "I am committed to the plan and can verify the results."
        )

        self.assertEqual(neutral["Commitment"]["statements"], 0.0)
        self.assertEqual(neutral["Commitment"]["power"], 0.0)
        self.assertEqual(committed["Commitment"]["statements"], 1.0)
        self.assertEqual(committed["Commitment"]["power"], 1.0)

    def test_identity_appeals_require_identity_context(self):
        ordinary = persuasion_index.score("Please consider our request.")
        identity = persuasion_index.score(
            "Please stand with our nation and protect our homeland."
        )

        self.assertEqual(
            ordinary["Propaganda"]["heuristic_identity_appeals"],
            0.0,
        )
        self.assertGreater(
            identity["Propaganda"]["heuristic_identity_appeals"],
            0.0,
        )


if __name__ == "__main__":
    unittest.main()

import argparse
import unittest
import subprocess
import sys
from pathlib import Path

from main import parse_match_count
from pickmychamp.counter_guides import (
    counter_picks,
    render_build,
    render_runes,
)
from pickmychamp.recommendations import (
    aggregate_matches,
    confidence,
    filter_queue,
    normalize_role,
    rank_champions,
)


class RecommendationTests(unittest.TestCase):
    def setUp(self):
        self.puuid = "player"
        self.matches = [
            {
                "info": {
                    "participants": [
                        {
                            "puuid": self.puuid,
                            "teamPosition": "TOP",
                            "championName": "Garen",
                            "win": True,
                            "kills": 4,
                            "deaths": 2,
                            "assists": 6,
                        }
                    ]
                }
            },
            {
                "info": {
                    "participants": [
                        {
                            "puuid": self.puuid,
                            "teamPosition": "JUNGLE",
                            "championName": "Garen",
                            "win": False,
                            "kills": 1,
                            "deaths": 5,
                            "assists": 2,
                        }
                    ]
                }
            },
        ]

    def test_role_aliases(self):
        self.assertEqual(normalize_role("mid"), "MIDDLE")
        self.assertEqual(normalize_role("support"), "UTILITY")
        with self.assertRaises(ValueError):
            normalize_role("roam")

    def test_role_filter_and_personal_stats(self):
        stats = aggregate_matches(self.matches, self.puuid, "top")
        self.assertEqual(stats["Garen"].games, 1)
        self.assertEqual(stats["Garen"].win_rate, 100)
        self.assertEqual(stats["Garen"].kda, 5)

    def test_rank_includes_mastered_champion_without_inventing_games(self):
        stats = aggregate_matches(self.matches, self.puuid, "top")
        ranked = rank_champions(stats, ["Garen", "Ahri"])
        self.assertEqual({item.champion for item, _ in ranked}, {"Garen", "Ahri"})
        self.assertEqual(stats["Garen"].games, 1)
        self.assertEqual(stats["Ahri"].games, 0)

    def test_confidence_reflects_sample_size(self):
        self.assertEqual(confidence(0), 0)
        self.assertLess(confidence(1), confidence(20))

    def test_queue_filter_excludes_other_modes(self):
        matches = [
            {"info": {"queueId": 420}},
            {"info": {"queueId": 440}},
            {"info": {"queueId": 400}},
            {"info": {"queueId": 450}},
        ]
        self.assertEqual(len(filter_queue(matches, "ranked")), 1)
        self.assertEqual(len(filter_queue(matches, "flex")), 1)
        self.assertEqual(len(filter_queue(matches, "normal")), 1)
        with self.assertRaises(ValueError):
            filter_queue(matches, "aram")

    def test_match_count_is_bounded(self):
        self.assertEqual(parse_match_count("100"), 100)
        for value in ("0", "101", "all"):
            with self.assertRaises(argparse.ArgumentTypeError):
                parse_match_count(value)

    def test_demo_runs_without_api_key_and_labels_synthetic_data(self):
        repository = Path(__file__).resolve().parents[1]
        result = subprocess.run(
            [
                sys.executable,
                str(repository / "main.py"),
                "demo",
                "--role",
                "adc",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("données synthétiques", result.stdout)
        self.assertIn("Vayne", result.stdout)

    def test_vayne_adc_counter_guides_include_three_options(self):
        picks = counter_picks("Vayne", "adc")
        self.assertEqual([pick.champion for pick in picks], ["Caitlyn", "Draven", "Ashe"])
        self.assertEqual(picks[0].support, "Karma")
        with self.assertRaises(ValueError):
            counter_picks("Darius", "top")

    def test_counter_guides_require_current_patch_catalog_entries(self):
        pick = counter_picks("Vayne", "adc")[0]
        rune_names = {key: key for key in pick.primary_runes + pick.secondary_runes}
        tree_names = {pick.primary_tree: "Precision", pick.secondary_tree: "Sorcery"}
        self.assertIn("FleetFootwork", render_runes(pick, rune_names, tree_names))
        with self.assertRaises(RuntimeError):
            render_build(pick, {})


if __name__ == "__main__":
    unittest.main()

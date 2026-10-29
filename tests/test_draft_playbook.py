import unittest

from pickmychamp.draft_playbook import generate_playbook


class DraftPlaybookTests(unittest.TestCase):
    def setUp(self):
        self.allies = {
            "top": "Malphite",
            "jungle": "Amumu",
            "mid": "Ahri",
            "adc": "Jinx",
            "support": "Lulu",
        }
        self.enemies = {
            "top": "Jayce",
            "jungle": "Nidalee",
            "mid": "Xerath",
            "adc": "Varus",
            "support": "Lux",
        }

    def test_engage_plan_is_grounded_in_allied_picks_and_role(self):
        playbook = generate_playbook(self.allies, self.enemies, "adc")

        self.assertEqual(playbook["allied_pattern"]["id"], "engage")
        self.assertEqual(playbook["your_champion"], "Jinx")
        self.assertIn("nearest safe target", playbook["your_job"])
        self.assertEqual(len(playbook["role_jobs"]), 5)
        self.assertEqual(
            {item["champion"] for item in playbook["evidence"]},
            {"Malphite", "Amumu"},
        )
        self.assertEqual(playbook["enemy_pattern"]["id"], "poke")
        self.assertIn("coordinated engage", playbook["counter_plan"])
        self.assertEqual(playbook["allied_coverage"]["profiled"], 5)

    def test_mixed_signals_do_not_force_a_primary_plan(self):
        allies = {
            "top": "Malphite",
            "jungle": "Amumu",
            "mid": "Xerath",
            "adc": "Varus",
            "support": "Unprofiled Champion",
        }

        playbook = generate_playbook(allies, self.enemies, "mid")

        self.assertIsNone(playbook["allied_pattern"]["id"])
        self.assertEqual(playbook["role_jobs"], [])
        self.assertIn("do not support a reliable", playbook["your_job"])
        self.assertIn(
            "Unprofiled Champion",
            playbook["allied_coverage"]["unprofiled_champions"],
        )

    def test_one_champion_signal_is_not_enough_to_name_a_team_plan(self):
        playbook = generate_playbook(
            {"top": "Malphite"},
            {"top": "Jayce"},
            "top",
        )

        self.assertIsNone(playbook["allied_pattern"]["id"])
        self.assertEqual(playbook["evidence"], [])

    def test_unprofiled_partial_drafts_are_explicitly_uncertain(self):
        playbook = generate_playbook(
            {"mid": "Unknown Mid"},
            {"mid": "Unknown Opponent"},
            "mid",
        )

        self.assertEqual(playbook["allied_pattern"]["id"], None)
        self.assertEqual(playbook["allied_coverage"]["selected"], 1)
        self.assertEqual(playbook["allied_coverage"]["profiled"], 0)
        self.assertIn("No clear opponent pattern", playbook["enemy_read"])
        self.assertTrue(playbook["notes"])

    def test_champion_matching_is_case_insensitive(self):
        playbook = generate_playbook(
            {"top": "malphite", "jungle": "AMUMU"},
            {"top": "Jayce"},
            "top",
        )

        self.assertEqual(playbook["allied_pattern"]["id"], "engage")

    def test_invalid_or_empty_inputs_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "at least one champion"):
            generate_playbook({}, {"top": "Jayce"}, "mid")
        with self.assertRaisesRegex(ValueError, "valid player role"):
            generate_playbook({"mid": "Ahri"}, {"mid": "Zed"}, "bot")
        with self.assertRaisesRegex(ValueError, "unsupported role"):
            generate_playbook({"bot": "Ahri"}, {"mid": "Zed"}, "mid")
        with self.assertRaisesRegex(ValueError, "must be an object"):
            generate_playbook(["Ahri"], {"mid": "Zed"}, "mid")
        with self.assertRaisesRegex(ValueError, "60 characters or fewer"):
            generate_playbook(
                {"mid": "A" * 61},
                {"mid": "Zed"},
                "mid",
            )


if __name__ == "__main__":
    unittest.main()

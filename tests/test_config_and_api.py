import tempfile
import unittest
from pathlib import Path

from pickmychamp.config import AccountConfig, load_config, save_config
from pickmychamp.riot_api import RiotApi


class ConfigAndApiTests(unittest.TestCase):
    def test_account_config_round_trip(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "config.json"
            original = AccountConfig(
                riot_id="player#EUW",
                region="euw",
                primary_role="top",
                secondary_roles=["mid"],
                mastered_champions=["Garen"],
                preferences=["tank"],
            )
            save_config(original, path)
            loaded = load_config(path)
        self.assertEqual(loaded.primary_role, "TOP")
        self.assertEqual(loaded.secondary_roles, ["MID"])
        self.assertEqual(loaded.riot_id, original.riot_id)
        self.assertEqual(loaded.region, original.region)
        self.assertEqual(loaded.mastered_champions, original.mastered_champions)
        self.assertEqual(loaded.preferences, original.preferences)
        self.assertEqual(loaded.game_name, "player")
        self.assertEqual(loaded.tag_line, "EUW")

    def test_riot_id_requires_both_parts(self):
        with self.assertRaises(ValueError):
            AccountConfig("player#", "euw", "top").tag_line
        with self.assertRaises(ValueError):
            AccountConfig("#tag", "euw", "top").game_name

    def test_euw_api_routes(self):
        api = RiotApi("euw", api_key="test-key")
        self.assertEqual(api.platform, "euw1")
        self.assertEqual(api.continental, "europe")


if __name__ == "__main__":
    unittest.main()

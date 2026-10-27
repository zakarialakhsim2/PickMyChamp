import unittest
from unittest.mock import patch

from api.index import app


class VercelApiFunctionalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config.update(TESTING=True)
        cls.client = app.test_client()

    def test_home_and_ads_txt_are_publicly_served(self):
        home = self.client.get("/")
        ads_txt = self.client.get("/ads.txt")

        self.assertEqual(home.status_code, 200)
        self.assertIn(b"PickMyChamp", home.data)
        self.assertIn(b"google-adsense-account", home.data)
        self.assertEqual(ads_txt.status_code, 200)
        self.assertIn(b"pub-6962406875891285", ads_txt.data)

    def test_counter_requires_an_enemy(self):
        response = self.client.get("/api/counter")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.get_json()["error"],
            "Indique le champion adverse.",
        )

    def test_counter_returns_serialized_recommendations(self):
        matchup = {
            "enemy": "Ahri",
            "enemy_role": "mid",
            "patch": "current",
            "scope": "OP.GG ranked",
            "source": "OP.GG",
            "source_url": "https://op.gg/lol/champions/ahri/build",
            "picks": [
                {"champion": "Naafiri", "slug": "naafiri", "win_rate": 54.2, "games": 300},
            ],
        }
        with patch("api.index.counter_payload", return_value={
            "enemy": "Ahri",
            "role": "mid",
            "picks": matchup["picks"],
            "source": "OP.GG",
        }) as payload:
            response = self.client.get("/api/counter?enemy=Ahri&role=mid")

        payload.assert_called_once_with("Ahri", "mid")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["picks"][0]["champion"], "Naafiri")

    def test_champion_catalog_failure_is_explicit(self):
        with patch("api.index.champion_catalog", side_effect=RuntimeError("upstream unavailable")):
            response = self.client.get("/api/champions")

        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.get_json()["error"], "upstream unavailable")


if __name__ == "__main__":
    unittest.main()

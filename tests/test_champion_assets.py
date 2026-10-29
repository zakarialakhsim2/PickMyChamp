import unittest
from unittest.mock import MagicMock, patch

from pickmychamp.champion_assets import fetch_champion_asset


class ChampionAssetTests(unittest.TestCase):
    def setUp(self):
        self.patch = "16.21.1"
        self.champions = [{"id": "Vayne", "name": "Vayne"}]

    def _response(self, image, content_type):
        response = MagicMock()
        response.read.return_value = image
        response.headers = {"Content-Type": content_type}
        response.__enter__.return_value = response
        return response

    def test_portrait_uses_fixed_current_patch_url(self):
        image = b"\x89PNG\r\n\x1a\nportrait"
        response = self._response(image, "image/png")
        with patch(
            "pickmychamp.champion_assets.champion_catalog",
            return_value=(self.patch, self.champions),
        ), patch("pickmychamp.champion_assets.urlopen", return_value=response) as open_url:
            result = fetch_champion_asset("portrait", "Vayne")

        self.assertEqual(result, (image, "image/png"))
        self.assertEqual(
            open_url.call_args.args[0].full_url,
            "https://ddragon.leagueoflegends.com/cdn/16.21.1/img/champion/Vayne.png",
        )

    def test_splash_uses_fixed_data_dragon_asset_url(self):
        image = b"\xff\xd8\xffsplash"
        response = self._response(image, "image/jpeg")
        with patch(
            "pickmychamp.champion_assets.champion_catalog",
            return_value=(self.patch, self.champions),
        ), patch("pickmychamp.champion_assets.urlopen", return_value=response) as open_url:
            result = fetch_champion_asset("splash", "Vayne")

        self.assertEqual(result, (image, "image/jpeg"))
        self.assertEqual(
            open_url.call_args.args[0].full_url,
            "https://ddragon.leagueoflegends.com/cdn/img/champion/splash/Vayne_0.jpg",
        )

    def test_unknown_champion_and_asset_type_are_rejected_before_fetch(self):
        with patch(
            "pickmychamp.champion_assets.champion_catalog",
            return_value=(self.patch, self.champions),
        ), patch("pickmychamp.champion_assets.urlopen") as open_url:
            with self.assertRaisesRegex(ValueError, "Champion inconnu"):
                fetch_champion_asset("portrait", "UnknownChampion")
            with self.assertRaisesRegex(ValueError, "Type d'image"):
                fetch_champion_asset("arbitrary", "Vayne")

        open_url.assert_not_called()

    def test_invalid_upstream_response_is_rejected(self):
        response = self._response(b"<html>blocked</html>", "text/html")
        with patch(
            "pickmychamp.champion_assets.champion_catalog",
            return_value=(self.patch, self.champions),
        ), patch("pickmychamp.champion_assets.urlopen", return_value=response):
            with self.assertRaisesRegex(RuntimeError, "invalid champion image"):
                fetch_champion_asset("portrait", "Vayne")


if __name__ == "__main__":
    unittest.main()
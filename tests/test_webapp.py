import json
import threading
import unittest
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from unittest.mock import patch

from pickmychamp.webapp import PickMyChampHandler, counter_payload
from pickmychamp.counter_source import CounterPageParser


class WebAppTests(unittest.TestCase):
    def test_public_matchup_page_parser_extracts_win_rate_and_sample(self):
        parser = CounterPageParser("Vayne")
        parser.feed(
            '<div>Best Picks vs Vayne</div>'
            '<a href="/lol/champions/draven/build">'
            '<div>Draven</div><div>52.83% WR</div>'
            '<div>848<!-- --> games</div></a>'
            '<div>Worst Picks vs Vayne</div>'
            '<a href="/lol/champions/ezreal/build">'
            '<div>Ezreal</div><div>45.10% WR</div><div>2,253 games</div></a>'
        )
        self.assertEqual(len(parser.entries), 1)
        self.assertEqual(parser.entries[0]["champion"], "Draven")
        self.assertEqual(parser.entries[0]["win_rate"], 52.83)
        self.assertEqual(parser.entries[0]["games"], 848)

    def test_counter_payload_contains_current_patch_runebook_and_build(self):
        catalog = (
            "16.21.1",
            {"1055": "Doran's Blade", "3032": "Yun Tal", "3006": "Boots",
             "3031": "Infinity Edge", "3094": "Rapid Firecannon",
             "3036": "Lord Dominik", "3072": "Bloodthirster",
             "3033": "Mortal Reminder", "3026": "Guardian Angel",
             "6672": "Kraken Slayer", "6673": "Immortal Shieldbow",
             "3085": "Runaan's Hurricane"},
            {
                "FleetFootwork": "Fleet Footwork",
                "PresenceOfMind": "Presence of Mind",
                "LegendBloodline": "Bloodline",
                "CutDown": "Cut Down",
                "AbsoluteFocus": "Absolute Focus",
                "GatheringStorm": "Gathering Storm",
                "PressTheAttack": "Press the Attack",
                "Triumph": "Triumph",
                "CoupDeGrace": "Coup de Grace",
                "NimbusCloak": "Nimbus Cloak",
                "LethalTempo": "Lethal Tempo",
                "BiscuitDelivery": "Biscuit Delivery",
                "ApproachVelocity": "Approach Velocity",
            },
            {"Precision": "Precision", "Sorcery": "Sorcery", "Inspiration": "Inspiration"},
        )
        matchup = {
            "enemy": "Vayne",
            "enemy_role": "adc",
            "patch": "26.21",
            "scope": "World Emerald+",
            "source": "U.GG",
            "source_url": "https://u.gg/lol/champions/vayne/counter",
            "picks": [
                {"champion": "Veigar", "slug": "veigar", "win_rate": 55.78, "games": 251},
                {"champion": "Kog'Maw", "slug": "kogmaw", "win_rate": 53.96, "games": 480},
                {"champion": "Draven", "slug": "draven", "win_rate": 52.83, "games": 848},
            ],
        }
        with patch("pickmychamp.webapp.current_patch_catalog", return_value=catalog):
            with patch("pickmychamp.webapp.matchup_counters", return_value=matchup) as source:
                payload = counter_payload("Vayne", "adc")
        source.assert_called_once_with("Vayne", "adc")
        self.assertEqual(payload["patch"], "26.21")
        self.assertEqual(len(payload["picks"]), 3)
        self.assertEqual(payload["picks"][0]["champion"], "Veigar")
        self.assertEqual(payload["picks"][0]["win_rate"], 55.78)
        self.assertEqual(payload["picks"][0]["games"], 251)
        self.assertFalse(payload["picks"][0]["guide_available"])
        self.assertTrue(payload["picks"][2]["guide_available"])
        self.assertIn("Press the Attack", payload["picks"][2]["runes"])

    def test_local_server_serves_ui_and_rejects_unsupported_matchup(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), PickMyChampHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        url = f"http://127.0.0.1:{server.server_port}"
        try:
            with urlopen(url, timeout=3) as response:
                body = response.read().decode("utf-8")
            self.assertIn("Choose your", body)
            self.assertIn("/app.js", body)
            mismatch = {
                "enemy": "Darius",
                "enemy_role": "top",
                "patch": "26.21",
                "scope": "World Emerald+",
                "source": "U.GG",
                "source_url": "https://u.gg/lol/champions/darius/counter",
                "picks": [
                    {"champion": "Heimerdinger", "slug": "heimerdinger",
                     "win_rate": 52.89, "games": 588}
                ],
            }
            with patch(
                "pickmychamp.webapp.matchup_counters", return_value=mismatch
            ):
                with urlopen(f"{url}/api/counter?enemy=Darius&role=adc", timeout=3) as response:
                    matchup = json.loads(response.read().decode("utf-8"))
            self.assertIn("may not fit your lane", matchup["role_warning"])
            self.assertEqual(matchup["picks"][0]["champion"], "Heimerdinger")
            with patch(
                "pickmychamp.webapp.champion_catalog",
                return_value=("16.21.1", [{"id": "Vayne", "name": "Vayne"}]),
            ):
                with urlopen(f"{url}/api/champions", timeout=3) as response:
                    catalog = json.loads(response.read().decode("utf-8"))
            self.assertEqual(catalog["champions"][0]["name"], "Vayne")

            image = b"\x89PNG\r\n\x1a\nportrait"
            with patch(
                "pickmychamp.webapp.fetch_champion_asset",
                return_value=(image, "image/png"),
            ) as fetch:
                with urlopen(
                    f"{url}/api/champion-asset/portrait/Vayne", timeout=3
                ) as response:
                    self.assertEqual(response.headers.get_content_type(), "image/png")
                    self.assertEqual(response.read(), image)
            fetch.assert_called_once_with("portrait", "Vayne")

            request = Request(
                f"{url}/api/playbook",
                data=json.dumps(
                    {
                        "player_role": "adc",
                        "allies": {
                            "top": "Malphite",
                            "jungle": "Amumu",
                            "adc": "Jinx",
                        },
                        "enemies": {
                            "mid": "Xerath",
                            "adc": "Varus",
                        },
                    }
                ).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urlopen(request, timeout=3) as response:
                playbook = json.loads(response.read().decode("utf-8"))
            self.assertEqual(playbook["allied_pattern"]["id"], "engage")
            self.assertEqual(playbook["your_champion"], "Jinx")

            invalid_request = Request(
                f"{url}/api/playbook",
                data=json.dumps(
                    {"player_role": "bot", "allies": {"mid": "Ahri"},
                     "enemies": {"mid": "Zed"}}
                ).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with self.assertRaises(HTTPError) as error:
                urlopen(invalid_request, timeout=3)
            self.assertEqual(error.exception.code, 400)
            error.exception.close()
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=3)


if __name__ == "__main__":
    unittest.main()

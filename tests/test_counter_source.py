import unittest

from pickmychamp.counter_source import (
    CounterPageParser,
    build_url,
    curated_fallback,
)


class CounterSourceTests(unittest.TestCase):
    def test_parser_ignores_worst_picks_and_extracts_numeric_values(self):
        parser = CounterPageParser("Vayne")
        parser.feed(
            "<div>Best Picks vs Vayne</div>"
            '<a href="/lol/champions/draven/build">'
            "Draven 52.83% WR 848 games</a>"
            "<div>Worst Picks vs Vayne</div>"
            '<a href="/lol/champions/ezreal/build">'
            "Ezreal 45.10% WR 2,253 games</a>"
        )

        self.assertEqual(parser.entries, [{
            "champion": "Draven",
            "slug": "draven",
            "win_rate": 52.83,
            "games": 848,
        }])

    def test_vayne_adc_has_curated_fallback(self):
        fallback = curated_fallback("Vayne", "adc", "https://u.gg/example")

        self.assertEqual(fallback["source"], "PickMyChamp guide")
        self.assertEqual(len(fallback["picks"]), 3)
        self.assertEqual(fallback["picks"][0]["games"], 0)

    def test_other_matchups_report_unavailable_data(self):
        fallback = curated_fallback("Ahri", "mid", "https://u.gg/example")

        self.assertEqual(fallback["picks"], [])
        self.assertEqual(fallback["source"], "U.GG unavailable")
        self.assertIn("blocking requests", fallback["fallback_message"])

    def test_build_url_uses_the_expected_u_gg_path(self):
        self.assertEqual(
            build_url("draven"),
            "https://u.gg/lol/champions/draven/build",
        )


if __name__ == "__main__":
    unittest.main()

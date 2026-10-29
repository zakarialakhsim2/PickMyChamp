import json
import unittest
from dataclasses import replace
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

from pickmychamp.counter_guides import current_patch_catalog, current_patch_item_catalog
from pickmychamp.item_companion import (
    GameSnapshot,
    ItemDefinition,
    ItemRule,
    parse_data_dragon_item_catalog,
    rank_item_recommendations,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "item_recommendation_synthetic_v1.json"


class ItemCompanionTests(unittest.TestCase):
    def setUp(self):
        self.fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        self.snapshot = GameSnapshot.from_dict(self.fixture["snapshot"])
        self.catalog = {
            item["item_id"]: ItemDefinition.from_dict(item)
            for item in self.fixture["catalog"]
        }
        self.rules = tuple(ItemRule.from_dict(rule) for rule in self.fixture["rules"])

    def test_data_dragon_item_payload_maps_to_typed_definitions(self):
        payload = {
            "data": {
                "test-item": {
                    "name": "Synthetic Data Dragon Item",
                    "maps": {"11": True, "12": False},
                    "gold": {"total": 2400, "purchasable": True},
                },
                "test-trinket": {
                    "name": "Synthetic Data Dragon Trinket",
                    "maps": {"11": True},
                    "gold": {"total": 0, "purchasable": False},
                },
            }
        }

        catalog = parse_data_dragon_item_catalog(payload)

        self.assertEqual(
            catalog["test-item"],
            ItemDefinition(
                item_id="test-item",
                name="Synthetic Data Dragon Item",
                total_cost=2400,
                map_ids=(11,),
                purchasable=True,
            ),
        )
        self.assertFalse(catalog["test-trinket"].purchasable)

    def test_data_dragon_item_parser_rejects_malformed_item_metadata(self):
        payload = {
            "data": {
                "test-item": {
                    "name": "Synthetic Item",
                    "maps": {"11": "yes"},
                    "gold": {"total": 2400, "purchasable": True},
                }
            }
        }

        with self.assertRaisesRegex(ValueError, "invalid map flag"):
            parse_data_dragon_item_catalog(payload)

    def test_current_patch_item_catalog_reuses_parsed_patch_payload(self):
        payload = {
            "data": {
                "test-item": {
                    "name": "Synthetic Data Dragon Item",
                    "maps": {"11": True},
                    "gold": {"total": 2400, "purchasable": True},
                }
            }
        }
        with patch(
            "pickmychamp.counter_guides._current_patch_item_payload",
            return_value=("test-patch", payload),
        ) as load_payload:
            patch_version, catalog = current_patch_item_catalog()

        self.assertEqual(patch_version, "test-patch")
        self.assertEqual(catalog["test-item"].total_cost, 2400)
        load_payload.assert_called_once_with()

    def test_existing_patch_catalog_contract_uses_mocked_data_dragon_responses(self):
        item_payload = {
            "data": {
                "test-item": {
                    "name": "Synthetic Data Dragon Item",
                    "maps": {"11": True},
                    "gold": {"total": 2400, "purchasable": True},
                }
            }
        }
        rune_payload = [
            {
                "key": "Precision",
                "name": "Precision",
                "slots": [{"runes": [{"key": "FleetFootwork", "name": "Fleet Footwork"}]}],
            }
        ]
        responses = [
            BytesIO(b'["test-patch"]'),
            BytesIO(json.dumps(item_payload).encode("utf-8")),
            BytesIO(json.dumps(rune_payload).encode("utf-8")),
        ]

        with patch("pickmychamp.counter_guides.urlopen", side_effect=responses) as open_url:
            catalog = current_patch_catalog()

        self.assertEqual(
            catalog,
            (
                "test-patch",
                {"test-item": "Synthetic Data Dragon Item"},
                {"FleetFootwork": "Fleet Footwork"},
                {"Precision": "Precision"},
            ),
        )
        self.assertEqual(open_url.call_count, 3)

    def test_synthetic_snapshot_replays_the_same_ranked_recommendations(self):
        first = rank_item_recommendations(self.snapshot, self.rules, self.catalog)
        second = rank_item_recommendations(self.snapshot, self.rules, self.catalog)

        expected = [
            (
                item["item_id"],
                item["action"],
                item["priority"],
                item["gold_shortfall"],
            )
            for item in self.fixture["expected"]
        ]
        actual = [
            (item.item_id, item.action, item.priority, item.gold_shortfall)
            for item in first
        ]
        self.assertEqual(actual, expected)
        self.assertEqual(first, second)
        self.assertTrue(all(item.state_version == 42 for item in first))

    def test_gold_changes_buy_action_without_changing_rule_priority(self):
        richer_snapshot = replace(self.snapshot, gold=3500)
        recommendations = rank_item_recommendations(
            richer_snapshot, self.rules, self.catalog
        )

        self.assertEqual(recommendations[0].action, "buy_next")
        self.assertEqual(recommendations[0].priority, 90)
        self.assertEqual(recommendations[0].gold_shortfall, 0)

    def test_unknown_item_rule_fails_closed(self):
        unknown_rule = replace(self.rules[0], item_id="missing-item")

        with self.assertRaisesRegex(ValueError, "missing from the item catalog"):
            rank_item_recommendations(
                self.snapshot, (unknown_rule,), self.catalog
            )

    def test_snapshot_rejects_invalid_level(self):
        invalid_snapshot = {**self.fixture["snapshot"], "level": 19}

        with self.assertRaisesRegex(ValueError, "between 1 and 18"):
            GameSnapshot.from_dict(invalid_snapshot)


if __name__ == "__main__":
    unittest.main()
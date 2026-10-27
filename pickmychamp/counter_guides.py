from dataclasses import dataclass
from functools import lru_cache
import json
from urllib.error import URLError
from urllib.request import urlopen


@dataclass(frozen=True)
class CounterPick:
    champion: str
    reason: str
    support: str
    support_alternative: str
    primary_tree: str
    secondary_tree: str
    primary_runes: tuple[str, ...]
    secondary_runes: tuple[str, ...]
    rune_shards: str
    summoner_spells: str
    skill_order: str
    starting_item: str
    build: tuple[str, ...]
    situational_items: tuple[tuple[str, str], ...]
    lane_plan: str


VAYNE_ADC_COUNTERS = (
    CounterPick(
        champion="Caitlyn",
        reason=(
            "Her range and traps let her contest Vayne's last hits before Vayne "
            "reaches her core items."
        ),
        support="Karma",
        support_alternative="Lux",
        primary_tree="Precision",
        secondary_tree="Sorcery",
        primary_runes=("FleetFootwork", "PresenceOfMind", "LegendBloodline", "CutDown"),
        secondary_runes=("AbsoluteFocus", "GatheringStorm"),
        rune_shards="Attack Speed, Adaptive Force, Scaling Health.",
        summoner_spells="Flash + Heal; take Cleanse instead of Heal against reliable hard crowd control.",
        skill_order="Q > W > E; ordre indicatif: Q-W-E-Q-Q-R, puis Q max, W max, E max.",
        starting_item="1055",
        build=("3032", "3006", "3031", "3094", "3036", "3072"),
        situational_items=(
            ("3033", "Consider against heavy healing instead of Lord Dominik's."),
            ("3026", "Defensive option if an assassin can reach Caitlyn."),
        ),
        lane_plan=(
            "Use your range to last-hit and place traps on predictable paths. Save E "
            "to dodge engages and do not push without jungle vision. Karma or Lux "
            "strengthens poke and helps control Vayne's access to the wave."
        ),
    ),
    CounterPick(
        champion="Draven",
        reason=(
            "An aggressive choice for winning lane early; his axes create strong "
            "pressure when you can catch them without overexposing yourself."
        ),
        support="Nautilus",
        support_alternative="Leona",
        primary_tree="Precision",
        secondary_tree="Sorcery",
        primary_runes=("PressTheAttack", "Triumph", "LegendBloodline", "CoupDeGrace"),
        secondary_runes=("NimbusCloak", "GatheringStorm"),
        rune_shards="Attack Speed, Adaptive Force, Scaling Health.",
        summoner_spells="Flash + Heal; take Cleanse if avoiding enemy crowd control is essential.",
        skill_order="Q > W > E; ordre indicatif: Q-W-E-Q-Q-R, puis Q max, W max, E max.",
        starting_item="1055",
        build=("6672", "3006", "3031", "3036", "3072", "3026"),
        situational_items=(
            ("3033", "Consider against heavy healing instead of Lord Dominik's."),
            ("6673", "Defensive alternative when burst fights are dangerous."),
        ),
        lane_plan=(
            "Look for short trades with an active axe when your support can follow. "
            "Do not chase Vayne down a long lane without vision: her invisibility "
            "and wall control can turn an all-in."
        ),
    ),
    CounterPick(
        champion="Ashe",
        reason=(
            "A utility-focused option: range, slows and an ultimate enable coordinated "
            "trades without relying on constant all-ins."
        ),
        support="Karma",
        support_alternative="Nami",
        primary_tree="Precision",
        secondary_tree="Inspiration",
        primary_runes=("LethalTempo", "PresenceOfMind", "LegendBloodline", "CutDown"),
        secondary_runes=("BiscuitDelivery", "ApproachVelocity"),
        rune_shards="Attack Speed, Adaptive Force, Scaling Health.",
        summoner_spells="Flash + Heal; take Cleanse against crowd control you must avoid.",
        skill_order="W > Q > E; ordre indicatif: W-Q-E-W-W-R, puis W max, Q max, E max.",
        starting_item="1055",
        build=("3032", "3006", "3085", "3036", "3072", "3026"),
        situational_items=(
            ("3033", "Consider against heavy healing instead of Lord Dominik's."),
            ("3094", "Alternative for increasing the range of a charged attack."),
        ),
        lane_plan=(
            "Poke with W when Vayne walks up to last-hit; save E to check gank areas. "
            "Your ultimate can engage from range, ideally with a support who can chain "
            "crowd control."
        ),
    ),
)

@lru_cache(maxsize=1)
def champion_catalog() -> tuple[str, list[dict[str, str]]]:
    try:
        with urlopen(
            "https://ddragon.leagueoflegends.com/api/versions.json", timeout=10
        ) as response:
            versions = json.loads(response.read().decode("utf-8"))
        if not isinstance(versions, list) or not versions:
            raise RuntimeError("Data Dragon did not return a game patch.")
        patch = versions[0]
        with urlopen(
            f"https://ddragon.leagueoflegends.com/cdn/{patch}/data/en_US/champion.json",
            timeout=10,
        ) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (URLError, TimeoutError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Could not load the current Riot champion list: {exc}") from exc

    champions = sorted(
        (
            {"id": champion["id"], "name": champion["name"]}
            for champion in payload.get("data", {}).values()
        ),
        key=lambda champion: champion["name"].casefold(),
    )
    if not champions:
        raise RuntimeError("Riot Data Dragon returned an empty champion list.")
    return patch, champions


def current_patch_catalog() -> tuple[str, dict[str, str], dict[str, str], dict[str, str]]:
    try:
        with urlopen(
            "https://ddragon.leagueoflegends.com/api/versions.json", timeout=10
        ) as response:
            versions = json.loads(response.read().decode("utf-8"))
        if not isinstance(versions, list) or not versions:
            raise RuntimeError("Data Dragon n'a renvoyé aucune version.")
        patch = versions[0]
        with urlopen(
            f"https://ddragon.leagueoflegends.com/cdn/{patch}/data/en_US/item.json",
            timeout=10,
        ) as response:
            item_payload = json.loads(response.read().decode("utf-8"))
        with urlopen(
            f"https://ddragon.leagueoflegends.com/cdn/{patch}/data/en_US/runesReforged.json",
            timeout=10,
        ) as response:
            rune_payload = json.loads(response.read().decode("utf-8"))
    except (URLError, TimeoutError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Could not load current Riot item and rune data: {exc}") from exc

    items = {
        item_id: item["name"]
        for item_id, item in item_payload.get("data", {}).items()
        if item.get("maps", {}).get("11") and item.get("gold", {}).get("purchasable")
    }
    runes = {
        rune["key"]: rune["name"]
        for tree in rune_payload
        for slot in tree["slots"]
        for rune in slot["runes"]
    }
    trees = {tree["key"]: tree["name"] for tree in rune_payload}
    return patch, items, runes, trees


def counter_picks(enemy: str, role: str) -> tuple[CounterPick, ...]:
    if enemy.strip().casefold() not in {"vayne", "shauna vayne"}:
        raise ValueError(
            f"No verified matchup guide is available for {enemy} yet. "
            "The current hand-authored guide covers Vayne ADC only. "
            "Choose Vayne to preview the available guide."
        )
    if role.strip().casefold() not in {"adc", "bot", "bottom"}:
        raise ValueError("The Vayne guide is available for ADC/Bot only.")
    return VAYNE_ADC_COUNTERS


def render_runes(
    pick: CounterPick, runes: dict[str, str], trees: dict[str, str]
) -> str:
    missing = [
        key
        for key in (*pick.primary_runes, *pick.secondary_runes)
        if key not in runes
    ]
    missing.extend(
        tree
        for tree in (pick.primary_tree, pick.secondary_tree)
        if tree not in trees
    )
    if missing:
        raise RuntimeError(
            "These guide runes are not present in the current patch data: "
            + ", ".join(missing)
        )
    return (
        f"{trees[pick.primary_tree]}: "
        + ", ".join(runes[key] for key in pick.primary_runes)
        + f" | {trees[pick.secondary_tree]}: "
        + ", ".join(runes[key] for key in pick.secondary_runes)
    )


def render_build(pick: CounterPick, items: dict[str, str]) -> tuple[str, ...]:
    missing = [
        item_id
        for item_id in (
            pick.starting_item,
            *pick.build,
            *(item_id for item_id, _ in pick.situational_items),
        )
        if item_id not in items
    ]
    if missing:
        raise RuntimeError(
            "A build item is not available in the current patch data "
            f"(IDs Data Dragon: {', '.join(missing)})."
        )
    return tuple(items[item_id] for item_id in pick.build)

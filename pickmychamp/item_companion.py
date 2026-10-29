from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from .recommendations import normalize_role


SUMMONERS_RIFT_MAP_ID = 11


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string.")
    return value.strip()


def _integer(value: Any, field: str, minimum: int = 0) -> int:
    if type(value) is not int or value < minimum:
        raise ValueError(f"{field} must be an integer of at least {minimum}.")
    return value


def _strings(value: Any, field: str) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{field} must be a list of strings.")
    return tuple(_text(item, field) for item in value)


def _records(value: Any, field: str) -> tuple[Mapping[str, Any], ...]:
    if not isinstance(value, list) or not all(
        isinstance(item, Mapping) for item in value
    ):
        raise ValueError(f"{field} must be a list of objects.")
    return tuple(value)


@dataclass(frozen=True)
class TeamMember:
    champion: str
    role: str

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "TeamMember":
        return cls(_text(value.get("champion"), "ally.champion"), _text(value.get("role"), "ally.role"))


@dataclass(frozen=True)
class OpponentState:
    champion: str
    role: str
    item_ids: tuple[str, ...]

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "OpponentState":
        return cls(
            _text(value.get("champion"), "opponent.champion"),
            _text(value.get("role"), "opponent.role"),
            _strings(value.get("item_ids", []), "opponent.item_ids"),
        )


@dataclass(frozen=True)
class ObjectiveState:
    name: str
    state: str
    seconds_until_spawn: int | None = None

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "ObjectiveState":
        seconds = value.get("seconds_until_spawn")
        if seconds is not None:
            seconds = _integer(seconds, "objective.seconds_until_spawn")
        return cls(
            _text(value.get("name"), "objective.name"),
            _text(value.get("state"), "objective.state"),
            seconds,
        )


@dataclass(frozen=True)
class RecentEvent:
    kind: str
    seconds_ago: int

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "RecentEvent":
        return cls(
            _text(value.get("kind"), "event.kind"),
            _integer(value.get("seconds_ago"), "event.seconds_ago"),
        )


@dataclass(frozen=True)
class CooldownContext:
    ready_abilities: tuple[str, ...]
    ultimate_ready: bool

    @classmethod
    def from_dict(cls, value: Any) -> "CooldownContext":
        if not isinstance(value, Mapping):
            raise ValueError("cooldown_context must be an object.")
        ultimate_ready = value.get("ultimate_ready")
        if not isinstance(ultimate_ready, bool):
            raise ValueError("cooldown_context.ultimate_ready must be a boolean.")
        return cls(
            _strings(value.get("ready_abilities", []), "cooldown_context.ready_abilities"),
            ultimate_ready,
        )


@dataclass(frozen=True)
class GameSnapshot:
    state_version: int
    champion: str
    role: str
    level: int
    gold: int
    item_ids: tuple[str, ...]
    rune_ids: tuple[str, ...]
    cooldown_context: CooldownContext
    allies: tuple[TeamMember, ...]
    visible_opponents: tuple[OpponentState, ...]
    objectives: tuple[ObjectiveState, ...]
    recent_events: tuple[RecentEvent, ...]
    signals: frozenset[str]

    @classmethod
    def from_dict(cls, value: Any) -> "GameSnapshot":
        if not isinstance(value, Mapping):
            raise ValueError("game snapshot must be an object.")
        snapshot = cls(
            state_version=_integer(value.get("state_version"), "state_version"),
            champion=_text(value.get("champion"), "champion"),
            role=_text(value.get("role"), "role"),
            level=_integer(value.get("level"), "level", minimum=1),
            gold=_integer(value.get("gold"), "gold"),
            item_ids=_strings(value.get("item_ids", []), "item_ids"),
            rune_ids=_strings(value.get("rune_ids", []), "rune_ids"),
            cooldown_context=CooldownContext.from_dict(value.get("cooldown_context")),
            allies=tuple(
                TeamMember.from_dict(row) for row in _records(value.get("allies"), "allies")
            ),
            visible_opponents=tuple(
                OpponentState.from_dict(row)
                for row in _records(value.get("visible_opponents"), "visible_opponents")
            ),
            objectives=tuple(
                ObjectiveState.from_dict(row)
                for row in _records(value.get("objectives"), "objectives")
            ),
            recent_events=tuple(
                RecentEvent.from_dict(row)
                for row in _records(value.get("recent_events"), "recent_events")
            ),
            signals=frozenset(_strings(value.get("signals", []), "signals")),
        )
        if snapshot.level > 18:
            raise ValueError("level must be between 1 and 18.")
        normalize_role(snapshot.role)
        return snapshot


@dataclass(frozen=True)
class ItemDefinition:
    item_id: str
    name: str
    total_cost: int
    map_ids: tuple[int, ...]
    purchasable: bool

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "ItemDefinition":
        map_ids = value.get("map_ids")
        if not isinstance(map_ids, list):
            raise ValueError("item.map_ids must be a list of integers.")
        purchasable = value.get("purchasable")
        if not isinstance(purchasable, bool):
            raise ValueError("item.purchasable must be a boolean.")
        return cls(
            item_id=_text(value.get("item_id"), "item.item_id"),
            name=_text(value.get("name"), "item.name"),
            total_cost=_integer(value.get("total_cost"), "item.total_cost"),
            map_ids=tuple(_integer(map_id, "item.map_ids") for map_id in map_ids),
            purchasable=purchasable,
        )


def parse_data_dragon_item_catalog(payload: Any) -> dict[str, ItemDefinition]:
    if not isinstance(payload, Mapping):
        raise ValueError("Data Dragon item payload must be an object.")
    raw_items = payload.get("data")
    if not isinstance(raw_items, Mapping) or not raw_items:
        raise ValueError("Data Dragon item payload must contain a non-empty data object.")

    catalog = {}
    for raw_item_id, raw_item in raw_items.items():
        item_id = _text(raw_item_id, "item ID")
        if not isinstance(raw_item, Mapping):
            raise ValueError(f"Data Dragon item {item_id} must be an object.")
        maps = raw_item.get("maps")
        gold = raw_item.get("gold")
        if not isinstance(maps, Mapping) or not isinstance(gold, Mapping):
            raise ValueError(f"Data Dragon item {item_id} is missing maps or gold data.")

        map_ids = []
        for raw_map_id, available in maps.items():
            if not isinstance(available, bool):
                raise ValueError(f"Data Dragon item {item_id} has an invalid map flag.")
            if available:
                try:
                    map_ids.append(int(raw_map_id))
                except (TypeError, ValueError) as exc:
                    raise ValueError(
                        f"Data Dragon item {item_id} has an invalid map ID."
                    ) from exc

        try:
            catalog[item_id] = ItemDefinition.from_dict(
                {
                    "item_id": item_id,
                    "name": raw_item.get("name"),
                    "total_cost": gold.get("total"),
                    "map_ids": map_ids,
                    "purchasable": gold.get("purchasable"),
                }
            )
        except ValueError as exc:
            raise ValueError(f"Invalid Data Dragon item {item_id}: {exc}") from exc

    return catalog


@dataclass(frozen=True)
class ItemRule:
    item_id: str
    priority: int
    reason: str
    roles: tuple[str, ...] = ()
    required_signals: frozenset[str] = frozenset()
    blocked_signals: frozenset[str] = frozenset()

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "ItemRule":
        rule = cls(
            item_id=_text(value.get("item_id"), "rule.item_id"),
            priority=_integer(value.get("priority"), "rule.priority"),
            reason=_text(value.get("reason"), "rule.reason"),
            roles=_strings(value.get("roles", []), "rule.roles"),
            required_signals=frozenset(
                _strings(value.get("required_signals", []), "rule.required_signals")
            ),
            blocked_signals=frozenset(
                _strings(value.get("blocked_signals", []), "rule.blocked_signals")
            ),
        )
        if rule.required_signals & rule.blocked_signals:
            raise ValueError("a rule cannot require and block the same signal.")
        for role in rule.roles:
            normalize_role(role)
        return rule


@dataclass(frozen=True)
class ItemRecommendation:
    item_id: str
    name: str
    action: str
    priority: int
    total_cost: int
    gold_shortfall: int
    reason: str
    state_version: int


def rank_item_recommendations(
    snapshot: GameSnapshot,
    rules: tuple[ItemRule, ...] | list[ItemRule],
    catalog: Mapping[str, ItemDefinition],
) -> tuple[ItemRecommendation, ...]:
    player_role = normalize_role(snapshot.role)
    owned_items = set(snapshot.item_ids)
    seen_items: set[str] = set()
    ranked: list[ItemRecommendation] = []

    for rule in rules:
        if rule.item_id in seen_items:
            raise ValueError(f"Duplicate item rule for {rule.item_id}.")
        seen_items.add(rule.item_id)
        item = catalog.get(rule.item_id)
        if item is None:
            raise ValueError(f"Item {rule.item_id} is missing from the item catalog.")
        if item.item_id != rule.item_id:
            raise ValueError(f"Catalog key does not match item ID {rule.item_id}.")
        if not item.purchasable or SUMMONERS_RIFT_MAP_ID not in item.map_ids:
            continue
        if item.item_id in owned_items:
            continue
        if rule.roles and player_role not in {normalize_role(role) for role in rule.roles}:
            continue
        if not rule.required_signals.issubset(snapshot.signals):
            continue
        if rule.blocked_signals.intersection(snapshot.signals):
            continue

        shortfall = max(0, item.total_cost - snapshot.gold)
        ranked.append(
            ItemRecommendation(
                item_id=item.item_id,
                name=item.name,
                action="buy_next" if shortfall == 0 else "save_for",
                priority=rule.priority,
                total_cost=item.total_cost,
                gold_shortfall=shortfall,
                reason=rule.reason,
                state_version=snapshot.state_version,
            )
        )

    return tuple(sorted(ranked, key=lambda item: (-item.priority, item.total_cost, item.item_id)))
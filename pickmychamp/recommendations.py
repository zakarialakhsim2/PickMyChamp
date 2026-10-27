from collections import defaultdict
from dataclasses import dataclass
from typing import Any


ROLE_ALIASES = {
    "TOP": "TOP",
    "JUNGLE": "JUNGLE",
    "MID": "MIDDLE",
    "MIDDLE": "MIDDLE",
    "ADC": "BOTTOM",
    "BOT": "BOTTOM",
    "BOTTOM": "BOTTOM",
    "SUPPORT": "UTILITY",
    "SUP": "UTILITY",
    "UTILITY": "UTILITY",
}

QUEUE_IDS = {
    "ranked": {420},
    "flex": {440},
    "normal": {400, 430, 490},
}


def normalize_role(role: str) -> str:
    try:
        return ROLE_ALIASES[role.strip().upper()]
    except KeyError as exc:
        raise ValueError(
            "Rôle invalide. Choisissez top, jungle, mid, adc/bot ou support."
        ) from exc


def filter_queue(matches: list[dict], queue: str | None) -> list[dict]:
    if queue is None:
        return matches
    try:
        allowed_ids = QUEUE_IDS[queue.lower()]
    except KeyError as exc:
        raise ValueError("File invalide. Choisissez ranked, flex ou normal.") from exc
    return [
        match for match in matches
        if match.get("info", {}).get("queueId") in allowed_ids
    ]


@dataclass
class ChampionStats:
    champion: str
    games: int = 0
    wins: int = 0
    kills: int = 0
    deaths: int = 0
    assists: int = 0
    mastery_points: int = 0
    declared_mastery: bool = False

    @property
    def win_rate(self) -> float:
        return 100 * self.wins / self.games if self.games else 0

    @property
    def kda(self) -> float:
        return (self.kills + self.assists) / max(self.deaths, 1)


def player_matches(api: Any, riot_id: str, count: int = 20) -> tuple[str, list[dict]]:
    game_name, tag_line = riot_id.rsplit("#", 1)
    account = api.account_by_riot_id(game_name.strip(), tag_line.strip())
    puuid = account["puuid"]
    matches = [api.match(match_id) for match_id in api.match_ids(puuid, count)]
    return puuid, matches


def participant_for(match: dict, puuid: str) -> dict | None:
    info = match.get("info", {})
    return next(
        (participant for participant in info.get("participants", [])
         if participant.get("puuid") == puuid),
        None,
    )


def aggregate_matches(
    matches: list[dict], puuid: str, role: str | None = None
) -> dict[str, ChampionStats]:
    selected_role = normalize_role(role) if role else None
    stats: dict[str, ChampionStats] = defaultdict(lambda: ChampionStats(champion=""))
    for match in matches:
        participant = participant_for(match, puuid)
        if not participant:
            continue
        match_role = participant.get("teamPosition", "")
        if selected_role and match_role != selected_role:
            continue
        champion = participant.get("championName")
        if not champion:
            continue
        item = stats[champion]
        item.champion = champion
        item.games += 1
        item.wins += int(bool(participant.get("win")))
        item.kills += int(participant.get("kills", 0))
        item.deaths += int(participant.get("deaths", 0))
        item.assists += int(participant.get("assists", 0))
    return dict(stats)


def attach_masteries(
    stats: dict[str, ChampionStats], masteries: list[dict], champion_names: dict[int, str]
) -> None:
    for mastery in masteries:
        name = champion_names.get(mastery.get("championId"))
        if not name:
            continue
        item = stats.setdefault(name, ChampionStats(champion=name))
        item.mastery_points = int(mastery.get("championPoints", 0))


def rank_champions(
    stats: dict[str, ChampionStats], mastered: list[str], limit: int = 3
) -> list[tuple[ChampionStats, float]]:
    mastered_names = {name.casefold() for name in mastered}
    for name in mastered:
        item = stats.setdefault(name, ChampionStats(champion=name))
        item.declared_mastery = True
    candidates = [
        item for item in stats.values()
        if item.games > 0 or item.mastery_points > 0
        or item.champion.casefold() in mastered_names
    ]

    def score(item: ChampionStats) -> float:
        # A light prior keeps one lucky game from dominating a longer record.
        smoothed_win_rate = (item.wins + 3) / (item.games + 6)
        kda_signal = min(item.kda, 5) / 5
        mastery_signal = (
            1 if item.declared_mastery else min(item.mastery_points / 100_000, 1)
        )
        experience = min(item.games / 20, 1)
        return (
            0.65 * smoothed_win_rate
            + 0.15 * kda_signal
            + 0.10 * mastery_signal
            + 0.10 * experience
        )

    ranked = sorted(candidates, key=score, reverse=True)[:limit]
    return [(item, score(item)) for item in ranked]


def confidence(games: int) -> int:
    return min(95, round(100 * games / (games + 10))) if games else 0

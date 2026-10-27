from dataclasses import dataclass
from html.parser import HTMLParser
from functools import lru_cache
import json
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


PAGE_LIMIT = 500_000
SOURCE_ROOT = "https://u.gg/lol/champions"
OPGG_MCP_URL = "https://mcp-api.op.gg/mcp"
ROLE_NAMES = {
    "ADC": "adc",
    "BOT": "adc",
    "BOTTOM": "adc",
    "TOP": "top",
    "JUNGLE": "jungle",
    "MID": "mid",
    "MIDDLE": "mid",
    "SUPPORT": "support",
    "UTILITY": "support",
}
UGG_SLUGS = {
    "aurelion sol": "aurelion-sol",
    "cho'gath": "chogath",
    "dr. mundo": "dr-mundo",
    "jarvan iv": "jarvan-iv",
    "lee sin": "lee-sin",
    "master yi": "master-yi",
    "miss fortune": "missfortune",
    "nunu & willump": "nunu-willump",
    "rek'sai": "reksai",
    "twisted fate": "twisted-fate",
    "vel'koz": "velkoz",
    "xin zhao": "xin-zhao",
}
UGG_DISPLAY_NAMES = {
    "nunu & willump": "nunu",
}
CURATED_FALLBACK_PICKS = (
    {"champion": "Caitlyn", "slug": "caitlyn"},
    {"champion": "Draven", "slug": "draven"},
    {"champion": "Ashe", "slug": "ashe"},
)


class CounterPageParser(HTMLParser):
    def __init__(self, enemy: str):
        super().__init__(convert_charrefs=True)
        self.enemy = UGG_DISPLAY_NAMES.get(enemy.casefold(), enemy.casefold())
        self.in_best_picks = False
        self.in_anchor = False
        self.anchor_slug = ""
        self.anchor_text: list[str] = []
        self.entries: list[dict] = []
        self.context: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "a":
            return
        attributes = dict(attrs)
        href = attributes.get("href", "") or ""
        match = re.fullmatch(r"/lol/champions/([^/]+)/build/?", href)
        if self.in_best_picks and match:
            self.in_anchor = True
            self.anchor_slug = match.group(1)
            self.anchor_text = []

    def handle_endtag(self, tag: str) -> None:
        if tag != "a" or not self.in_anchor:
            return
        text = " ".join(part.strip() for part in self.anchor_text if part.strip())
        win_match = re.search(r"(\d+(?:\.\d+)?)%\s*WR\b", text)
        games_match = re.search(r"([\d,]+)\s*games\b", text, re.IGNORECASE)
        if win_match and games_match:
            name = text[:win_match.start()].strip()
            games = int(games_match.group(1).replace(",", ""))
            if name and games > 0:
                self.entries.append(
                    {
                        "champion": name,
                        "slug": self.anchor_slug,
                        "win_rate": float(win_match.group(1)),
                        "games": games,
                    }
                )
        self.in_anchor = False
        self.anchor_slug = ""
        self.anchor_text = []

    def handle_data(self, data: str) -> None:
        text = data.strip()
        if not text:
            return
        self.context.append(text)
        if self.in_anchor:
            self.anchor_text.append(text)
        if text.casefold().startswith("best picks vs "):
            page_enemy = text[len("Best Picks vs "):].strip().casefold()
            if page_enemy == self.enemy:
                self.in_best_picks = True
        elif self.in_best_picks and text.casefold().startswith("worst picks vs "):
            self.in_best_picks = False


def curated_fallback(enemy: str, role: str | None, url: str) -> dict | None:
    if enemy.casefold() != "vayne" or ROLE_NAMES.get((role or "").upper()) != "adc":
        return {
            "enemy": enemy,
            "enemy_role": ROLE_NAMES.get((role or "").upper()),
            "patch": "unavailable",
            "scope": "U.GG unavailable from serverless hosting",
            "source_url": url,
            "source": "U.GG unavailable",
            "fallback_message": (
                "U.GG is blocking requests from the deployment server. "
                "Try Vayne ADC for the built-in curated guide, or try again later."
            ),
            "picks": [],
        }
    return {
        "enemy": enemy,
        "enemy_role": "adc",
        "patch": "current guide",
        "scope": "PickMyChamp curated guide",
        "source_url": url,
        "source": "PickMyChamp guide",
        "fallback_message": (
            "Live U.GG statistics are unavailable, so these recommendations use "
            "the built-in PickMyChamp guide."
        ),
        "picks": [
            {**pick, "win_rate": 0.0, "games": 0}
            for pick in CURATED_FALLBACK_PICKS
        ],
    }


def opgg_matchup_counters(enemy: str, role: str) -> dict:
        champion = re.sub(r"[^A-Za-z0-9]+", "_", enemy).strip("_").upper()
        init_body = json.dumps(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-03-26",
                    "capabilities": {},
                    "clientInfo": {"name": "PickMyChamp", "version": "1.0"},
                },
            }
        ).encode()
        init_request = Request(
            OPGG_MCP_URL,
            data=init_body,
            headers={"Accept": "application/json, text/event-stream", "Content-Type": "application/json"},
        )
        with urlopen(init_request, timeout=15) as response:
            session_id = response.headers.get("Mcp-Session-Id")
        if not session_id:
            raise RuntimeError("OP.GG did not return a session.")

        fields = [
            "champion",
            "position",
            "data.weak_counters[].{champion_name,counter_win_rate,my_win_rate,play,win_rate}",
            "data.summary.positions[].counters[].{champion_name,play,win}",
        ]
        call_body = json.dumps(
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "lol_get_champion_analysis",
                    "arguments": {
                        "game_mode": "ranked",
                        "champion": champion,
                        "position": ROLE_NAMES.get(role.upper(), "adc"),
                        "desired_output_fields": fields,
                    },
                },
            }
        ).encode()
        call_request = Request(
            OPGG_MCP_URL,
            data=call_body,
            headers={
                "Accept": "application/json, text/event-stream",
                "Content-Type": "application/json",
                "Mcp-Session-Id": session_id,
            },
        )
        with urlopen(call_request, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
        text = payload["result"]["content"][0]["text"]
        entries = re.findall(
            r'WeakCounter\("([^"]+)",(\d+),([0-9.]+),([0-9.]+),([0-9.]+)\)',
            text,
        )
        if not entries:
            raw_entries = re.findall(r'Counter\("([^"]+)",(\d+),(\d+)\)', text)
            entries = [
                (name, play, "0", str(int(wins) / int(play)), str(int(wins) / int(play)))
                for name, play, wins in raw_entries
                if int(play) > 0
            ]
        if not entries:
            raise ValueError(f"OP.GG returned no counter data for {enemy}.")
        return {
            "enemy": enemy,
            "enemy_role": ROLE_NAMES.get(role.upper()),
            "patch": "current",
            "scope": "OP.GG ranked",
            "source_url": f"https://op.gg/lol/champions/{enemy.lower()}/build",
            "source": "OP.GG",
            "picks": [
                {
                    "champion": name,
                    "slug": re.sub(r"[^a-z0-9]+", "", name.casefold()),
                    "win_rate": float(counter_win_rate) * 100,
                    "games": int(play),
                }
                for name, play, _my_win_rate, counter_win_rate, _win_rate in entries[:3]
            ],
        }
@lru_cache(maxsize=64)
def matchup_counters(enemy: str, role: str | None = None) -> dict:
    normalized = enemy.strip()
    slug = UGG_SLUGS.get(
        normalized.casefold(),
        re.sub(r"[^a-z0-9]+", "", normalized.casefold()),
    )
    if not slug:
        raise ValueError("Select a valid enemy champion.")
    requested_role = ROLE_NAMES.get((role or "").strip().upper())
    url = f"{SOURCE_ROOT}/{slug}/counter"
    if requested_role:
        url = f"{url}?role={requested_role}"
    request = Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://u.gg/",
        },
    )
    try:
        with urlopen(request, timeout=15) as response:
            if response.status != 200:
                raise RuntimeError(f"U.GG returned HTTP {response.status}.")
            page = response.read(PAGE_LIMIT).decode("utf-8", "replace")
    except HTTPError as exc:
        if exc.code == 403:
            try:
                return opgg_matchup_counters(normalized, role or "adc")
            except (HTTPError, URLError, TimeoutError, KeyError, ValueError, json.JSONDecodeError):
                pass
        fallback = curated_fallback(normalized, role, url)
        if exc.code == 403 and fallback:
            return fallback
        raise RuntimeError(f"U.GG returned HTTP {exc.code} for {normalized}.") from exc
    except (URLError, TimeoutError) as exc:
        raise RuntimeError(f"Could not load matchup data from U.GG: {exc}") from exc

    parser = CounterPageParser(normalized)
    parser.feed(page)
    title = " ".join(parser.context[:100])
    page_role = re.search(
        rf"{re.escape(normalized)}\s*Counter\s+for\s+(ADC|Bot|Top|Jungle|Mid|Support)",
        title,
        re.IGNORECASE,
    )
    patch_match = re.search(r"\bPatch\s+([\d.]+)", title)
    if not parser.entries:
        raise ValueError(
            f"U.GG has no readable counter table for {normalized}. "
            "Try again later or choose another champion."
        )
    return {
        "enemy": normalized,
        "enemy_role": ROLE_NAMES.get(page_role.group(1).upper()) if page_role else None,
        "patch": patch_match.group(1) if patch_match else "not specified",
        "scope": "World Emerald+",
        "source_url": url,
        "source": "U.GG",
        "picks": parser.entries[:3],
    }


def build_url(slug: str) -> str:
    return f"{SOURCE_ROOT}/{slug}/build"

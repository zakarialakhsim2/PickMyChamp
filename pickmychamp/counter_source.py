from dataclasses import dataclass
from html.parser import HTMLParser
from functools import lru_cache
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


PAGE_LIMIT = 500_000
SOURCE_ROOT = "https://u.gg/lol/champions"
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
        fallback = curated_fallback(normalized, role, url)
        if exc.code == 403:
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

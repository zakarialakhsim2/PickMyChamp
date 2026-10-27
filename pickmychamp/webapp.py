import json
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse
import webbrowser

from pickmychamp.config import AccountConfig, load_config, save_config
from pickmychamp.counter_guides import (
    champion_catalog,
    counter_picks,
    current_patch_catalog,
    render_build,
    render_runes,
)
from pickmychamp.counter_source import build_url, matchup_counters
from pickmychamp.recommendations import normalize_role
from pickmychamp.riot_api import PLATFORM_ROUTES


WEB_ROOT = Path(__file__).resolve().parent.parent / "web"
MAX_REQUEST_SIZE = 64 * 1024


def counter_payload(enemy: str, role: str) -> dict:
    selected_role = normalize_role(role)
    matchup = matchup_counters(enemy, role)
    role_warning = None
    if matchup["enemy_role"] and selected_role != normalize_role(matchup["enemy_role"]):
        role_warning = (
            f"Your selected role is {role}, but U.GG's matchup table is for "
            f"{matchup['enemy_role']}. These picks may not fit your lane."
        )
    guide_by_name = {}
    try:
        guides = counter_picks(enemy, role)
    except ValueError:
        guides = ()
    if guides:
        guide_patch, items, runes, rune_trees = current_patch_catalog()
        for guide in guides:
            guide_by_name[guide.champion.casefold()] = {
                "guide": guide,
                "runes": render_runes(guide, runes, rune_trees),
                "build": list(render_build(guide, items)),
                "starting_item": items[guide.starting_item],
                "items": items,
                "patch": guide_patch,
            }

    picks = []
    for stat in matchup["picks"]:
        guide_data = guide_by_name.get(stat["champion"].casefold())
        guide = guide_data["guide"] if guide_data else None
        picks.append(
            {
                "champion": stat["champion"],
                "reason": (
                    f"{stat['win_rate']:.2f}% win rate across {stat['games']:,} "
                    "games in U.GG's matchup dataset."
                    if matchup["source"] == "U.GG"
                    else "Curated guide pick; live matchup statistics are unavailable."
                ),
                "win_rate": stat["win_rate"],
                "games": stat["games"],
                "has_stats": matchup["source"] == "U.GG",
                "support": guide.support if guide else "Not included in matchup data",
                "support_alternative": (
                    guide.support_alternative if guide else "Check a duo-synergy guide"
                ),
                "runes": (
                    guide_data["runes"] if guide_data
                    else "See the current English build guide"
                ),
                "rune_shards": (
                    guide.rune_shards if guide else "Not included in matchup statistics"
                ),
                "spells": (
                    guide.summoner_spells if guide
                    else "See the current English build guide"
                ),
                "skills": (
                    guide.skill_order if guide
                    else "See the current English build guide"
                ),
                "starting_item": (
                    guide_data["starting_item"] if guide_data else "See the build guide"
                ),
                "build": guide_data["build"] if guide_data else [],
                "build_url": build_url(stat["slug"]),
                "situational_items": (
                    [
                        {"item": guide_data["items"][item_id], "reason": reason}
                        for item_id, reason in guide.situational_items
                    ]
                    if guide_data else []
                ),
                "lane_plan": (
                    guide.lane_plan if guide
                    else "The matchup source provides win rate and sample size, not "
                    "lane-specific tactical advice."
                ),
                "guide_available": guide is not None,
            }
        )
    return {
        "enemy": matchup["enemy"],
        "role": role,
        "patch": matchup["patch"],
        "scope": matchup["scope"],
        "enemy_role": matchup["enemy_role"],
        "role_warning": role_warning,
        "source": matchup["source"],
        "source_url": matchup["source_url"],
        "picks": picks,
    }


def profile_payload() -> dict:
    try:
        profile = load_config()
    except FileNotFoundError:
        return {"configured": False}
    return {
        "configured": True,
        "riot_id": profile.riot_id,
        "region": profile.region,
        "primary_role": profile.primary_role.lower(),
        "secondary_roles": [role.lower() for role in profile.secondary_roles],
        "mastered_champions": profile.mastered_champions,
        "preferences": profile.preferences,
        "path": str(Path.home() / ".pickmychamp" / "config.json"),
    }


class PickMyChampHandler(BaseHTTPRequestHandler):
    server_version = "PickMyChamp/1.0"

    def log_message(self, format_string: str, *args: object) -> None:
        print(f"[web] {self.address_string()} {format_string % args}")

    def _json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict:
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError as exc:
            raise ValueError("En-tête Content-Length invalide.") from exc
        if length < 1 or length > MAX_REQUEST_SIZE:
            raise ValueError("Taille de requête invalide.")
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("Corps JSON invalide.") from exc
        if not isinstance(payload, dict):
            raise ValueError("Le corps JSON doit être un objet.")
        return payload

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/champions":
            try:
                patch, champions = champion_catalog()
                self._json(200, {"patch": patch, "champions": champions})
            except RuntimeError as exc:
                self._json(502, {"error": str(exc)})
            return
        if parsed.path == "/api/profile":
            try:
                self._json(200, profile_payload())
            except ValueError as exc:
                self._json(500, {"error": str(exc)})
            return
        if parsed.path == "/api/counter":
            params = parse_qs(parsed.query)
            enemy = params.get("enemy", [""])[0].strip()
            role = params.get("role", ["adc"])[0].strip()
            if not enemy:
                self._json(400, {"error": "Indique le champion adverse."})
                return
            try:
                self._json(200, counter_payload(enemy, role))
            except ValueError as exc:
                self._json(400, {"error": str(exc)})
            except RuntimeError as exc:
                self._json(502, {"error": str(exc)})
            return

        relative = "index.html" if parsed.path == "/" else parsed.path.lstrip("/")
        if relative not in {"index.html", "styles.css", "app.js"}:
            self.send_error(404)
            return
        file_path = WEB_ROOT / relative
        try:
            body = file_path.read_bytes()
        except OSError:
            self.send_error(404)
            return
        content_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:
        if urlparse(self.path).path != "/api/profile":
            self.send_error(404)
            return
        try:
            payload = self._read_json()
            riot_id = payload.get("riot_id", "")
            region = payload.get("region", "euw")
            primary_role = payload.get("primary_role", "")
            if not all(isinstance(value, str) for value in (riot_id, region, primary_role)):
                raise ValueError("Riot ID, région et rôle principal doivent être du texte.")
            riot_id = riot_id.strip()
            region = region.strip().lower()
            primary_role = primary_role.strip().lower()
            secondary_roles = payload.get("secondary_roles", [])
            champions = payload.get("mastered_champions", [])
            preferences = payload.get("preferences", [])
            if not isinstance(secondary_roles, list) or not all(
                isinstance(role, str) for role in secondary_roles
            ):
                raise ValueError("Les rôles secondaires doivent être une liste de textes.")
            if not isinstance(champions, list) or not all(
                isinstance(name, str) and name.strip() for name in champions
            ):
                raise ValueError("Les maîtrises doivent être une liste de noms de champions.")
            if not isinstance(preferences, list) or not all(
                isinstance(value, str) for value in preferences
            ):
                raise ValueError("Les préférences doivent être une liste de textes.")
            if region not in PLATFORM_ROUTES:
                raise ValueError(f"Région inconnue: {region}")
            normalize_role(primary_role)
            for secondary_role in secondary_roles:
                normalize_role(secondary_role)
            profile = AccountConfig(
                riot_id=riot_id,
                region=region,
                primary_role=primary_role,
                secondary_roles=secondary_roles,
                mastered_champions=[name.strip() for name in champions],
                preferences=[value.strip() for value in preferences if value.strip()],
            )
            profile.game_name
            profile.tag_line
            save_config(profile)
        except (ValueError, OSError) as exc:
            self._json(400, {"error": str(exc)})
            return
        self._json(200, profile_payload())


def run_webapp(host: str = "127.0.0.1", port: int = 8765) -> None:
    try:
        server = ThreadingHTTPServer((host, port), PickMyChampHandler)
    except OSError as exc:
        raise RuntimeError(
            f"Impossible de démarrer l'interface sur {host}:{port}: {exc}"
        ) from exc
    url = f"http://{host}:{port}"
    print(f"PickMyChamp est disponible sur {url}")
    print("Garde cette fenêtre de terminal ouverte pendant que tu utilises l'application.")
    try:
        webbrowser.open(url)
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nArrêt de PickMyChamp.")
    finally:
        server.server_close()

import base64
import json
import os
import ssl
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


class LcuError(RuntimeError):
    pass


def find_lockfile() -> Path:
    configured = os.environ.get("LEAGUE_CLIENT_LOCKFILE")
    if configured:
        candidate = Path(configured)
        if candidate.is_file():
            return candidate
        raise LcuError(f"LEAGUE_CLIENT_LOCKFILE ne désigne pas un fichier: {candidate}")
    candidates = []
    candidates.extend(
        [
            Path(os.environ.get("PROGRAMFILES", r"C:\Program Files"))
            / "Riot Games" / "League of Legends" / "lockfile",
            Path(os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)"))
            / "Riot Games" / "League of Legends" / "lockfile",
        ]
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise LcuError(
        "Client League introuvable. Ouvrez le client et définissez "
        "LEAGUE_CLIENT_LOCKFILE vers son fichier lockfile si nécessaire."
    )


def get_live_game() -> dict[str, Any]:
    try:
        lockfile = find_lockfile()
        name, pid, port, password, protocol = lockfile.read_text(
            encoding="utf-8"
        ).strip().split(":")
    except (OSError, ValueError) as exc:
        raise LcuError(f"Lecture du lockfile League impossible: {exc}") from exc

    token = base64.b64encode(f"{name}:{password}".encode()).decode("ascii")
    request = urllib.request.Request(
        f"{protocol}://127.0.0.1:{port}/lol-gameflow/v1/session",
        headers={"Authorization": f"Basic {token}", "Accept": "application/json"},
    )
    context = ssl._create_unverified_context()
    session = {}
    try:
        with urllib.request.urlopen(request, context=context, timeout=3) as response:
            session = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code not in (404, 503):
            raise LcuError(f"Client League a répondu HTTP {exc.code}.") from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise LcuError(f"Impossible de contacter le client League local: {exc}") from exc
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise LcuError("Réponse du client League illisible.") from exc

    if not isinstance(session, dict):
        raise LcuError("Format de session renvoyé par le client League inattendu.")
    phase = session.get("phase", "inconnue")
    game_data = session.get("gameData", {})
    player = game_data.get("playerChampionSelections", [])
    live_data = None
    live_request = urllib.request.Request(
        "https://127.0.0.1:2999/liveclientdata/allgamedata",
        headers={"Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(live_request, context=context, timeout=3) as response:
            live_data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code not in (404, 503):
            raise LcuError(f"Live Client Data a répondu HTTP {exc.code}.") from exc
    except (urllib.error.URLError, TimeoutError):
        pass
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise LcuError("Réponse Live Client Data illisible.") from exc
    return {
        "phase": phase,
        "game_data": game_data,
        "player_selections": player,
        "live_data": live_data,
    }

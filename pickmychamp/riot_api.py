import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Optional


PLATFORM_ROUTES = {
    "br": ("br1", "americas"),
    "eune": ("eun1", "europe"),
    "euw": ("euw1", "europe"),
    "jp": ("jp1", "asia"),
    "kr": ("kr", "asia"),
    "lan": ("la1", "americas"),
    "las": ("la2", "americas"),
    "na": ("na1", "americas"),
    "oce": ("oc1", "sea"),
    "ph": ("ph2", "sea"),
    "ru": ("ru", "europe"),
    "sg": ("sg2", "sea"),
    "th": ("th2", "sea"),
    "tr": ("tr1", "europe"),
    "tw": ("tw2", "sea"),
    "vn": ("vn2", "sea"),
}


class RiotApiError(RuntimeError):
    pass


class RiotApi:
    def __init__(self, region: str, api_key: Optional[str] = None):
        try:
            self.platform, self.continental = PLATFORM_ROUTES[region.lower()]
        except KeyError as exc:
            raise ValueError(f"Région Riot inconnue: {region}") from exc
        self.api_key = api_key or os.environ.get("RIOT_API_KEY")
        if not self.api_key:
            raise RiotApiError(
                "Clé Riot API absente. Créez-en une sur developer.riotgames.com "
                "puis définissez la variable d'environnement RIOT_API_KEY."
            )

    def _get(self, host: str, path: str) -> Any:
        request = urllib.request.Request(
            f"https://{host}.api.riotgames.com{path}",
            headers={"X-Riot-Token": self.api_key, "User-Agent": "PickMyChamp/1.0"},
        )
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            messages = {
                401: "clé API Riot refusée (401); vérifiez RIOT_API_KEY.",
                403: "accès refusé par Riot (403); vérifiez la clé et ses autorisations.",
                404: "profil ou ressource introuvable (404).",
                429: "limite de requêtes Riot atteinte (429); réessayez plus tard.",
            }
            raise RiotApiError(messages.get(exc.code, f"Riot API a répondu HTTP {exc.code}.")) from exc
        except (urllib.error.URLError, TimeoutError) as exc:
            raise RiotApiError(f"Impossible de joindre Riot API: {exc}") from exc
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise RiotApiError("Réponse Riot API illisible.") from exc

    def account_by_riot_id(self, game_name: str, tag_line: str) -> dict[str, Any]:
        name = urllib.parse.quote(game_name, safe="")
        tag = urllib.parse.quote(tag_line, safe="")
        return self._get(
            self.continental,
            f"/riot/account/v1/accounts/by-riot-id/{name}/{tag}",
        )

    def match_ids(self, puuid: str, count: int = 20) -> list[str]:
        encoded = urllib.parse.quote(puuid, safe="")
        result = self._get(
            self.continental,
            f"/lol/match/v5/matches/by-puuid/{encoded}/ids?start=0&count={count}",
        )
        if not isinstance(result, list):
            raise RiotApiError("Format inattendu pour l'historique Riot.")
        return result

    def match(self, match_id: str) -> dict[str, Any]:
        encoded = urllib.parse.quote(match_id, safe="")
        return self._get(self.continental, f"/lol/match/v5/matches/{encoded}")

    def champion_masteries(self, puuid: str, count: int = 20) -> list[dict[str, Any]]:
        encoded = urllib.parse.quote(puuid, safe="")
        result = self._get(
            f"{self.platform}.api.riotgames.com",
            f"/lol/champion-mastery/v4/champion-masteries/by-puuid/{encoded}/top?count={count}",
        )
        if not isinstance(result, list):
            raise RiotApiError("Format inattendu pour les maîtrises Riot.")
        return result

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path


CONFIG_PATH = Path.home() / ".pickmychamp" / "config.json"


@dataclass
class AccountConfig:
    riot_id: str
    region: str
    primary_role: str
    secondary_roles: list[str] = field(default_factory=list)
    mastered_champions: list[str] = field(default_factory=list)
    preferences: list[str] = field(default_factory=list)

    @property
    def game_name(self) -> str:
        if self.riot_id.count("#") != 1:
            raise ValueError("Le Riot ID doit être au format nom#tag.")
        game_name = self.riot_id.rsplit("#", 1)[0].strip()
        if not game_name:
            raise ValueError("Le Riot ID doit contenir un nom avant le #.")
        return game_name

    @property
    def tag_line(self) -> str:
        if self.riot_id.count("#") != 1:
            raise ValueError("Le Riot ID doit être au format nom#tag.")
        tag_line = self.riot_id.rsplit("#", 1)[1].strip()
        if not tag_line:
            raise ValueError("Le Riot ID doit contenir un tag après le #.")
        return tag_line


def load_config(path: Path = CONFIG_PATH) -> AccountConfig:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise FileNotFoundError(
            "Compte non configuré. Lancez `python main.py setup`."
        ) from exc
    if not isinstance(raw, dict):
        raise ValueError(f"Configuration invalide dans {path}.")
    try:
        for field_name in ("secondary_roles", "mastered_champions", "preferences"):
            value = raw.get(field_name, [])
            if not isinstance(value, list) or not all(
                isinstance(item, str) for item in value
            ):
                raise ValueError(f"Le champ {field_name} doit être une liste de textes.")
        config = AccountConfig(
            riot_id=raw["riot_id"],
            region=raw["region"].lower(),
            primary_role=raw["primary_role"].upper(),
            secondary_roles=[role.upper() for role in raw.get("secondary_roles", [])],
            mastered_champions=raw.get("mastered_champions", []),
            preferences=raw.get("preferences", []),
        )
        config.game_name
        config.tag_line
        return config
    except (KeyError, AttributeError, TypeError) as exc:
        raise ValueError(f"Configuration invalide dans {path}: {exc}") from exc


def save_config(config: AccountConfig, path: Path = CONFIG_PATH) -> None:
    config.game_name
    config.tag_line
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(asdict(config), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

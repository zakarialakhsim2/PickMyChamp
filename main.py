import argparse
import json
import os
import sys
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

from pickmychamp.config import AccountConfig, load_config, save_config
from pickmychamp.lcu import LcuError, get_live_game
from pickmychamp.recommendations import (
    ChampionStats,
    aggregate_matches,
    attach_masteries,
    confidence,
    filter_queue,
    normalize_role,
    player_matches,
    rank_champions,
)
from pickmychamp.riot_api import PLATFORM_ROUTES, RiotApi, RiotApiError
from pickmychamp.webapp import counter_payload, run_webapp


def prompt(label: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    value = input(f"{label}{suffix}: ").strip()
    return value or default


def parse_list(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def parse_match_count(value: str) -> int:
    try:
        count = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Le nombre de parties doit être un entier.") from exc
    if not 1 <= count <= 100:
        raise argparse.ArgumentTypeError("Le nombre de parties doit être compris entre 1 et 100.")
    return count


def launch_app(_: argparse.Namespace) -> int:
    try:
        host = os.environ.get(
            "HOST",
            "0.0.0.0" if os.environ.get("PORT") else "127.0.0.1",
        )
        port = int(os.environ.get("PORT", "8765"))
        run_webapp(host=host, port=port)
    except RuntimeError as exc:
        print(f"Erreur: {exc}", file=sys.stderr)
        return 1
    return 0


def setup(_: argparse.Namespace) -> int:
    try:
        existing = load_config()
    except FileNotFoundError:
        existing = None
    except ValueError as exc:
        print(f"Erreur: {exc}", file=sys.stderr)
        return 1
    riot_id = prompt("Riot ID au format nom#tag", existing.riot_id if existing else "")
    region = prompt("Région (euw, na, etc.)", existing.region if existing else "euw")
    primary = prompt(
        "Rôle principal (top/jungle/mid/adc/support)",
        existing.primary_role if existing else "",
    )
    try:
        if not primary:
            raise ValueError("Le rôle principal est obligatoire.")
        normalize_role(primary)
    except ValueError as exc:
        print(f"Erreur: {exc}", file=sys.stderr)
        return 1
    secondary = parse_list(
        prompt("Rôles secondaires, séparés par des virgules",
               ",".join(existing.secondary_roles) if existing else "")
    )
    try:
        for role in secondary:
            normalize_role(role)
    except ValueError as exc:
        print(f"Erreur: {exc}", file=sys.stderr)
        return 1
    champions = parse_list(
        prompt("Champions maîtrisés, séparés par des virgules",
               ",".join(existing.mastered_champions) if existing else "")
    )
    preferences = parse_list(
        prompt("Préférences de jeu, séparées par des virgules",
               ",".join(existing.preferences) if existing else "")
    )
    config = AccountConfig(riot_id, region.lower(), primary, secondary, champions, preferences)
    try:
        config.game_name
        config.tag_line
        if config.region not in PLATFORM_ROUTES:
            raise ValueError(f"Région Riot inconnue: {config.region}")
    except ValueError as exc:
        print(f"Erreur: {exc}", file=sys.stderr)
        return 1
    save_config(config)
    print(f"Configuration enregistrée dans {Path.home() / '.pickmychamp' / 'config.json'}")
    print("La clé API Riot doit être définie séparément dans RIOT_API_KEY.")
    return 0


def api_for(config: AccountConfig) -> RiotApi:
    return RiotApi(config.region)


def get_history(api: RiotApi, config: AccountConfig, count: int = 20):
    puuid, matches = player_matches(api, config.riot_id, count)
    try:
        masteries = api.champion_masteries(puuid)
    except RiotApiError as exc:
        print(f"Avertissement: maîtrises indisponibles: {exc}", file=sys.stderr)
        masteries = []
    return puuid, matches, masteries


def attach_available_masteries(stats: dict, masteries: list[dict]) -> None:
    if not masteries:
        return
    try:
        names = champion_names()
    except RuntimeError as exc:
        print(f"Avertissement: noms de champions Data Dragon indisponibles: {exc}",
              file=sys.stderr)
        return
    attach_masteries(stats, masteries, names)


def champion_names() -> dict[int, str]:
    try:
        with urlopen(
            "https://ddragon.leagueoflegends.com/api/versions.json", timeout=10
        ) as response:
            versions = json.loads(response.read().decode("utf-8"))
        if not isinstance(versions, list) or not versions:
            raise RuntimeError("Data Dragon n'a renvoyé aucune version.")
        version = versions[0]
        with urlopen(
            f"https://ddragon.leagueoflegends.com/cdn/{version}/data/en_US/champion.json",
            timeout=10,
        ) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (URLError, TimeoutError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise RuntimeError(f"Impossible de charger la liste Data Dragon: {exc}") from exc
    return {
        int(champion["key"]): champion["name"]
        for champion in payload.get("data", {}).values()
    }


def history(args: argparse.Namespace) -> int:
    try:
        config = load_config()
        api = api_for(config)
        puuid, matches, masteries = get_history(api, config, args.count)
        recent = matches[:10]
        all_stats = aggregate_matches(matches, puuid)
        recent_stats = aggregate_matches(recent, puuid)
        attach_available_masteries(all_stats, masteries)
    except (OSError, ValueError, RiotApiError, RuntimeError, KeyError) as exc:
        print(f"Erreur: {exc}", file=sys.stderr)
        return 1

    total_games = sum(item.games for item in all_stats.values())
    total_wins = sum(item.wins for item in all_stats.values())
    recent_games = sum(item.games for item in recent_stats.values())
    recent_wins = sum(item.wins for item in recent_stats.values())
    print(f"Historique récupéré: {len(matches)} parties (maximum demandé: {args.count}).")
    print(
        f"Sur les {len(matches)} parties récupérées: {total_wins}/{total_games} victoires "
        f"({100 * total_wins / total_games:.1f}%)"
        if total_games else "Aucune partie exploitable trouvée."
    )
    print(
        f"10 dernières parties: {recent_wins}/{recent_games} victoires "
        f"({100 * recent_wins / recent_games:.1f}%)"
        if recent_games else "Aucune statistique récente disponible."
    )
    print("\nChampions les plus joués:")
    for item in sorted(all_stats.values(), key=lambda stat: stat.games, reverse=True)[:8]:
        print(
            f"- {item.champion}: {item.wins}/{item.games} victoires "
            f"({item.win_rate:.1f}%), KDA {item.kda:.2f}"
        )
    print("\nPerformances par rôle (sur les parties récupérées):")
    for role in ("TOP", "JUNGLE", "MIDDLE", "BOTTOM", "UTILITY"):
        role_stats = aggregate_matches(matches, puuid, role)
        role_games = sum(item.games for item in role_stats.values())
        role_wins = sum(item.wins for item in role_stats.values())
        if role_games:
            best = max(role_stats.values(), key=lambda item: item.games)
            print(
                f"- {role}: {role_wins}/{role_games} victoires "
                f"({100 * role_wins / role_games:.1f}%), plus joué: {best.champion} "
                f"({best.games} parties)"
            )
    print("\nL'API Riot ne garantit ici qu'un historique récent limité, pas un profil OP.GG.")
    return 0


def draft(args: argparse.Namespace) -> int:
    try:
        config = load_config()
        selected_role = normalize_role(args.role or config.primary_role)
        api = api_for(config)
        puuid, matches, masteries = get_history(api, config, args.count)
        matches = filter_queue(matches, args.queue)
        stats = aggregate_matches(matches, puuid, selected_role)
        attach_available_masteries(stats, masteries)
        ranked = rank_champions(stats, config.mastered_champions)
    except (OSError, ValueError, RiotApiError, RuntimeError, KeyError) as exc:
        print(f"Erreur: {exc}", file=sys.stderr)
        return 1

    if not ranked:
        print(
            "Pas assez de données personnelles pour proposer un champion. "
            "Complétez la liste de champions maîtrisés avec `python main.py setup`."
        )
        return 0

    queue_text = f", file {args.queue}" if args.queue else ""
    print(
        f"Suggestions pour {selected_role}{queue_text} contre {args.enemy} "
        "(ordre personnalisé):"
    )
    for index, (item, score) in enumerate(ranked, 1):
        reasons = []
        if item.games:
            reasons.append(f"{item.win_rate:.1f}% de victoires en {item.games} parties sur ce rôle")
            reasons.append(f"KDA personnel {item.kda:.2f}")
        if item.mastery_points:
            reasons.append(f"{item.mastery_points:,} points de maîtrise")
        if not item.games:
            reasons.append("champion déclaré maîtrisé, sans partie récente trouvée sur ce rôle")
        print(f"\n{index}. {item.champion} — score de profil {score * 100:.1f}/100")
        print("   " + "; ".join(reasons))
        print(
            f"   Indice de confiance heuristique: {confidence(item.games)}% "
            f"(non probabiliste) — {item.games} partie(s) exploitées."
        )
        print(
            "   Avantage observé: performances personnelles récentes."
            if item.games
            else "   Avantage observé: champion déclaré maîtrisé."
        )
        print("   Matchup contre l'adversaire: données fiables indisponibles via l'API Riot officielle.")
        print("   Difficulté du matchup: inconnue (aucune statistique de matchup utilisée).")
        print("   Risque: échantillon personnel faible." if item.games < 10
              else "   Limite: statistiques personnelles récentes, pas une prédiction du résultat.")

    print(
        "\nLes scores n'intègrent pas de taux de victoire de matchup, de synergies "
        "d'équipe, de runes ou de builds: Riot ne fournit pas ces recommandations "
        f"prêtes à l'emploi. Les statistiques utilisent jusqu'aux {args.count} "
        "dernières parties demandées "
        "et ne sont pas filtrées au patch actuel."
    )
    return 0


def demo(args: argparse.Namespace) -> int:
    examples = {
        "top": [
            ChampionStats("Garen", 18, 11, 92, 83, 106, 82_000, True),
            ChampionStats("Malphite", 9, 6, 32, 39, 101, 46_000, True),
            ChampionStats("Camille", 4, 1, 21, 28, 16, 0, True),
            ChampionStats("Darius", 3, 1, 24, 21, 12, 0, True),
        ],
        "jungle": [
            ChampionStats("Warwick", 17, 10, 95, 78, 111, 92_000, True),
            ChampionStats("Amumu", 8, 5, 28, 36, 76, 35_000, True),
            ChampionStats("Vi", 5, 2, 31, 29, 22, 12_000, True),
        ],
        "mid": [
            ChampionStats("Ahri", 14, 9, 71, 61, 93, 71_000, True),
            ChampionStats("Lux", 9, 6, 52, 48, 69, 42_000, True),
            ChampionStats("Orianna", 3, 1, 11, 16, 19, 0, True),
        ],
        "adc": [
            ChampionStats("Vayne", 20, 12, 108, 86, 91, 220_000, True),
            ChampionStats("Ashe", 13, 8, 68, 57, 91, 63_000, True),
            ChampionStats("Jinx", 7, 4, 55, 42, 44, 38_000, True),
            ChampionStats("Caitlyn", 3, 1, 18, 21, 13, 0, True),
        ],
        "support": [
            ChampionStats("Nami", 12, 8, 14, 47, 186, 57_000, True),
            ChampionStats("Leona", 8, 5, 21, 39, 83, 48_000, True),
            ChampionStats("Lulu", 4, 2, 9, 18, 43, 0, True),
        ],
    }
    role = args.role or "adc"
    examples_for_role = examples[role]
    ranked = rank_champions(
        {item.champion: item for item in examples_for_role}, []
    )
    print("MODE DÉMO — données synthétiques, aucune donnée Riot réelle.")
    print(f"Suggestions de démonstration pour {role} contre {args.enemy}:")
    for index, (item, score) in enumerate(ranked, 1):
        print(
            f"{index}. {item.champion} — profil {score * 100:.1f}/100; "
            f"{item.win_rate:.1f}% en {item.games} parties; KDA {item.kda:.2f}; "
            f"confiance heuristique {confidence(item.games)}%."
        )
    print(
        "Matchup, synergies, runes, compétences et build ne sont pas estimés "
        "dans cette démo."
    )
    return 0


def counter(args: argparse.Namespace) -> int:
    try:
        result = counter_payload(args.enemy, args.role)
    except (ValueError, RuntimeError) as exc:
        print(f"Erreur: {exc}", file=sys.stderr)
        return 1

    print(
        f"Counter picks for {args.enemy} — {result['source']} "
        f"{result['scope']}, patch {result['patch']}."
    )
    if result["role_warning"]:
        print(f"Lane note: {result['role_warning']}")
    for index, pick in enumerate(result["picks"], 1):
        print(
            f"\n{index}. {pick['champion']} — {pick['win_rate']:.2f}% WR, "
            f"{pick['games']:,} games"
        )
        print(f"   {pick['reason']}")
        if pick["guide_available"]:
            print(f"   Support suggestion: {pick['support']}; alternative {pick['support_alternative']}.")
            print(f"   Runes: {pick['runes']}")
            print(f"   Summoner spells: {pick['spells']}")
            print(f"   Skill order: {pick['skills']}")
            print(f"   Build: {pick['starting_item']} > {' > '.join(pick['build'])}")
        else:
            print(f"   Support, runes, spells and build: see {pick['build_url']}")
        print(f"   Lane notes: {pick['lane_plan']}")
    print(
        f"\nSource: {result['source_url']}. Matchup rates are population statistics, "
        "not a prediction of your personal result."
    )
    return 0


def build(_: argparse.Namespace) -> int:
    try:
        live = get_live_game()
    except LcuError as exc:
        print(f"Erreur: {exc}", file=sys.stderr)
        return 1
    print(f"État du client League: {live['phase']}.")
    live_data = live["live_data"]
    if not live_data:
        print(
            "Aucune donnée Live Client Data accessible. Lancez une partie (en jeu, "
            "hors écran de chargement), puis réessayez."
        )
        return 0
    active = live_data.get("activePlayer", {})
    player = next(
        (
            candidate
            for candidate in live_data.get("allPlayers", [])
            if candidate.get("summonerName") == active.get("summonerName")
        ),
        {},
    )
    stats = player.get("scores", {})
    print(
        f"Partie en cours — {active.get('championName', 'champion inconnu')} "
        f"(niveau {active.get('level', 'inconnu')}, "
        f"rôle {player.get('position', 'inconnu')})"
    )
    if stats:
        print(
            f"K/D/A: {stats.get('kills', '?')}/{stats.get('deaths', '?')}/"
            f"{stats.get('assists', '?')} — farm: {stats.get('creepScore', '?')} — "
            f"or actuel: {active.get('currentGold', '?')}"
        )
    game_data = live_data.get("gameData", {})
    print(f"Temps écoulé: {game_data.get('gameTime', 'inconnu')} secondes.")
    print("Inventaire relevé par le client:")
    for item in player.get("items", []):
        name = item.get("displayName")
        if name:
            print(f"- {name}")
    print("Champions visibles dans la partie:")
    for player in live_data.get("allPlayers", []):
        print(
            f"- {player.get('team', '?')}: {player.get('championName', '?')} "
            f"({player.get('position', 'rôle inconnu')})"
        )
    print(
        "\nLes recommandations d'objets ne sont pas calculées: l'API Riot ne fournit "
        "pas de statistiques de performance d'objets par matchup. L'or et l'inventaire "
        "ci-dessus sont les données du client au moment de la requête; aucun objet "
        "futur n'est présenté comme un fait."
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Assistant personnel League of Legends")
    parser.set_defaults(func=launch_app)
    commands = parser.add_subparsers(dest="command")
    app_parser = commands.add_parser(
        "app", help="Ouvrir l'interface graphique locale dans le navigateur"
    )
    app_parser.set_defaults(func=launch_app)
    setup_parser = commands.add_parser("setup", help="Configurer votre profil Riot")
    setup_parser.set_defaults(func=setup)
    draft_parser = commands.add_parser("draft", help="Obtenir des choix basés sur votre profil")
    draft_parser.add_argument("--role", help="top, jungle, mid, adc ou support (défaut: rôle principal)")
    draft_parser.add_argument("--enemy", required=True, help="Champion adverse (contexte uniquement)")
    draft_parser.add_argument("--queue", choices=("ranked", "flex", "normal"))
    draft_parser.add_argument("--count", type=parse_match_count, default=20)
    draft_parser.set_defaults(func=draft)
    history_parser = commands.add_parser("history", help="Consulter vos statistiques récentes")
    history_parser.add_argument("--count", type=parse_match_count, default=20)
    history_parser.set_defaults(func=history)
    build_parser = commands.add_parser("build", help="Inspecter la session du client local")
    build_parser.set_defaults(func=build)
    demo_parser = commands.add_parser(
        "demo", help="Tester le classement avec des données synthétiques hors ligne"
    )
    demo_parser.add_argument(
        "--role",
        choices=("top", "jungle", "mid", "adc", "support"),
        default="adc",
    )
    demo_parser.add_argument("--enemy", default="Jhin")
    demo_parser.set_defaults(func=demo)
    counter_parser = commands.add_parser(
        "counter",
        help="Conseils de draft, runes, sorts et build contre un matchup pris en charge",
    )
    counter_parser.add_argument("--enemy", required=True, help="Champion adverse")
    counter_parser.add_argument(
        "--role", default="adc", help="Rôle du matchup (guide Vayne: adc)"
    )
    counter_parser.set_defaults(func=counter)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

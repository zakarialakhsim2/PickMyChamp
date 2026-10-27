from flask import Flask, jsonify, request

from pickmychamp.config import AccountConfig, load_config, save_config
from pickmychamp.counter_guides import champion_catalog
from pickmychamp.webapp import counter_payload, profile_payload
from pickmychamp.riot_api import PLATFORM_ROUTES
from pickmychamp.recommendations import normalize_role


app = Flask(__name__)


@app.get("/api/champions")
def champions():
    try:
        patch, catalog = champion_catalog()
    except RuntimeError as exc:
        return jsonify(error=str(exc)), 502
    return jsonify(patch=patch, champions=catalog)


@app.get("/api/counter")
def counter():
    enemy = request.args.get("enemy", "").strip()
    role = request.args.get("role", "adc").strip()
    if not enemy:
        return jsonify(error="Indique le champion adverse."), 400
    try:
        return jsonify(counter_payload(enemy, role))
    except ValueError as exc:
        return jsonify(error=str(exc)), 400
    except RuntimeError as exc:
        return jsonify(error=str(exc)), 502


@app.get("/api/profile")
def profile():
    try:
        return jsonify(profile_payload())
    except ValueError as exc:
        return jsonify(error=str(exc)), 500


@app.post("/api/profile")
def save_profile():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify(error="Le corps JSON doit être un objet."), 400
    try:
        riot_id = payload.get("riot_id", "").strip()
        region = payload.get("region", "").strip().lower()
        primary_role = payload.get("primary_role", "").strip().lower()
        secondary_roles = payload.get("secondary_roles", [])
        champions = payload.get("mastered_champions", [])
        preferences = payload.get("preferences", [])
        if not isinstance(riot_id, str) or not isinstance(primary_role, str):
            raise ValueError("Riot ID et rôle principal doivent être du texte.")
        if not isinstance(region, str) or region not in PLATFORM_ROUTES:
            raise ValueError(f"Région inconnue: {region}")
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
        normalize_role(primary_role)
        for role in secondary_roles:
            normalize_role(role)
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
        return jsonify(error=str(exc)), 400
    return jsonify(profile_payload())

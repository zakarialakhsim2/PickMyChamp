from collections import Counter


ROLE_ORDER = ("top", "jungle", "mid", "adc", "support")
ROLE_LABELS = {
    "top": "Top",
    "jungle": "Jungle",
    "mid": "Mid",
    "adc": "ADC",
    "support": "Support",
}

CHAMPION_TRAITS = {
    "amumu": frozenset({"engage"}),
    "aphelios": frozenset({"scaling"}),
    "ashe": frozenset({"poke", "pick"}),
    "ahri": frozenset({"pick"}),
    "bard": frozenset({"pick"}),
    "blitzcrank": frozenset({"pick"}),
    "braum": frozenset({"protect"}),
    "caitlyn": frozenset({"poke"}),
    "camille": frozenset({"split"}),
    "draven": frozenset({"pick"}),
    "ezreal": frozenset({"poke", "scaling"}),
    "fiora": frozenset({"split"}),
    "heimerdinger": frozenset({"poke"}),
    "jarvan iv": frozenset({"engage"}),
    "jax": frozenset({"split", "scaling"}),
    "janna": frozenset({"protect"}),
    "jayce": frozenset({"poke"}),
    "jinx": frozenset({"scaling"}),
    "kai'sa": frozenset({"scaling"}),
    "kaisa": frozenset({"scaling"}),
    "kassadin": frozenset({"scaling"}),
    "kayle": frozenset({"scaling"}),
    "kog'maw": frozenset({"scaling"}),
    "leona": frozenset({"engage"}),
    "lulu": frozenset({"protect"}),
    "lux": frozenset({"poke", "pick"}),
    "malphite": frozenset({"engage"}),
    "maokai": frozenset({"engage", "pick"}),
    "milio": frozenset({"protect"}),
    "morgana": frozenset({"pick", "protect"}),
    "nautilus": frozenset({"engage", "pick"}),
    "nami": frozenset({"protect"}),
    "nidalee": frozenset({"poke", "pick"}),
    "orianna": frozenset({"scaling"}),
    "ornn": frozenset({"engage", "scaling"}),
    "pyke": frozenset({"pick"}),
    "rakan": frozenset({"engage", "pick"}),
    "rell": frozenset({"engage"}),
    "renata glasc": frozenset({"protect"}),
    "sejuani": frozenset({"engage", "pick"}),
    "senna": frozenset({"scaling"}),
    "smolder": frozenset({"scaling"}),
    "soraka": frozenset({"protect"}),
    "swain": frozenset({"engage"}),
    "thresh": frozenset({"pick", "protect"}),
    "trundle": frozenset({"split"}),
    "twisted fate": frozenset({"pick"}),
    "varus": frozenset({"poke", "pick"}),
    "veigar": frozenset({"scaling", "pick"}),
    "vel'koz": frozenset({"poke"}),
    "vi": frozenset({"engage", "pick"}),
    "viego": frozenset({"pick"}),
    "vayne": frozenset({"scaling"}),
    "wukong": frozenset({"engage"}),
    "xerath": frozenset({"poke"}),
    "yasuo": frozenset({"scaling"}),
    "zac": frozenset({"engage"}),
    "ziggs": frozenset({"poke", "scaling"}),
}

STRATEGIES = {
    "engage": {
        "label": "Coordinated engage",
        "win_condition": (
            "Look for a coordinated fight your team can start and follow up on."
        ),
        "avoid": "Do not start while key allies are too far away to follow.",
        "fallback": (
            "If a direct fight is unsafe, wait for an isolated target or a better "
            "position instead of forcing a grouped fight."
        ),
        "jobs": {
            "top": "Start only when your team is close enough to follow.",
            "jungle": "Coordinate the engage with nearby allies; avoid going in alone.",
            "mid": "Stay in follow-up range and hold key control for the engage.",
            "adc": "Stay behind your frontline and deal damage to the nearest safe target.",
            "support": "Check ally positions before engaging; make the follow-up possible.",
        },
    },
    "poke": {
        "label": "Poke before the fight",
        "win_condition": (
            "Use ranged pressure to make an objective area safer before committing."
        ),
        "avoid": "Do not face-check or start a fight after your team has been separated.",
        "fallback": (
            "If you cannot safely poke, give up the unsafe approach and regroup "
            "around vision rather than entering alone."
        ),
        "jobs": {
            "top": "Keep side pressure available without abandoning the team before an objective.",
            "jungle": "Control approach routes and avoid starting before allies can follow.",
            "mid": "Apply pressure from a safe angle before the enemy can force an engage.",
            "adc": "Chip targets from safety; do not trade your position for one extra hit.",
            "support": "Help establish vision safely and preserve tools that stop an engage.",
        },
    },
    "pick": {
        "label": "Catch an isolated target",
        "win_condition": (
            "Create a numbers advantage by finding a safe catch before committing."
        ),
        "avoid": "Do not spend key catch tools on a target your team cannot reach.",
        "fallback": (
            "If no safe catch appears, group around vision and protect the route "
            "to the next objective."
        ),
        "jobs": {
            "top": "Keep a safe route to the team and join when a catch is confirmed.",
            "jungle": "Use vision to find a safe approach; do not chase without backup.",
            "mid": "Hold control for a catch your team can convert into an advantage.",
            "adc": "Stay close enough to follow a catch without entering first.",
            "support": "Help control vision and only commit when allies can follow.",
        },
    },
    "protected_scaling": {
        "label": "Protect the scaling carry",
        "win_condition": (
            "Give your scaling damage dealers safe time and space to contribute "
            "in later fights."
        ),
        "avoid": "Do not leave the carry alone to chase a low-value target.",
        "fallback": (
            "If the carry cannot safely join, trade space for safe farm and regroup "
            "instead of forcing a fight."
        ),
        "jobs": {
            "top": "Keep pressure off your backline and avoid leaving it exposed.",
            "jungle": "Help the team reach objectives without abandoning the backline.",
            "mid": "Use control and positioning to keep threats away from your carry.",
            "adc": "Prioritize safe farm and consistent damage over risky chases.",
            "support": "Save protection for the threat that can reach your carry.",
        },
    },
    "scaling": {
        "label": "Reach your scaling strengths",
        "win_condition": (
            "Protect safe farm and avoid low-value risks while your team reaches "
            "its stronger fights."
        ),
        "avoid": "Do not contest every early fight when your team cannot follow up.",
        "fallback": (
            "If pressured, trade unsafe objectives for safe farm and regroup "
            "around your strongest players."
        ),
        "jobs": {
            "top": "Take safe farm and avoid unnecessary early skirmishes.",
            "jungle": "Choose safe routes and avoid forcing fights without a clear advantage.",
            "mid": "Protect your farm and be ready to join fights your team can support.",
            "adc": "Stay alive and prioritize safe farm over a risky early trade.",
            "support": "Protect your scaling teammates and keep their route to farm safe.",
        },
    },
}

STRATEGY_REQUIREMENTS = {
    "engage": {"engage": 2},
    "poke": {"poke": 2},
    "pick": {"pick": 2},
    "protected_scaling": {"protect": 1, "scaling": 1},
    "scaling": {"scaling": 2},
}

ENEMY_READS = {
    "engage": (
        "Their known picks point toward coordinated engage. Avoid giving them "
        "a grouped target without a response ready."
    ),
    "poke": (
        "Their known picks point toward ranged poke. Avoid waiting in exposed "
        "range before an objective."
    ),
    "pick": (
        "Their known picks point toward catching isolated targets. Do not face-check "
        "or move through vision alone."
    ),
    "protected_scaling": (
        "Their known picks point toward protecting scaling damage. Avoid letting "
        "their carry deal damage uncontested."
    ),
    "scaling": (
        "Their known picks point toward scaling. Look for safe advantages rather "
        "than giving them uncontested time."
    ),
}

COUNTER_PLANS = {
    "engage": (
        "Their known engagement tools can punish poor spacing. Stay aware of ally "
        "positions and keep a response for the first commitment."
    ),
    "poke": (
        "Their known ranged pressure can wear the team down before a fight. Use "
        "cover and seek a coordinated approach rather than waiting exposed."
    ),
    "pick": (
        "Their known catch tools make isolated rotations risky. Move with teammates "
        "when checking vision."
    ),
    "protected_scaling": (
        "Their known protection and scaling signals reward patience. Coordinate "
        "pressure instead of diving alone."
    ),
    "scaling": (
        "Their known scaling picks reward a long, undisturbed game. Seek safe "
        "advantages without forcing unsupported fights."
    ),
}

PAIR_COUNTER_PLANS = {
    ("engage", "poke"): (
        "Your coordinated engage can stop repeated poke from controlling the approach. "
        "Wait for a clear window and make sure allies can follow before committing."
    ),
    ("poke", "engage"): (
        "Use range to apply pressure before they close, but keep your team together "
        "and avoid spending escape tools before their engage."
    ),
    ("protected_scaling", "engage"): (
        "Your plan depends on keeping your scaling carry safe. Preserve protection "
        "for the enemy's commitment instead of starting an unsupported dive."
    ),
    ("scaling", "engage"): (
        "Avoid repeated early fights on their terms. Keep safe farm available and "
        "group when your team can answer their engage."
    ),
    ("pick", "scaling"): (
        "Use vision and coordinated catches to contest their safe scaling, but do "
        "not chase alone when they group."
    ),
}


def _normalize_team(team: object, team_label: str) -> dict[str, str]:
    if not isinstance(team, dict):
        raise ValueError(f"{team_label} must be an object of role-to-champion picks.")
    unknown_roles = set(team) - set(ROLE_ORDER)
    if unknown_roles:
        raise ValueError(f"{team_label} contains an unsupported role.")

    normalized = {}
    for role, champion in team.items():
        if not isinstance(champion, str):
            raise ValueError(f"{team_label} champion names must be text.")
        name = champion.strip()
        if len(name) > 60:
            raise ValueError(f"{team_label} champion names must be 60 characters or fewer.")
        if name:
            normalized[role] = name
    return normalized


def _analyze_team(picks: dict[str, str]) -> dict:
    traits_by_role = {
        role: CHAMPION_TRAITS.get(champion.casefold(), frozenset())
        for role, champion in picks.items()
    }
    counts = Counter(trait for traits in traits_by_role.values() for trait in traits)
    candidates = {}
    for strategy, requirements in STRATEGY_REQUIREMENTS.items():
        if all(counts[trait] >= minimum for trait, minimum in requirements.items()):
            candidates[strategy] = min(counts[trait] for trait in requirements)
    if "protected_scaling" in candidates:
        candidates.pop("scaling", None)

    best_score = max(candidates.values(), default=0)
    winners = [
        strategy for strategy, score in candidates.items() if score == best_score
    ]
    pattern = STRATEGIES[winners[0]] if len(winners) == 1 else None
    pattern_id = winners[0] if len(winners) == 1 else None
    evidence = []
    if pattern_id:
        evidence_traits = STRATEGY_REQUIREMENTS[pattern_id]
        evidence = [
            {"role": role, "champion": champion}
            for role, champion in picks.items()
            if traits_by_role.get(role, frozenset()) & set(evidence_traits)
        ]

    profiled = [
        champion for role, champion in picks.items()
        if traits_by_role.get(role, frozenset())
    ]
    unprofiled = [
        champion for role, champion in picks.items()
        if not traits_by_role.get(role, frozenset())
    ]
    return {
        "pattern_id": pattern_id,
        "pattern": pattern,
        "evidence": evidence,
        "selected_count": len(picks),
        "profiled_count": len(profiled),
        "unprofiled_champions": unprofiled,
        "trait_counts": dict(counts),
    }


def generate_playbook(allies: object, enemies: object, player_role: object) -> dict:
    """Build a conservative, rules-based briefing from manually entered draft picks."""
    allied_picks = _normalize_team(allies, "Your team")
    enemy_picks = _normalize_team(enemies, "Opponent team")
    if not allied_picks or not enemy_picks:
        raise ValueError("Add at least one champion to each team.")
    if not isinstance(player_role, str) or player_role not in ROLE_ORDER:
        raise ValueError("Select a valid player role.")

    allied = _analyze_team(allied_picks)
    enemy = _analyze_team(enemy_picks)
    allied_pattern = allied["pattern"]
    enemy_pattern_id = enemy["pattern_id"]

    role_jobs = []
    if allied_pattern:
        role_jobs = [
            {
                "role": role,
                "label": ROLE_LABELS[role],
                "champion": allied_picks[role],
                "job": allied_pattern["jobs"][role],
            }
            for role in ROLE_ORDER
            if role in allied_picks
        ]
        your_job = allied_pattern["jobs"][player_role]
    else:
        your_job = (
            "The starter rules do not support a reliable role-specific plan for "
            "this draft yet. Use the counter-pick advice as lane preparation."
        )

    enemy_read = (
        ENEMY_READS[enemy_pattern_id]
        if enemy_pattern_id
        else (
            "No clear opponent pattern is supported by the current starter profiles."
        )
    )
    counter_plan = "No specific counter-plan is available from the current opponent picks."
    if enemy_pattern_id:
        counter_plan = PAIR_COUNTER_PLANS.get(
            (allied["pattern_id"], enemy_pattern_id),
            COUNTER_PLANS[enemy_pattern_id],
        )
    return {
        "allied_pattern": {
            "id": allied["pattern_id"],
            "label": allied_pattern["label"] if allied_pattern else "No clear pattern yet",
            "win_condition": (
                allied_pattern["win_condition"] if allied_pattern else
                "The starter rules do not find a well-supported primary win condition."
            ),
            "avoid": allied_pattern["avoid"] if allied_pattern else "",
            "fallback": allied_pattern["fallback"] if allied_pattern else "",
        },
        "enemy_pattern": {
            "id": enemy["pattern_id"],
            "label": (
                enemy["pattern"]["label"] if enemy["pattern"] else "No clear pattern yet"
            ),
        },
        "your_role": player_role,
        "your_champion": allied_picks.get(player_role, ""),
        "your_job": your_job,
        "role_jobs": role_jobs,
        "enemy_read": enemy_read,
        "counter_plan": counter_plan,
        "evidence": allied["evidence"],
        "allied_coverage": {
            "selected": allied["selected_count"],
            "profiled": allied["profiled_count"],
            "unprofiled_champions": allied["unprofiled_champions"],
        },
        "enemy_coverage": {
            "selected": enemy["selected_count"],
            "profiled": enemy["profiled_count"],
            "unprofiled_champions": enemy["unprofiled_champions"],
        },
        "notes": [
            (
                "This is a rules-based heuristic from a limited set of curated "
                "champion profiles, not a win-rate prediction."
            ),
            (
                "Missing or unprofiled champions can change the plan. Treat it as "
                "provisional until the draft data is broader."
            ),
        ],
    }

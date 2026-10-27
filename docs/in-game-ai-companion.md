# Future feature: in-game AI companion

This document describes a future product direction. It is intentionally
planning-only: the current web application remains unchanged.

## Goal

Build an in-game companion that reads permitted game-state information during a
match and gives timely, contextual build recommendations using an LLM. The
companion should help the player understand choices, not play the game or
automate actions.

Example guidance:

- recommend the next item based on the current inventory, gold, level and
  matchup;
- explain whether to prioritize damage, defense, penetration or utility;
- adapt the build after a major objective, team-fight pattern or enemy item
  spike;
- show a short explanation and confidence level rather than an unexplained
  command.

## Proposed architecture

```text
League client / permitted game-state source
        |
        v
Local companion service
  - state collector
  - privacy filter
  - game-state normalizer
  - local cache and rule guardrails
        |
        +--> deterministic build engine
        |
        +--> optional LLM gateway
               - prompt construction
               - timeout and retry budget
               - response schema validation
               - provider/API key isolation
        |
        v
In-game overlay or companion window
```

The local companion should be the source of truth for live state. The hosted
PickMyChamp web application can provide account settings, build knowledge and
history, but the live loop must not depend on a slow or unavailable web
request.

## Live decision loop

1. Receive a permitted game-state update.
2. Normalize it into a small typed snapshot:
   champion, role, level, gold, items, runes, cooldown context, allies,
   visible opponents, objectives and recent events.
3. Apply deterministic safety and validity checks.
4. Check a short-lived cache for an equivalent recommendation.
5. Ask the rules engine for a baseline build recommendation.
6. Optionally ask the LLM to rank or explain the valid alternatives.
7. Validate the LLM response against a strict schema and known item data.
8. Display one concise recommendation with its reason and freshness.

The LLM must not invent item IDs, costs, stats or unavailable game state. If
the LLM is slow, unavailable or returns invalid data, the deterministic
recommendation remains usable.

## LLM requirements

- Use structured JSON responses, never free-form text as the only output.
- Enforce a short timeout and bounded token budget.
- Keep prompts compact and send only the state needed for the decision.
- Do not send Riot IDs, account credentials or unrelated personal data.
- Keep provider keys on a controlled backend or local secret store; never put
  them in frontend JavaScript or an overlay package.
- Log anonymized latency and validation failures, not full match histories by
  default.
- Make the provider optional so the companion still works without an LLM.

Suggested response shape:

```json
{
  "recommendation": {
    "item_id": "3031",
    "action": "buy_next",
    "confidence": 0.82
  },
  "reason": "The enemy team has low armor and your next damage spike is available.",
  "alternatives": ["3072"],
  "state_version": 42,
  "expires_in_seconds": 30
}
```

## Product and compliance constraints

Before implementation, verify the current Riot Games developer policy,
third-party application rules and any restrictions on overlays, game-state
access, automation and real-time assistance. The companion must:

- remain advisory and never control the game client;
- never simulate clicks, inputs or actions;
- avoid revealing information unavailable to the player;
- use only an approved and technically permitted data source;
- include a visible privacy notice and a way to disable telemetry;
- define retention and deletion behavior for match data;
- handle rate limits and provider outages explicitly.

The product should be reviewed against Riot's current policies before
distribution or public monetization. This document is not legal advice.

## Planned phases

### Phase 0 — feasibility and policy review

- Confirm an allowed game-state integration path.
- Decide whether the first version is a companion window or an overlay.
- Define the supported game modes, regions and data fields.
- Choose whether the LLM runs through a hosted gateway or locally.

### Phase 1 — offline recommendation engine

- Create typed game-state fixtures.
- Build deterministic item/build ranking.
- Add replayable snapshots and golden tests.
- Measure recommendation quality without any live integration.

### Phase 2 — local read-only companion

- Read permitted state locally.
- Normalize and cache updates.
- Display deterministic recommendations.
- Add failure states, opt-out and local diagnostics.

### Phase 3 — bounded LLM explanations

- Add the optional LLM gateway.
- Validate structured responses.
- Compare LLM suggestions with deterministic guardrails.
- Add latency, timeout, cost and abuse limits.

### Phase 4 — beta validation

- Run private tests with explicit consent.
- Measure accuracy, latency, crashes and rejected responses.
- Recheck Riot policy and privacy requirements.
- Only then consider public release or monetization.

## Current status

Not implemented. The current PickMyChamp deployment is a web draft
assistant. This document records the intended direction so that future work
starts with a safe, testable and policy-aware scope.

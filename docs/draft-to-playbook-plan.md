# Product plan: Draft-to-Playbook

**Status:** MVP prototype implemented; player validation and broader profile coverage remain.
**Purpose:** Candidate product direction for PickMyChamp; implementation has not started.

## Product idea

Turn champion select into a short, practical team strategy briefing.

> **PickMyChamp does not just tell you who to pick. It tells your team how to win with the draft you have.**

Most pick tools help players compare champions, matchups, builds, and draft fit. PickMyChamp should take the next step: translate the completed draft into an understandable win condition and a concrete job for each role.

This is a product hypothesis, not a claim that no other product offers anything similar. Blitz, for example, already promotes draft recommendations based on fit, synergy, and threats. The differentiation to validate is the **actionable, team-wide playbook**, rather than another draft score or pick ranking.

## User problem

Players can see recommendations and statistics but may still not know:

- what their team composition is good at;
- what their team should try to do in the game;
- how their own role contributes to that plan;
- what to avoid, or how the plan changes when the team falls behind.

The feature should turn draft information into decisions a player can remember and use.

## Intended experience

1. The player fills in their lane and the champions revealed on both teams.
2. PickMyChamp updates a preliminary strategy as the draft develops.
3. After the teams are set, PickMyChamp generates a concise playbook.
4. The player can focus on their role or share the team briefing with allies.

### Playbook contents

- **Team identity:** a plain-language description of the composition's strengths and constraints.
- **Primary win condition:** the most plausible way this team should seek advantages.
- **Role assignments:** one actionable responsibility for each role, with the user's job emphasized.
- **Timing or trigger:** a recognizable condition for taking a fight, contesting an objective, or changing the plan.
- **Avoid:** a costly pattern that conflicts with the composition's strengths.
- **Fallback:** a simple adjustment if the first plan is unavailable or the team falls behind.
- **Reasoning and confidence:** which draft traits support the advice, and how uncertain it is.

The plan should be brief enough to scan before the game. It must not present generic advice as if it were specific to the draft.

## Example of the intended output

> - **Plan:** Your draft is strongest when it can start a coordinated fight, not when it spreads out to trade poke.
> - **Your job:** Keep your engage available for a fight your team can follow up on.
> - **Look for:** A grouped objective fight when the key engage tools are ready.
> - **Avoid:** Starting alone or spending the main engage tool before your team can join.
> - **If behind:** Avoid forcing a straight fight; look for a safer pick or trade elsewhere.
> - **Why:** The advice is tied to the engage and follow-up tools present in this draft.

This is illustrative product copy, not champion-specific strategic advice.

## MVP scope

- Add a full-draft input to the existing draft assistant: allied and enemy champions, with role assignments.
- Generate a compact, role-aware playbook that updates when the draft changes.
- Start with a small set of explicit, testable composition patterns and curated rules.
- Tie each recommendation to visible draft evidence; show a useful uncertainty or insufficient-data state rather than inventing certainty.
- Make the final briefing easy to copy or share. A polished share link can follow after the core experience is validated.

### Initial composition patterns to investigate

- engage and follow-up;
- pick and skirmish;
- poke and siege;
- protect-the-carry;
- scaling and team fight;
- split pressure.

These are candidate categories, not a commitment to force every draft into exactly one archetype. Mixed or unclear compositions should be represented honestly.

## Not in the first version

- A live in-game overlay or real-time match coach.
- Automated gameplay actions or any system that plays for the user.
- A guaranteed game outcome or a draft win-rate score presented as certainty.
- Detailed item-by-item build recommendations.
- Full post-game replay analysis or automatic performance grading.
- A free-form LLM as the source of strategic facts.

## Product principles

1. **Specific over verbose:** Give a few usable instructions, not a long generic essay.
2. **Evidence over authority:** Explain which picks or draft traits support each recommendation.
3. **Useful uncertainty:** Say when the draft is mixed, the evidence is weak, or no clear plan is supported.
4. **Player agency:** Present advice as a plan to consider, not a command or guarantee.
5. **Patch awareness:** Recheck champion abilities and data assumptions as the game changes.
6. **Fast to use:** The player should be able to understand the briefing before loading into the game.

## Current implementation status

The web MVP now includes a manual five-role board for both teams and a
`POST /api/playbook` endpoint. It can produce conservative signals for
coordinated engage, poke, pick, protect-the-scaling-carry, and scaling patterns
from a limited curated champion profile set. The briefing includes the
selected player's role job, role responsibilities, opposing-team read,
supporting picks, profile coverage, and explicit limitations. The existing
counter-pick flow remains available, and its enemy pick is copied into the
matching opponent lane slot.

This is a first vertical slice, not a finished strategy product. Many
champions are not yet profiled; split-push and other patterns are not
implemented; there is no share link or saved draft; and the rules have not yet
been validated with players. Unknown or mixed drafts intentionally receive no
invented win condition.

## Implementation approach to evaluate

Begin with structured, deterministic rules or curated templates for a limited set of draft patterns. Keep the strategy logic separate from the presentation so the team can test whether the recommendations are correct and useful. An LLM may later help phrase validated facts, but it should not invent champion capabilities, matchup evidence, or strategic claims.

Before implementation, decide:

- how the user enters the full draft without making the existing flow cumbersome;
- what data is available and permitted for the chosen experience;
- how role assignments and uncertain picks are handled;
- how patch changes invalidate or refresh strategic rules;
- whether sharing is needed for the first release or can wait.

## Validation plan

Test the concept on a varied set of realistic drafts, including strong, weak, mixed, and unusual compositions. Have League players judge whether each playbook is:

- specific to the selected draft;
- understandable at a glance;
- actionable for their role;
- honest about uncertainty.

Record which advice players find vague, incorrect, or impossible to coordinate. Do not expand the number of draft patterns until the initial set meets an agreed quality bar.

Suggested prototype success criteria to confirm with testers:

- players can explain their role's main job after reading the briefing once;
- players can identify the team's primary win condition;
- the briefing is perceived as more useful than a pick ranking alone;
- advice is rejected or qualified when the supporting evidence is inadequate.

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| Advice sounds generic | Require each instruction to cite a visible draft trait and test against contrasting drafts. |
| A single archetype oversimplifies a composition | Allow mixed identities and explicitly report when there is no clear primary plan. |
| Strategy claims become stale after patches | Version the rules and review them when relevant champion mechanics change. |
| Full-draft entry adds too much friction | Prototype the input flow before expanding the strategy engine; reuse the current champion and lane selection patterns where possible. |
| The plan promises more than the data supports | Keep confidence visible and prefer no recommendation over fabricated certainty. |

## Next working session

1. Review the existing output against realistic, contrasting drafts with League players.
2. Record incorrect, vague, or missing advice and expand curated profiles only where evidence supports it.
3. Agree on a quality bar for when to show a primary plan versus an uncertain or mixed result.
4. Evaluate a copy/share card after the core playbook is useful and trusted.
5. Recheck patch and competitor assumptions before making comparative product claims.

## Competitive positioning to validate

The intended distinction from OP.GG, U.GG, and Blitz is not access to more counters or another ranking. It is the transition from draft information to a shareable, role-specific team plan. Competitor capabilities change; verify current products again before making public comparative claims.

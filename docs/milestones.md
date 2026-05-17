# Milestones

Milestones are one-shot achievements that recognize meaningful firsts in
the Research Entity's history. They reward research points exactly once,
they are deterministic, and they are auto-claimed the moment their
condition becomes true.

Milestones complement surveys: surveys ask the player to commit to a
*plan*, milestones reward *moments*.

## Default catalogue

| ID | Name | Reward | Trigger |
|----|------|--------|---------|
| `first_light` | First Light | 5 | Complete the entity's first observation pass |
| `named_entity` | Founding Charter | 5 | Give the entity a name other than the default |
| `first_planet` | First Planet Confirmed | 5 | Confirm a planet (≥ 75% confidence) |
| `first_moon` | First Moon Confirmed | 5 | Confirm a moon (≥ 75% confidence) |
| `first_comet` | First Comet Detected | 10 | Detect a comet (≥ 50% confidence) |
| `first_upgrade` | First Telescope Upgrade | 10 | Unlock any tier beyond the naked eye |
| `radio_first_light` | Radio First Light | 20 | Make a radio-band observation |
| `first_deep_sky_object` | First Deep-Sky Object | 40 | Discover a galaxy, quasar, or LAB |
| `first_black_hole_candidate` | First Black Hole Candidate | 75 | Identify a candidate black hole |
| `first_magnetar` | First Magnetar Confirmed | 75 | Confirm a magnetar |
| `multi_messenger_confirmation` | Multi-Messenger Confirmation | 100 | Confirm an object with ≥ 3 signal types |
| `cosmic_web_mapped` | Cosmic Web Mapped | 150 | Confirm a cosmic web filament/node |
| `dark_matter_inferred` | Dark Matter Inferred | 200 | Use a dark-matter inference signal |
| `now_scope_first_light` ⚠ | Now-Scope First Light *(speculative)* | 300 | First speculative now-signal observation |

## Evaluation

`evaluate_milestones(state)` walks every milestone, runs its predicate,
and for newly satisfied conditions:

- writes a `MilestoneRecord` with `achieved=True`, `reward_claimed=True`,
  and `achieved_at_turn=state.turn`;
- adds `reward_research_points` to the state's RP balance;
- returns the list of newly-achieved milestones.

`claim_milestone_rewards(state)` is an idempotent alias — calling it
repeatedly never double-credits a reward.

## When milestones are evaluated

- After each `game observe` (Python and UI).
- Manually via `game claim-milestones` (useful right after `game init`,
  which doesn't currently invoke evaluation).
- Inside the browser UI on every observation/upgrade and once at load
  time, so importing a CLI-saved state immediately credits any
  unevaluated milestones.

## CLI

```bash
# List achievements with status, rewards, and speculative markers
uv run universe game milestones --state data/generated/game-state.json

# Re-evaluate (no-op if nothing new is eligible)
uv run universe game claim-milestones \
  --state data/generated/game-state.json \
  --out data/generated/game-state.json
```

## UI

The browser UI shows milestones in the **Milestones** tab — achieved at
the top, remaining below — with rewards and a SPECULATIVE badge for the
now-scope milestone.

## Implementation note

Conditions are written as plain Python predicates over `ResearchState` in
`src/universe/game/milestones.py`. There is intentionally no rules engine.
If the catalog grows beyond ~30 entries, refactor at that point.

## Balance playtesting

Milestone trigger turns appear in playtest `summary.milestone_turn` and `milestone_achieved` events. See [balance-playtesting.md](balance-playtesting.md).

## Limitations

- Hidden milestones are supported by the model (`hidden: bool`) but the
  default catalog does not currently use them.
- Achievement notifications appear in the discovery log only; there is no
  toast/popup yet.
- The `condition_type` field is currently informational; it is not used
  for filtering or grouping.

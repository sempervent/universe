# Manual playtest guide (30–45 minutes)

Use this checklist for first-run UX validation. **Godot** is the preferred manual playtest surface; **CLI `game status`** is mission control; static HTML is useful but cannot hot-swap scenes.

## Setup

```bash
uv sync
uv run universe demo godot --reset
uv run universe demo check

(`demo godot` runs Godot headless validation when a binary is detected; `demo check` does the same by default.)
```

Open the Godot project (`frontends/godot/project.godot`) and press Play.

**Expected default view:** Observatory / telescope perspective (sky dome, not a
cluster of nearby planet spheres). If you see floating balls in space, press **V**
or switch **View mode** to **Observatory View** (Scene Map is debug-only).

Equivalent manual steps (if you prefer granular CLI):

```bash
uv run universe game generate-scene --scene solar-system
# ... other campaign scenes ...
uv run universe game init --name "..." --entity-type private_institute --out data/generated/game-state.json
uv run universe game export-godot-data --out frontends/godot/data
```

Optional static HTML (one scene only):

```bash
uv run universe demo html --scene solar-system --reset --open
```

## Checklist

| Step | Action | Expected UI cue | Expected state change | Bug notes |
|------|--------|-----------------|----------------------|-----------|
| 1 | Name entity / confirm objective | Header shows entity name; Objectives tab shows active tutorial objective; “Next action” line | `research_entity` set; `active_objective_ids` populated | |
| 2 | Observe local sky (Observatory View) | Sky dome / targets visible; header says **View: Observatory**; Observe works | Discovery progress, RP possible | Scene Map (V) shows spatial debug layout only |
| 3 | Start / complete First Light | Objective card updates; next objective activates | `objectives.*.status` completed; RP awarded | |
| 4 | Upgrade telescope | Tech tab shows affordable tier; upgrade succeeds | `unlocked_tiers`, RP spent | |
| 5 | Observe solar transient (when active) | Transients tab: **Active** group; button “Observe: …” | Transient reward, log entry | |
| 6 | Unlock Scene 001 | Campaign / CLI shows scene-001 unlocked | `campaign.scenes.scene-001.unlocked` | |
| 7 | Campaign: generate / load / set Scene 001 | Missing file shows `generate-scene` command; Load + Set Active works | Active scene `scene-001`; deep field loads | |
| 8 | Start Deep Field Survey | Surveys: recommended marker; start survey | `active_survey_id` set | |
| 9 | Deep-field discovery | Survey progress increments | Survey progress / discovery | |
| 10 | Switch signal modes | Signal dropdown changes sky emphasis | `known_signal_types` / visuals | |
| 11 | Load radio survey scene | Campaign load `radio-cmb-survey` | Scene JSON loaded | |
| 12 | Observe transient if active | Active / Upcoming / Expired groups; blocked reason if any | Transient observed or blocked message | |
| 13 | Save / Reload | Log shows exact paths; header save lines update | State persisted | |
| 14 | Export state | Export window / file written | JSON export | |
| 15 | CLI status / report | `Next actions`, recommended next step | Matches in-game hints | |

CLI spot-check:

```bash
uv run universe game status --state data/generated/game-state.json
uv run universe game report \
  --scene data/generated/solar-system/scene.json \
  --state data/generated/game-state.json \
  --out data/generated/game-report.md
```

## Bug report template

```
**Build:** (git sha / date)
**Frontend:** Godot | HTML | CLI
**Step:** (checklist #)
**Expected:**
**Actual:**
**State file:** data/generated/game-state.json (attach if possible)
**Scene:** (id + path)
**Repro:**
1.
2.
**Screenshots / logs:**
```

# Godot 4 Telescope Frontend (Prototype)

A real, runnable Godot 4 frontend for the `universe` telescope game.
This prototype consumes the Python project's canonical scene/state JSON,
renders a legible 3D representation, and exposes the full observe →
discover → survey → milestone loop.

## Status

- ✅ Loads `scene.json` and `game-state.json` from the parent repo
- ✅ **Observatory View (default)** — sky dome / instrument perspective; solar-system and deep-field objects as apparent sky targets (`ObservatoryRenderer` + `SkyProjection`)
- ✅ **Scene Map (debug)** — floating 3D spatial layout (`SkyRenderer`); toggle via **V** or View mode dropdown
- ✅ Renders solar-system and **deep-field** scenes in both modes (Scene Map: log-radial AU / Mpc layout; Observatory: deterministic sky projection)
- ✅ **3D picking** — click targets in the viewport (ray + `Area3D`); selection syncs with list + detail + log
- ✅ **Telescope camera** — Observatory pan/zoom FOV or Scene Map orbit; **F** center/focus, **R** reset, **L** labels, **V** view toggle
- ✅ **Viewfinder overlay** — reticle, FOV ring, tier/signal HUD, target lock (`TelescopeOverlay.gd`)
- ✅ **Tier/signal visibility** — hide/dim sky targets by instrument (`InstrumentVisibility.gd`)
- ✅ **Signal visualization modes** — palette + emphasize/dim by instrument (from `discovery_requirements.json` + heuristics)
- ✅ **Discovery visuals** — materials reflect confidence band; selected object gets a highlight pass
- ✅ Observatory console UI (header, object list, detail, tech tree, surveys, milestones, **Campaign / Observing Program** tab, log, reset + export JSON)
- ✅ **Campaign scene picker** — list all catalog scenes, lock/unlock status, file present/missing, load / set active / generate commands (Python CLI only)
- ✅ Save/load game state (repo path with `user://game-state.json` fallback; path shown in header)
- ✅ Tech-tree unlocks, survey progression, milestone evaluation
- ⚠ Visual polish is intentionally minimal — clarity over beauty

The Python CLI and the static HTML telescope UI remain canonical.

**Manual playtest:** follow [docs/manual-playtest.md](../../docs/manual-playtest.md). Header shows active objective, next action, and save paths. Use `uv run universe game status` for **Next actions**.

## Project layout

```
frontends/godot/
  project.godot
  icon.svg
  scenes/
    Main.tscn            ← entry scene (just hosts Main.gd)
  scripts/
    Main.gd              ← orchestrator: loads data, builds 3D + UI
    FilePaths.gd         ← autoload: resolves scene/state paths
    SceneLoader.gd       ← scene.json loader + minimal validation
    GameState.gd         ← state JSON load/save + backward-compat
    TechTree.gd          ← derive aggregate telescope capabilities
    DiscoveryEngine.gd   ← confidence + RP award (mirrors Python)
    SurveyEngine.gd      ← survey status / start / claim / progress
    MilestoneEngine.gd   ← milestone predicates + auto-claim
    ObservatoryRenderer.gd ← primary sky-dome telescope view
    SkyProjection.gd       ← deterministic sky angles / apparent size
    SkyRenderer.gd         ← Scene Map spatial builder (debug)
    TelescopeCamera.gd     ← observatory or orbit camera; pick threshold
    TelescopeConsole.gd  ← CanvasLayer UI overlay
  data/
    *.json               ← committed copy of `game export-godot-data`
  assets/
    README.md            ← placeholder for future binary assets
```

## Quickstart

1. From the repo root, prepare everything:

    ```bash
    uv sync
    uv run universe demo godot --reset
    ```

    When Godot is on PATH (or `GODOT_BIN` is set), that command also runs headless script validation and fails before you open a broken project. Use `--skip-godot-validate` only to bypass.

    Optional: `uv run universe demo godot --reset --launch` if Godot is installed.

2. Open `frontends/godot/project.godot` in Godot 4.x (any 4.2+).

3. Press **F5** to run. The default main scene (`scenes/Main.tscn`) loads
   the solar-system scene and your game state automatically.

If Godot shows the wrong scene, delete `user://overrides.json` (see
`--clear-overrides` on `universe demo godot`) or use **Project → Open User Data Folder**.

### Troubleshooting

**`Could not resolve script "res://scripts/TelescopeConsole.gd"`**

Usually a **parse error inside** `TelescopeConsole.gd` (Godot reports it as unresolved), not a missing file.

1. `uv run universe demo check` — verifies scripts exist and `res://` paths resolve.
2. Open **`frontends/godot/project.godot`** (not the repo root).
3. Confirm `frontends/godot/scripts/TelescopeConsole.gd` exists (exact casing).
4. In Godot: **Project → Reload Current Project** after pulling fixes.
5. Only if paths are correct: clear `.godot/` cache under `frontends/godot/` and reopen.

### Campaign scene picker (Observing Program tab)

Godot **cannot** run Python generators. Use the **Campaign** tab (right panel) to:

1. See all six campaign scenes, unlock status, and whether `scene.json` exists on disk.
2. **Load Scene** — switch the 3D view to a generated scene file (catalog default path).
3. **Set Active** — update `campaign.active_scene_id` in game state (mirror of `universe game set-scene`).
4. **Load + Set Active** — both at once when the file exists.

If a scene file is missing, the tab shows:

```bash
uv run universe game generate-scene --scene radio-cmb-survey
```

Generate all campaign scenes once:

```bash
uv run universe game generate-scene --scene solar-system
uv run universe game generate-scene --scene scene-001
uv run universe game generate-scene --scene radio-cmb-survey
uv run universe game generate-scene --scene stellar-remnant-field
uv run universe game generate-scene --scene cosmic-web-map
uv run universe game generate-scene --scene now-scope-anomaly-field
```

**Active scene vs loaded scene:** the campaign tracks which program you are on (`active_scene_id`); the loaded `scene.json` is what you see in the viewport. They can differ — the tab warns you when they do.

Advanced: `user://overrides.json` still overrides default scene/state paths for manual setups.

### Switching to Scene 001 (deep field)

Generate the deep-field scene from the repo root, then use the Campaign tab or overrides:

```bash
uv run universe game generate-scene --scene scene-001
```

Use absolute paths in `user://overrides.json` (via *Project → Open User Data Folder*):

```json
{
  "scene_path": "/ABS/PATH/TO/universe/data/generated/scene-001/scene.json",
  "state_path": "/ABS/PATH/TO/universe/data/generated/game-state.json"
}
```

Restart the game or press **Reload Scene/State** after editing overrides.

## Controls (viewport + console)

| Control | Action |
|--------|--------|
| Click object (tap, no drag) | Select object in 3D |
| Mouse wheel | Zoom in / out |
| Left or right drag | Orbit around focus target |
| Middle drag, or Shift + left drag | Pan |
| **F** | Focus camera on selected object |
| **R** | Reset camera |
| **L** | Toggle object labels |
| **+** / **-** (or keypad) | Zoom |

## Configuring data paths

By default the Godot project reads:

- scene: `frontends/godot/../../data/generated/solar-system/scene.json`
- state: `frontends/godot/../../data/generated/game-state.json`

To point at different files without editing scripts, drop a JSON file at
`user://overrides.json`:

```json
{
  "scene_path": "/abs/path/to/scene.json",
  "state_path": "/abs/path/to/game-state.json"
}
```

The `user://` directory is shown in Godot's *Project → Open User Data
Folder* menu.

## Saving state

Press **Save State** in the console. Success or failure is written to the
discovery log. The engine prefers the path it loaded (`_state_path`); if that
path is not writable, it saves to `user://game-state.json` and updates the
in-memory path so the next save goes to the same fallback. The header shows
**Scene** and **Last save** paths.

**Reset State…** clears progress to a fresh in-memory state (with a confirm
dialog); use **Save State** to persist. **Export State…** opens a window with
the current JSON (copy-friendly).

## What lives where

| Concern | Source of truth |
|---|---|
| Scene generation | Python (`src/universe/procedural/`) |
| Game definitions (tiers, surveys, milestones, requirements) | Python — exported as JSON to `data/` |
| Game-state schema | Python (`ResearchState`) |
| Discovery / survey / milestone *rules* | Mirrored in GDScript; treat Python as canonical when they diverge |
| 3D rendering | Godot |
| Console UI | Godot |

When Python rules change, regenerate the data bundle and (if rules
themselves changed) update the matching GDScript engine.

## Limitations

- GDScript discovery engine is a subset of Python; treat CLI as canonical when in doubt.
- No automated Godot runtime tests in CI (Python tests cover export + script/doc markers).
- Solar-system layout uses coarse logarithmic compression in world space.
- Deep-field polish is **prototype legibility**, not a cinematic renderer: LAB is nested translucent shells with a gentle emission pulse; filaments are segmented cylinders; quasars use deterministic jet axes from object ids.
- Arrow / WASD camera nudges are not implemented (mouse + keys above only).
- `now-scope` content uses the same primitives; speculative tiers are labelled in UI.

## Scene 001 manual test checklist (Godot)

After `uv run universe generate scene-001 …` and `user://overrides.json` with absolute paths to `scene-001/scene.json` and `game-state.json`, press **Reload Scene/State** and verify:

1. Header shows **Deep Field · High-z protocluster**, redshift **z**, and region **cMpc**.
2. Initial camera frames the protocluster / LAB neighborhood (not collapsed at origin).
3. **LAB** reads as a large translucent multi-shell blob with subtle pulse; **Ultraviolet** signal mode boosts it.
4. **Quasar** has a bright core and bipolar jets; **Radio** boosts jets, **X-ray** boosts core emphasis vs LAB.
5. **Black hole** is a dark core with a faint accretion ring; almost invisible in **Visible light** until inference modes.
6. **Magnetar** is compact with faint torus “field” placeholders; **X-ray / Gamma** favor it.
7. **Filaments** follow graph control points (not only node–node); **Weak lensing** / **Dark matter inference** brighten them; labels stay sparse until confidence/selection.
8. **Survey hint** appears when no survey is active (suggests Deep Field / Radio / Compact programs when unlocked).
9. Object list **filter** (All / Unknown / …) narrows the list without breaking selection metadata.

## See also

- `docs/godot-frontend.md` — design notes and data contract
- `docs/import-planning.md` — original Unreal/Godot mapping notes
- `docs/telescope-ui.md` — the static HTML UI prototype

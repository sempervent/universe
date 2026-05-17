"""Command-line interface for the universe project."""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

import click

from universe.export.scene_json import export_scene
from universe.models import SceneRegion
from universe.procedural.region import generate_scene_001


@click.group()
@click.version_option(package_name="universe")
def main() -> None:
    """universe — engine-agnostic cosmic visualization sandbox."""


# ── Scene generation commands ──────────────────────────────────────────


@main.command()
@click.argument("scene_id")
@click.option("--seed", default="lyman-alpha-furnace", help="Deterministic seed string.")
@click.option("--out", default="data/generated/scene-001", help="Output directory.")
@click.option("--galaxies", default=80, type=int, help="Number of galaxies to generate.")
@click.option("--nodes", default=12, type=int, help="Number of cosmic web nodes.")
def generate(scene_id: str, seed: str, out: str, galaxies: int, nodes: int) -> None:
    """Generate a scene.  Supported: scene-001, solar-system."""
    if scene_id == "scene-001":
        scene = generate_scene_001(seed=seed, num_nodes=nodes, num_galaxies=galaxies)
    elif scene_id in ("solar-system", "starter"):
        from universe.procedural.solar_system import generate_solar_system

        scene = generate_solar_system(seed=seed)
        if out == "data/generated/scene-001":
            out = "data/generated/solar-system"
    else:
        click.echo(f"Unknown scene: {scene_id}. Available: scene-001, solar-system", err=True)
        sys.exit(1)

    click.echo(f"Generating {scene_id} with seed='{seed}' ...")
    artifacts = export_scene(scene, out)

    click.echo("Artifacts written:")
    for name, path in artifacts.items():
        click.echo(f"  {name}: {path}")
    click.echo("Done.")


@main.command()
@click.argument("scene_json", type=click.Path(exists=True))
def inspect(scene_json: str) -> None:
    """Print a summary of a scene.json file."""
    data = json.loads(Path(scene_json).read_text())
    scene = SceneRegion.model_validate(data)

    counts = Counter(obj.type.value for obj in scene.objects)

    click.echo(f"Scene: {scene.name}")
    click.echo(f"  ID:       {scene.id}")
    click.echo(f"  Seed:     {scene.seed}")
    click.echo(f"  Redshift: {scene.redshift}")
    click.echo(f"  Size:     {scene.size_mpc} cMpc")
    click.echo(f"  Nodes:    {len(scene.nodes)}")
    click.echo(f"  Filaments:{len(scene.filaments)}")
    click.echo("  Objects:")
    for otype, cnt in sorted(counts.items()):
        click.echo(f"    {otype}: {cnt}")

    notable = [o for o in scene.objects if o.type.value in (
        "lyman_alpha_blob", "quasar", "black_hole", "magnetar",
    )]
    if notable:
        click.echo("  Notable:")
        for obj in notable:
            click.echo(f"    {obj.name} ({obj.type.value}) — {obj.description[:80]}")


@main.command()
@click.argument("scene_json", type=click.Path(exists=True))
@click.option("--out", default=None, help="Output path for summary.md (default: alongside scene.json).")
def summarize(scene_json: str, out: str | None) -> None:
    """Generate or refresh the Markdown summary for a scene."""
    data = json.loads(Path(scene_json).read_text())
    scene = SceneRegion.model_validate(data)

    from universe.export.scene_json import _build_summary

    summary = _build_summary(scene)
    out_path = Path(out) if out else Path(scene_json).parent / "summary.md"
    out_path.write_text(summary, encoding="utf-8")
    click.echo(f"Summary written to {out_path}")


# ── Game commands ──────────────────────────────────────────────────────


@main.group()
def game() -> None:
    """Telescope progression and discovery game commands."""


def _load_game_state(state_path: str):
    from universe.game.models import ResearchState
    from universe.game.scenes import ensure_campaign_state

    return ensure_campaign_state(
        ResearchState.model_validate_json(Path(state_path).read_text(encoding="utf-8"))
    )


def _save_game_state(state, path: Path) -> None:
    from universe.game.scenes import ensure_campaign_state

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(ensure_campaign_state(state).model_dump_json(indent=2), encoding="utf-8")


@game.command("tech-tree")
@click.option(
    "--state",
    "state_path",
    default=None,
    type=click.Path(exists=True),
    help="Optional game state — show effective RP costs for your entity background.",
)
def game_tech_tree(state_path: str | None) -> None:
    """Print the telescope tech tree."""
    from universe.game.models import ResearchState
    from universe.game.tech_tree import effective_tier_research_cost, get_default_tech_tree

    state = None
    if state_path:
        state = ResearchState.model_validate_json(Path(state_path).read_text())

    tree = get_default_tech_tree()
    for tier in tree:
        spec = " [SPECULATIVE]" if tier.speculative else ""
        click.echo(f"Tier {tier.tier_index}: {tier.name}{spec}")
        click.echo(f"  ID:            {tier.id}")
        if state is not None:
            eff = effective_tier_research_cost(tier, state)
            if eff != tier.research_cost:
                click.echo(f"  Cost:          {eff} RP (base {tier.research_cost} RP)")
            else:
                click.echo(f"  Cost:          {eff} RP")
        else:
            click.echo(f"  Cost:          {tier.research_cost} RP")
        click.echo(f"  Signals:       {', '.join(s.value for s in tier.signal_types)}")
        click.echo(f"  Prerequisites: {', '.join(tier.prerequisites) or '(none)'}")
        click.echo(f"  Resolution:    {tier.resolution_arcsec}\"")
        click.echo(f"  Sensitivity:   {tier.sensitivity}")
        click.echo(f"  Max distance:  {tier.max_effective_distance_mpc} Mpc")
        click.echo(f"  {tier.description}")
        click.echo()


@game.command("init")
@click.option("--out", default="data/generated/game-state.json", help="Output path for game state.")
@click.option("--starting-rp", default=0, type=int, help="Starting research points.")
@click.option("--name", default=None, help="Research entity name.")
@click.option("--entity-type", "etype", default="custom", help="Entity type (e.g. backyard_observatory, private_institute).")
@click.option("--motto", default=None, help="Entity motto.")
def game_init(out: str, starting_rp: int, name: str | None, etype: str, motto: str | None) -> None:
    """Initialize a new game state."""
    from universe.game.entity import (
        ENTITY_TYPE_LABELS,
        format_entity_modifier_summary,
        make_research_entity,
    )
    from universe.game.models import ResearchState

    entity = make_research_entity(
        name=name or "Unnamed Research Entity",
        entity_type=etype,
        motto=motto,
    )
    from universe.game.scenes import ensure_campaign_state

    state = ensure_campaign_state(
        ResearchState(research_points=starting_rp, research_entity=entity)
    )
    out_path = Path(out)
    _save_game_state(state, out_path)
    click.echo(f"Game state initialized: {out_path}")
    click.echo(f"  Entity: {entity.name}")
    if entity.motto:
        click.echo(f"  Motto: \"{entity.motto}\"")
    type_label = ENTITY_TYPE_LABELS.get(entity.entity_type, entity.entity_type)
    click.echo(f"  Type: {entity.entity_type} ({type_label})")
    click.echo(f"  Background: {format_entity_modifier_summary(entity.entity_type)}")
    click.echo(f"  Telescope: {state.active_telescope_tier}")
    click.echo(f"  RP: {state.research_points}")
    click.echo(f"  Signals: {', '.join(state.known_signal_types)}")


@game.command("observe")
@click.option("--scene", "scene_path", required=True, type=click.Path(exists=True), help="scene.json to observe.")
@click.option("--state", "state_path", required=True, type=click.Path(exists=True), help="Current game state.")
@click.option("--out", default=None, help="Output path for updated state (default: overwrite --state).")
def game_observe(scene_path: str, state_path: str, out: str | None) -> None:
    """Observe a scene and discover objects."""
    from universe.game.discovery import observe_scene

    scene_data = json.loads(Path(scene_path).read_text())
    scene_data.pop("_units", None)
    scene = SceneRegion.model_validate(scene_data)

    state = _load_game_state(state_path)
    new_state, results = observe_scene(scene, state)

    entity_name = state.research_entity.name

    if not results:
        click.echo(f"{entity_name}: No new discoveries or upgrades in this observation.")
    else:
        click.echo(f"{entity_name} — observation results (turn {new_state.turn}):")
        for r in results:
            click.echo(f"  {r.message}")
        total_rp = new_state.research_points - state.research_points
        click.echo(f"Net RP this turn: +{total_rp} (now {new_state.research_points})")

    out_path = Path(out) if out else Path(state_path)
    _save_game_state(new_state, out_path)
    click.echo(f"State saved: {out_path}")


@game.command("upgrade")
@click.option("--state", "state_path", required=True, type=click.Path(exists=True))
@click.option("--tier", required=True, help="Tier ID to unlock.")
@click.option("--out", default=None, help="Output path for updated state.")
def game_upgrade(state_path: str, tier: str, out: str | None) -> None:
    """Unlock a telescope tier."""
    from universe.game.tech_tree import unlock_tier

    state = _load_game_state(state_path)
    new_state, message = unlock_tier(state, tier)
    click.echo(message)

    out_path = Path(out) if out else Path(state_path)
    _save_game_state(new_state, out_path)
    click.echo(f"State saved: {out_path}")


@game.command("set-telescope")
@click.option("--state", "state_path", required=True, type=click.Path(exists=True))
@click.option("--tier", required=True, help="Tier ID to set as active.")
@click.option("--out", default=None, help="Output path for updated state.")
def game_set_telescope(state_path: str, tier: str, out: str | None) -> None:
    """Set the active telescope tier (must already be unlocked)."""

    state = _load_game_state(state_path)
    if tier not in state.unlocked_tiers:
        click.echo(f"Tier '{tier}' is not unlocked.", err=True)
        sys.exit(1)

    new_state = state.model_copy(update={"active_telescope_tier": tier})
    out_path = Path(out) if out else Path(state_path)
    _save_game_state(new_state, out_path)
    click.echo(f"Active telescope set to: {tier}")
    click.echo(f"State saved: {out_path}")


def _print_campaign_status(state) -> None:
    from universe.game.scenes import (
        catalog_generate_command,
        generate_scene_command,
        get_default_scene_catalog,
        get_scene_definition,
        recommended_next_scene,
        scene_json_path,
    )

    active = get_scene_definition(state.campaign.active_scene_id)
    active_name = active.name if active else state.campaign.active_scene_id
    click.echo(f"  Active campaign scene: {active_name} ({state.campaign.active_scene_id})")
    nxt = recommended_next_scene(state)
    if nxt:
        click.echo(f"  Recommended next: {nxt.name} ({nxt.id})")
        click.echo(f"    {generate_scene_command(nxt)}")
    click.echo("  Campaign scenes:")
    for defn in sorted(get_default_scene_catalog(), key=lambda d: d.order_index):
        cs = state.campaign.scenes.get(defn.id)
        if cs is None:
            continue
        marker = " *" if defn.id == state.campaign.active_scene_id else ""
        lock = "unlocked" if cs.unlocked else "locked"
        visit = ", visited" if cs.visited else ""
        req = ""
        if not cs.unlocked and defn.unlock_tier_id:
            req = f" (needs {defn.unlock_tier_id})"
        click.echo(f"    [{lock}{visit}]{marker} {defn.id} — {defn.name}{req}")
        if cs.unlocked:
            path = Path(scene_json_path(defn))
            if not path.exists():
                click.echo(f"      generate: {generate_scene_command(defn)}")
            click.echo(f"      legacy: {catalog_generate_command(defn)}")


@game.command("scenes")
@click.option("--state", "state_path", required=True, type=click.Path(exists=True))
def game_scenes(state_path: str) -> None:
    """List campaign observation scenes and unlock status."""
    from universe.game.scenes import generate_scene_command, get_default_scene_catalog
    from universe.game.surveys import get_survey_by_id

    state = _load_game_state(state_path)
    click.echo("Campaign observation scenes:")
    for defn in sorted(get_default_scene_catalog(), key=lambda d: d.order_index):
        cs = state.campaign.scenes.get(defn.id)
        unlocked = cs.unlocked if cs else False
        active = defn.id == state.campaign.active_scene_id
        click.echo("")
        click.echo(f"  {defn.id} — {defn.name}{'  [ACTIVE]' if active else ''}")
        click.echo(f"    Status: {'unlocked' if unlocked else 'locked'}")
        if defn.unlock_tier_id:
            click.echo(f"    Unlock: tier {defn.unlock_tier_id}")
        if defn.unlock_milestone_id:
            click.echo(f"    Narrative trigger: milestone {defn.unlock_milestone_id}")
        if defn.recommended_survey_ids:
            names = []
            for sid in defn.recommended_survey_ids[:4]:
                s = get_survey_by_id(sid)
                names.append(s.name if s else sid)
            click.echo(f"    Surveys: {', '.join(names)}")
        if defn.recommended_signal_modes:
            click.echo(
                "    Signals: "
                + ", ".join(s.value for s in defn.recommended_signal_modes[:6])
            )
        click.echo(f"    Generate: {generate_scene_command(defn)}")


@game.command("set-scene")
@click.option("--state", "state_path", required=True, type=click.Path(exists=True))
@click.option("--scene", "scene_id", required=True, help="Campaign scene id (e.g. scene-001).")
@click.option("--out", default=None, help="Output path for updated state.")
def game_set_scene(state_path: str, scene_id: str, out: str | None) -> None:
    """Set the active campaign observation scene."""
    from universe.game.scenes import set_active_scene

    state = _load_game_state(state_path)
    new_state, message = set_active_scene(state, scene_id)
    click.echo(message)
    if "locked" in message.lower():
        sys.exit(1)
    out_path = Path(out) if out else Path(state_path)
    _save_game_state(new_state, out_path)
    click.echo(f"State saved: {out_path}")


@game.command("generate-scene")
@click.option("--scene", "scene_id", required=True, help="Campaign scene id to generate.")
@click.option("--seed", default=None, help="Override default seed from catalog.")
@click.option("--out", default=None, help="Override default output directory.")
def game_generate_scene(scene_id: str, seed: str | None, out: str | None) -> None:
    """Generate a campaign scene using catalog defaults (wraps universe generate)."""
    from universe.export.scene_json import export_scene
    from universe.game.scenes import get_scene_definition

    defn = get_scene_definition(scene_id)
    if defn is None:
        click.echo(f"Unknown campaign scene: {scene_id}", err=True)
        sys.exit(1)

    use_seed = seed or defn.default_seed
    use_out = out or defn.default_output_path
    gen = defn.generator_name or defn.id

    if gen in ("solar-system", "starter"):
        from universe.procedural.solar_system import generate_solar_system

        scene = generate_solar_system(seed=use_seed)
    elif gen == "scene-001":
        from universe.procedural.region import generate_scene_001

        scene = generate_scene_001(seed=use_seed)
    else:
        click.echo(f"No generator for scene: {gen}", err=True)
        sys.exit(1)

    click.echo(f"Generating {defn.name} (id={scene_id}, seed={use_seed}) ...")
    artifacts = export_scene(scene, use_out)
    click.echo("Artifacts written:")
    for name, path in artifacts.items():
        click.echo(f"  {name}: {path}")


@game.command("campaign")
@click.option("--state", "state_path", required=True, type=click.Path(exists=True))
def game_campaign(state_path: str) -> None:
    """Show campaign progression (active scene, unlocks, recommended next)."""
    state = _load_game_state(state_path)
    click.echo("=== Campaign ===")
    _print_campaign_status(state)


@game.command("status")
@click.option("--state", "state_path", required=True, type=click.Path(exists=True))
def game_status(state_path: str) -> None:
    """Print current game status."""
    from universe.game.entity import format_entity_modifier_summary, get_entity_modifier
    from universe.game.surveys import (
        SurveyProgramStatus,
        available_surveys,
        effective_survey_reward,
        get_survey_by_id,
    )
    from universe.game.tech_tree import available_upgrades, effective_tier_research_cost

    state = _load_game_state(state_path)

    entity = state.research_entity
    mod = get_entity_modifier(entity.entity_type)
    click.echo(f"=== {entity.name} ===")
    if entity.motto:
        click.echo(f"  \"{entity.motto}\"")
    click.echo(f"  Type: {entity.entity_type}")
    click.echo(f"  Background: {mod.name} — {mod.description}")
    click.echo(f"  Effects: {format_entity_modifier_summary(entity.entity_type)}")
    click.echo(f"  Turn: {state.turn}")
    click.echo(f"  Research Points: {state.research_points}")
    click.echo(f"  Active Telescope: {state.active_telescope_tier}")
    click.echo(f"  Unlocked Tiers: {', '.join(state.unlocked_tiers)}")
    click.echo(f"  Known Signals: {', '.join(state.known_signal_types)}")
    click.echo(f"  Discoveries: {len(state.discoveries)}")
    click.echo(f"  Confirmed (≥75%): {state.completed_discoveries}")

    completed_surveys = sum(1 for p in state.survey_progress.values() if p.completed)
    achieved = sum(1 for r in state.milestones.values() if r.achieved)
    click.echo(f"  Surveys completed: {completed_surveys}")
    click.echo(f"  Milestones achieved: {achieved}")

    click.echo("")
    click.echo("  Campaign:")
    _print_campaign_status(state)

    if state.active_survey_id:
        active = get_survey_by_id(state.active_survey_id)
        if active is not None:
            prog = state.survey_progress.get(active.id)
            done = prog.discoveries_completed if prog else 0
            click.echo(
                f"  Active Survey: {active.name} ({done}/{active.completion_goal})"
            )

    ups = available_upgrades(state)
    if ups:
        click.echo("  Available Upgrades:")
        for u in ups:
            eff = effective_tier_research_cost(u, state)
            if eff != u.research_cost:
                click.echo(f"    {u.id} — {u.name} ({eff} RP, base {u.research_cost} RP)")
            else:
                click.echo(f"    {u.id} — {u.name} ({eff} RP)")

    avail_surveys = available_surveys(state)
    if avail_surveys:
        click.echo("  Available Surveys:")
        for s in avail_surveys:
            rew = effective_survey_reward(s, state)
            rew_note = f"+{rew} RP" if rew != s.reward_research_points else f"+{s.reward_research_points} RP"
            click.echo(
                f"    {s.id} — {s.name} (goal {s.completion_goal}, {rew_note})"
            )
    elif not state.active_survey_id:
        from universe.game.surveys import _all_programs, survey_status

        any_locked = any(
            survey_status(state, p) == SurveyProgramStatus.LOCKED for p in _all_programs()
        )
        if any_locked:
            click.echo("  (More surveys unlock as you upgrade telescopes.)")

    from universe.game.guidance import get_guidance_hints

    # Guidance requires a scene; skip if none on disk.
    click.echo("")
    click.echo("  Guidance:")
    hints = []
    for candidate in (
        Path("data/generated/solar-system/scene.json"),
        Path("data/generated/scene-001/scene.json"),
    ):
        if candidate.exists():
            scene_data = json.loads(candidate.read_text())
            scene_data.pop("_units", None)
            scene = SceneRegion.model_validate(scene_data)
            hints = get_guidance_hints(scene, state)
            break
    if hints:
        for h in hints:
            click.echo(f"    [{h.severity.value}] {h.title}: {h.message}")
            if h.suggested_action:
                click.echo(f"      → {h.suggested_action}")
    else:
        click.echo("    (No hints — generate a scene and observe to refresh.)")


@game.command("surveys")
@click.option("--state", "state_path", required=True, type=click.Path(exists=True))
@click.option("--scene", "scene_path", default=None, type=click.Path(exists=True), help="Optional scene context for scope filtering.")
def game_surveys(state_path: str, scene_path: str | None) -> None:
    """List survey programs with status and progress."""
    from universe.game.models import ResearchState
    from universe.game.surveys import (
        SurveyProgramStatus,
        _all_programs,
        effective_survey_reward,
        survey_status,
    )

    state = ResearchState.model_validate_json(Path(state_path).read_text())
    scene_id = None
    if scene_path:
        scene_data = json.loads(Path(scene_path).read_text())
        scene_id = scene_data.get("id")

    click.echo(f"=== Survey Programs ({state.research_entity.name}) ===")
    for s in _all_programs():
        status = survey_status(state, s)
        prog = state.survey_progress.get(s.id)
        done = prog.discoveries_completed if prog else 0
        spec = " [SPECULATIVE]" if s.speculative else ""
        scope_note = ""
        if scene_id and s.scene_scope != "any":
            scope_match = (
                (s.scene_scope == "solar_system" and scene_id == "solar-system")
                or (s.scene_scope == "deep_field" and scene_id != "solar-system")
            )
            if not scope_match:
                scope_note = " (scope mismatch)"
        marker = {
            SurveyProgramStatus.LOCKED: "🔒",
            SurveyProgramStatus.AVAILABLE: " · ",
            SurveyProgramStatus.ACTIVE: "▶ ",
            SurveyProgramStatus.COMPLETED: "✓ ",
        }[status]
        click.echo(
            f"  {marker} {s.name}{spec}{scope_note}"
        )
        rew = effective_survey_reward(s, state)
        base = s.reward_research_points
        rew_txt = f"+{rew} RP" if rew == base else f"+{rew} RP (base {base})"
        click.echo(
            f"      id={s.id}  status={status.value}  "
            f"progress={done}/{s.completion_goal}  reward={rew_txt}"
        )
        if s.required_tier_ids:
            click.echo(f"      requires tiers: {', '.join(s.required_tier_ids)}")
        if s.required_signal_types:
            click.echo(f"      requires signals: {', '.join(s.required_signal_types)}")
        if s.flavor:
            click.echo(f"      \"{s.flavor}\"")


@game.command("start-survey")
@click.option("--state", "state_path", required=True, type=click.Path(exists=True))
@click.option("--survey", "survey_id", required=True, help="Survey program ID to activate.")
@click.option("--out", default=None, help="Output path for updated state.")
def game_start_survey(state_path: str, survey_id: str, out: str | None) -> None:
    """Mark a survey program as the active campaign."""
    from universe.game.models import ResearchState
    from universe.game.surveys import start_survey

    state = ResearchState.model_validate_json(Path(state_path).read_text())
    new_state, message = start_survey(state, survey_id)
    click.echo(message)

    out_path = Path(out) if out else Path(state_path)
    out_path.write_text(new_state.model_dump_json(indent=2), encoding="utf-8")
    click.echo(f"State saved: {out_path}")


@game.command("claim-survey")
@click.option("--state", "state_path", required=True, type=click.Path(exists=True))
@click.option("--survey", "survey_id", required=True, help="Survey program ID to claim.")
@click.option("--out", default=None, help="Output path for updated state.")
def game_claim_survey(state_path: str, survey_id: str, out: str | None) -> None:
    """Idempotently claim a completed survey's reward."""
    from universe.game.models import ResearchState
    from universe.game.surveys import claim_survey_reward

    state = ResearchState.model_validate_json(Path(state_path).read_text())
    new_state, message = claim_survey_reward(state, survey_id)
    click.echo(message)

    out_path = Path(out) if out else Path(state_path)
    out_path.write_text(new_state.model_dump_json(indent=2), encoding="utf-8")
    click.echo(f"State saved: {out_path}")


@game.command("milestones")
@click.option("--state", "state_path", required=True, type=click.Path(exists=True))
def game_milestones(state_path: str) -> None:
    """List milestones with achievement status."""
    from universe.game.milestones import _all_milestones, effective_milestone_reward
    from universe.game.models import ResearchState

    state = ResearchState.model_validate_json(Path(state_path).read_text())
    click.echo(f"=== Milestones ({state.research_entity.name}) ===")

    achieved_ids = {r.milestone_id for r in state.milestones.values() if r.achieved}
    for m in _all_milestones():
        spec = " [SPECULATIVE]" if m.speculative else ""
        marker = "✓" if m.id in achieved_ids else " "
        eff = effective_milestone_reward(m, state)
        rp_txt = f"+{eff} RP" if eff == m.reward_research_points else f"+{eff} RP (base {m.reward_research_points})"
        click.echo(f"  [{marker}] {m.name}{spec}  ({rp_txt})")
        click.echo(f"        id={m.id}  {m.description}")


@game.command("claim-milestones")
@click.option("--state", "state_path", required=True, type=click.Path(exists=True))
@click.option("--out", default=None, help="Output path for updated state.")
def game_claim_milestones(state_path: str, out: str | None) -> None:
    """Re-evaluate milestones and credit any newly-earned rewards (idempotent)."""
    from universe.game.milestones import claim_milestone_rewards
    from universe.game.models import ResearchState

    state = ResearchState.model_validate_json(Path(state_path).read_text())
    new_state, achieved = claim_milestone_rewards(state)
    if not achieved:
        click.echo("No newly achieved milestones.")
    else:
        total = sum(a.research_points for a in achieved)
        for a in achieved:
            m = a.milestone
            spec = " [SPECULATIVE]" if m.speculative else ""
            click.echo(f"  ✓ {m.name}{spec} — +{a.research_points} RP")
        click.echo(f"Total RP awarded: +{total} (now {new_state.research_points})")

    out_path = Path(out) if out else Path(state_path)
    out_path.write_text(new_state.model_dump_json(indent=2), encoding="utf-8")
    click.echo(f"State saved: {out_path}")


@game.command("export-godot-data")
@click.option(
    "--out",
    default="frontends/godot/data",
    help="Output directory for Godot frontend data bundle.",
)
def game_export_godot_data(out: str) -> None:
    """Export tech tree, surveys, milestones, and discovery requirements as JSON.

    These files are consumed by the Godot frontend (see frontends/godot/).
    Regenerate after any change to the Python game definitions.
    """
    from universe.game.discovery import get_discovery_requirements
    from universe.game.entity import ENTITY_TYPE_LABELS, RANDOM_ENTITY_NAMES, get_all_entity_modifiers
    from universe.game.milestones import get_default_milestones
    from universe.game.models import SignalType
    from universe.game.scenes import catalog_for_export
    from universe.game.surveys import get_default_survey_programs
    from universe.game.tech_tree import get_default_tech_tree

    out_dir = Path(out)
    out_dir.mkdir(parents=True, exist_ok=True)

    bundle = {
        "tech_tree.json": [t.model_dump(mode="json") for t in get_default_tech_tree()],
        "surveys.json": [s.model_dump(mode="json") for s in get_default_survey_programs()],
        "milestones.json": [m.model_dump(mode="json") for m in get_default_milestones()],
        "discovery_requirements.json": [
            r.model_dump(mode="json") for r in get_discovery_requirements()
        ],
        "signal_types.json": [s.value for s in SignalType],
        "entity_types.json": ENTITY_TYPE_LABELS,
        "random_entity_names.json": RANDOM_ENTITY_NAMES,
        "entity_modifiers.json": [m.model_dump(mode="json") for m in get_all_entity_modifiers()],
        "scene_catalog.json": catalog_for_export(),
    }
    manifest = {"files": list(bundle.keys()), "schema_version": "0.3.0"}
    bundle["manifest.json"] = manifest

    written: list[Path] = []
    for filename, payload in bundle.items():
        path = out_dir / filename
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        written.append(path)

    click.echo(f"Godot data bundle written to {out_dir}")
    for p in written:
        click.echo(f"  {p.name} ({p.stat().st_size} bytes)")


@game.command("export-unreal-data")
@click.option(
    "--scene",
    "scene_path",
    required=True,
    type=click.Path(exists=True),
    help="Canonical scene.json to transform.",
)
@click.option(
    "--out",
    default="frontends/unreal/Data",
    help="Output directory for Unreal convenience bundle.",
)
def game_export_unreal_data(scene_path: str, out: str) -> None:
    """Export Unreal-friendly JSON (scene_unreal.json, material hints, manifest).

    Canonical contract remains scene.json; this bundle adds normalized render
    coordinates and material profiles for the Unreal prototype importer.
    """
    from universe.export.unreal_data import export_unreal_data

    scene_data = json.loads(Path(scene_path).read_text(encoding="utf-8"))
    scene_data.pop("_units", None)
    scene = SceneRegion.model_validate(scene_data)
    paths = export_unreal_data(scene, out)
    click.echo(f"Unreal data bundle written to {out}")
    for name, path in sorted(paths.items()):
        click.echo(f"  {name} ({path.stat().st_size} bytes)")


@game.command("export-ui")
@click.option("--scene", "scene_path", required=True, type=click.Path(exists=True), help="scene.json to embed.")
@click.option("--state", "state_path", default=None, type=click.Path(exists=True), help="Game state JSON (uses default if omitted).")
@click.option("--out", default="data/generated/telescope-ui.html", help="Output HTML path.")
def game_export_ui(scene_path: str, state_path: str | None, out: str) -> None:
    """Export a playable telescope UI as a static HTML file."""
    from universe.game.models import ResearchState
    from universe.game.telescope_ui import export_telescope_ui

    scene_data = json.loads(Path(scene_path).read_text())
    scene_data.pop("_units", None)
    scene = SceneRegion.model_validate(scene_data)

    state = None
    if state_path:
        state = ResearchState.model_validate_json(Path(state_path).read_text())

    result = export_telescope_ui(scene, state=state, out_path=out)
    click.echo(f"Telescope UI written to {result}")
    click.echo(f"  Open in browser: open {result}")


@game.command("report")
@click.option("--scene", "scene_path", required=True, type=click.Path(exists=True))
@click.option("--state", "state_path", required=True, type=click.Path(exists=True))
@click.option("--out", default="data/generated/game-report.md", help="Output path for report.")
def game_report(scene_path: str, state_path: str, out: str) -> None:
    """Generate a Markdown discovery report."""
    from universe.game.discovery import observable_objects
    from universe.game.entity import get_entity_modifier
    from universe.game.models import ResearchState
    from universe.game.surveys import effective_survey_reward
    from universe.game.tech_tree import (
        available_upgrades,
        effective_tier_research_cost,
        get_tier_by_id,
    )

    scene_data = json.loads(Path(scene_path).read_text())
    scene_data.pop("_units", None)
    scene = SceneRegion.model_validate(scene_data)
    state = ResearchState.model_validate_json(Path(state_path).read_text())

    active = get_tier_by_id(state.active_telescope_tier)
    active_name = active.name if active else state.active_telescope_tier
    entity = state.research_entity
    mod = get_entity_modifier(entity.entity_type)

    lines = [
        f"# {entity.name} — Discovery Report",
        "",
    ]
    if entity.motto:
        lines.append(f"*\"{entity.motto}\"*  ")
    lines += [
        f"**Entity Type:** {entity.entity_type}  ",
        f"**Scene:** {scene.name}  ",
        f"**Telescope:** {active_name}  ",
        f"**Research Points:** {state.research_points}  ",
        f"**Discoveries:** {len(state.discoveries)} total, {state.completed_discoveries} confirmed  ",
        "",
        "## Research Entity Background",
        "",
        f"- **Modifier:** {mod.name}",
        f"- **Description:** {mod.description}",
    ]
    if mod.notes:
        for n in mod.notes:
            lines.append(f"- *{n}*")
    lines.append("")

    # Existing discoveries
    if state.discoveries:
        lines += ["## Discovered Objects", ""]
        for d in sorted(state.discoveries.values(), key=lambda d: -d.confidence):
            label = _confidence_label_md(d.confidence)
            lines.append(f"- **{d.object_id}** ({d.object_type}) — {label} ({d.confidence:.0%})")
        lines.append("")

    # New observables
    results = observable_objects(scene, state)
    if results:
        lines += ["## New Observations Available", ""]
        for r in results:
            lines.append(f"- {r.message}")
        lines.append("")

    # Undetectable categories
    detected_types = {d.object_type for d in state.discoveries.values()}
    scene_types = {o.type.value for o in scene.objects}
    missing = scene_types - detected_types
    if missing:
        lines += ["## Undetected Categories", ""]
        for t in sorted(missing):
            lines.append(f"- {t}")
        lines.append("")

    # Upgrades
    ups = available_upgrades(state)
    if ups:
        lines += ["## Available Upgrades", ""]
        for u in ups:
            spec = " ⚠ speculative" if u.speculative else ""
            eff = effective_tier_research_cost(u, state)
            cost_txt = f"{eff} RP" if eff == u.research_cost else f"{eff} RP (base {u.research_cost})"
            lines.append(f"- **{u.name}** ({cost_txt}) — {u.description[:80]}{spec}")
        lines.append("")

    # Surveys
    from universe.game.surveys import _all_programs, survey_status

    survey_lines: list[str] = []
    for s in _all_programs():
        status = survey_status(state, s)
        prog = state.survey_progress.get(s.id)
        done = prog.discoveries_completed if prog else 0
        spec = " ⚠ speculative" if s.speculative else ""
        rew = effective_survey_reward(s, state)
        rew_s = str(rew) if rew == s.reward_research_points else f"{rew} (base {s.reward_research_points})"
        if status.value == "completed":
            survey_lines.append(
                f"- ✅ **{s.name}**{spec} — {done}/{s.completion_goal}, +{rew_s} RP"
            )
        elif status.value == "active":
            survey_lines.append(
                f"- ▶ **{s.name}**{spec} — {done}/{s.completion_goal} (active)"
            )
        elif status.value == "available":
            survey_lines.append(
                f"- · {s.name}{spec} — available, goal {s.completion_goal}"
            )
    if survey_lines:
        lines += ["## Survey Programs", ""] + survey_lines + [""]

    # Milestones
    from universe.game.milestones import _all_milestones

    achieved_ids = {r.milestone_id for r in state.milestones.values() if r.achieved}
    achieved_ms = [m for m in _all_milestones() if m.id in achieved_ids]
    if achieved_ms:
        lines += ["## Achieved Milestones", ""]
        for m in achieved_ms:
            spec = " ⚠ speculative" if m.speculative else ""
            lines.append(f"- **{m.name}**{spec} — {m.description}")
        lines.append("")

    from universe.game.guidance import get_guidance_hints

    hints = get_guidance_hints(scene, state)
    if hints:
        lines += ["## Guidance", ""]
        for h in hints:
            lines.append(f"- **{h.title}** ({h.severity.value}): {h.message}")
            if h.suggested_action:
                lines.append(f"  - Action: `{h.suggested_action}`")
        lines.append("")

    # Suggestions
    lines += ["## Suggested Next Steps", ""]
    if ups:
        cheapest = min(ups, key=lambda u: effective_tier_research_cost(u, state))
        need = effective_tier_research_cost(cheapest, state)
        if state.research_points >= need:
            lines.append(f"- You can afford **{cheapest.name}** — upgrade to unlock new signals.")
        else:
            lines.append(
                f"- Earn {need - state.research_points} more RP to unlock "
                f"**{cheapest.name}** (effective cost {need} RP)."
            )
    if missing:
        lines.append(f"- {len(missing)} object type(s) remain undetected in this scene.")
    lines.append("")

    out_path = Path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")
    click.echo(f"Report written to {out_path}")


@game.command("playtest")
@click.option("--scenario", required=True, help="Playtest scenario id (e.g. solar_tutorial_basic).")
@click.option("--entity-type", "entity_type", required=True, help="Research entity type.")
@click.option("--seed", default="local-sky", help="Deterministic seed for scene generation.")
@click.option("--max-turns", default=None, type=int, help="Override scenario max turns.")
@click.option("--out", required=True, type=click.Path(), help="Output path for run JSON.")
@click.option("--no-events", is_flag=True, help="Skip writing events.jsonl sidecar.")
def game_playtest(
    scenario: str,
    entity_type: str,
    seed: str,
    max_turns: int | None,
    out: str,
    no_events: bool,
) -> None:
    """Run one deterministic balance playtest."""
    from universe.game.playtest import get_scenario_by_id, run_playtest, write_playtest_run

    sc = get_scenario_by_id(scenario)
    if sc is None:
        click.echo(f"Unknown scenario: {scenario}", err=True)
        sys.exit(1)

    run = run_playtest(sc, entity_type=entity_type, seed=seed, max_turns=max_turns)
    paths = write_playtest_run(run, Path(out), write_events=not no_events)
    click.echo(f"Playtest run written: {paths['run']}")
    if "events" in paths:
        click.echo(f"  Events: {paths['events']}")
    click.echo(f"  Summary: {paths['summary']}")
    click.echo(f"  Turns: {run.summary.get('turns_played')}  RP: {run.summary.get('final_rp')}")


@game.command("playtest-matrix")
@click.option("--out", required=True, type=click.Path(), help="Output directory for matrix runs.")
@click.option(
    "--scenario",
    "scenario_ids",
    multiple=True,
    help="Scenario id(s) to run (default: all).",
)
@click.option(
    "--entity-type",
    "entity_types",
    multiple=True,
    help="Entity type(s) to run (default: all non-custom).",
)
@click.option("--seed", default="local-sky", help="Seed passed to scene generators.")
@click.option("--max-turns", default=None, type=int, help="Override max turns per run.")
@click.option(
    "--include-deep-field/--no-deep-field",
    default=True,
    help="Include deep-field scenarios (scene-001).",
)
def game_playtest_matrix(
    out: str,
    scenario_ids: tuple[str, ...],
    entity_types: tuple[str, ...],
    seed: str,
    max_turns: int | None,
    include_deep_field: bool,
) -> None:
    """Run playtest matrix across scenarios and entity types."""
    from universe.game.playtest import run_playtest_matrix

    result = run_playtest_matrix(
        Path(out),
        scenario_ids=list(scenario_ids) or None,
        entity_types=list(entity_types) or None,
        seed=seed,
        max_turns=max_turns,
        include_deep_field=include_deep_field,
    )
    click.echo(f"Matrix summary: {result['summary_path']}")
    click.echo(f"  Runs: {len(result['runs'])}")


@game.command("balance-report")
@click.option("--input", "input_path", required=True, type=click.Path(exists=True))
@click.option("--out", required=True, type=click.Path(), help="Output markdown report path.")
def game_balance_report(input_path: str, out: str) -> None:
    """Generate balance report from playtest run(s) or matrix directory."""
    from universe.game.playtest import write_balance_report

    report_path = write_balance_report(Path(input_path), Path(out))
    click.echo(f"Balance report written: {report_path}")


def _confidence_label_md(c: float) -> str:
    if c < 0.25:
        return "not detected"
    if c < 0.50:
        return "signal anomaly"
    if c < 0.75:
        return "candidate"
    if c < 0.95:
        return "confirmed"
    return "characterized"

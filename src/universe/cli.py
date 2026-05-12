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


@game.command("tech-tree")
def game_tech_tree() -> None:
    """Print the telescope tech tree."""
    from universe.game.tech_tree import get_default_tech_tree

    tree = get_default_tech_tree()
    for tier in tree:
        spec = " [SPECULATIVE]" if tier.speculative else ""
        click.echo(f"Tier {tier.tier_index}: {tier.name}{spec}")
        click.echo(f"  ID:            {tier.id}")
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
    from universe.game.entity import make_research_entity
    from universe.game.models import ResearchState

    entity = make_research_entity(
        name=name or "Unnamed Research Entity",
        entity_type=etype,
        motto=motto,
    )
    state = ResearchState(research_points=starting_rp, research_entity=entity)
    out_path = Path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(state.model_dump_json(indent=2), encoding="utf-8")
    click.echo(f"Game state initialized: {out_path}")
    click.echo(f"  Entity: {entity.name}")
    if entity.motto:
        click.echo(f"  Motto: \"{entity.motto}\"")
    click.echo(f"  Type: {entity.entity_type}")
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
    from universe.game.models import ResearchState

    scene_data = json.loads(Path(scene_path).read_text())
    scene_data.pop("_units", None)
    scene = SceneRegion.model_validate(scene_data)

    state = ResearchState.model_validate_json(Path(state_path).read_text())
    new_state, results = observe_scene(scene, state)

    entity_name = state.research_entity.name

    if not results:
        click.echo(f"{entity_name}: No new discoveries or upgrades in this observation.")
    else:
        click.echo(f"{entity_name} — observation results ({len(results)} objects):")
        for r in results:
            click.echo(f"  {r.message}")
        total_rp = sum(r.research_points_awarded for r in results)
        click.echo(f"Total RP earned: +{total_rp} (now {new_state.research_points})")

    out_path = Path(out) if out else Path(state_path)
    out_path.write_text(new_state.model_dump_json(indent=2), encoding="utf-8")
    click.echo(f"State saved: {out_path}")


@game.command("upgrade")
@click.option("--state", "state_path", required=True, type=click.Path(exists=True))
@click.option("--tier", required=True, help="Tier ID to unlock.")
@click.option("--out", default=None, help="Output path for updated state.")
def game_upgrade(state_path: str, tier: str, out: str | None) -> None:
    """Unlock a telescope tier."""
    from universe.game.models import ResearchState
    from universe.game.tech_tree import unlock_tier

    state = ResearchState.model_validate_json(Path(state_path).read_text())
    new_state, message = unlock_tier(state, tier)
    click.echo(message)

    out_path = Path(out) if out else Path(state_path)
    out_path.write_text(new_state.model_dump_json(indent=2), encoding="utf-8")
    click.echo(f"State saved: {out_path}")


@game.command("set-telescope")
@click.option("--state", "state_path", required=True, type=click.Path(exists=True))
@click.option("--tier", required=True, help="Tier ID to set as active.")
@click.option("--out", default=None, help="Output path for updated state.")
def game_set_telescope(state_path: str, tier: str, out: str | None) -> None:
    """Set the active telescope tier (must already be unlocked)."""
    from universe.game.models import ResearchState

    state = ResearchState.model_validate_json(Path(state_path).read_text())
    if tier not in state.unlocked_tiers:
        click.echo(f"Tier '{tier}' is not unlocked.", err=True)
        sys.exit(1)

    new_state = state.model_copy(update={"active_telescope_tier": tier})
    out_path = Path(out) if out else Path(state_path)
    out_path.write_text(new_state.model_dump_json(indent=2), encoding="utf-8")
    click.echo(f"Active telescope set to: {tier}")
    click.echo(f"State saved: {out_path}")


@game.command("status")
@click.option("--state", "state_path", required=True, type=click.Path(exists=True))
def game_status(state_path: str) -> None:
    """Print current game status."""
    from universe.game.models import ResearchState
    from universe.game.tech_tree import available_upgrades

    state = ResearchState.model_validate_json(Path(state_path).read_text())

    entity = state.research_entity
    click.echo(f"=== {entity.name} ===")
    if entity.motto:
        click.echo(f"  \"{entity.motto}\"")
    click.echo(f"  Type: {entity.entity_type}")
    click.echo(f"  Research Points: {state.research_points}")
    click.echo(f"  Active Telescope: {state.active_telescope_tier}")
    click.echo(f"  Unlocked Tiers: {', '.join(state.unlocked_tiers)}")
    click.echo(f"  Known Signals: {', '.join(state.known_signal_types)}")
    click.echo(f"  Discoveries: {len(state.discoveries)}")
    click.echo(f"  Confirmed (≥75%): {state.completed_discoveries}")

    ups = available_upgrades(state)
    if ups:
        click.echo("  Available Upgrades:")
        for u in ups:
            click.echo(f"    {u.id} — {u.name} ({u.research_cost} RP)")


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
    from universe.game.models import ResearchState
    from universe.game.tech_tree import available_upgrades, get_tier_by_id

    scene_data = json.loads(Path(scene_path).read_text())
    scene_data.pop("_units", None)
    scene = SceneRegion.model_validate(scene_data)
    state = ResearchState.model_validate_json(Path(state_path).read_text())

    active = get_tier_by_id(state.active_telescope_tier)
    active_name = active.name if active else state.active_telescope_tier
    entity = state.research_entity

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
    ]

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
            lines.append(f"- **{u.name}** ({u.research_cost} RP) — {u.description[:80]}{spec}")
        lines.append("")

    # Suggestions
    lines += ["## Suggested Next Steps", ""]
    if ups:
        cheapest = min(ups, key=lambda u: u.research_cost)
        if state.research_points >= cheapest.research_cost:
            lines.append(f"- You can afford **{cheapest.name}** — upgrade to unlock new signals.")
        else:
            lines.append(
                f"- Earn {cheapest.research_cost - state.research_points} more RP to unlock "
                f"**{cheapest.name}**."
            )
    if missing:
        lines.append(f"- {len(missing)} object type(s) remain undetected in this scene.")
    lines.append("")

    out_path = Path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")
    click.echo(f"Report written to {out_path}")


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

"""Tests for Research Entity model, helpers, and backward compatibility."""

import json
import tempfile
from pathlib import Path

from universe.game.entity import (
    DEFAULT_ENTITY_NAME,
    RANDOM_ENTITY_NAMES,
    ResearchEntity,
    generate_random_entity_name,
    make_research_entity,
    slugify_entity_name,
)
from universe.game.models import ResearchState
from universe.game.telescope_ui import export_telescope_ui
from universe.procedural.solar_system import generate_solar_system


class TestResearchEntity:
    def test_default_entity(self):
        e = ResearchEntity()
        assert e.name == DEFAULT_ENTITY_NAME
        assert e.entity_type == "custom"
        assert e.motto == ""

    def test_make_entity_with_name(self):
        e = make_research_entity("Hydrogen Ghost Institute")
        assert e.name == "Hydrogen Ghost Institute"
        assert e.id.startswith("hydrogen-ghost-institute-")
        assert e.created_at != ""

    def test_make_entity_with_all_fields(self):
        e = make_research_entity(
            "Test Lab",
            entity_type="university_lab",
            motto="We test things.",
        )
        assert e.name == "Test Lab"
        assert e.entity_type == "university_lab"
        assert e.motto == "We test things."

    def test_make_entity_empty_name_fallback(self):
        e = make_research_entity("")
        assert e.name == DEFAULT_ENTITY_NAME

    def test_make_entity_whitespace_name_fallback(self):
        e = make_research_entity("   ")
        assert e.name == DEFAULT_ENTITY_NAME

    def test_entity_serialization_roundtrip(self):
        e = make_research_entity("Roundtrip Lab", motto="Testing JSON.")
        data = e.model_dump_json()
        e2 = ResearchEntity.model_validate_json(data)
        assert e2.name == e.name
        assert e2.motto == e.motto
        assert e2.id == e.id

    def test_entity_type_accepted(self):
        for etype in ["backyard_observatory", "university_lab", "ai_research_bureau", "custom"]:
            e = make_research_entity("Test", entity_type=etype)
            assert e.entity_type == etype

    def test_motto_optional(self):
        e = make_research_entity("No Motto Lab")
        assert e.motto == ""
        e2 = make_research_entity("With Motto", motto="We observe.")
        assert e2.motto == "We observe."


class TestSlugify:
    def test_basic_slug(self):
        assert slugify_entity_name("Hydrogen Ghost Institute") == "hydrogen-ghost-institute"

    def test_special_chars(self):
        assert slugify_entity_name("The Bureau of Unreasonable Telescopes!!!") == "the-bureau-of-unreasonable-telescopes"

    def test_empty_string(self):
        assert slugify_entity_name("") == "unnamed"


class TestRandomName:
    def test_returns_string(self):
        name = generate_random_entity_name()
        assert isinstance(name, str)
        assert len(name) > 0

    def test_deterministic_with_seed(self):
        a = generate_random_entity_name(seed="test-seed")
        b = generate_random_entity_name(seed="test-seed")
        assert a == b

    def test_different_seeds(self):
        a = generate_random_entity_name(seed="alpha")
        b = generate_random_entity_name(seed="beta")
        assert a != b or len(RANDOM_ENTITY_NAMES) == 1

    def test_from_known_list(self):
        name = generate_random_entity_name(seed="check")
        assert name in RANDOM_ENTITY_NAMES


class TestBackwardCompatibility:
    def test_old_state_json_loads_with_default_entity(self):
        old_json = json.dumps({
            "research_points": 42,
            "unlocked_tiers": ["naked_eye"],
            "active_telescope_tier": "naked_eye",
            "known_signal_types": ["visible_light"],
            "discoveries": {},
        })
        state = ResearchState.model_validate_json(old_json)
        assert state.research_points == 42
        assert state.research_entity.name == DEFAULT_ENTITY_NAME
        assert state.research_entity.entity_type == "custom"

    def test_new_state_json_preserves_entity(self):
        entity = make_research_entity("Persistent Lab", motto="We endure.")
        state = ResearchState(research_points=10, research_entity=entity)
        raw = state.model_dump_json()
        loaded = ResearchState.model_validate_json(raw)
        assert loaded.research_entity.name == "Persistent Lab"
        assert loaded.research_entity.motto == "We endure."

    def test_state_with_entity_in_discoveries(self):
        entity = make_research_entity("Discovery Lab")
        state = ResearchState(research_entity=entity)
        assert state.discovered_object_ids == set()
        assert state.completed_discoveries == 0


class TestResearchStateEntity:
    def test_default_state_has_entity(self):
        state = ResearchState()
        assert state.research_entity is not None
        assert state.research_entity.name == DEFAULT_ENTITY_NAME

    def test_state_with_custom_entity(self):
        entity = make_research_entity("Custom Entity")
        state = ResearchState(research_entity=entity)
        assert state.research_entity.name == "Custom Entity"


class TestUIWithEntity:
    def test_exported_html_contains_entity_data(self):
        scene = generate_solar_system(seed="test-entity-ui")
        entity = make_research_entity("UI Test Lab", motto="Rendering.")
        state = ResearchState(research_entity=entity)
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "ui.html"
            export_telescope_ui(scene, state=state, out_path=out)
            content = out.read_text(encoding="utf-8")
            assert "UI Test Lab" in content
            assert "Rendering." in content

    def test_exported_html_has_naming_modal(self):
        scene = generate_solar_system(seed="test-modal")
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "ui.html"
            export_telescope_ui(scene, out_path=out)
            content = out.read_text(encoding="utf-8")
            assert "naming-modal" in content
            assert "nm-name" in content
            assert "nm-begin" in content
            assert "nm-random" in content

    def test_exported_html_has_random_names(self):
        scene = generate_solar_system(seed="test-random")
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "ui.html"
            export_telescope_ui(scene, out_path=out)
            content = out.read_text(encoding="utf-8")
            assert "RANDOM_NAMES" in content
            assert "Hydrogen Ghost Institute" in content

    def test_exported_html_has_entity_types(self):
        scene = generate_solar_system(seed="test-types")
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "ui.html"
            export_telescope_ui(scene, out_path=out)
            content = out.read_text(encoding="utf-8")
            assert "ENTITY_TYPES" in content
            assert "backyard_observatory" in content

    def test_exported_html_uses_safe_escaping(self):
        scene = generate_solar_system(seed="test-esc")
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "ui.html"
            export_telescope_ui(scene, out_path=out)
            content = out.read_text(encoding="utf-8")
            assert "function esc(" in content
            assert "textContent" in content

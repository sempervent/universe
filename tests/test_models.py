"""Tests for core data models."""

import json

from universe.models import (
    CosmicObject,
    CosmicWebNode,
    NodeClass,
    ObjectType,
    Relationship,
    SceneRegion,
    Vector3,
    VisualHints,
    VisualMode,
)


class TestVector3:
    def test_defaults(self):
        v = Vector3()
        assert v.x == 0.0 and v.y == 0.0 and v.z == 0.0

    def test_distance(self):
        a = Vector3(x=0, y=0, z=0)
        b = Vector3(x=3, y=4, z=0)
        assert abs(a.distance_to(b) - 5.0) < 1e-9


class TestCosmicWebNode:
    def test_roundtrip(self):
        node = CosmicWebNode(
            id="n1",
            position_mpc=Vector3(x=1, y=2, z=3),
            density=1.5,
            node_class=NodeClass.PROTOCLUSTER_CORE,
        )
        data = json.loads(node.model_dump_json())
        restored = CosmicWebNode.model_validate(data)
        assert restored.id == "n1"
        assert restored.node_class == NodeClass.PROTOCLUSTER_CORE


class TestCosmicObject:
    def test_relationships(self):
        obj = CosmicObject(
            id="q1",
            name="Quasar",
            type=ObjectType.QUASAR,
            position_mpc=Vector3(),
            relationships=[
                Relationship(target_id="bh1", relation="powered_by", description="test"),
            ],
        )
        assert len(obj.relationships) == 1
        assert obj.relationships[0].target_id == "bh1"

    def test_visual_hints(self):
        obj = CosmicObject(
            id="g1",
            name="Galaxy",
            type=ObjectType.GALAXY,
            position_mpc=Vector3(),
            visual=VisualHints(color="#ff0000", emissive=True, glow=True),
        )
        assert obj.visual.glow is True


class TestSceneRegion:
    def test_visual_modes_default(self):
        region = SceneRegion(
            id="test", name="Test", seed="s", redshift=3.0, size_mpc=80.0,
        )
        assert "beauty" in region.visual_modes
        assert len(region.visual_modes) == len(VisualMode)

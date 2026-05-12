"""Core data models for the universe scene graph.

All models are Pydantic v2 BaseModels with JSON-friendly serialization.
They form the engine-agnostic data contract — rendering frontends consume
the exported JSON without importing this module.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Primitives
# ---------------------------------------------------------------------------


class Vector3(BaseModel):
    """3D vector in comoving megaparsecs (cMpc) for positions."""

    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    def distance_to(self, other: Vector3) -> float:
        return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2 + (self.z - other.z) ** 2) ** 0.5


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class ObjectType(str, Enum):
    GALAXY = "galaxy"
    LYMAN_ALPHA_BLOB = "lyman_alpha_blob"
    QUASAR = "quasar"
    BLACK_HOLE = "black_hole"
    MAGNETAR = "magnetar"
    COSMIC_WEB_NODE = "cosmic_web_node"
    COSMIC_WEB_FILAMENT = "cosmic_web_filament"
    CMB_BACKGROUND = "cmb_background"
    VOID = "void"
    # Solar system / local objects
    STAR = "star"
    PLANET = "planet"
    MOON = "moon"
    ASTEROID = "asteroid"
    COMET = "comet"
    OBSERVATORY = "observatory"


class NodeClass(str, Enum):
    VOID_BOUNDARY = "void_boundary"
    FILAMENT_INTERSECTION = "filament_intersection"
    PROTOCLUSTER_CORE = "protocluster_core"
    CLUSTER_CORE = "cluster_core"


class VisualMode(str, Enum):
    BEAUTY = "beauty"
    SCIENCE = "science"
    LYMAN_ALPHA = "lyman_alpha"
    XRAY = "xray"
    RADIO = "radio"
    DENSITY = "density"
    CMB = "cmb"


# ---------------------------------------------------------------------------
# Visual hints (consumed by renderers, ignored by simulation)
# ---------------------------------------------------------------------------


class VisualHints(BaseModel):
    """Renderer-agnostic visual hints attached to each object."""

    color: str | None = None
    emissive: bool = False
    opacity: float = 1.0
    scale: float = 1.0
    glow: bool = False
    label: str | None = None
    extras: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Cosmic web primitives
# ---------------------------------------------------------------------------


class CosmicWebNode(BaseModel):
    id: str
    position_mpc: Vector3
    density: float = 1.0
    node_class: NodeClass = NodeClass.FILAMENT_INTERSECTION


class CosmicWebFilament(BaseModel):
    id: str
    start_node_id: str
    end_node_id: str
    control_points_mpc: list[Vector3] = Field(default_factory=list)
    density: float = 1.0
    radius_mpc: float = 0.5
    galaxy_count_hint: int = 0


# ---------------------------------------------------------------------------
# Cosmic objects
# ---------------------------------------------------------------------------


class Relationship(BaseModel):
    """Typed link between two objects."""

    target_id: str
    relation: str  # e.g. "hosts", "powers", "embedded_in", "connected_to"
    description: str = ""


class CosmicObject(BaseModel):
    id: str
    name: str
    type: ObjectType
    position_mpc: Vector3
    redshift: float = 0.0
    description: str = ""
    properties: dict[str, Any] = Field(default_factory=dict)
    visual: VisualHints = Field(default_factory=VisualHints)
    relationships: list[Relationship] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Scene region (top-level container)
# ---------------------------------------------------------------------------


class SceneMetadata(BaseModel):
    schema_version: str = "0.1.0"
    generator: str = "universe"
    description: str = ""
    scientific_caveats: list[str] = Field(default_factory=list)


class SceneRegion(BaseModel):
    id: str
    name: str
    seed: str
    redshift: float
    size_mpc: float
    objects: list[CosmicObject] = Field(default_factory=list)
    nodes: list[CosmicWebNode] = Field(default_factory=list)
    filaments: list[CosmicWebFilament] = Field(default_factory=list)
    metadata: SceneMetadata = Field(default_factory=SceneMetadata)
    visual_modes: list[str] = Field(
        default_factory=lambda: [m.value for m in VisualMode]
    )

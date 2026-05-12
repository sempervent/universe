# Scene JSON Schema Documentation

## Overview

`scene.json` is the primary interchange format produced by the `universe` generator. It is a single JSON object representing a `SceneRegion` — one navigable volume of the universe.

## Top-level fields

| Field | Type | Description |
|---|---|---|
| `id` | string | Unique scene identifier (e.g. `"scene-001"`) |
| `name` | string | Human-readable scene name |
| `seed` | string | Deterministic seed used for generation |
| `redshift` | float | Central redshift of the scene |
| `size_mpc` | float | Side length of the cubic region in comoving Mpc |
| `objects` | array | List of `CosmicObject` entries |
| `nodes` | array | List of `CosmicWebNode` entries |
| `filaments` | array | List of `CosmicWebFilament` entries |
| `metadata` | object | `SceneMetadata` with schema version, generator, caveats |
| `visual_modes` | array | List of supported visual mode strings |
| `_units` | object | Unit conventions (added at export time, not part of model) |

## Unit conventions

```json
{
  "position": "comoving Mpc (cMpc)",
  "size": "comoving kpc (ckpc) unless noted",
  "mass": "solar masses (M☉)",
  "luminosity": "erg/s or solar luminosities (L☉)",
  "redshift": "dimensionless z",
  "coordinate_system": "right-handed Cartesian"
}
```

## CosmicObject

```json
{
  "id": "qso-001",
  "name": "Lucerna",
  "type": "quasar",
  "position_mpc": {"x": 1.2, "y": -0.5, "z": 3.1},
  "redshift": 3.1,
  "description": "High-redshift quasar with relativistic jets.",
  "properties": {
    "bolometric_luminosity_erg_s": "4.2e47",
    "jet_opening_angle_deg": 15.3
  },
  "visual": {
    "color": "#ffffff",
    "emissive": true,
    "opacity": 1.0,
    "scale": 1.5,
    "glow": true,
    "label": "Lucerna (QSO)",
    "extras": {"jet_color": "#ff4400"}
  },
  "relationships": [
    {
      "target_id": "bh-001",
      "relation": "powered_by",
      "description": "Accretion onto supermassive black hole"
    }
  ]
}
```

### Object types

`galaxy`, `lyman_alpha_blob`, `quasar`, `black_hole`, `magnetar`, `cosmic_web_node`, `cosmic_web_filament`, `cmb_background`, `void`

## CosmicWebNode

```json
{
  "id": "node-000",
  "position_mpc": {"x": 0.5, "y": -1.2, "z": 0.3},
  "density": 2.1,
  "node_class": "protocluster_core"
}
```

### Node classes

`void_boundary`, `filament_intersection`, `protocluster_core`, `cluster_core`

## CosmicWebFilament

```json
{
  "id": "fil-003",
  "start_node_id": "node-000",
  "end_node_id": "node-005",
  "control_points_mpc": [
    {"x": 5.1, "y": 2.3, "z": -1.0},
    {"x": 10.2, "y": 4.1, "z": -0.5}
  ],
  "density": 1.3,
  "radius_mpc": 0.6,
  "galaxy_count_hint": 7
}
```

## Relationship

```json
{
  "target_id": "bh-001",
  "relation": "powered_by",
  "description": "Accretion onto supermassive black hole Tenebris"
}
```

### Relationship types used in Scene 001

| Relation | From | To | Meaning |
|---|---|---|---|
| `powered_by` | quasar | black_hole | Quasar accretion energy source |
| `powers` | black_hole | quasar | Reciprocal: BH powers the quasar |
| `embeds` | lyman_alpha_blob | galaxy | LAB contains embedded galaxy |
| `hosted_by` | magnetar | galaxy | Magnetar resides in host galaxy |

Relationships are directional. The quasar↔black hole pair uses reciprocal links
(`powered_by` / `powers`) so either object can be traversed to find the other.

## SceneMetadata

```json
{
  "schema_version": "0.1.0",
  "generator": "universe",
  "description": "A high-redshift protocluster scene...",
  "scientific_caveats": [
    "Positions use simplified random placement, not N-body simulation."
  ]
}
```

## VisualHints

Renderer-agnostic hints. Frontends may ignore or reinterpret any field.

```json
{
  "color": "#6688ff",
  "emissive": true,
  "opacity": 0.85,
  "scale": 0.7,
  "glow": false,
  "label": "Galaxy Name",
  "extras": {}
}
```

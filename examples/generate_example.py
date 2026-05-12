#!/usr/bin/env python3
"""Generate a small example scene for documentation and testing.

Usage:
    python examples/generate_example.py

Produces examples/scene_001_example/ with a minimal 5-galaxy scene.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from universe.procedural.region import generate_scene_001  # noqa: E402
from universe.units import UNIT_CONVENTIONS  # noqa: E402


def main() -> None:
    out_dir = Path(__file__).parent / "scene_001_example"
    out_dir.mkdir(exist_ok=True)

    scene = generate_scene_001(
        seed="example-small",
        num_nodes=4,
        num_galaxies=5,
    )

    scene_dict = json.loads(scene.model_dump_json())
    scene_dict["_units"] = UNIT_CONVENTIONS

    (out_dir / "scene.json").write_text(
        json.dumps(scene_dict, indent=2), encoding="utf-8"
    )

    print(f"Wrote {out_dir / 'scene.json'}")
    print(f"  {len(scene.objects)} objects, {len(scene.nodes)} nodes, {len(scene.filaments)} filaments")


if __name__ == "__main__":
    main()

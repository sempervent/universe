"""Procedural cosmic web graph generator.

Produces a set of CosmicWebNodes connected by CosmicWebFilaments.
The algorithm is intentionally simple: scatter nodes with density-biased
positioning, then connect nearby pairs with filaments using a proximity
threshold.  One node is promoted to protocluster_core; boundary nodes
near region edges become void_boundary.

This is *not* a cosmological N-body simulation.  It produces a plausible-
looking graph suitable for visualization scaffolding.
"""

from __future__ import annotations

import hashlib
import random
from typing import Sequence

from universe.models import (
    CosmicWebFilament,
    CosmicWebNode,
    NodeClass,
    Vector3,
)


def _seed_rng(seed: str, salt: str = "") -> random.Random:
    digest = hashlib.sha256(f"{seed}:{salt}".encode()).hexdigest()
    return random.Random(int(digest[:16], 16))


def generate_nodes(
    seed: str,
    count: int = 12,
    region_size: float = 80.0,
) -> list[CosmicWebNode]:
    """Generate cosmic web nodes within a cubic region."""
    rng = _seed_rng(seed, "nodes")
    half = region_size / 2.0
    nodes: list[CosmicWebNode] = []

    for i in range(count):
        pos = Vector3(
            x=rng.uniform(-half, half),
            y=rng.uniform(-half, half),
            z=rng.uniform(-half, half),
        )
        dist_from_center = (pos.x**2 + pos.y**2 + pos.z**2) ** 0.5
        density = max(0.1, 1.0 - (dist_from_center / half) + rng.gauss(0, 0.2))

        edge_threshold = half * 0.85
        if dist_from_center > edge_threshold:
            node_class = NodeClass.VOID_BOUNDARY
        elif i == 0:
            node_class = NodeClass.PROTOCLUSTER_CORE
        else:
            node_class = NodeClass.FILAMENT_INTERSECTION

        nodes.append(
            CosmicWebNode(
                id=f"node-{i:03d}",
                position_mpc=pos,
                density=round(density, 4),
                node_class=node_class,
            )
        )

    # Force node-000 toward center for protocluster core
    nodes[0].position_mpc = Vector3(
        x=rng.gauss(0, region_size * 0.05),
        y=rng.gauss(0, region_size * 0.05),
        z=rng.gauss(0, region_size * 0.05),
    )
    nodes[0].density = round(rng.uniform(1.5, 2.5), 4)

    return nodes


def generate_filaments(
    seed: str,
    nodes: Sequence[CosmicWebNode],
    max_distance_mpc: float = 35.0,
    min_filaments: int = 16,
) -> list[CosmicWebFilament]:
    """Connect nearby nodes with filaments.  Guarantees at least min_filaments."""
    rng = _seed_rng(seed, "filaments")

    edges: list[tuple[int, int, float]] = []
    for i, a in enumerate(nodes):
        for j, b in enumerate(nodes):
            if j <= i:
                continue
            dist = a.position_mpc.distance_to(b.position_mpc)
            if dist < max_distance_mpc:
                edges.append((i, j, dist))

    edges.sort(key=lambda e: e[2])

    # Ensure minimum count by relaxing threshold if needed
    if len(edges) < min_filaments:
        all_edges = []
        for i, a in enumerate(nodes):
            for j, b in enumerate(nodes):
                if j <= i:
                    continue
                dist = a.position_mpc.distance_to(b.position_mpc)
                all_edges.append((i, j, dist))
        all_edges.sort(key=lambda e: e[2])
        edges = all_edges[:min_filaments]

    filaments: list[CosmicWebFilament] = []
    for idx, (i, j, dist) in enumerate(edges):
        a, b = nodes[i], nodes[j]
        # Generate 1–3 control points along the filament with slight offsets
        n_ctrl = rng.randint(1, 3)
        controls = []
        for k in range(1, n_ctrl + 1):
            t = k / (n_ctrl + 1)
            controls.append(
                Vector3(
                    x=a.position_mpc.x + t * (b.position_mpc.x - a.position_mpc.x) + rng.gauss(0, 1.5),
                    y=a.position_mpc.y + t * (b.position_mpc.y - a.position_mpc.y) + rng.gauss(0, 1.5),
                    z=a.position_mpc.z + t * (b.position_mpc.z - a.position_mpc.z) + rng.gauss(0, 1.5),
                )
            )

        avg_density = (a.density + b.density) / 2.0
        filaments.append(
            CosmicWebFilament(
                id=f"fil-{idx:03d}",
                start_node_id=a.id,
                end_node_id=b.id,
                control_points_mpc=controls,
                density=round(avg_density, 4),
                radius_mpc=round(rng.uniform(0.2, 1.0), 3),
                galaxy_count_hint=rng.randint(2, 12),
            )
        )

    return filaments

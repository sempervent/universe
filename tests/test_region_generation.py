"""Tests for deterministic Scene 001 generation."""

from universe.models import NodeClass, ObjectType
from universe.procedural.region import generate_scene_001


SEED = "lyman-alpha-furnace"


class TestDeterminism:
    def test_same_seed_same_output(self):
        a = generate_scene_001(seed=SEED)
        b = generate_scene_001(seed=SEED)

        assert a.id == b.id
        assert a.name == b.name
        assert len(a.objects) == len(b.objects)
        assert len(a.nodes) == len(b.nodes)
        assert len(a.filaments) == len(b.filaments)

        for oa, ob in zip(a.objects, b.objects):
            assert oa.id == ob.id
            assert oa.position_mpc == ob.position_mpc

    def test_different_seed_different_output(self):
        a = generate_scene_001(seed=SEED)
        b = generate_scene_001(seed="different-seed")
        assert a.objects[0].position_mpc != b.objects[0].position_mpc


class TestObjectCounts:
    def test_has_lyman_alpha_blob(self):
        scene = generate_scene_001(seed=SEED)
        labs = [o for o in scene.objects if o.type == ObjectType.LYMAN_ALPHA_BLOB]
        assert len(labs) >= 1

    def test_has_quasar(self):
        scene = generate_scene_001(seed=SEED)
        quasars = [o for o in scene.objects if o.type == ObjectType.QUASAR]
        assert len(quasars) >= 1

    def test_has_black_hole(self):
        scene = generate_scene_001(seed=SEED)
        bhs = [o for o in scene.objects if o.type == ObjectType.BLACK_HOLE]
        assert len(bhs) >= 1

    def test_has_magnetar(self):
        scene = generate_scene_001(seed=SEED)
        mags = [o for o in scene.objects if o.type == ObjectType.MAGNETAR]
        assert len(mags) >= 1

    def test_has_galaxies(self):
        scene = generate_scene_001(seed=SEED)
        gals = [o for o in scene.objects if o.type == ObjectType.GALAXY]
        assert len(gals) >= 40

    def test_has_multiple_filaments(self):
        scene = generate_scene_001(seed=SEED)
        assert len(scene.filaments) >= 16

    def test_has_protocluster_core(self):
        scene = generate_scene_001(seed=SEED)
        cores = [n for n in scene.nodes if n.node_class == NodeClass.PROTOCLUSTER_CORE]
        assert len(cores) >= 1

    def test_has_voids(self):
        scene = generate_scene_001(seed=SEED)
        voids = [o for o in scene.objects if o.type == ObjectType.VOID]
        assert len(voids) >= 1

    def test_has_cmb(self):
        scene = generate_scene_001(seed=SEED)
        cmbs = [o for o in scene.objects if o.type == ObjectType.CMB_BACKGROUND]
        assert len(cmbs) >= 1


class TestDataIntegrity:
    def test_unique_object_ids(self):
        scene = generate_scene_001(seed=SEED)
        ids = [o.id for o in scene.objects]
        assert len(ids) == len(set(ids))

    def test_unique_node_ids(self):
        scene = generate_scene_001(seed=SEED)
        ids = [n.id for n in scene.nodes]
        assert len(ids) == len(set(ids))

    def test_filaments_reference_valid_nodes(self):
        scene = generate_scene_001(seed=SEED)
        node_ids = {n.id for n in scene.nodes}
        for fil in scene.filaments:
            assert fil.start_node_id in node_ids, f"Filament {fil.id} has invalid start_node_id"
            assert fil.end_node_id in node_ids, f"Filament {fil.id} has invalid end_node_id"

    def test_filaments_link_start_end_nodes(self):
        scene = generate_scene_001(seed=SEED)
        node_ids = {n.id for n in scene.nodes}
        for fil in scene.filaments:
            assert fil.start_node_id in node_ids
            assert fil.end_node_id in node_ids
            assert fil.start_node_id != fil.end_node_id


class TestRelationships:
    """Comprehensive relationship validation."""

    def test_quasar_links_to_black_hole(self):
        scene = generate_scene_001(seed=SEED)
        quasar = next(o for o in scene.objects if o.type == ObjectType.QUASAR)
        bh_ids = {o.id for o in scene.objects if o.type == ObjectType.BLACK_HOLE}
        powered_by = [r for r in quasar.relationships if r.relation == "powered_by"]
        assert len(powered_by) >= 1
        assert powered_by[0].target_id in bh_ids

    def test_black_hole_links_to_quasar(self):
        """BH should have a reciprocal 'powers' link back to the quasar."""
        scene = generate_scene_001(seed=SEED)
        bh = next(o for o in scene.objects if o.type == ObjectType.BLACK_HOLE)
        qso_ids = {o.id for o in scene.objects if o.type == ObjectType.QUASAR}
        powers = [r for r in bh.relationships if r.relation == "powers"]
        assert len(powers) >= 1
        assert powers[0].target_id in qso_ids

    def test_lab_embeds_galaxies(self):
        scene = generate_scene_001(seed=SEED)
        lab = next(o for o in scene.objects if o.type == ObjectType.LYMAN_ALPHA_BLOB)
        gal_ids = {o.id for o in scene.objects if o.type == ObjectType.GALAXY}
        embeds = [r for r in lab.relationships if r.relation == "embeds"]
        assert len(embeds) >= 1
        for rel in embeds:
            assert rel.target_id in gal_ids

    def test_magnetar_links_to_host_galaxy(self):
        scene = generate_scene_001(seed=SEED)
        mag = next(o for o in scene.objects if o.type == ObjectType.MAGNETAR)
        gal_ids = {o.id for o in scene.objects if o.type == ObjectType.GALAXY}
        hosted = [r for r in mag.relationships if r.relation == "hosted_by"]
        assert len(hosted) >= 1
        assert hosted[0].target_id in gal_ids

    def test_all_relationship_targets_resolve(self):
        """Every relationship target_id must point to an existing object or node."""
        scene = generate_scene_001(seed=SEED)
        all_ids = {o.id for o in scene.objects} | {n.id for n in scene.nodes}
        for obj in scene.objects:
            for rel in obj.relationships:
                assert rel.target_id in all_ids, (
                    f"Object {obj.id} has relationship to unknown target {rel.target_id}"
                )

    def test_no_self_referencing_relationships(self):
        scene = generate_scene_001(seed=SEED)
        for obj in scene.objects:
            for rel in obj.relationships:
                assert rel.target_id != obj.id, (
                    f"Object {obj.id} has self-referencing relationship"
                )

    def test_quasar_bh_reciprocal_pair(self):
        """Quasar→BH and BH→Quasar should form a reciprocal pair."""
        scene = generate_scene_001(seed=SEED)
        qso = next(o for o in scene.objects if o.type == ObjectType.QUASAR)
        bh = next(o for o in scene.objects if o.type == ObjectType.BLACK_HOLE)

        qso_to_bh = [r for r in qso.relationships if r.target_id == bh.id]
        bh_to_qso = [r for r in bh.relationships if r.target_id == qso.id]

        assert len(qso_to_bh) >= 1, "Quasar should link to black hole"
        assert len(bh_to_qso) >= 1, "Black hole should link back to quasar"

    def test_relationship_descriptions_non_empty(self):
        scene = generate_scene_001(seed=SEED)
        for obj in scene.objects:
            for rel in obj.relationships:
                assert rel.description, (
                    f"Relationship {obj.id}->{rel.target_id} has empty description"
                )

    def test_relationship_relations_non_empty(self):
        scene = generate_scene_001(seed=SEED)
        for obj in scene.objects:
            for rel in obj.relationships:
                assert rel.relation, (
                    f"Relationship {obj.id}->{rel.target_id} has empty relation type"
                )

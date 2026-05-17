"""Tests for the starter solar system scene."""

from universe.models import ObjectType
from universe.procedural.solar_system import generate_solar_system


class TestSolarSystemScene:
    def test_contains_sun(self):
        scene = generate_solar_system()
        suns = [o for o in scene.objects if o.type == ObjectType.STAR]
        assert len(suns) >= 1

    def test_contains_moon(self):
        scene = generate_solar_system()
        moons = [o for o in scene.objects if o.id == "moon"]
        assert len(moons) == 1

    def test_contains_planets(self):
        scene = generate_solar_system()
        planets = [o for o in scene.objects if o.type == ObjectType.PLANET]
        assert len(planets) >= 7  # Mercury through Neptune

    def test_contains_observatory(self):
        scene = generate_solar_system()
        obs = [o for o in scene.objects if o.type == ObjectType.OBSERVATORY]
        assert len(obs) >= 1

    def test_unique_object_ids(self):
        scene = generate_solar_system()
        ids = [o.id for o in scene.objects]
        assert len(ids) == len(set(ids))

    def test_objects_have_properties(self):
        scene = generate_solar_system()
        for obj in scene.objects:
            assert obj.name, f"Object {obj.id} missing name"
            assert obj.description, f"Object {obj.id} missing description"

    def test_planets_have_distance(self):
        scene = generate_solar_system()
        planets = [o for o in scene.objects if o.type == ObjectType.PLANET]
        for p in planets:
            assert "distance_au" in p.properties, f"Planet {p.id} missing distance_au"

    def test_redshift_is_zero(self):
        scene = generate_solar_system()
        assert scene.redshift == 0.0

    def test_scene_id(self):
        scene = generate_solar_system()
        assert scene.id == "solar-system"

    def test_contains_asteroid(self):
        scene = generate_solar_system()
        asteroids = [o for o in scene.objects if o.type == ObjectType.ASTEROID]
        assert len(asteroids) >= 1

    def test_contains_comet(self):
        scene = generate_solar_system()
        comets = [o for o in scene.objects if o.type == ObjectType.COMET]
        assert len(comets) >= 1

    def test_contains_galilean_moons(self):
        scene = generate_solar_system()
        jup_moons = [o for o in scene.objects if o.type == ObjectType.MOON and
                      o.properties.get("parent") == "Jupiter"]
        assert len(jup_moons) == 4

    def test_metadata_scene_class_solar_system(self):
        scene = generate_solar_system()
        assert scene.metadata.scene_class == "solar_system"
        assert scene.metadata.recommended_camera_target_object_id == "sun"

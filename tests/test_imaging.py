"""Imaging capture and composite."""

from universe.game.imaging import (
    available_cameras,
    capture_image,
    combine_images,
    get_default_camera_catalog,
)
from universe.game.models import ResearchState
from universe.game.tech_tree import unlock_tier


class TestImaging:
    def test_camera_catalog_valid(self):
        cats = get_default_camera_catalog()
        assert len(cats) >= 3
        ids = {c.id for c in cats}
        assert "naked_eye_memory" in ids

    def test_default_unlocked_camera(self):
        state = ResearchState()
        cams = available_cameras(state)
        assert any(c.id == "naked_eye_memory" for c in cams)

    def test_capture_visible_sun_day(self):
        state = ResearchState(research_points=100)
        state, img, msg = capture_image(
            "solar-system",
            state,
            "sun",
            "visible_light",
            "naked_eye_memory",
            object_name="Sun",
            object_type="star",
            confidence=0.5,
        )
        assert img is not None
        assert "Captured" in msg

    def test_daylight_blocks_galaxy_visible(self):
        state = ResearchState()
        state, img, msg = capture_image(
            "scene-001",
            state,
            "quasar-1",
            "visible_light",
            "naked_eye_memory",
            object_name="Q",
            object_type="galaxy",
            confidence=0.5,
        )
        assert img is None
        assert "Daylight" in msg or "blocked" in msg.lower()

    def test_composite_requires_two_signals(self):
        state = ResearchState(research_points=100)
        state, img1, _ = capture_image(
            "solar-system",
            state,
            "sun",
            "visible_light",
            "naked_eye_memory",
            object_name="Sun",
            object_type="star",
            confidence=0.6,
        )
        state, _ = unlock_tier(state, "ground_optical")
        state, _ = unlock_tier(state, "improved_ground")
        state, img2, _ = capture_image(
            "solar-system",
            state,
            "sun",
            "infrared",
            "infrared_sensor",
            object_name="Sun",
            object_type="star",
            confidence=0.7,
        )
        assert img1 and img2
        state, comp, msg = combine_images(state, [img1.id, img2.id])
        assert comp is not None
        assert comp.image_type.value == "composite"
        assert len(comp.signal_modes) >= 2

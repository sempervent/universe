"""Camera catalog and captured image archive (metadata-first)."""

from __future__ import annotations

import uuid
from enum import Enum

from pydantic import BaseModel, Field

from universe.game.models import ResearchState
from universe.game.observatory_time import get_observatory_time, sky_brightness_factor
from universe.game.tech_tree import all_signal_types_for_state, get_tier_by_id


class CameraType(str, Enum):
    VISUAL_CAMERA = "visual_camera"
    INFRARED_SENSOR = "infrared_sensor"
    RADIO_ARRAY = "radio_array"
    MICROWAVE_DETECTOR = "microwave_detector"
    XRAY_DETECTOR = "xray_detector"
    GAMMA_DETECTOR = "gamma_detector"
    GRAVITATIONAL_WAVE_DETECTOR = "gravitational_wave_detector"
    NEUTRINO_DETECTOR = "neutrino_detector"
    WEAK_LENSING_MAPPER = "weak_lensing_mapper"
    DARK_MATTER_MAPPER = "dark_matter_mapper"
    NOW_SCOPE_IMAGER = "now_scope_imager"


class ImageType(str, Enum):
    SINGLE_SIGNAL = "single_signal"
    COMPOSITE = "composite"
    INFERENCE_MAP = "inference_map"
    SPECULATIVE = "speculative"


class CameraDefinition(BaseModel):
    id: str
    name: str
    camera_type: CameraType
    required_tier_id: str
    signal_types: list[str]
    resolution_rating: float = 1.0
    sensitivity_rating: float = 1.0
    field_of_view_deg: float = 5.0
    noise_level: float = 0.2
    description: str = ""
    research_cost: int = 0
    upgrade_level: int = 0
    speculative: bool = False


class CapturedImage(BaseModel):
    id: str
    object_id: str | None = None
    scene_id: str = ""
    object_name: str = ""
    captured_turn: int = 0
    local_day_fraction: float = 0.5
    signal_modes: list[str] = Field(default_factory=list)
    camera_ids: list[str] = Field(default_factory=list)
    image_type: ImageType = ImageType.SINGLE_SIGNAL
    quality_score: float = 0.0
    confidence_at_capture: float = 0.0
    title: str = ""
    description: str = ""
    data_uri: str | None = None
    thumbnail_path: str | None = None
    metadata: dict = Field(default_factory=dict)


def get_default_camera_catalog() -> list[CameraDefinition]:
    return [
        CameraDefinition(
            id="naked_eye_memory",
            name="Naked-Eye Sketch Memory",
            camera_type=CameraType.VISUAL_CAMERA,
            required_tier_id="naked_eye",
            signal_types=["visible_light"],
            resolution_rating=0.2,
            sensitivity_rating=0.15,
            field_of_view_deg=120.0,
            noise_level=0.5,
            description="Mental note / hand sketch — very low resolution.",
        ),
        CameraDefinition(
            id="basic_visual_camera",
            name="Basic Visual Camera",
            camera_type=CameraType.VISUAL_CAMERA,
            required_tier_id="ground_optical",
            signal_types=["visible_light"],
            resolution_rating=0.6,
            sensitivity_rating=0.4,
            field_of_view_deg=2.0,
            description="Ground optical imager for planets and bright targets.",
        ),
        CameraDefinition(
            id="infrared_sensor",
            name="Infrared Sensor",
            camera_type=CameraType.INFRARED_SENSOR,
            required_tier_id="improved_ground",
            signal_types=["infrared"],
            resolution_rating=0.7,
            sensitivity_rating=0.55,
            field_of_view_deg=1.5,
            description="Thermal / near-IR channel.",
        ),
        CameraDefinition(
            id="radio_array",
            name="Radio Interferometer Array",
            camera_type=CameraType.RADIO_ARRAY,
            required_tier_id="radio",
            signal_types=["radio"],
            resolution_rating=0.8,
            sensitivity_rating=0.7,
            field_of_view_deg=0.5,
            description="Radio synthesis imaging.",
        ),
        CameraDefinition(
            id="microwave_detector",
            name="Microwave Sky Mapper",
            camera_type=CameraType.MICROWAVE_DETECTOR,
            required_tier_id="radio",
            signal_types=["microwave"],
            resolution_rating=0.5,
            sensitivity_rating=0.8,
            field_of_view_deg=8.0,
            description="All-sky microwave / CMB channel.",
        ),
        CameraDefinition(
            id="xray_detector",
            name="X-ray Imager",
            camera_type=CameraType.XRAY_DETECTOR,
            required_tier_id="xray_gamma",
            signal_types=["xray"],
            resolution_rating=0.75,
            sensitivity_rating=0.65,
            description="High-energy compact sources.",
        ),
        CameraDefinition(
            id="weak_lensing_mapper",
            name="Weak-Lensing Mass Mapper",
            camera_type=CameraType.WEAK_LENSING_MAPPER,
            required_tier_id="dark_matter_mapper",
            signal_types=["weak_lensing"],
            resolution_rating=0.6,
            sensitivity_rating=0.5,
            field_of_view_deg=3.0,
            description="Inferred mass map — not a photograph.",
            speculative=False,
        ),
        CameraDefinition(
            id="now_scope_imager",
            name="Now-Scope Imager",
            camera_type=CameraType.NOW_SCOPE_IMAGER,
            required_tier_id="now_scope",
            signal_types=["speculative_now_signal"],
            resolution_rating=1.0,
            sensitivity_rating=1.0,
            speculative=True,
            description="Fictional causality-independent imager.",
        ),
    ]


def camera_catalog_by_id() -> dict[str, CameraDefinition]:
    return {c.id: c for c in get_default_camera_catalog()}


def default_unlocked_cameras() -> list[str]:
    return ["naked_eye_memory"]


def ensure_imaging_state(state: ResearchState) -> ResearchState:
    updates: dict = {}
    if not state.unlocked_camera_ids:
        updates["unlocked_camera_ids"] = default_unlocked_cameras()
    if updates:
        return state.model_copy(update=updates)
    return state


def cameras_unlocked_for_state(state: ResearchState) -> set[str]:
    catalog = camera_catalog_by_id()
    unlocked_tiers = set(state.unlocked_tiers)
    out = set(state.unlocked_camera_ids)
    for cam in catalog.values():
        if cam.required_tier_id in unlocked_tiers:
            out.add(cam.id)
    return out


def available_cameras(state: ResearchState) -> list[CameraDefinition]:
    catalog = camera_catalog_by_id()
    ids = cameras_unlocked_for_state(state)
    return [catalog[cid] for cid in sorted(ids) if cid in catalog]


def _signal_allowed(state: ResearchState, signal: str) -> bool:
    return signal in all_signal_types_for_state(state)


def _daylight_penalty(
    obj_type: str,
    signal: str,
    state: ResearchState,
    object_id: str = "",
) -> tuple[float, str | None]:
    if signal != "visible_light" and signal not in ("infrared", "ultraviolet"):
        return 1.0, None
    bright = sky_brightness_factor(state)
    if bright < 0.35:
        return 1.0, None
    if object_id == "sun":
        return 0.85, "Solar daylight capture — use appropriate filtering."
    if obj_type in ("galaxy", "quasar", "lyman_alpha_blob", "cosmic_web_node"):
        return 0.05, "Daylight blocks faint optical/deep-sky capture."
    if obj_type == "star" and bright > 0.5:
        return 0.15, "Stars washed out in daylight (visible light)."
    return max(0.25, 1.0 - bright * 0.7), "Daylight reduces optical capture quality."


def capture_image(
    scene_id: str,
    state: ResearchState,
    object_id: str,
    signal_mode: str,
    camera_id: str,
    *,
    object_name: str = "",
    object_type: str = "",
    confidence: float = 0.0,
) -> tuple[ResearchState, CapturedImage | None, str]:
    state = ensure_imaging_state(state)
    catalog = camera_catalog_by_id()
    if camera_id not in catalog:
        return state, None, f"Unknown camera: {camera_id}"
    cam = catalog[camera_id]
    if camera_id not in cameras_unlocked_for_state(state):
        return state, None, f"Camera '{cam.name}' not unlocked (requires tier {cam.required_tier_id})."
    if not _signal_allowed(state, signal_mode):
        return state, None, f"Signal '{signal_mode}' not unlocked."
    if signal_mode not in cam.signal_types:
        return state, None, f"Camera '{cam.name}' does not support signal '{signal_mode}'."

    penalty, block_msg = _daylight_penalty(object_type, signal_mode, state, object_id)
    if penalty < 0.08 and block_msg:
        return state, None, block_msg

    ot = get_observatory_time(state)
    quality = clamp01(
        0.35 * cam.resolution_rating
        + 0.35 * cam.sensitivity_rating
        + 0.2 * confidence
        + 0.1 * (1.0 - cam.noise_level)
    )
    quality *= penalty
    tier = get_tier_by_id(state.active_telescope_tier)
    if tier:
        quality *= clamp01(0.5 + tier.sensitivity)

    img_id = f"img-{uuid.uuid4().hex[:10]}"
    title = f"{object_name or object_id} · {signal_mode}"
    img = CapturedImage(
        id=img_id,
        object_id=object_id,
        scene_id=scene_id,
        object_name=object_name or object_id,
        captured_turn=state.turn,
        local_day_fraction=ot.local_day_fraction,
        signal_modes=[signal_mode],
        camera_ids=[camera_id],
        image_type=ImageType.SPECULATIVE if cam.speculative else ImageType.SINGLE_SIGNAL,
        quality_score=round(quality, 3),
        confidence_at_capture=confidence,
        title=title,
        description=f"Captured with {cam.name} at day fraction {ot.local_day_fraction:.2f}.",
        metadata={"camera_type": cam.camera_type.value, "blocked_reason": block_msg or ""},
    )
    images = dict(state.captured_images)
    images[img_id] = img.model_dump()
    unlocked = list(state.unlocked_camera_ids)
    if camera_id not in unlocked:
        unlocked.append(camera_id)
    new_state = state.model_copy(
        update={"captured_images": images, "unlocked_camera_ids": unlocked}
    )
    return new_state, img, f"Captured '{title}' (quality {quality:.0%})."


def combine_images(
    state: ResearchState, image_ids: list[str]
) -> tuple[ResearchState, CapturedImage | None, str]:
    if len(image_ids) < 2:
        return state, None, "Need at least two images to combine."
    raw_images = state.captured_images
    refs: list[CapturedImage] = []
    for iid in image_ids:
        if iid not in raw_images:
            return state, None, f"Unknown image: {iid}"
        refs.append(CapturedImage.model_validate(raw_images[iid]))

    obj_ids = {r.object_id for r in refs if r.object_id}
    if len(obj_ids) > 1:
        return state, None, "Composite requires images of the same object."

    signals: set[str] = set()
    cameras: set[str] = set()
    for r in refs:
        signals.update(r.signal_modes)
        cameras.update(r.camera_ids)
    if len(signals) < 2:
        return state, None, "Composite requires different signal modes."

    quality = clamp01(sum(r.quality_score for r in refs) / len(refs) + 0.15 * len(signals))
    obj_id = next(iter(obj_ids)) if obj_ids else None
    obj_name = refs[0].object_name
    img_id = f"img-{uuid.uuid4().hex[:10]}"
    img = CapturedImage(
        id=img_id,
        object_id=obj_id,
        scene_id=refs[0].scene_id,
        object_name=obj_name,
        captured_turn=state.turn,
        local_day_fraction=refs[0].local_day_fraction,
        signal_modes=sorted(signals),
        camera_ids=sorted(cameras),
        image_type=ImageType.COMPOSITE,
        quality_score=round(quality, 3),
        confidence_at_capture=max(r.confidence_at_capture for r in refs),
        title=f"{obj_name} · composite ({len(signals)} channels)",
        description="Multi-instrument composite from " + ", ".join(image_ids),
        metadata={"source_image_ids": image_ids},
    )
    all_images = dict(state.captured_images)
    all_images[img_id] = img.model_dump()
    return state.model_copy(update={"captured_images": all_images}), img, "Composite created."


def images_for_object(state: ResearchState, object_id: str) -> list[CapturedImage]:
    out: list[CapturedImage] = []
    for raw in state.captured_images.values():
        img = CapturedImage.model_validate(raw)
        if img.object_id == object_id:
            out.append(img)
    return out


def image_archive_summary(state: ResearchState) -> dict:
    imgs = [CapturedImage.model_validate(v) for v in state.captured_images.values()]
    return {
        "count": len(imgs),
        "objects": len({i.object_id for i in imgs if i.object_id}),
        "composite_count": sum(1 for i in imgs if i.image_type == ImageType.COMPOSITE),
    }


def clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


def auto_composite_for_object(state: ResearchState, object_id: str) -> tuple[ResearchState, CapturedImage | None, str]:
    singles = [
        CapturedImage.model_validate(v)
        for v in state.captured_images.values()
        if CapturedImage.model_validate(v).object_id == object_id
        and CapturedImage.model_validate(v).image_type == ImageType.SINGLE_SIGNAL
    ]
    by_signal: dict[str, str] = {}
    for img in singles:
        for sig in img.signal_modes:
            if sig not in by_signal:
                by_signal[sig] = img.id
    if len(by_signal) < 2:
        return state, None, "Need single-signal captures in two different modes."
    return combine_images(state, list(by_signal.values())[:4])

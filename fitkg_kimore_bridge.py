#!/usr/bin/env python3
"""Bridge PG-XFormer KIMORE classes → FitKG muscles + COCO-17 pose demos."""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

OUT = Path(__file__).resolve().parent / "outputs" / "fitkg_kg"
MAP_PATH = OUT / "muscle_region_map.json"
DEMOS_PATH = OUT / "kimore_pose_demos.json"

KIMORE_CLASSES: Tuple[str, ...] = (
    "unilateral_stance",
    "sit_to_stand",
    "pelvis_tilt",
    "squat",
    "trunk_flexion",
)

# COCO-17 edges (same as pgxformer_colab_standalone.py)
COCO_EDGES: Tuple[Tuple[int, int], ...] = (
    (0, 1), (0, 2), (1, 3), (2, 4), (5, 6), (5, 7), (7, 9), (6, 8), (8, 10),
    (5, 11), (6, 12), (11, 13), (13, 15), (12, 14), (14, 16), (11, 12),
)

# Clinical presets: tight muscle highlights + FitKG Chinese queries
KIMORE_PRESETS: Dict[str, Dict[str, Any]] = {
    "unilateral_stance": {
        "label_en": "Unilateral stance",
        "label_zh": "单腿站立",
        "fitkg_query": "单腿站立 平衡",
        "regions": ["glutes", "thigh_l", "thigh_r", "calf_l", "calf_r", "abs", "hip_flexor"],
        "primary_muscles_en": ["gluteus medius", "quadriceps", "gastrocnemius", "core stabilizers"],
        "primary_muscles_zh": ["臀中肌", "股四头肌", "腓肠肌", "核心稳定肌"],
    },
    "sit_to_stand": {
        "label_en": "Sit-to-stand",
        "label_zh": "坐站转移",
        "fitkg_query": "坐站 起立 深蹲",
        "regions": ["thigh_l", "thigh_r", "glutes", "abs"],
        "primary_muscles_en": ["quadriceps", "gluteus maximus", "rectus abdominis"],
        "primary_muscles_zh": ["股四头肌", "臀大肌", "腹直肌"],
    },
    "pelvis_tilt": {
        "label_en": "Pelvis tilt",
        "label_zh": "骨盆倾斜",
        "fitkg_query": "骨盆 倾斜 核心",
        "regions": ["abs", "glutes", "lower_back", "hip_flexor"],
        "primary_muscles_en": ["rectus abdominis", "gluteus maximus", "erector spinae", "hip flexors"],
        "primary_muscles_zh": ["腹直肌", "臀大肌", "竖脊肌", "髋屈肌"],
    },
    "squat": {
        "label_en": "Squat",
        "label_zh": "深蹲",
        "fitkg_query": "深蹲",
        "regions": ["thigh_l", "thigh_r", "glutes", "abs", "lower_back"],
        "primary_muscles_en": ["quadriceps", "gluteus maximus", "erector spinae", "core"],
        "primary_muscles_zh": ["股四头肌", "臀大肌", "竖脊肌", "核心"],
    },
    "trunk_flexion": {
        "label_en": "Trunk flexion",
        "label_zh": "躯干屈曲",
        "fitkg_query": "躯干 屈曲 仰卧起坐",
        "regions": ["abs", "hip_flexor", "lower_back"],
        "primary_muscles_en": ["rectus abdominis", "hip flexors", "erector spinae"],
        "primary_muscles_zh": ["腹直肌", "髋屈肌", "竖脊肌"],
    },
}


def _standing_pose() -> np.ndarray:
    """Normalized COCO-17 (17, 2), pelvis-centred, y-up positive."""
    kp = np.array([
        [0.0, 0.95], [-0.08, 0.98], [0.08, 0.98], [-0.12, 0.92], [0.12, 0.92],
        [-0.22, 0.72], [0.22, 0.72], [-0.30, 0.48], [0.30, 0.48],
        [-0.34, 0.22], [0.34, 0.22],
        [-0.14, 0.0], [0.14, 0.0], [-0.16, -0.42], [0.16, -0.42],
        [-0.16, -0.82], [0.16, -0.82],
    ], dtype=np.float32)
    return kp


def _lerp_pose(a: np.ndarray, b: np.ndarray, t: float) -> np.ndarray:
    return a * (1.0 - t) + b * t * 1.0


def _squat_pose(depth: float) -> np.ndarray:
    """depth 0=stand, 1=deep squat."""
    base = _standing_pose()
    pose = base.copy()
    drop = 0.55 * depth
    knee_bend = 0.35 * depth
    # hips drop
    pose[[11, 12], 1] -= drop
    # knees forward/down
    pose[[13, 14], 0] += 0.06 * depth
    pose[[13, 14], 1] -= drop * 0.55
    pose[[15, 16], 1] -= drop * 0.25
    # torso slight forward
    pose[[0, 5, 6], 0] += 0.04 * depth
    pose[[0, 5, 6], 1] -= drop * 0.15
    pose[[7, 8], 1] -= drop * 0.1
    pose[[9, 10], 0] += 0.08 * depth
    # arms forward for balance
    pose[[9, 10], 1] = 0.35 - 0.1 * depth
    return pose


def _sit_pose(seated: float) -> np.ndarray:
    """seated 0=stand, 1=full sit."""
    base = _standing_pose()
    pose = base.copy()
    hip_drop = 0.62 * seated
    pose[[11, 12], 1] -= hip_drop
    pose[[13, 14], 1] -= hip_drop * 0.35
    pose[[13, 14], 0] += 0.12 * seated
    pose[[15, 16], 1] -= hip_drop * 0.05
    pose[[0, 5, 6], 1] -= hip_drop * 0.55
    pose[[7, 8, 9, 10], 1] -= hip_drop * 0.45
    return pose


def _pelvis_tilt_pose(tilt: float) -> np.ndarray:
    pose = _standing_pose()
    # anterior tilt: hips back, lumbar arch
    pose[[11, 12], 0] += 0.06 * tilt
    pose[[11, 12], 1] += 0.04 * tilt
    pose[[0, 5, 6], 0] -= 0.05 * tilt
    pose[[0, 5, 6], 1] += 0.03 * tilt
    return pose


def _trunk_flex_pose(flex: float) -> np.ndarray:
    pose = _standing_pose()
    angle = flex * 0.55
    for idx in (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10):
        pose[idx, 1] -= angle * 0.9
        pose[idx, 0] += angle * 0.15
    return pose


def _unilateral_pose(phase: float) -> np.ndarray:
    pose = _standing_pose()
    # lift right leg (indices 12,14,16)
    lift = math.sin(phase * math.pi) * 0.55
    pose[12, 1] += lift * 0.35
    pose[14, 1] += lift
    pose[16, 1] += lift * 1.1
    pose[12, 0] += lift * 0.08
    # slight lean to left stance leg
    pose[11, 0] -= 0.03
    return pose


def generate_demo_sequence(class_id: str, frames: int = 16) -> List[List[List[float]]]:
    """Return list of frames, each frame is 17×2 normalised keypoints."""
    out: List[np.ndarray] = []
    for i in range(frames):
        t = i / max(frames - 1, 1)
        if class_id == "squat":
            # down then up
            phase = math.sin(t * math.pi)
            kp = _squat_pose(phase)
        elif class_id == "sit_to_stand":
            kp = _sit_pose(max(0.0, 1.0 - t * 1.2))
        elif class_id == "pelvis_tilt":
            kp = _pelvis_tilt_pose(math.sin(t * 2 * math.pi) * 0.5 + 0.5)
        elif class_id == "trunk_flexion":
            kp = _trunk_flex_pose(math.sin(t * math.pi))
        elif class_id == "unilateral_stance":
            kp = _unilateral_pose(t * 2)
        else:
            kp = _standing_pose()
        out.append(kp.tolist())
    return out


def ensure_pose_demos(frames: int = 16) -> Dict[str, Any]:
    """Write/read cached demo keypoint sequences."""
    if DEMOS_PATH.is_file():
        try:
            data = json.loads(DEMOS_PATH.read_text(encoding="utf-8"))
            if data.get("frames") == frames and data.get("classes"):
                return data
        except (json.JSONDecodeError, KeyError):
            pass
    payload = {
        "frames": frames,
        "joints": 17,
        "coord": "normalised_pelvis_centric_y_up",
        "edges": [list(e) for e in COCO_EDGES],
        "classes": {
            cid: {
                "sequence": generate_demo_sequence(cid, frames),
                **{k: v for k, v in KIMORE_PRESETS[cid].items() if k != "regions"},
                "regions": KIMORE_PRESETS[cid]["regions"],
            }
            for cid in KIMORE_CLASSES
        },
    }
    OUT.mkdir(parents=True, exist_ok=True)
    DEMOS_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def get_kimore_preset(class_id: str) -> Optional[Dict[str, Any]]:
    key = class_id.strip().lower().replace("-", "_").replace(" ", "_")
    if key not in KIMORE_PRESETS:
        return None
    return {"id": key, **KIMORE_PRESETS[key]}


def regions_for_kimore(class_id: str, *, strict: bool = True) -> List[str]:
    preset = get_kimore_preset(class_id)
    if preset:
        return list(preset["regions"])
    if strict:
        return []
    from fitkg_body_map import regions_from_exercise_preset
    return regions_from_exercise_preset(class_id)


def kimore_fitkg_context(rag: Any, class_id: str) -> Dict[str, Any]:
    preset = get_kimore_preset(class_id)
    if not preset:
        return {"error": f"unknown class: {class_id}"}
    query = preset["fitkg_query"]
    ctx = rag.retrieve(query)
    return {
        "class_id": preset.get("id", class_id),
        "label_en": preset["label_en"],
        "label_zh": preset["label_zh"],
        "fitkg_query": query,
        "regions": preset["regions"],
        "primary_muscles_en": preset["primary_muscles_en"],
        "primary_muscles_zh": preset["primary_muscles_zh"],
        "nodes": ctx.get("nodes", [])[:8],
        "triples": ctx.get("triples", [])[:10],
        "passage_count": len(ctx.get("passages", [])),
    }


def live_rep_feedback(
    rag: Any,
    exercise_class: str,
    confidence: float = 1.0,
    keypoints: Optional[List[List[List[float]]]] = None,
) -> Dict[str, Any]:
    preset = get_kimore_preset(exercise_class)
    if not preset:
        return {"error": f"unknown exercise_class: {exercise_class}"}
    ctx = kimore_fitkg_context(rag, exercise_class)
    return {
        "exercise": exercise_class,
        "label_en": preset["label_en"],
        "label_zh": preset["label_zh"],
        "confidence": confidence,
        "highlighted_regions": preset["regions"],
        "fitkg_query": preset["fitkg_query"],
        "primary_muscles_en": preset["primary_muscles_en"],
        "primary_muscles_zh": preset["primary_muscles_zh"],
        "triples": ctx.get("triples", []),
        "keypoints_frames": len(keypoints) if keypoints else 0,
        "cue_text": _cue_text(preset),
    }


def _cue_text(preset: Dict[str, Any]) -> str:
    muscles = ", ".join(preset.get("primary_muscles_en", [])[:4])
    return (
        f"{preset['label_en']}: focus on {muscles}. "
        f"Keep controlled tempo and stable alignment."
    )


def list_kimore_catalog() -> List[Dict[str, Any]]:
    return [
        {"id": cid, **{k: v for k, v in KIMORE_PRESETS[cid].items()}}
        for cid in KIMORE_CLASSES
    ]


if __name__ == "__main__":
    ensure_pose_demos()
    print(f"Wrote {DEMOS_PATH}")

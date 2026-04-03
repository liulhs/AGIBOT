# x2_api/motion_catalog.py
"""Parses resource_config.yaml into a friendly motion catalog.

Maps resource keys to human-readable IDs, generates correct tags and paths
for the RegisterCustomMotion and SetMcMotion ROS2 services.
"""
import re
from typing import Optional
import yaml
from config import MOTION_TYPE_ANIMATION, MOTION_TYPE_MIMIC


# Friendly name overrides for known resource keys.
# Keys not listed here get auto-generated IDs from their display name.
KNOWN_MOTIONS = {
    "linkcraft_resource_onnx_01KMS0NMK8F7MMFSET1MDV0BG6": "golf_swing_pro",
    "linkcraft_resource_onnx_erlianti": "double_kick",
    "linkcraft_resource_onnx_zuiquan": "drunk_kungfu",
    "linkcraft_resource_onnx_taiji": "taichi",
    "linkcraft_resource_onnx_tianmao": "miao",
    "linkcraft_resource_onnx_depasito": "despacito",
    "linkcraft_resource_onnx_01KEVJX7PSAZQ04TW6YGPBP5SV": "love_you",
}

# Resources that are in resource_config.yaml but don't work with MC's
# BmimicRLController. ANIMATION (CSV) type motions register and return
# success from SetMcMotion, but MC never physically executes them.
# Only MIMIC (ONNX) motions work.
IGNORED_RESOURCES = {
    "linkcraft_resource_01KMRTZQ9HWX5WBEAYEK251GQ2",  # golf_swing_csv — ANIMATION/CSV, MC ignores
}


def _slugify(name: str) -> str:
    """Convert a display name to a snake_case ID."""
    s = name.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    return s.strip("_")


class MotionCatalog:
    """Reads resource_config.yaml and builds a catalog of available LinkCraft motions."""

    def __init__(self, config_path: str, resource_base: str):
        self._motions = {}
        self._resource_base = resource_base
        self._load(config_path)

    def _load(self, config_path: str):
        with open(config_path) as f:
            data = yaml.safe_load(f)

        for entry in data.get("resource_config", []):
            key = entry.get("resource_key", "")
            if not key.startswith("linkcraft_resource"):
                continue
            if key in IGNORED_RESOURCES:
                continue

            version_info = entry.get("current_version", {})
            version = version_info.get("version", "0.0.1")
            name = version_info.get("name", key)

            is_onnx = "_onnx_" in key or key.startswith("linkcraft_resource_onnx")
            motion_type = MOTION_TYPE_MIMIC if is_onnx else MOTION_TYPE_ANIMATION

            # Tag = resource_key + version (exact format MC expects)
            tag = f"{key}_{version}"

            # Resource path = base / key / version / unzip / (policy.onnx or motion.csv)
            filename = "policy.onnx" if is_onnx else "motion.csv"
            res_path = f"{self._resource_base}/{key}/{version}/unzip/{filename}"

            # Friendly ID
            friendly_id = KNOWN_MOTIONS.get(key, _slugify(name))

            self._motions[friendly_id] = {
                "id": friendly_id,
                "name": name,
                "resource_key": key,
                "tag": tag,
                "version": version,
                "motion_type": motion_type,
                "motion_type_name": "MIMIC" if is_onnx else "ANIMATION",
                "res_path": res_path,
                "registered": False,
            }

    def list_all(self) -> list[dict]:
        """Return all motions as a list of dicts."""
        return list(self._motions.values())

    def get_by_id(self, motion_id: str) -> Optional[dict]:
        """Look up a motion by friendly ID. Returns None if not found."""
        return self._motions.get(motion_id)

    def mark_registered(self, motion_id: str):
        """Mark a motion as registered with MC."""
        if motion_id in self._motions:
            self._motions[motion_id]["registered"] = True

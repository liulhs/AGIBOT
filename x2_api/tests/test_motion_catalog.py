# x2_api/tests/test_motion_catalog.py
"""Tests for motion_catalog.py — parses resource_config.yaml into a usable catalog."""
import os
import tempfile
import pytest
from motion_catalog import MotionCatalog


SAMPLE_RESOURCE_CONFIG = """
resource_config:
  - resource_key: linkcraft_resource_onnx_01KMS0NMK8F7MMFSET1MDV0BG6
    hot_update: false
    current_version:
      version: 0.0.1
      name: Golf Swing
      files:
        - /agibot/data/var/robot_proxy/resources/linkcraft_resource_onnx_01KMS0NMK8F7MMFSET1MDV0BG6/0.0.1/unzip
  - resource_key: linkcraft_resource_onnx_zuiquan
    hot_update: false
    current_version:
      version: 0.0.1
      name: DrunkKungfu
      files:
        - /agibot/data/var/robot_proxy/resources/linkcraft_resource_onnx_zuiquan/0.0.1/unzip
  - resource_key: linkcraft_resource_01KMRTZQ9HWX5WBEAYEK251GQ2
    hot_update: false
    current_version:
      version: 0.0.1
      name: Golf Swing
      files:
        - /agibot/data/var/robot_proxy/resources/linkcraft_resource_01KMRTZQ9HWX5WBEAYEK251GQ2/0.0.1/unzip
  - resource_key: interaction_audio_nlg
    hot_update: true
    current_version:
      version: v1.2.0
      name: NLG Audio
      files:
        - /some/path
"""


@pytest.fixture
def catalog_from_string():
    """Create a MotionCatalog from a sample YAML string."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(SAMPLE_RESOURCE_CONFIG)
        f.flush()
        catalog = MotionCatalog(f.name, resource_base="/fake/base")
    yield catalog
    os.unlink(f.name)


def test_catalog_only_includes_linkcraft_resources(catalog_from_string):
    """Non-linkcraft resources (interaction_audio_nlg) should be excluded."""
    motions = catalog_from_string.list_all()
    ids = [m["id"] for m in motions]
    assert "interaction_audio_nlg" not in ids
    assert len(motions) == 3


def test_catalog_generates_correct_tag(catalog_from_string):
    """Tag must be {resource_key}_{version}."""
    motions = {m["id"]: m for m in catalog_from_string.list_all()}
    golf = motions["golf_swing_pro"]
    assert golf["tag"] == "linkcraft_resource_onnx_01KMS0NMK8F7MMFSET1MDV0BG6_0.0.1"


def test_catalog_onnx_gets_mimic_type(catalog_from_string):
    """Resources with 'onnx' in key should be type MIMIC (2)."""
    motions = {m["id"]: m for m in catalog_from_string.list_all()}
    assert motions["golf_swing_pro"]["motion_type"] == 2  # MIMIC


def test_catalog_csv_gets_animation_type(catalog_from_string):
    """Resources without 'onnx' in key should be type ANIMATION (1)."""
    motions = {m["id"]: m for m in catalog_from_string.list_all()}
    csv_motions = [m for m in catalog_from_string.list_all() if m["motion_type"] == 1]
    assert len(csv_motions) == 1


def test_catalog_generates_correct_onnx_path(catalog_from_string):
    """ONNX resources should have res_path pointing to policy.onnx file."""
    motions = {m["id"]: m for m in catalog_from_string.list_all()}
    golf = motions["golf_swing_pro"]
    assert golf["res_path"].endswith("/policy.onnx")
    assert "linkcraft_resource_onnx_01KMS0NMK8F7MMFSET1MDV0BG6/0.0.1/unzip" in golf["res_path"]


def test_catalog_generates_correct_csv_path(catalog_from_string):
    """CSV resources should have res_path pointing to motion.csv file."""
    csv_motions = [m for m in catalog_from_string.list_all() if m["motion_type"] == 1]
    assert len(csv_motions) == 1
    assert csv_motions[0]["res_path"].endswith("/motion.csv")


def test_catalog_get_by_id(catalog_from_string):
    """get_by_id should return a single motion or None."""
    result = catalog_from_string.get_by_id("golf_swing_pro")
    assert result is not None
    assert result["name"] == "Golf Swing"

    result = catalog_from_string.get_by_id("nonexistent")
    assert result is None


def test_catalog_friendly_id_generation(catalog_from_string):
    """Friendly IDs should be snake_case, human-readable."""
    motions = catalog_from_string.list_all()
    ids = [m["id"] for m in motions]
    # Should have sensible IDs, not raw resource keys
    assert all("linkcraft_resource" not in id for id in ids)

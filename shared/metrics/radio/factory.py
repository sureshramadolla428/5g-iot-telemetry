"""Factory: terrestrial default; NTN/A2G only when flags are set."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from metrics.radio.a2g_model import A2gRadioModel
from metrics.radio.base import RadioModel
from metrics.radio.ntn_model import NtnRadioModel
from metrics.radio.terrestrial import TerrestrialUmaModel


def load_radio_config(path: str | Path) -> dict[str, Any]:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError("radio model YAML must be a mapping")
    return data


def build_radio_model(cfg: dict[str, Any]) -> RadioModel:
    enable_ntn = bool(cfg.get("enable_ntn", False))
    enable_a2g = bool(cfg.get("enable_a2g", False))
    if enable_ntn and enable_a2g:
        raise ValueError("enable_ntn and enable_a2g are mutually exclusive")
    profile = str(cfg.get("profile", "terrestrial")).lower()
    if enable_ntn or profile == "ntn":
        return NtnRadioModel()
    if enable_a2g or profile == "a2g":
        return A2gRadioModel()
    return TerrestrialUmaModel()

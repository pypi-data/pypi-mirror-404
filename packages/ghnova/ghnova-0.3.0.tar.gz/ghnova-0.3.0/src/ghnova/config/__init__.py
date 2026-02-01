"""Initialization of the configuration module for ghnova."""

from __future__ import annotations

from ghnova.config.manager import ConfigManager
from ghnova.config.model import AccountConfig, Config

__all__ = ["AccountConfig", "Config", "ConfigManager"]

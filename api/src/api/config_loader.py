"""Configuration loader for YAML files."""
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from functools import lru_cache


# Get the configs directory path
CONFIGS_DIR = Path(__file__).parent / "configs"


@lru_cache(maxsize=1)
def load_metrics_config() -> Dict[str, Any]:
    """Load and cache the metrics configuration."""
    config_path = CONFIGS_DIR / "metrics.yaml"
    if not config_path.exists():
        return {}
    
    with open(config_path, 'r') as f:
        return yaml.safe_load(f) or {}


@lru_cache(maxsize=1)
def load_agents_config() -> Dict[str, Any]:
    """Load and cache the agents configuration."""
    config_path = CONFIGS_DIR / "agents.yaml"
    if not config_path.exists():
        return {}
    
    with open(config_path, 'r') as f:
        return yaml.safe_load(f) or {}


@lru_cache(maxsize=1)
def load_project_config() -> Dict[str, Any]:
    """Load and cache the project configuration."""
    config_path = CONFIGS_DIR / "project.yaml"
    if not config_path.exists():
        return {}
    
    with open(config_path, 'r') as f:
        return yaml.safe_load(f) or {}


def get_metric_target(category: str, metric: str) -> Optional[Dict[str, float]]:
    """Get target values for a specific metric."""
    config = load_metrics_config()
    if category in config and metric in config[category]:
        return config[category][metric]
    return None


def get_agent_config(agent_name: str) -> Optional[Dict[str, Any]]:
    """Get configuration for a specific agent."""
    config = load_agents_config()
    return config.get(agent_name)


def get_project_setting(setting: str) -> Any:
    """Get a project setting value."""
    config = load_project_config()
    return config.get(setting)


# Convenience functions
def get_edge_intensity() -> int:
    """Get the edge intensity setting."""
    return get_project_setting("edge_intensity") or 1


def get_patch_variants() -> list:
    """Get the list of patch variants to generate."""
    return get_project_setting("patch_variants") or ["safe", "bold"]


def get_banned_words() -> list:
    """Get the global list of banned words."""
    return get_project_setting("banned_global") or []
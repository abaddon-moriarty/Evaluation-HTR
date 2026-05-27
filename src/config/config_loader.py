from pathlib import Path

import yaml


def load_config(
    path="/home/barachiel/Documents/Projects/Evaluation HTR/src/config/default.yaml",
):
    """Load a YAML config file and return as dict."""
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

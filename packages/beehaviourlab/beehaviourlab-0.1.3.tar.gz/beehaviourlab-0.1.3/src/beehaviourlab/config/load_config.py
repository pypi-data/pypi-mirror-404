import logging
import sys
from enum import Enum
from importlib import resources
from pathlib import Path
from types import SimpleNamespace
from typing import Union

import yaml


class ConfigFiles(Enum):
    TRACKING = "tracking_config.yaml"


def get_config(data: Union[ConfigFiles, Path, dict, None]) -> SimpleNamespace:
    """Given a path to a YAML file, a dictionary object or an ConfigFiles enum
    member, returns a simple namespace object holding config data.
    If the data is None, an empty namespace is returned.
    """
    if data is None:
        return SimpleNamespace()
    elif isinstance(data, ConfigFiles):
        local_path = Path(str(data.value))
        if local_path.exists():
            return get_config(local_path)
        resource = resources.files("beehaviourlab.config").joinpath(str(data.value))
        with resources.as_file(resource) as config_path:
            return get_config(config_path)
    elif isinstance(data, Path):
        logging.info(f"Loading config from {data}")
        if data.exists():
            with open(data, "r") as stream:
                config_dict = yaml.safe_load(stream)
            config_dict = _resolve_paths(config_dict, data.parent)
            return SimpleNamespace(**config_dict)
        else:
            logging.error("Couldn't find config file... Exiting!")
            sys.exit(1)
    elif isinstance(data, dict):
        return SimpleNamespace(**data)


def _resolve_paths(config_dict: dict, base_dir: Path) -> dict:
    """Resolve known path entries relative to the config file location."""
    if not isinstance(config_dict, dict):
        return config_dict
    resolved = dict(config_dict)
    path_keys = {"ultralytics_config"}
    for key, value in config_dict.items():
        if isinstance(value, str) and (key.endswith("_path") or key in path_keys):
            path = Path(value)
            if not path.is_absolute():
                candidate = base_dir / path
                if candidate.exists():
                    resolved[key] = str(candidate)
                else:
                    resolved[key] = str(base_dir.parent / path)
    return resolved

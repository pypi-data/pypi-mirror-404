"""
Configuration loader module
"""

import os
from pathlib import Path
from typing import TypedDict
import json
import yaml
from zscams.agent.src.support.yaml import YamlIndentedListsDumper,  resolve_placeholders


config = {}

ROOT_PATH = Path(__file__).parent.parent.parent

CONFIG_PATH = os.path.join(ROOT_PATH.absolute(), "config.yaml")


class RemoteConfig(TypedDict):
    """Type definition for remote configuration."""

    host: str
    port: str
    verify_cert: bool
    client_key: str
    ca_cert: str
    ca_chain: str

def reinitialize(**kwargs):
    import zscams
    BASE_DIR = Path(zscams.__file__).resolve().parent
    template_path = f"{BASE_DIR}/agent/configuration/config.j2"
    with open(template_path) as f:
        template = yaml.safe_load(f)
    resolve_placeholders(template, kwargs)
    override_config(template)

def save_config(data):
    """Save the YAML config back to disk."""
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, default_flow_style=False)


def load_config():
    """
    Load and parse the YAML configuration file.

    Returns:
        dict: Configuration dictionary containing remote settings and forwards.
    """
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
        return config


def get_config():
    """
    Get the loaded configuration.

    Returns:
        dict: Configuration dictionary containing remote settings and forwards.
    """

    if not config:
        return load_config()

    return config


def override_config(new_config: dict):
    """
    Override the existing configuration with a new one.
    Args:
        new_config (dict): New configuration dictionary to override the existing one.
    """
    config = new_config

    with open(CONFIG_PATH, "w", encoding="utf-8") as file:
        yaml.dump(
            config,
            file,
            Dumper=YamlIndentedListsDumper,
            default_flow_style=False,
            explicit_start=True,
        )

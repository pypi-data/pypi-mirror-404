import yaml
import os
from pathlib import Path
from typing import Any, Dict

def load_yaml(file_path: Path) -> Dict[str, Any]:
    try:
        with open(file_path, mode='r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Error: Configuration file not found at {file_path}")
    except yaml.YAMLError as e:
        print(f"Error parsing YAML file {file_path}: {e}")


def merge_configs(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_configs(result[key], value)
        else:
            result[key] = value
    return result

def insert_env_vars(context: Dict[str, Any]) -> None:
    context['ssh_config'].update({"username": os.getenv('USERNAME')})
    context['ssh_config'].update({"password": os.getenv('PASSWORD')})
    context['ssh_config'].update({"private_key_file": os.getenv('SSH_PRIVATE_KEY_FILE')})
    context['ssh_config'].update({"pub_key": os.getenv('SSH_PUBLIC_KEY')})
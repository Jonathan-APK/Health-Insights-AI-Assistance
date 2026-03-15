import logging
from pathlib import Path
from typing import Any, Dict

import yaml

logger = logging.getLogger("prompt_loader")


def load_prompt_config(module: str, key: str, version: str = "v1.0") -> Dict[str, Any]:
    """
    Load full prompt configuration including system, model, temperature, etc.
    Structure:
        prompts/module/version/config.yaml  (metadata: model, temperature, etc.)
        prompts/module/version/{key}.txt    (actual prompt text)
    Args:
        module: e.g., "orchestrator", "clinical_analysis"
        key: e.g., "classification", "analysis"
        version: e.g., "v1.0", "v1.2"
    Returns:
        Dictionary with 'system', 'model', 'temperature', 'description', etc.
    Raises:
        FileNotFoundError: If config or prompt file doesn't exist
        KeyError: If key not found in config
        ValueError: If YAML is invalid
    """
    backend_dir = Path(__file__).parent.parent
    prompt_dir = backend_dir / "prompts" / module / version
    config_file = prompt_dir / "config.yaml"

    # Check if config file exists
    if not config_file.exists():
        raise FileNotFoundError(f"Config file not found: {config_file}")

    # Load config YAML
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML file {config_file}: {e}")
        raise ValueError(f"Invalid YAML in {config_file}: {e}")

    # Check if key exists in config
    if key not in config_data:
        available_keys = list(config_data.keys())
        raise KeyError(
            f"Prompt key '{key}' not found in {module}/{version}\n"
            f"Available keys: {available_keys}"
        )

    config = config_data[key].copy()

    # Determine prompt file name
    # Use 'prompt_file' if specified, otherwise default to '{key}.txt'
    prompt_filename = config.get("prompt_file", f"{key}.txt")
    prompt_file = prompt_dir / prompt_filename

    # Load the actual prompt text
    if not prompt_file.exists():
        raise FileNotFoundError(
            f"Prompt file not found: {prompt_file}\n"
            f"Expected file: {prompt_filename} in {prompt_dir}"
        )

    try:
        with open(prompt_file, "r", encoding="utf-8") as f:
            config["system"] = f.read()
        logger.debug(f"Loaded prompt from {prompt_file}")
    except Exception as e:
        logger.error(f"Error reading prompt file {prompt_file}: {e}")
        raise

    # Remove prompt_file reference from config if it exists
    if "prompt_file" in config:
        del config["prompt_file"]

    # Validate that prompt is not empty
    if not config["system"] or not config["system"].strip():
        raise ValueError(f"Prompt file is empty: {prompt_file}")

    # Add metadata for tracking
    config["_metadata"] = {
        "module": module,
        "key": key,
        "version": version,
        "prompt_file": str(prompt_file),
        "config_file": str(config_file),
    }

    logger.info(f"Loaded prompt: {module}/{key} v{version}")

    return config

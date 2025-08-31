"""Utility functions and configuration management."""

import logging
import yaml
from pathlib import Path
from typing import Dict, Any


def setup_logging(config: Dict[str, Any]) -> None:
    """Set up logging configuration."""
    log_config = config.get('logging', {})
    level = log_config.get('level', 'INFO')
    format_str = log_config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    log_file = log_config.get('file')
    
    # Create logs directory if specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
    
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=format_str,
        filename=log_file
    )


def load_config(config_path: Path) -> Dict[str, Any]:
    """Load configuration from YAML file."""
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def get_default_config_path() -> Path:
    """Get the default configuration file path."""
    return Path(__file__).parent.parent.parent.parent / "config" / "default.yaml"
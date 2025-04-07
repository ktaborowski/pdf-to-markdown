"""Configuration handling for PDF to Markdown converter."""

import sys
import yaml
from pathlib import Path
from typing import Dict, Any


def load_config(config_path: Path = None) -> Dict[str, Any]:
    """Load configuration from YAML file.
    
    Args:
        config_path: Path to the config YAML file. If None, uses default location.
        
    Returns:
        Dictionary containing configuration settings.
        
    Raises:
        SystemExit: If the configuration file cannot be loaded.
    """
    if config_path is None:
        # Use default location relative to this file
        config_path = Path(__file__).parents[2] / 'config.yaml'
    
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Error loading config: {e}", file=sys.stderr)
        sys.exit(1) 
"""
Configuration management for the DAS Auto Experiment Application.
"""
import json
import os
from typing import Dict, Any
from ..core.interfaces import ConfigProvider

class JsonConfigManager(ConfigProvider):
    """JSON-based configuration manager."""
    
    def __init__(self, config_file: str = "experiment_config.json"):
        self.config_file = config_file
        self.default_config = {
            "amplitude": {"min": 0.0, "max": 10.0, "step": 1.0},
            "bias": {"min": -5.0, "max": 5.0, "step": 1.0},
            "frequency": {"min": 1.0, "max": 100.0, "step": 10.0},
            "waveform_type": "Z",  # Z: sine, F: square, S: triangle, J: sawtooth
            "prefix": "experiment",
            "nfiles": 3,
            "nrefls": 10000
        }
        self.config = self.load_config()

    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default if not exists."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print(f"Error reading {self.config_file}, using default config")
                return self.default_config.copy()
        return self.default_config.copy()

    def save_config(self, config: Dict[str, Any]) -> None:
        """Save configuration to file."""
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=4)
        self.config = config

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate configuration values."""
        try:
            # Check required fields
            required_fields = ["amplitude", "bias", "frequency", "waveform_type", "prefix"]
            for field in required_fields:
                if field not in config:
                    return False

            # Validate numeric ranges
            for param in ["amplitude", "bias", "frequency"]:
                if not all(k in config[param] for k in ["min", "max", "step"]):
                    return False
                if config[param]["min"] > config[param]["max"]:
                    return False
                if config[param]["step"] <= 0:
                    return False

            # Validate waveform type
            if config["waveform_type"] not in ["Z", "F", "S", "J"]:
                return False

            # Validate nfiles and nrefls
            if not isinstance(config.get("nfiles", 0), int) or config["nfiles"] <= 0:
                return False
            if not isinstance(config.get("nrefls", 0), int) or config["nrefls"] <= 0:
                return False

            return True
        except Exception:
            return False 
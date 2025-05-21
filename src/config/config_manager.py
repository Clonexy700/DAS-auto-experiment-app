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
            "serial_port": "com4",
            "parallel_sweep": True,
            "prefix": "experiment",
            "nfiles": 3,
            "nrefls": 10000,
            "ch1": {
                "amplitude": {"min": 0.0, "max": 10.0, "step": 1.0},
                "bias": {"min": -5.0, "max": 5.0, "step": 1.0},
                "frequency": {"min": 0.0, "max": 100.0, "step": 10.0},
                "waveform_type": "Z"
            },
            "ch2": {
                "amplitude": {"min": 0.0, "max": 10.0, "step": 1.0},
                "bias": {"min": -5.0, "max": 5.0, "step": 1.0},
                "frequency": {"min": 0.0, "max": 100.0, "step": 10.0},
                "waveform_type": "Z"
            },
            "ch3": {
                "amplitude": {"min": 0.0, "max": 10.0, "step": 1.0},
                "bias": {"min": -5.0, "max": 5.0, "step": 1.0},
                "frequency": {"min": 0.0, "max": 100.0, "step": 10.0},
                "waveform_type": "Z"
            }
        }
        self.config = self.load_config()

    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default if not exists."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    # Ensure all required fields exist
                    for key, value in self.default_config.items():
                        if key not in config:
                            config[key] = value
                    return config
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error reading {self.config_file}: {e}")
        return self.default_config.copy()

    def save_config(self, config: Dict[str, Any]) -> None:
        """Save configuration to file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=4)
            self.config = config
        except IOError as e:
            print(f"Error saving {self.config_file}: {e}")

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate configuration values."""
        try:
            # Check required fields
            required_fields = ["serial_port", "parallel_sweep", "prefix", "nfiles", "nrefls"]
            for field in required_fields:
                if field not in config:
                    return False

            # Validate DAS-specific fields
            if not isinstance(config["nfiles"], int) or config["nfiles"] <= 0:
                return False
            if not isinstance(config["nrefls"], int) or config["nrefls"] <= 0:
                return False
            if not isinstance(config["prefix"], str) or not config["prefix"]:
                return False

            # Validate each channel
            for ch in ["ch1", "ch2", "ch3"]:
                if ch not in config:
                    return False
                
                ch_config = config[ch]
                required_params = ["amplitude", "bias", "frequency", "waveform_type"]
                for param in required_params:
                    if param not in ch_config:
                        return False

                # Validate numeric ranges for each parameter
                for param in ["amplitude", "bias", "frequency"]:
                    if not all(k in ch_config[param] for k in ["min", "max", "step"]):
                        return False
                    if ch_config[param]["min"] > ch_config[param]["max"]:
                        return False
                    if ch_config[param]["step"] < 0:  # Allow step = 0 for fixed parameters
                        return False

                # Validate waveform type
                if ch_config["waveform_type"] not in ["Z", "F", "S", "J"]:
                    return False

            return True
        except Exception:
            return False 
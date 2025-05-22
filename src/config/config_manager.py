"""
Configuration manager for the application.
"""
import json
import os
from typing import Dict, Any

class ConfigManager:
    """Manages application configuration."""

    def __init__(self, config_path: str):
        """Initialize with config file path."""
        self.config_path = config_path

    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(f"Invalid JSON in config file: {str(e)}", e.doc, e.pos)

    def save_config(self, config: Dict[str, Any]) -> None:
        """Save configuration to file."""
        if not isinstance(config, dict):
            raise TypeError("Config must be a dictionary")
        
        with open(self.config_path, 'w') as f:
            json.dump(config, f, indent=4)

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate configuration structure."""
        required_fields = {
            "serial_port": str,
            "prefix": str,
            "parallel_sweep": bool,
            "ch1": dict
        }
        
        # Check required fields
        for field, field_type in required_fields.items():
            if field not in config:
                return False
            if not isinstance(config[field], field_type):
                return False
        
        # Check ch1 configuration
        ch1_config = config["ch1"]
        required_ch1_fields = {
            "amplitude": dict,
            "bias": dict,
            "frequency": dict,
            "waveform_type": str
        }
        
        for field, field_type in required_ch1_fields.items():
            if field not in ch1_config:
                return False
            if not isinstance(ch1_config[field], field_type):
                return False
        
        # Check parameter ranges
        for param in ["amplitude", "bias", "frequency"]:
            param_config = ch1_config[param]
            if not all(k in param_config for k in ["min", "max", "step"]):
                return False
            if not all(isinstance(param_config[k], (int, float)) for k in ["min", "max", "step"]):
                return False
        
        return True

    def get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "serial_port": "com4",
            "prefix": "experiment",
            "parallel_sweep": True,
            "ch1": {
                "amplitude": {"min": 0.0, "max": 10.0, "step": 1.0},
                "bias": {"min": -5.0, "max": 5.0, "step": 1.0},
                "frequency": {"min": 100.0, "max": 200.0, "step": 10.0},
                "waveform_type": "Z"
            }
        } 
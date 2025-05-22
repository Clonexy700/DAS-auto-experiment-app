"""
Tests for configuration manager.
"""
import unittest
import os
import json
from src.config.config_manager import ConfigManager

class TestConfigManager(unittest.TestCase):
    """Test cases for ConfigManager."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_config = {
            "serial_port": "com4",
            "prefix": "test",
            "parallel_sweep": True,
            "ch1": {
                "amplitude": {"min": 0.0, "max": 10.0, "step": 5.0},
                "bias": {"min": -5.0, "max": 5.0, "step": 5.0},
                "frequency": {"min": 100.0, "max": 200.0, "step": 50.0},
                "waveform_type": "Z"
            }
        }
        self.config_file = "test_config.json"
        self.manager = ConfigManager(self.config_file)

    def tearDown(self):
        """Tear down test fixtures."""
        if os.path.exists(self.config_file):
            os.remove(self.config_file)

    def test_load_config(self):
        """Test loading configuration."""
        # Save test config
        with open(self.config_file, 'w') as f:
            json.dump(self.test_config, f)
        
        # Load and verify
        config = self.manager.load_config()
        self.assertEqual(config, self.test_config)

    def test_load_config_missing_file(self):
        """Test loading non-existent configuration."""
        with self.assertRaises(FileNotFoundError):
            self.manager.load_config()

    def test_save_config(self):
        """Test saving configuration."""
        self.manager.save_config(self.test_config)
        
        # Verify file exists and contains correct data
        self.assertTrue(os.path.exists(self.config_file))
        with open(self.config_file, 'r') as f:
            saved_config = json.load(f)
        self.assertEqual(saved_config, self.test_config)

    def test_save_invalid_config(self):
        """Test saving invalid configuration."""
        with self.assertRaises(TypeError):
            self.manager.save_config("invalid")

    def test_validate_config(self):
        """Test configuration validation."""
        # Test valid config
        self.assertTrue(self.manager.validate_config(self.test_config))
        
        # Test missing required field
        invalid_config = self.test_config.copy()
        del invalid_config["serial_port"]
        self.assertFalse(self.manager.validate_config(invalid_config))
        
        # Test invalid field type
        invalid_config = self.test_config.copy()
        invalid_config["parallel_sweep"] = "true"  # Should be bool
        self.assertFalse(self.manager.validate_config(invalid_config))
        
        # Test invalid ch1 configuration
        invalid_config = self.test_config.copy()
        invalid_config["ch1"]["amplitude"] = "invalid"  # Should be dict
        self.assertFalse(self.manager.validate_config(invalid_config))

    def test_get_default_config(self):
        """Test getting default configuration."""
        default_config = self.manager.get_default_config()
        
        # Verify structure
        self.assertIn("serial_port", default_config)
        self.assertIn("prefix", default_config)
        self.assertIn("parallel_sweep", default_config)
        self.assertIn("ch1", default_config)
        
        # Verify ch1 structure
        ch1_config = default_config["ch1"]
        self.assertIn("amplitude", ch1_config)
        self.assertIn("bias", ch1_config)
        self.assertIn("frequency", ch1_config)
        self.assertIn("waveform_type", ch1_config)
        
        # Verify parameter ranges
        for param in ["amplitude", "bias", "frequency"]:
            param_config = ch1_config[param]
            self.assertIn("min", param_config)
            self.assertIn("max", param_config)
            self.assertIn("step", param_config)

if __name__ == '__main__':
    unittest.main() 
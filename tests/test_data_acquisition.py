"""
Tests for DASDataAcquisition.
"""
import unittest
from unittest.mock import Mock, patch, call
import os
import shutil
import subprocess
from src.acquisition.data_acquisition import DASDataAcquisition

class TestDASDataAcquisition(unittest.TestCase):
    """Test cases for DASDataAcquisition."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_config = {
            "nfiles": 3,
            "nrefls": 10000,
            "prefix": "test"
        }
        self.acquisition = DASDataAcquisition(self.test_config)
        
        # Create test directories
        os.makedirs("refls1", exist_ok=True)
        
        # Create some test files
        for i in range(3):
            with open(f"refls1/test_file_{i}.dat", "w") as f:
                f.write(f"test data {i}")

    def tearDown(self):
        """Tear down test fixtures."""
        # Clean up test directories
        if os.path.exists("refls1"):
            shutil.rmtree("refls1")
        if os.path.exists("test_output"):
            shutil.rmtree("test_output")

    @patch('subprocess.check_call')
    def test_acquire_data_success(self, mock_check_call):
        """Test successful data acquisition."""
        result = self.acquisition.acquire_data()
        self.assertTrue(result)
        
        mock_check_call.assert_called_once_with([
            "./read_udp_das.exe",
            "--dir", "refls1",
            "--nfiles", "3",
            "--nrefls", "10000"
        ])

    @patch('subprocess.check_call')
    def test_acquire_data_failure(self, mock_check_call):
        """Test data acquisition failure."""
        mock_check_call.side_effect = subprocess.CalledProcessError(1, "read_udp_das.exe")
        
        with self.assertRaises(subprocess.CalledProcessError):
            self.acquisition.acquire_data()

    def test_move_data_files_success(self):
        """Test successful file movement."""
        os.makedirs("test_output", exist_ok=True)
        
        self.acquisition.move_data_files("test_output")
        
        # Check if files were moved
        self.assertEqual(len(os.listdir("test_output")), 3)
        self.assertEqual(len(os.listdir("refls1")), 0)

    def test_move_data_files_no_files(self):
        """Test file movement with no files."""
        os.makedirs("test_output", exist_ok=True)
        shutil.rmtree("refls1")
        os.makedirs("refls1")
        
        with self.assertRaises(Exception) as context:
            self.acquisition.move_data_files("test_output")
        
        self.assertIn("No data files were acquired", str(context.exception))

    def test_cleanup(self):
        """Test cleanup."""
        self.acquisition.cleanup()
        self.assertEqual(len(os.listdir("refls1")), 0)

    def test_prepare_directories(self):
        """Test directory preparation."""
        shutil.rmtree("refls1")
        self.acquisition._prepare_directories()
        self.assertTrue(os.path.exists("refls1"))

    def test_clear_data_directory(self):
        """Test data directory clearing."""
        self.acquisition._clear_data_directory()
        self.assertEqual(len(os.listdir("refls1")), 0)

    def test_config_validation(self):
        """Test configuration validation."""
        # Test valid config
        valid_config = {
            "nfiles": 3,
            "nrefls": 10000,
            "prefix": "test"
        }
        self.assertTrue(self.acquisition.validate_config(valid_config))
        
        # Test invalid config - missing required field
        invalid_config = {
            "nfiles": 3,
            "prefix": "test"
        }
        self.assertFalse(self.acquisition.validate_config(invalid_config))
        
        # Test invalid config - wrong type
        invalid_config = {
            "nfiles": "3",  # Should be int
            "nrefls": 10000,
            "prefix": "test"
        }
        self.assertFalse(self.acquisition.validate_config(invalid_config))

    def test_file_operations(self):
        """Test file operations."""
        # Test file creation
        test_file = "refls1/test_file.dat"
        with open(test_file, "w") as f:
            f.write("test data")
        self.assertTrue(os.path.exists(test_file))
        
        # Test file reading
        with open(test_file, "r") as f:
            content = f.read()
        self.assertEqual(content, "test data")
        
        # Test file deletion
        os.remove(test_file)
        self.assertFalse(os.path.exists(test_file))

    def test_directory_operations(self):
        """Test directory operations."""
        # Test directory creation
        test_dir = "test_dir"
        os.makedirs(test_dir, exist_ok=True)
        self.assertTrue(os.path.exists(test_dir))
        
        # Test directory listing
        test_file = os.path.join(test_dir, "test.txt")
        with open(test_file, "w") as f:
            f.write("test")
        files = os.listdir(test_dir)
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0], "test.txt")
        
        # Test directory removal
        shutil.rmtree(test_dir)
        self.assertFalse(os.path.exists(test_dir))

    @patch('subprocess.check_call')
    def test_acquire_data_with_different_configs(self, mock_check_call):
        """Test data acquisition with different configurations."""
        # Test with different number of files
        config = self.test_config.copy()
        config["nfiles"] = 5
        acquisition = DASDataAcquisition(config)
        acquisition.acquire_data()
        
        mock_check_call.assert_called_with([
            "./read_udp_das.exe",
            "--dir", "refls1",
            "--nfiles", "5",
            "--nrefls", "10000"
        ])
        
        # Test with different number of reflections
        config["nrefls"] = 20000
        acquisition = DASDataAcquisition(config)
        acquisition.acquire_data()
        
        mock_check_call.assert_called_with([
            "./read_udp_das.exe",
            "--dir", "refls1",
            "--nfiles", "5",
            "--nrefls", "20000"
        ])

if __name__ == '__main__':
    unittest.main() 
"""
Data acquisition implementation.
"""
import os
import shutil
import subprocess
import logging
from typing import Dict, Any
from ..core.interfaces import DataAcquisition

class DASDataAcquisition(DataAcquisition):
    """Data acquisition system for DAS experiments."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize DAS data acquisition with configuration."""
        self.config = config
        self._prepare_directories()
        
    def _prepare_directories(self) -> None:
        """Prepare necessary directories."""
        try:
            if not os.path.exists("refls1"):
                os.makedirs("refls1")
        except Exception as e:
            logging.error(f"Failed to prepare directories: {str(e)}")
            raise
            
    def _clear_data_directory(self) -> None:
        """Clear the data directory."""
        try:
            for file in os.listdir("refls1"):
                os.remove(os.path.join("refls1", file))
        except Exception as e:
            logging.error(f"Failed to clear data directory: {str(e)}")
            raise
            
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate configuration structure."""
        required_fields = {
            "nfiles": int,
            "nrefls": int,
            "prefix": str
        }
        
        # Check required fields
        for field, field_type in required_fields.items():
            if field not in config:
                return False
            if not isinstance(config[field], field_type):
                return False
            
            # Validate numeric fields
            if field in ["nfiles", "nrefls"]:
                if config[field] <= 0:
                    return False
        
        return True

    def acquire_data(self) -> bool:
        """Acquire data using the DAS system."""
        try:
            self._clear_data_directory()
            
            # Validate required configuration
            if not all(k in self.config for k in ["nfiles", "nrefls"]):
                raise ValueError("Missing required configuration: nfiles or nrefls")
            
            # Run the data acquisition program
            subprocess.check_call([
                "./udp_das_cringe.exe",
                "--dir", "refls1",
                "--nfiles", str(self.config["nfiles"]),
                "--nrefls", str(self.config["nrefls"])
            ])
            return True
        except subprocess.CalledProcessError as e:
            logging.error(f"Data acquisition failed: {str(e)}")
            raise
        except Exception as e:
            logging.error(f"Unexpected error during data acquisition: {str(e)}")
            raise
            
    def move_data_files(self, target_folder: str) -> None:
        """Move acquired data files to target folder."""
        try:
            # Ensure target folder exists
            os.makedirs(target_folder, exist_ok=True)
            
            files = os.listdir("refls1")
            if not files:
                raise Exception("No data files were acquired")
            
            for file in files:
                src = os.path.join("refls1", file)
                dst = os.path.join(target_folder, file)
                shutil.move(src, dst)
                
            logging.info(f"Successfully moved {len(files)} files to {target_folder}")
        except Exception as e:
            logging.error(f"Failed to move data files: {str(e)}")
            raise
            
    def cleanup(self) -> None:
        """Clean up resources."""
        try:
            self._clear_data_directory()
        except Exception as e:
            logging.error(f"Cleanup failed: {str(e)}")
            # Don't raise during cleanup to ensure other cleanup operations can proceed 
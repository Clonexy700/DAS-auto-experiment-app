"""
Data acquisition implementation.
"""
import os
import shutil
import subprocess
from typing import Dict, Any
from ..core.interfaces import DataAcquisition

class DASDataAcquisition(DataAcquisition):
    """Data acquisition system for DAS experiments."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._prepare_directories()
        
    def _prepare_directories(self) -> None:
        """Prepare necessary directories."""
        if not os.path.exists("refls1"):
            os.makedirs("refls1")
            
    def _clear_data_directory(self) -> None:
        """Clear the data directory."""
        for file in os.listdir("refls1"):
            os.remove(os.path.join("refls1", file))
            
    def acquire_data(self) -> bool:
        """Acquire data using the DAS system."""
        try:
            self._clear_data_directory()
            
            subprocess.check_call([
                "./read_udp_das.exe",
                "--dir", "refls1",
                "--nfiles", str(self.config["nfiles"]),
                "--nrefls", str(self.config["nrefls"])
            ])
            return True
        except subprocess.CalledProcessError as e:
            raise Exception(f"Data acquisition failed: {str(e)}")
            
    def move_data_files(self, target_folder: str) -> None:
        """Move acquired data files to target folder."""
        try:
            files = os.listdir("refls1")
            if not files:
                raise Exception("No data files were acquired")
            
            for file in files:
                src = os.path.join("refls1", file)
                dst = os.path.join(target_folder, file)
                shutil.move(src, dst)
        except Exception as e:
            raise Exception(f"Failed to move data files: {str(e)}")
            
    def cleanup(self) -> None:
        """Clean up resources."""
        try:
            self._clear_data_directory()
        except Exception:
            pass  # Ignore cleanup errors 
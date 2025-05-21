"""
Core interfaces for the DAS Auto Experiment Application.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any

class ConfigProvider(ABC):
    """Interface for configuration providers."""
    
    @abstractmethod
    def load_config(self) -> Dict[str, Any]:
        """Load configuration."""
        pass
    
    @abstractmethod
    def save_config(self, config: Dict[str, Any]) -> None:
        """Save configuration."""
        pass
    
    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate configuration."""
        pass

class DeviceController(ABC):
    """Interface for device controllers."""
    
    @abstractmethod
    def configure(self, params: Dict[str, Any]) -> None:
        """Configure device with given parameters."""
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """Clean up resources."""
        pass

class DataAcquisition(ABC):
    """Interface for data acquisition systems."""
    
    @abstractmethod
    def acquire_data(self) -> bool:
        """Acquire data."""
        pass
    
    @abstractmethod
    def move_data_files(self, target_folder: str) -> None:
        """Move acquired data files to target folder."""
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """Clean up resources."""
        pass

class ExperimentController(ABC):
    """Interface for experiment controllers."""
    
    @abstractmethod
    def start_experiment(self) -> None:
        """Start the experiment."""
        pass
    
    @abstractmethod
    def stop_experiment(self) -> None:
        """Stop the experiment."""
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """Clean up resources."""
        pass

class ExperimentObserver(ABC):
    """Interface for experiment observers."""
    
    @abstractmethod
    def on_progress(self, current: int, total: int):
        """Called when experiment progress is updated.
        
        Args:
            current: Current step number
            total: Total number of steps
        """
        pass
    
    @abstractmethod
    def on_error(self, error: str):
        """Called when an error occurs during the experiment.
        
        Args:
            error: Error message
        """
        pass
    
    @abstractmethod
    def on_complete(self):
        """Called when the experiment completes successfully."""
        pass 
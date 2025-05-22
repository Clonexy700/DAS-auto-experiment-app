"""
Piezo device controller implementation.
"""
import logging
from typing import Dict, Any
from pztlibrary.usart_lib import SerialConfigurator, USARTError
from ..core.interfaces import DeviceController

class PiezoController(DeviceController):
    """Controller for piezo actuator device."""
    
    def __init__(self, port: str = 'com4', baudrate: int = 115200):
        """Initialize piezo controller with serial connection."""
        try:
            self.serial = SerialConfigurator(port=port, baudrate=baudrate)
            logging.info(f"Initialized PiezoController on port {port}")
        except USARTError as e:
            logging.error(f"Failed to initialize PiezoController: {str(e)}")
            raise
        
    def configure(self, params: Dict[str, Any]) -> None:
        """Configure piezo with given parameters."""
        try:
            # Convert parameters to the format expected by SerialConfigurator
            config = {
                "wave_type": params["waveform_type"],
                "ch1": {
                    "v": params["amplitude"],
                    "b": params["bias"],
                    "f": params["frequency"]
                },
                "ch2": {"v": 0.0, "b": 0.0, "f": 0.0},  # Disable other channels
                "ch3": {"v": 0.0, "b": 0.0, "f": 0.0}
            }
            
            logging.info(f"Configuring piezo with parameters: {params}")
            self.serial.configure_channels(config)
            logging.info("Piezo configuration successful")
            
        except USARTError as e:
            logging.error(f"Failed to configure piezo: {str(e)}")
            raise
        except Exception as e:
            logging.error(f"Unexpected error during piezo configuration: {str(e)}")
            raise
            
    def cleanup(self) -> None:
        """Clean up resources."""
        try:
            # Set all channels to zero before closing
            zero_config = {
                "wave_type": "Z",
                "ch1": {"v": 0.0, "b": 0.0, "f": 0.0},
                "ch2": {"v": 0.0, "b": 0.0, "f": 0.0},
                "ch3": {"v": 0.0, "b": 0.0, "f": 0.0}
            }
            self.serial.configure_channels(zero_config)
            logging.info("Set all channels to zero")
            
            self.serial.close()
            logging.info("Closed serial connection")
        except Exception as e:
            logging.error(f"Error during piezo cleanup: {str(e)}")
            # Don't raise during cleanup to ensure other cleanup operations can proceed 
"""
Piezo device controller implementation.
"""
from typing import Dict, Any
from pztlibrary.usart_lib import SerialConfigurator, USARTError
from ..core.interfaces import DeviceController

class PiezoController(DeviceController):
    """Controller for piezo actuator device."""
    
    def __init__(self, port: str = 'com4', baudrate: int = 115200):
        self.serial = SerialConfigurator(port=port, baudrate=baudrate)
        
    def configure(self, params: Dict[str, Any]) -> None:
        """Configure piezo with given parameters."""
        try:
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
            self.serial.configure_channels(config)
        except USARTError as e:
            raise Exception(f"Failed to configure piezo: {str(e)}")
            
    def cleanup(self) -> None:
        """Clean up resources."""
        try:
            self.serial.close()
        except Exception:
            pass  # Ignore cleanup errors 
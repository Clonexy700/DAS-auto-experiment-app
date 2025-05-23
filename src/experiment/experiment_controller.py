"""
Experiment controller for parameter sweep experiments.
"""
import os
import itertools
import logging
import time
from typing import List, Dict, Any, Optional
from ..core.interfaces import ExperimentController, ExperimentObserver
from ..devices.piezo_controller import PiezoController
from ..acquisition.data_acquisition import DASDataAcquisition
from ..acquisition.acquisition_controller import AcquisitionController

class ParameterSweepController(ExperimentController):
    """Controller for parameter sweep experiments."""

    def __init__(self, config: Dict[str, Any], observer: Optional[ExperimentObserver] = None):
        """Initialize the experiment controller."""
        self.config = config
        self.observer = observer
        self.piezo: Optional[PiezoController] = None
        self.acquisition: Optional[AcquisitionController] = None
        self.running = False
        self.current_step = 0
        self.total_steps = self._calculate_total_steps()
        self._initialize_controllers()

    def _initialize_controllers(self):
        """Initialize controllers with proper error handling"""
        try:
            # First try to initialize piezo controller
            self.piezo = PiezoController(port=self.config.get("serial_port", "com4"))
            time.sleep(0.5)  # Give time for port to stabilize
            
            # Then initialize acquisition controller
            self.acquisition = AcquisitionController(self.config)
            
        except Exception as e:
            logging.error(f"Failed to initialize controllers: {str(e)}")
            self.cleanup()
            raise

    def get_progress(self) -> int:
        """Get experiment progress as percentage."""
        if self.total_steps == 0:
            return 0
        return int((self.current_step / self.total_steps) * 100)

    def is_running(self) -> bool:
        """Check if experiment is running."""
        return self.running

    def _calculate_total_steps(self) -> int:
        """Calculate total number of steps in the experiment."""
        try:
            amp_steps = len(self._get_range(self.config["ch1"]["amplitude"]))
            bias_steps = len(self._get_range(self.config["ch1"]["bias"]))
            freq_steps = len(self._get_range(self.config["ch1"]["frequency"]))
            
            if self.config.get("parallel_sweep", True):
                # For parallel sweeping, we take the maximum number of steps
                return max(amp_steps, bias_steps, freq_steps)
            else:
                # For sequential sweeping, we multiply the steps
                return amp_steps * bias_steps * freq_steps
        except Exception as e:
            logging.error(f"Error calculating total steps: {str(e)}")
            raise

    def _get_range(self, param: Dict[str, float]) -> List[float]:
        """Generate range of values for a parameter."""
        try:
            start = param["min"]
            stop = param["max"]
            step = param["step"]
            
            if step == 0:
                # For step=0, we use a single value (the max value)
                return [stop]
            
            return [start + i * step for i in range(int((stop - start) / step) + 1)]
        except Exception as e:
            logging.error(f"Error generating parameter range: {str(e)}")
            raise

    def _generate_parameter_combinations(self) -> List[Dict[str, float]]:
        """Generate parameter combinations for the experiment."""
        try:
            amp_range = self._get_range(self.config["ch1"]["amplitude"])
            bias_range = self._get_range(self.config["ch1"]["bias"])
            freq_range = self._get_range(self.config["ch1"]["frequency"])
            
            if self.config.get("parallel_sweep", True):
                # For parallel sweeping, we zip the ranges together
                max_len = max(len(amp_range), len(bias_range), len(freq_range))
                # Pad shorter ranges with their last value
                amp_range = amp_range + [amp_range[-1]] * (max_len - len(amp_range))
                bias_range = bias_range + [bias_range[-1]] * (max_len - len(bias_range))
                freq_range = freq_range + [freq_range[-1]] * (max_len - len(freq_range))
                
                return [
                    {"amplitude": a, "bias": b, "frequency": f}
                    for a, b, f in zip(amp_range, bias_range, freq_range)
                ]
            else:
                # For sequential sweeping, we generate all combinations
                return [
                    {"amplitude": a, "bias": b, "frequency": f}
                    for a, b, f in itertools.product(amp_range, bias_range, freq_range)
                ]
        except Exception as e:
            logging.error(f"Error generating parameter combinations: {str(e)}")
            raise

    def _create_output_folder(self, params: Dict[str, float]) -> str:
        """Create folder for output data."""
        try:
            folder_name = f"{self.config['prefix']}_a{params['amplitude']:.1f}_b{params['bias']:.1f}_f{params['frequency']:.1f}"
            os.makedirs(folder_name, exist_ok=True)
            return folder_name
        except Exception as e:
            logging.error(f"Error creating output folder: {str(e)}")
            raise

    def start_experiment(self) -> None:
        """Start the experiment."""
        if self.running:
            logging.warning("Experiment already running")
            return

        try:
            self.running = True
            self.current_step = 0
            
            # Prepare directories
            os.makedirs("data", exist_ok=True)
            
            # Initialize controllers using context manager
            with PiezoController(port=self.config.get("serial_port", "com4")) as self.piezo:
                self.piezo.start_monitoring()
                
                # Generate parameter combinations
                param_combinations = self._generate_parameter_combinations()
                
                for params in param_combinations:
                    if not self.running:
                        break
                    
                    # Configure piezo
                    self.piezo.configure({
                        "waveform_type": self.config["ch1"]["waveform_type"],
                        "amplitude": params["amplitude"],
                        "bias": params["bias"],
                        "frequency": params["frequency"]
                    })
                    
                    # Create output folder
                    output_folder = self._create_output_folder(params)
                    
                    # Acquire data
                    if self.acquisition.acquire_data():
                        self.acquisition.move_data_files(output_folder)
                    
                    # Update progress
                    self.current_step += 1
                    if self.observer:
                        self.observer.on_progress(self.get_progress(), self.get_total())
                
                if self.observer:
                    self.observer.on_complete()
                    
        except Exception as e:
            logging.error(f"Error during experiment: {str(e)}")
            if self.observer:
                self.observer.on_error(str(e))
        finally:
            self.running = False

    def stop_experiment(self) -> None:
        """Stop the experiment."""
        self.running = False

    def cleanup(self) -> None:
        """Clean up resources."""
        try:
            if self.piezo:
                self.piezo.close()
                time.sleep(0.5)  # Give time for port to be released
            if self.acquisition:
                self.acquisition.cleanup()
        except Exception as e:
            logging.error(f"Error during cleanup: {str(e)}")
        finally:
            self.running = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup() 
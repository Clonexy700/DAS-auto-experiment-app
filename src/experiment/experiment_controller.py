"""
Experiment controller implementation.
"""
import os
from typing import Dict, Any, Generator, Tuple
from ..core.interfaces import ExperimentController, ExperimentObserver
from ..devices.piezo_controller import PiezoController
from ..acquisition.data_acquisition import DASDataAcquisition

class ParameterSweepController(ExperimentController):
    """Controller for parameter sweep experiments."""
    
    def __init__(self, config: Dict[str, Any], observer: ExperimentObserver = None):
        self.config = config
        self.observer = observer
        self.piezo = PiezoController()
        self.data_acquisition = DASDataAcquisition(config)
        self.is_running = False
        self.current_step = (0, 0, 0)
        self.total_steps = self._calculate_total_steps()
        self.current_step_number = 0
        self._prepare_directories()
        
    def _calculate_total_steps(self) -> int:
        """Calculate total number of steps in the experiment."""
        amp_steps = int((self.config["amplitude"]["max"] - self.config["amplitude"]["min"]) / 
                       self.config["amplitude"]["step"]) + 1
        bias_steps = int((self.config["bias"]["max"] - self.config["bias"]["min"]) / 
                        self.config["bias"]["step"]) + 1
        freq_steps = int((self.config["frequency"]["max"] - self.config["frequency"]["min"]) / 
                        self.config["frequency"]["step"]) + 1
        return amp_steps * bias_steps * freq_steps
        
    def _prepare_directories(self) -> None:
        """Create necessary directories for the experiment."""
        prefix = self.config["prefix"]
        if not os.path.exists(prefix):
            os.makedirs(prefix)
            
    def _generate_parameter_combinations(self) -> Generator[Tuple[float, float, float], None, None]:
        """Generate all parameter combinations based on min/max/step values."""
        amp_range = self._get_range(self.config["amplitude"])
        bias_range = self._get_range(self.config["bias"])
        freq_range = self._get_range(self.config["frequency"])

        for a in amp_range:
            for b in bias_range:
                for f in freq_range:
                    yield a, b, f
                    
    def _get_range(self, param: Dict[str, float]) -> Generator[float, None, None]:
        """Generate range of values for a parameter."""
        current = param["min"]
        while current <= param["max"]:
            yield current
            current += param["step"]
            
    def _create_output_folder(self, i: int, j: int, k: int, a: float, b: float, f: float) -> str:
        """Create and return path to output folder for current step."""
        folder_name = f"{i}_{j}_{k}_{self.config['prefix']} f={f} a={a} b={b}"
        folder_path = os.path.join(self.config["prefix"], folder_name)
        os.makedirs(folder_path, exist_ok=True)
        return folder_path
        
    def start_experiment(self) -> None:
        """Start the experiment."""
        self.is_running = True
        self.current_step_number = 0
        i, j, k = 1, 1, 1

        try:
            for a, b, f in self._generate_parameter_combinations():
                if not self.is_running:
                    break

                self.current_step_number += 1
                if self.observer:
                    self.observer.on_progress(self.current_step_number, self.total_steps)

                # Configure piezo
                self.piezo.configure({
                    "amplitude": a,
                    "bias": b,
                    "frequency": f,
                    "waveform_type": self.config["waveform_type"]
                })

                # Create output folder
                output_folder = self._create_output_folder(i, j, k, a, b, f)

                # Acquire data
                if not self.data_acquisition.acquire_data():
                    raise Exception("Data acquisition failed")

                # Move files
                self.data_acquisition.move_data_files(output_folder)

                # Update step counters
                k += 1
                if k > 9:
                    k = 1
                    j += 1
                if j > 9:
                    j = 1
                    i += 1

            if self.observer:
                self.observer.on_complete()

        except Exception as e:
            self.is_running = False
            if self.observer:
                self.observer.on_error(str(e))
            raise e
            
    def stop_experiment(self) -> None:
        """Stop the experiment."""
        self.is_running = False
        
    def cleanup(self) -> None:
        """Clean up resources."""
        self.piezo.cleanup()
        self.data_acquisition.cleanup() 
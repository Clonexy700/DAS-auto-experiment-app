"""
Experiment controller for parameter sweep experiments.
"""
import os
import itertools
from typing import List, Dict, Any, Optional
from ..core.interfaces import ExperimentController, ExperimentObserver
from ..devices.piezo_controller import PiezoController
from ..acquisition.data_acquisition import DASDataAcquisition

class ParameterSweepController(ExperimentController):
    """Controller for parameter sweep experiments."""

    def __init__(self, config: Dict[str, Any], observer: Optional[ExperimentObserver] = None):
        self.config = config
        self.observer = observer
        self.piezo = PiezoController()
        self.das = DASDataAcquisition()
        self.running = False
        self.current_step = 0
        self.total_steps = self._calculate_total_steps()

    def _calculate_total_steps(self) -> int:
        """Calculate total number of steps in the experiment."""
        amp_steps = len(self._get_range(self.config["amplitude"]))
        bias_steps = len(self._get_range(self.config["bias"]))
        freq_steps = len(self._get_range(self.config["frequency"]))
        
        if self.config.get("parallel_sweep", True):
            # For parallel sweeping, we take the maximum number of steps
            return max(amp_steps, bias_steps, freq_steps)
        else:
            # For sequential sweeping, we multiply the steps
            return amp_steps * bias_steps * freq_steps

    def _get_range(self, param: Dict[str, float]) -> List[float]:
        """Generate range of values for a parameter."""
        start = param["min"]
        stop = param["max"]
        step = param["step"]
        
        if step == 0:
            # For step=0, we use a single value (the max value)
            return [stop]
        
        return [start + i * step for i in range(int((stop - start) / step) + 1)]

    def _generate_parameter_combinations(self) -> List[Dict[str, float]]:
        """Generate parameter combinations for the experiment."""
        amp_range = self._get_range(self.config["amplitude"])
        bias_range = self._get_range(self.config["bias"])
        freq_range = self._get_range(self.config["frequency"])
        
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

    def _create_output_folder(self, params: Dict[str, float]) -> str:
        """Create folder for output data."""
        folder_name = f"{self.config['prefix']}_a{params['amplitude']:.1f}_b{params['bias']:.1f}_f{params['frequency']:.1f}"
        os.makedirs(folder_name, exist_ok=True)
        return folder_name

    def start_experiment(self) -> None:
        """Start the experiment."""
        if self.running:
            return

        self.running = True
        self.current_step = 0
        
        try:
            # Prepare directories
            os.makedirs("data", exist_ok=True)
            
            # Generate parameter combinations
            param_combinations = self._generate_parameter_combinations()
            
            for params in param_combinations:
                if not self.running:
                    break
                
                # Configure piezo
                self.piezo.configure_channels({
                    "wave_type": self.config["waveform_type"],
                    "ch1": {
                        "v": params["amplitude"],
                        "b": params["bias"],
                        "f": params["frequency"]
                    }
                })
                
                # Create output folder
                output_folder = self._create_output_folder(params)
                
                # Acquire data
                self.das.acquire_data(
                    nfiles=self.config["nfiles"],
                    nrefls=self.config["nrefls"],
                    target_folder=output_folder
                )
                
                # Update progress
                self.current_step += 1
                if self.observer:
                    self.observer.on_progress(self.current_step, self.total_steps)
            
            if self.observer:
                self.observer.on_complete()
                
        except Exception as e:
            if self.observer:
                self.observer.on_error(str(e))
        finally:
            self.cleanup()

    def stop_experiment(self) -> None:
        """Stop the experiment."""
        self.running = False

    def cleanup(self) -> None:
        """Clean up resources."""
        self.piezo.cleanup()
        self.das.cleanup()
        self.running = False 
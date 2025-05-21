import os
import shutil
import subprocess
from typing import Dict, Any, Generator, Tuple
from pztlibrary.usart_lib import SerialConfigurator, USARTError

class ExperimentController:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.serial = SerialConfigurator()
        self.is_running = False
        self.current_step = (0, 0, 0)
        self.total_steps = self._calculate_total_steps()
        self.current_step_number = 0
        self._prepare_directories()

    def _calculate_total_steps(self) -> int:
        """Calculate total number of steps in the experiment"""
        amp_steps = int((self.config["amplitude"]["max"] - self.config["amplitude"]["min"]) / 
                       self.config["amplitude"]["step"]) + 1
        bias_steps = int((self.config["bias"]["max"] - self.config["bias"]["min"]) / 
                        self.config["bias"]["step"]) + 1
        freq_steps = int((self.config["frequency"]["max"] - self.config["frequency"]["min"]) / 
                        self.config["frequency"]["step"]) + 1
        return amp_steps * bias_steps * freq_steps

    def _prepare_directories(self):
        """Create necessary directories for the experiment"""
        prefix = self.config["prefix"]
        if not os.path.exists(prefix):
            os.makedirs(prefix)
        if not os.path.exists("refls1"):
            os.makedirs("refls1")

    def _generate_parameter_combinations(self) -> Generator[Tuple[float, float, float], None, None]:
        """Generate all parameter combinations based on min/max/step values"""
        amp_range = self._get_range(self.config["amplitude"])
        bias_range = self._get_range(self.config["bias"])
        freq_range = self._get_range(self.config["frequency"])

        for a in amp_range:
            for b in bias_range:
                for f in freq_range:
                    yield a, b, f

    def _get_range(self, param: Dict[str, float]) -> Generator[float, None, None]:
        """Generate range of values for a parameter"""
        current = param["min"]
        while current <= param["max"]:
            yield current
            current += param["step"]

    def _create_output_folder(self, i: int, j: int, k: int, a: float, b: float, f: float) -> str:
        """Create and return path to output folder for current step"""
        folder_name = f"{i}_{j}_{k}_{self.config['prefix']} f={f} a={a} b={b}"
        folder_path = os.path.join(self.config["prefix"], folder_name)
        os.makedirs(folder_path, exist_ok=True)
        return folder_path

    def _configure_piezo(self, amplitude: float, bias: float, frequency: float):
        """Configure piezo with current parameters"""
        try:
            config = {
                "wave_type": self.config["waveform_type"],
                "ch1": {
                    "v": amplitude,
                    "b": bias,
                    "f": frequency
                },
                "ch2": {"v": 0.0, "b": 0.0, "f": 0.0},  # Disable other channels
                "ch3": {"v": 0.0, "b": 0.0, "f": 0.0}
            }
            self.serial.configure_channels(config)
        except USARTError as e:
            raise Exception(f"Failed to configure piezo: {str(e)}")

    def _acquire_data(self) -> bool:
        """Run data acquisition program"""
        try:
            # Clear the refls1 directory before acquisition
            for file in os.listdir("refls1"):
                os.remove(os.path.join("refls1", file))

            # Run the data acquisition program
            subprocess.check_call([
                "./read_udp_das.exe",
                "--dir", "refls1",
                "--nfiles", str(self.config["nfiles"]),
                "--nrefls", str(self.config["nrefls"])
            ])
            return True
        except subprocess.CalledProcessError as e:
            raise Exception(f"Data acquisition failed: {str(e)}")

    def _move_data_files(self, target_folder: str):
        """Move data files from refls1 to target folder"""
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

    def start_experiment(self):
        """Start the experiment"""
        self.is_running = True
        self.current_step_number = 0
        i, j, k = 1, 1, 1

        try:
            for a, b, f in self._generate_parameter_combinations():
                if not self.is_running:
                    break

                self.current_step_number += 1
                print(f"Step {self.current_step_number}/{self.total_steps}: "
                      f"A={a:.2f}V, B={b:.2f}V, F={f:.2f}Hz")

                # Configure piezo
                self._configure_piezo(a, b, f)

                # Create output folder
                output_folder = self._create_output_folder(i, j, k, a, b, f)

                # Acquire data
                if not self._acquire_data():
                    raise Exception("Data acquisition failed")

                # Move files
                self._move_data_files(output_folder)

                # Update step counters
                k += 1
                if k > 9:
                    k = 1
                    j += 1
                if j > 9:
                    j = 1
                    i += 1

        except Exception as e:
            self.is_running = False
            raise e

    def stop_experiment(self):
        """Stop the experiment"""
        self.is_running = False

    def cleanup(self):
        """Clean up resources"""
        try:
            self.serial.close()
        except Exception:
            pass  # Ignore cleanup errors 
import os
import shutil
import subprocess
import logging
import json
from typing import Dict, Any, Generator, Tuple
from pztlibrary.usart_lib import SerialConfigurator, USARTError

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Console output
        logging.FileHandler('experiment.log')  # File output
    ]
)
logger = logging.getLogger(__name__)

class ExperimentController:
    def __init__(self, config: Dict[str, Any]):
        logger.info("Initializing ExperimentController")
        logger.debug(f"Configuration: {json.dumps(config, indent=2)}")
        self.config = config
        self.serial = SerialConfigurator()
        logger.info("Serial connection initialized")
        self.is_running = False
        self.current_step = (0, 0, 0)
        self.total_steps = self._calculate_total_steps()
        self.current_step_number = 0
        logger.info(f"Total experiment steps: {self.total_steps}")
        self._prepare_directories()

    def _calculate_total_steps(self) -> int:
        """Calculate total number of steps in the experiment"""
        amp_steps = int((self.config["amplitude"]["max"] - self.config["amplitude"]["min"]) / 
                       self.config["amplitude"]["step"]) + 1
        bias_steps = int((self.config["bias"]["max"] - self.config["bias"]["min"]) / 
                        self.config["bias"]["step"]) + 1
        freq_steps = int((self.config["frequency"]["max"] - self.config["frequency"]["min"]) / 
                        self.config["frequency"]["step"]) + 1
        total = amp_steps * bias_steps * freq_steps
        logger.debug(f"Step calculation: amp={amp_steps}, bias={bias_steps}, freq={freq_steps}, total={total}")
        return total

    def _prepare_directories(self):
        """Create necessary directories for the experiment"""
        logger.info("Preparing experiment directories")
        prefix = self.config["prefix"]
        if not os.path.exists(prefix):
            logger.debug(f"Creating prefix directory: {prefix}")
            os.makedirs(prefix)
            logger.info(f"Created directory: {prefix}")
        if not os.path.exists("refls1"):
            logger.debug("Creating refls1 directory")
            os.makedirs("refls1")
            logger.info("Created directory: refls1")

    def _generate_parameter_combinations(self) -> Generator[Tuple[float, float, float], None, None]:
        """Generate all parameter combinations based on min/max/step values"""
        logger.debug("Generating parameter combinations")
        amp_range = self._get_range(self.config["amplitude"])
        bias_range = self._get_range(self.config["bias"])
        freq_range = self._get_range(self.config["frequency"])

        for a in amp_range:
            for b in bias_range:
                for f in freq_range:
                    logger.debug(f"Generated combination: A={a:.2f}V, B={b:.2f}V, F={f:.2f}Hz")
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
        logger.debug(f"Creating output folder: {folder_path}")
        os.makedirs(folder_path, exist_ok=True)
        logger.info(f"Created output folder: {folder_path}")
        return folder_path

    def _configure_piezo(self, amplitude: float, bias: float, frequency: float):
        """Configure piezo with current parameters"""
        logger.info(f"Configuring piezo: A={amplitude:.2f}V, B={bias:.2f}V, F={frequency:.2f}Hz")
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
            logger.debug(f"Piezo configuration: {json.dumps(config, indent=2)}")
            self.serial.configure_channels(config)
            logger.info("Piezo configuration successful")
        except USARTError as e:
            logger.error(f"Piezo configuration failed: {str(e)}")
            raise Exception(f"Failed to configure piezo: {str(e)}")

    def _acquire_data(self) -> bool:
        """Run data acquisition program"""
        logger.info("Starting data acquisition")
        try:
            # Clear the refls1 directory before acquisition
            logger.debug("Clearing refls1 directory")
            files_removed = 0
            for file in os.listdir("refls1"):
                file_path = os.path.join("refls1", file)
                logger.debug(f"Removing file: {file_path}")
                os.remove(file_path)
                files_removed += 1
            logger.info(f"Cleared {files_removed} files from refls1 directory")

            # Run the data acquisition program
            cmd = [
                "./udp_das_cringe.exe",
                "--dir", "refls1",
                "--nfiles", str(self.config["nfiles"]),
                "--nrefls", str(self.config["nrefls"])
            ]
            logger.debug(f"Running acquisition command: {' '.join(cmd)}")
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            stdout, stderr = process.communicate()
            
            if stdout:
                logger.debug(f"Acquisition stdout: {stdout}")
            if stderr:
                logger.warning(f"Acquisition stderr: {stderr}")
            
            if process.returncode != 0:
                logger.error(f"Acquisition failed with return code: {process.returncode}")
                raise subprocess.CalledProcessError(process.returncode, cmd)
                
            logger.info("Data acquisition completed successfully")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Data acquisition failed: {str(e)}")
            raise Exception(f"Data acquisition failed: {str(e)}")

    def _move_data_files(self, target_folder: str):
        """Move data files from refls1 to target folder"""
        logger.info(f"Moving data files to: {target_folder}")
        try:
            files = os.listdir("refls1")
            if not files:
                logger.error("No data files found in refls1 directory")
                raise Exception("No data files were acquired")
            
            logger.debug(f"Found {len(files)} files to move")
            for file in files:
                src = os.path.join("refls1", file)
                dst = os.path.join(target_folder, file)
                logger.debug(f"Moving file: {src} -> {dst}")
                shutil.move(src, dst)
                logger.debug(f"Moved file: {file}")
            logger.info(f"Successfully moved {len(files)} files to {target_folder}")
        except Exception as e:
            logger.error(f"Failed to move data files: {str(e)}")
            raise Exception(f"Failed to move data files: {str(e)}")

    def start_experiment(self):
        """Start the experiment"""
        logger.info("Starting experiment")
        self.is_running = True
        self.current_step_number = 0
        i, j, k = 1, 1, 1

        try:
            for a, b, f in self._generate_parameter_combinations():
                if not self.is_running:
                    logger.info("Experiment stopped by user")
                    break

                self.current_step_number += 1
                logger.info(f"Step {self.current_step_number}/{self.total_steps}: "
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
                logger.debug(f"Updated step counters: i={i}, j={j}, k={k}")

        except Exception as e:
            logger.error(f"Experiment failed: {str(e)}")
            self.is_running = False
            raise e

        logger.info("Experiment completed successfully")

    def stop_experiment(self):
        """Stop the experiment"""
        logger.info("Stopping experiment")
        self.is_running = False
        logger.info("Experiment stopped")

    def cleanup(self):
        """Clean up resources"""
        logger.info("Cleaning up resources")
        try:
            self.serial.close()
            logger.info("Serial connection closed successfully")
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
            pass  # Ignore cleanup errors 
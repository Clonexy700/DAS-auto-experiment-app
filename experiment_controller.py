import os
import shutil
import subprocess
from typing import Dict, Any, Generator, Tuple, List
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
        total_steps = 1
        for ch in ['ch1', 'ch2', 'ch3']:
            if ch in self.config:
                ch_config = self.config[ch]
                # Skip channels with step=0 (fixed value)
                if ch_config['amplitude']['step'] > 0:
                    amp_steps = int((ch_config['amplitude']['max'] - ch_config['amplitude']['min']) / 
                                  ch_config['amplitude']['step']) + 1
                    total_steps *= amp_steps
                if ch_config['bias']['step'] > 0:
                    bias_steps = int((ch_config['bias']['max'] - ch_config['bias']['min']) / 
                                   ch_config['bias']['step']) + 1
                    total_steps *= bias_steps
                if ch_config['frequency']['step'] > 0:
                    freq_steps = int((ch_config['frequency']['max'] - ch_config['frequency']['min']) / 
                                   ch_config['frequency']['step']) + 1
                    total_steps *= freq_steps
        return total_steps

    def _prepare_directories(self):
        """Create necessary directories for the experiment"""
        prefix = self.config["prefix"]
        if not os.path.exists(prefix):
            os.makedirs(prefix)
        if not os.path.exists("refls1"):
            os.makedirs("refls1")

    def _get_range(self, param: Dict[str, float]) -> List[float]:
        """Generate range of values for a parameter"""
        if param['step'] == 0:
            return [param['min']]  # Return single value if step is 0
        values = []
        current = param['min']
        while current <= param['max']:
            values.append(current)
            current += param['step']
        return values

    def _is_channel_active(self, ch_params: Dict[str, Dict[str, float]]) -> bool:
        """Check if a channel has any non-zero parameters and is not fixed at zero"""
        return (ch_params['amplitude']['min'] != 0 or ch_params['amplitude']['max'] != 0 or
                ch_params['bias']['min'] != 0 or ch_params['bias']['max'] != 0 or
                ch_params['frequency']['min'] != 0 or ch_params['frequency']['max'] != 0)

    def _generate_parameter_combinations(self) -> Generator[Dict[str, Dict[str, float]], None, None]:
        """Generate all parameter combinations for all channels"""
        # Get ranges for each parameter of each channel
        channel_ranges = {}
        for ch in ['ch1', 'ch2', 'ch3']:
            if ch in self.config and self._is_channel_active(self.config[ch]):
                ch_config = self.config[ch]
                channel_ranges[ch] = {
                    'amplitude': self._get_range(ch_config['amplitude']),
                    'bias': self._get_range(ch_config['bias']),
                    'frequency': self._get_range(ch_config['frequency'])
                }
            else:
                # For inactive channels, use single zero value
                channel_ranges[ch] = {
                    'amplitude': [0.0],
                    'bias': [0.0],
                    'frequency': [0.0]
                }

        # Generate all combinations
        for a1 in channel_ranges['ch1']['amplitude']:
            for b1 in channel_ranges['ch1']['bias']:
                for f1 in channel_ranges['ch1']['frequency']:
                    for a2 in channel_ranges['ch2']['amplitude']:
                        for b2 in channel_ranges['ch2']['bias']:
                            for f2 in channel_ranges['ch2']['frequency']:
                                for a3 in channel_ranges['ch3']['amplitude']:
                                    for b3 in channel_ranges['ch3']['bias']:
                                        for f3 in channel_ranges['ch3']['frequency']:
                                            yield {
                                                'ch1': {'amplitude': a1, 'bias': b1, 'frequency': f1},
                                                'ch2': {'amplitude': a2, 'bias': b2, 'frequency': f2},
                                                'ch3': {'amplitude': a3, 'bias': b3, 'frequency': f3}
                                            }

    def _create_output_folder(self, i: int, j: int, k: int, params: Dict[str, Dict[str, float]]) -> str:
        """Create and return path to output folder for current step"""
        # Create base folder name
        base_name = f"{i}_{j}_{k}_{self.config['prefix']}"
        base_path = os.path.join(self.config["prefix"], base_name)
        os.makedirs(base_path, exist_ok=True)

        # Create subfolders for each active channel
        for ch in ['ch1', 'ch2', 'ch3']:
            ch_params = params[ch]
            if self._is_channel_active(self.config[ch]):
                ch_folder_name = f"{ch} f={ch_params['frequency']:.1f} a={ch_params['amplitude']:.1f} b={ch_params['bias']:.1f}"
                ch_folder_path = os.path.join(base_path, ch_folder_name)
                os.makedirs(ch_folder_path, exist_ok=True)

        return base_path

    def _configure_piezo(self, params: Dict[str, Dict[str, float]]):
        """Configure piezo with current parameters for all channels"""
        try:
            config = {
                'wave_type': 'Z',  # Default to sine wave
                'ch1': {
                    'v': params['ch1']['amplitude'],
                    'b': params['ch1']['bias'],
                    'f': params['ch1']['frequency']
                },
                'ch2': {
                    'v': params['ch2']['amplitude'],
                    'b': params['ch2']['bias'],
                    'f': params['ch2']['frequency']
                },
                'ch3': {
                    'v': params['ch3']['amplitude'],
                    'b': params['ch3']['bias'],
                    'f': params['ch3']['frequency']
                }
            }
            # Set waveform type for each active channel
            for ch in ['ch1', 'ch2', 'ch3']:
                if self._is_channel_active(self.config[ch]):
                    config['wave_type'] = self.config[ch]['waveform_type']
                    break  # Use first active channel's waveform type

            self.serial.configure_channels(config)
        except USARTError as e:
            self._safe_shutdown()  # Ensure channels are zeroed on error
            raise Exception(f"Failed to configure piezo: {str(e)}")

    def _safe_shutdown(self):
        """Safely shut down all channels"""
        try:
            zero_config = {
                'wave_type': 'Z',
                'ch1': {'v': 0.0, 'b': 0.0, 'f': 0.0},
                'ch2': {'v': 0.0, 'b': 0.0, 'f': 0.0},
                'ch3': {'v': 0.0, 'b': 0.0, 'f': 0.0}
            }
            self.serial.configure_channels(zero_config)
        except Exception:
            pass  # Ignore errors during shutdown

    def _acquire_data(self) -> bool:
        """Run data acquisition program"""
        try:
            # Clear the refls1 directory before acquisition
            for file in os.listdir("refls1"):
                os.remove(os.path.join("refls1", file))

            # Run the data acquisition program
            subprocess.check_call([
                "./udp_das_cringe.exe",
                "--dir", "refls1",
                "--nfiles", str(self.config["nfiles"]),
                "--nrefls", str(self.config["nrefls"])
            ])
            return True
        except subprocess.CalledProcessError as e:
            self._safe_shutdown()  # Ensure channels are zeroed on error
            raise Exception(f"Data acquisition failed: {str(e)}")

    def _move_data_files(self, target_folder: str):
        """Move data files from refls1 to target folder"""
        try:
            files = os.listdir("refls1")
            if not files:
                raise Exception("No data files were acquired")
            
            # Move files to appropriate channel subfolder
            for file in files:
                src = os.path.join("refls1", file)
                # For now, move all files to ch1 folder if it exists, otherwise to base folder
                ch1_folder = os.path.join(target_folder, "ch1 f=0.0 a=0.0 b=0.0")
                if os.path.exists(ch1_folder):
                    dst = os.path.join(ch1_folder, file)
                else:
                    dst = os.path.join(target_folder, file)
                shutil.move(src, dst)
        except Exception as e:
            self._safe_shutdown()  # Ensure channels are zeroed on error
            raise Exception(f"Failed to move data files: {str(e)}")

    def start_experiment(self):
        """Start the experiment"""
        self.is_running = True
        self.current_step_number = 0
        i, j, k = 1, 1, 1

        try:
            for params in self._generate_parameter_combinations():
                if not self.is_running:
                    break

                self.current_step_number += 1
                print(f"\nStep {self.current_step_number}/{self.total_steps}")
                for ch in ['ch1', 'ch2', 'ch3']:
                    if self._is_channel_active(self.config[ch]):
                        ch_params = params[ch]
                        print(f"{ch}: A={ch_params['amplitude']:.2f}V, B={ch_params['bias']:.2f}V, F={ch_params['frequency']:.2f}Hz")

                # Configure piezo for all channels
                self._configure_piezo(params)

                # Create output folder
                output_folder = self._create_output_folder(i, j, k, params)

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
            self._safe_shutdown()  # Ensure channels are zeroed on error
            raise e

    def stop_experiment(self):
        """Stop the experiment"""
        self.is_running = False
        self._safe_shutdown()  # Ensure channels are zeroed on stop

    def cleanup(self):
        """Clean up resources"""
        self._safe_shutdown()  # Ensure channels are zeroed during cleanup
        try:
            self.serial.close()
        except Exception:
            pass  # Ignore cleanup errors 
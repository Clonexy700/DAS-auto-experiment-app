from pztlibrary.usart_lib import SerialConfigurator, load_configuration, USARTError
import json
import time
import threading
import subprocess
import os
import shutil

class PiezoSweepIterator:
    def __init__(self, config_path='config.json'):
        with open(config_path, 'r') as f:
            self.base_config = json.load(f)
        self._reset_state()

    def _reset_state(self):
        self.steps = self.base_config.get('steps', [])
        self.current_step = 0
        self.finished = False
        print(f'[PiezoSweepIterator] Loaded {len(self.steps)} steps from config')
        for i, step in enumerate(self.steps):
            print(f'Step {i+1}:')
            for ch in ['ch1', 'ch2', 'ch3']:
                v = step.get(ch, {}).get('v', 0.0)
                b = step.get(ch, {}).get('b', 0.0)
                f_ = step.get(ch, {}).get('f', 0.0)
                print(f'  {ch}: v={v}, b={b}, f={f_}')

    def __iter__(self):
        self._reset_state()
        return self

    def __next__(self):
        if self.finished or self.current_step >= len(self.steps):
            print('[PiezoSweepIterator] Iteration finished.')
            raise StopIteration
        result = self.steps[self.current_step].copy()
        result['wave_type'] = self.base_config.get('wave_type', 'Z')
        print(f'[PiezoSweepIterator] Executing step {self.current_step + 1}:')
        for ch in ['ch1', 'ch2', 'ch3']:
            v = result.get(ch, {}).get('v', 0.0)
            b = result.get(ch, {}).get('b', 0.0)
            f_ = result.get(ch, {}).get('f', 0.0)
            print(f'  {ch}: v={v}, b={b}, f={f_}')
        self.current_step += 1
        if self.current_step >= len(self.steps):
            self.finished = True
        return result

# Singleton for sweep iterator
_sweep_iter = None

def get_config_for_now():
    global _sweep_iter
    if _sweep_iter is None:
        _sweep_iter = iter(PiezoSweepIterator())
    try:
        return next(_sweep_iter)
    except StopIteration:
        return None

def reset_sweep():
    global _sweep_iter
    _sweep_iter = iter(PiezoSweepIterator())

def initialize_piezo(port: str):
    with SerialConfigurator(port=port) as sc:
        sc.start_monitoring()

def run_piezo_experiment(sleep_time=5.0, config_path='config.json', stop_event=None):
    """Run the piezo sweep experiment, nullify at the end or on error or stop."""
    with open(config_path, 'r') as f:
        base_config = json.load(f)
    port = base_config.get('port', 'com4')
    nullify_config = {
        'ch1': {'v': 0, 'b': 0, 'f': 0},
        'ch2': {'v': 0, 'b': 0, 'f': 0},
        'ch3': {'v': 0, 'b': 0, 'f': 0},
        'wave_type': base_config.get('wave_type', 'Z')
    }
    udp_dir = base_config.get('dir', 'refls1')
    udp_nfiles = str(base_config.get('nfiles', 3))
    udp_nrefls = str(base_config.get('nrefls', 10000))
    prefix = base_config.get('prefix', 'experiment')
    os.makedirs(prefix, exist_ok=True)
    counter = 1
    try:
        with SerialConfigurator(port=port) as sc:
            sc.start_monitoring()
            sweep = PiezoSweepIterator(config_path)
            for config in sweep:
                if stop_event is not None and stop_event.is_set():
                    print('[PiezoSweepIterator] Stopped by user.')
                    sc.configure_channels(nullify_config)
                    time.sleep(5)
                    return
                sc.configure_channels(config)
                time.sleep(sleep_time)
                # Call udp_das_cringe.exe and wait for code 0
                try:
                    subprocess.check_call([
                        './udp_das_cringe.exe',
                        '--dir', udp_dir,
                        '--nfiles', udp_nfiles,
                        '--nrefls', udp_nrefls
                    ])
                except subprocess.CalledProcessError as e:
                    print(f'[PiezoSweepIterator] udp_das_cringe.exe failed with code {e.returncode}')
                    sc.configure_channels(nullify_config)
                    time.sleep(5)
                    return
                # After process, move files to {prefix}/{counter} {prefix} f=..., v=..., b=...
                v = config['ch1']['v']
                b = config['ch1']['b']
                f_ = config['ch1']['f']
                folder_name = f"{counter} {prefix} f={f_}, v={v}, b={b}"
                dest_dir = os.path.join(prefix, folder_name)
                os.makedirs(dest_dir, exist_ok=True)
                # Move all files from udp_dir to dest_dir
                for fname in os.listdir(udp_dir):
                    src_path = os.path.join(udp_dir, fname)
                    dst_path = os.path.join(dest_dir, fname)
                    if os.path.isfile(src_path):
                        shutil.move(src_path, dst_path)
                counter += 1
            # Nullify at the end
            sc.configure_channels(nullify_config)
            time.sleep(5)
            return
    except Exception as e:
        # Nullify on error
        try:
            with SerialConfigurator(port=port) as sc:
                sc.start_monitoring()
                sc.configure_channels(nullify_config)
                time.sleep(5)
                return
        except Exception:
            pass
        raise
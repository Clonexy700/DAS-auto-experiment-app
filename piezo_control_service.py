from pztlibrary.usart_lib import SerialConfigurator, load_configuration, USARTError
import json
import time

class PiezoSweepIterator:
    def __init__(self, config_path='config.json'):
        with open(config_path, 'r') as f:
            self.base_config = json.load(f)
        self._reset_state()

    def _reset_state(self):
        self.state = {}
        self.channel_done = {ch: False for ch in ['ch1', 'ch2', 'ch3']}
        for ch in ['ch1', 'ch2', 'ch3']:
            ch_conf = self.base_config.get(ch, {})
            self.state[ch] = {
                'v': ch_conf.get('max_v', 0.0),
                'b': ch_conf.get('max_b', 0.0),
                'f': ch_conf.get('min_f', 0.0)
            }
        self.finished = False
        print('[PiezoSweepIterator] State reset:', self.state)

    def __iter__(self):
        self._reset_state()
        return self

    def __next__(self):
        if self.finished:
            print('[PiezoSweepIterator] Iteration finished.')
            raise StopIteration
        result = {}
        all_channels_done = True
        print('[PiezoSweepIterator] Yielding config:')
        for ch in ['ch1', 'ch2', 'ch3']:
            ch_conf = self.base_config.get(ch, {})
            v = self.state[ch]['v']
            b = self.state[ch]['b']
            f_ = self.state[ch]['f']
            min_v = ch_conf.get('min_v', 0.0)
            min_b = ch_conf.get('min_b', 0.0)
            min_f = ch_conf.get('min_f', 0.0)
            max_v = ch_conf.get('max_v', 0.0)
            max_b = ch_conf.get('max_b', 0.0)
            max_f = ch_conf.get('max_f', 0.0)
            step_v = ch_conf.get('step_v', 0.0)
            step_b = ch_conf.get('step_b', 0.0)
            step_f = ch_conf.get('step_f', 0.0)
            if self.channel_done[ch]:
                print(f'  {ch}: DONE, holding last value v={v}, b={b}, f={f_}')
                result[ch] = {'v': v, 'b': b, 'f': f_}
                continue
            # Clamp values
            v = max(min_v, min(v, max_v))
            b = max(min_b, min(b, max_b))
            f_ = max(min_f, min(f_, max_f))
            result[ch] = {'v': v, 'b': b, 'f': f_}
            print(f'  {ch}: v={v}, b={b}, f={f_}')
            # If any sweepable parameter is out of range, mark channel as done
            v_done = (step_v > 0 and v < min_v)
            b_done = (step_b > 0 and b < min_b)
            f_done = (step_f > 0 and f_ > max_f)
            if v_done or b_done or f_done:
                self.channel_done[ch] = True
                print(f'    {ch} is now DONE (v_done={v_done}, b_done={b_done}, f_done={f_done})')
            else:
                all_channels_done = False
        result['wave_type'] = self.base_config.get('wave_type', 'Z')
        # Prepare next state for channels not done
        for ch in ['ch1', 'ch2', 'ch3']:
            if self.channel_done[ch]:
                continue
            ch_conf = self.base_config.get(ch, {})
            # v and b: decrement by step, stop if below min
            if ch_conf.get('step_v', 0.0) != 0:
                self.state[ch]['v'] -= ch_conf.get('step_v', 0.0)
            else:
                self.state[ch]['v'] = ch_conf.get('min_v', 0.0)
            if ch_conf.get('step_b', 0.0) != 0:
                self.state[ch]['b'] -= ch_conf.get('step_b', 0.0)
            else:
                self.state[ch]['b'] = ch_conf.get('min_b', 0.0)
            # f: increment by step, stop if above max
            if ch_conf.get('step_f', 0.0) != 0:
                self.state[ch]['f'] += ch_conf.get('step_f', 0.0)
            else:
                self.state[ch]['f'] = ch_conf.get('min_f', 0.0)
        print('[PiezoSweepIterator] Next state:', self.state)
        if all_channels_done:
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

def run_piezo_experiment(sleep_time=1.0, config_path='config.json'):
    """Run the piezo sweep experiment, nullify at the end or on error."""
    with open(config_path, 'r') as f:
        base_config = json.load(f)
    port = base_config.get('port', 'com4')
    nullify_config = {
        'ch1': {'v': 0, 'b': 0, 'f': 0},
        'ch2': {'v': 0, 'b': 0, 'f': 0},
        'ch3': {'v': 0, 'b': 0, 'f': 0},
        'wave_type': base_config.get('wave_type', 'Z')
    }
    try:
        with SerialConfigurator(port=port) as sc:
            sc.start_monitoring()
            sweep = PiezoSweepIterator(config_path)
            for config in sweep:
                sc.configure_channels(config)
                time.sleep(sleep_time)
            # Nullify at the end
            sc.configure_channels(nullify_config)
            time.sleep(3)
            return
    except Exception as e:
        # Nullify on error
        try:
            with SerialConfigurator(port=port) as sc:
                sc.start_monitoring()
                sc.configure_channels(nullify_config)
                time.sleep(3)
                return
        except Exception:
            pass
        raise
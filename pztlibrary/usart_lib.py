"""
Communication Library
---------------------------
Enhanced version supporting multichannel configuration
"""

import json
import serial
import struct
import threading 
from time import sleep
from typing import Dict, List, Optional
from datetime import datetime


class USARTError(Exception):
    """Base class for exceptions"""
    pass


class SerialConfigurator:
    """Handles multichannel serial communication with configuration support"""

    """
    - 'Z': 正弦波 (Sine waveform)

    - 'F': 方波 (Square waveform)

    - 'S': 三角波 (Triangle waveform)

    - 'J': 锯齿波 (Sawtooth waveform)
    """

    VALID_WAVEFORMS = {'Z', 'F', 'S', 'J'}
    CHANNELS = ['ch1', 'ch2', 'ch3']

    def __init__(self, port: str = 'com4',
                 baudrate: int = 115200,
                 timeout: float = 0.000):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.ser = serial.Serial()
        self._init_serial()
        self.rx_thread: Optional[threading.Thread] = None
        self.running = False

    def _init_serial(self):
        """Initialize serial connection with error handling"""
        try:
            self.ser = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout,
                write_timeout=0.0
            )
            if not self.ser.is_open:
                raise USARTError(f"Failed to open {self.port}")

            print(f"Connected to {self.port} @ {self.baudrate} baud")

        except serial.SerialException as e:
            raise USARTError(f"Serial init failed: {str(e)}") from e

    def configure_channels(self, config: dict):
        """EXACT reproduction of original configuration sequence"""
        try:
            # Validate first
            print('1')
            safe_config = config.copy()
            self.validate_config(safe_config)
            print('1')
            wave_type = safe_config.get('wave_type', 'Z').upper()
            print('1')
            # Process all 3 channels
            for ch_idx, ch_key in enumerate(self.CHANNELS):
                print('2')
                ch_config = safe_config[ch_key]
                print('3')
                voltage = ch_config.get('v', 0.0)
                bias = ch_config.get('b', 0.0)
                freq = ch_config.get('f', 0.0)
                try:
                    v_packet = self.send_voltage(voltage, ch_idx)
                    self.ser.write(v_packet)
                    b_packet = self.send_bias(bias, ch_idx)
                    self.ser.write(b_packet)
                    w_packet = self.send_waveform(
                        voltage=voltage,
                        freq=freq,
                        wave_type=wave_type,
                        channel=ch_idx
                    )
                    self.ser.write(w_packet)
                except USARTError as e:
                    print(f"Channel {ch_idx+1} configuration error: {str(e)}")
                    continue

        except Exception as e:
            raise USARTError(f"Configuration failed: {str(e)}") from e

    def send_voltage(self, voltage: float, channel: int):
        v_bytes = self._float_to_bytes(voltage)
        return self._build_packet(
            command=0x0B,
            subcmd=0x00,
            channel=channel,
            data_bytes=v_bytes
        )

    def send_bias(self, bias: float, channel: int):
        """Reproduce exact Move command structure"""
        b_bytes = self._float_to_bytes(bias)
        return self._build_packet(
            command=0x0B,
            subcmd=0x01,
            channel=channel,
            data_bytes=b_bytes
        )

    def send_waveform(self, voltage: float, freq: float, wave_type: str, channel: int):
        """EXACT reproduction of original sendLowSpeedVoltageFreq"""
        # Create 20-byte array initialized with zeros
        payload = [0x00] * 20

        # Set fixed header values
        payload[0] = 0xAA
        payload[1] = 0x01
        payload[2] = 0x14  # Command
        payload[3] = 0x0F  # Subcommand
        payload[4] = 0x00  # Reserved
        payload[5] = channel  # Channel selection

        # Set waveform type
        payload[6] = ord(wave_type.upper())

        # Add voltage bytes at positions 7-10
        v_bytes = self._float_to_bytes(voltage)
        payload[7:11] = v_bytes

        # Add frequency bytes at positions 11-14
        f_bytes = self._float_to_bytes(freq)
        payload[11:15] = f_bytes

        # Calculate XOR checksum for ALL 20 bytes
        xor = 0
        for b in payload:
            xor ^= b

        # Set XOR at position 19
        payload[19] = xor
        send_arr = struct.pack("%dB" % (len(payload)), *payload)  # 解析成16进制 Parse into hexadecimal
        print(send_arr)
        return send_arr

    def _build_packet(self, command: int, subcmd: int, channel: int, data_bytes: list) -> bytes:
        """Fixed packet builder with explicit parameters"""
        header = [
            0xAA,  # Start byte
            0x01,  # Device address
            command,
            subcmd,
            0x00,  # Reserved
            channel
        ]

        packet = header + data_bytes
        packet = packet  # Ensure exactly 10 bytes for XOR calculation

        # Calculate XOR checksum
        xor = 0x00
        for b in packet:
            xor ^= b

        packet.append(xor)
        send_arr = struct.pack("%dB" % (len(packet)), *packet)
        print(send_arr)
        return send_arr

    def _float_to_bytes(self, value: float) -> list:
        """EXACT reproduction of original DataAnla logic"""
        try:
            if value < 0:
                f_abs = abs(value)
                a = int(f_abs)
                byte0 = (a // 256) + 0x80
                byte1 = a % 256
                decimal = int((f_abs - a + 0.00001) * 10000)
            else:
                a = int(value)
                byte0 = a // 256
                byte1 = a % 256
                decimal = int((value - a + 0.00001) * 10000)

            byte2 = decimal // 256
            byte3 = decimal % 256

            return [byte0, byte1, byte2, byte3]
        except Exception as e:
            raise USARTError(f"Float conversion failed: {str(e)}") from e

    def _calculate_xor(self, data: List[int]) -> int:
        """Calculate XOR checksum"""
        print(len(data))
        checksum = 0x00
        for byte in data:
            checksum ^= byte
            print(checksum)
        return checksum

    def validate_config(self, config: Dict):
        """Validate configuration structure"""
        defaults = {
            'v': 0.0,
            'b': 0.0,
            'f': 0.0
        }
        # Ensure all channels exist
        for ch in self.CHANNELS:
            if ch not in config:
                print(f"Warning: Missing {ch}, using defaults values like 'v': 0.0")
                config[ch] = defaults.copy()
            else:
                # Check individual keys
                for key in ['v', 'b', 'f']:
                    if key not in config[ch]:
                        print(f"Warning: {ch} missing '{key}', using 0.0")
                        config[ch][key] = 0.0

        # Handle waveform type
        wave = config.get('wave_type', 'Z').upper()
        if wave not in self.VALID_WAVEFORMS:
            print(f"Invalid waveform '{wave}', defaulting to 'Z', sin waveform")
            config['wave_type'] = 'Z'

    def start_monitoring(self):
        """Start background data monitoring"""
        self.running = True
        self.rx_thread = threading.Thread(target=self._monitor_serial, daemon=True)
        self.rx_thread.start()

    def _monitor_serial(self):
        """Background serial monitoring thread"""
        while self.running and self.ser.is_open:
            if self.ser.in_waiting:
                try:
                    data = self.ser.read_all()
                    print(f"RX: {datetime.now().isoformat()} - {data.hex()}")
                except serial.SerialException:
                    break
            sleep(0.01)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        """Cleanup resources"""
        self.running = False
        if self.ser.is_open:
            self.ser.close()
        return not self.ser.is_open


def load_configuration(path: str) -> Dict:
    """Load and validate configuration file"""
    try:
        with open(path, 'r') as f:
            config = json.load(f)

        if not isinstance(config, dict):
            raise ValueError("Invalid config format")

        return config

    except (FileNotFoundError, json.JSONDecodeError) as e:
        raise USARTError(f"Config load failed: {str(e)}") from e
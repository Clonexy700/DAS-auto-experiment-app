"""
Main window implementation for the DAS Auto Experiment Application.
"""
import os
import logging
import traceback
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                            QLabel, QLineEdit, QComboBox, QPushButton,
                            QMessageBox, QGroupBox, QFormLayout, QSpinBox,
                            QDoubleSpinBox, QProgressBar, QTabWidget)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from ..core.interfaces import ExperimentObserver
from ..config.config_manager import JsonConfigManager
from ..experiment.experiment_controller import ParameterSweepController
from .experiment_thread import ExperimentThread
from pztlibrary import SerialConfigurator

class MainWindow(QMainWindow):
    """Main window for the application."""
    
    def __init__(self):
        try:
            super().__init__()
            logging.info("Initializing MainWindow")
            self.config_manager = JsonConfigManager()
            self.experiment_controller = None
            self.experiment_thread = None
            self.serial_controller = None
            self.init_ui()
            self.setup_connections()
            logging.info("MainWindow initialized successfully")
        except Exception as e:
            error_msg = f"Error initializing MainWindow: {str(e)}\n{traceback.format_exc()}"
            logging.error(error_msg)
            QMessageBox.critical(None, "Error", f"Failed to initialize application: {str(e)}")
            raise

    def init_ui(self):
        """Initialize the user interface."""
        try:
            self.setWindowTitle('Piezo Experiment Controller')
            self.setMinimumWidth(800)

            # Create central widget and main layout
            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            layout = QVBoxLayout(central_widget)

            # Add serial port configuration
            serial_group = QGroupBox("Serial Configuration")
            serial_layout = QFormLayout()
            self.port_input = QLineEdit()
            self.port_input.setPlaceholderText("Enter COM port (e.g., COM4)")
            serial_layout.addRow("Serial Port:", self.port_input)
            serial_group.setLayout(serial_layout)
            layout.addWidget(serial_group)

            # Add DAS configuration
            das_group = QGroupBox("DAS Configuration")
            das_layout = QFormLayout()
            
            # Prefix for experiment files
            self.prefix_input = QLineEdit()
            self.prefix_input.setPlaceholderText("Enter experiment prefix")
            das_layout.addRow("Experiment Prefix:", self.prefix_input)
            
            # Number of files
            self.nfiles_input = QSpinBox()
            self.nfiles_input.setRange(1, 1000)
            self.nfiles_input.setValue(3)
            das_layout.addRow("Number of Files:", self.nfiles_input)
            
            # Number of reflections
            self.nrefls_input = QSpinBox()
            self.nrefls_input.setRange(1, 100000)
            self.nrefls_input.setValue(10000)
            das_layout.addRow("Number of Reflections:", self.nrefls_input)
            
            das_group.setLayout(das_layout)
            layout.addWidget(das_group)

            # Create tab widget for channels
            self.tab_widget = QTabWidget()
            
            # Create tabs for each channel
            self.channel_tabs = []
            for i in range(3):
                channel_tab = QWidget()
                channel_layout = QVBoxLayout(channel_tab)
                
                # Add parameter configuration group for this channel
                param_group = self._create_parameter_group(i + 1)
                channel_layout.addWidget(param_group)
                
                self.channel_tabs.append(channel_tab)
                self.tab_widget.addTab(channel_tab, f"Channel {i + 1}")
            
            layout.addWidget(self.tab_widget)

            # Progress bar
            self.progress_bar = QProgressBar()
            self.progress_bar.setVisible(False)
            layout.addWidget(self.progress_bar)

            # Status label
            self.status_label = QLabel("Ready")
            layout.addWidget(self.status_label)

            # Control buttons
            button_layout = QHBoxLayout()
            self.start_button = QPushButton("Start Experiment")
            self.stop_button = QPushButton("Stop Experiment")
            self.stop_button.setEnabled(False)
            button_layout.addWidget(self.start_button)
            button_layout.addWidget(self.stop_button)
            layout.addLayout(button_layout)

            # Load saved configuration
            self.load_config()
            logging.info("UI initialized successfully")
        except Exception as e:
            error_msg = f"Error initializing UI: {str(e)}\n{traceback.format_exc()}"
            logging.error(error_msg)
            raise

    def _create_parameter_group(self, channel: int) -> QGroupBox:
        """Create the parameter configuration group for a specific channel."""
        param_group = QGroupBox(f"Channel {channel} Parameters")
        param_layout = QFormLayout()

        # Amplitude configuration
        amp_min = QDoubleSpinBox()
        amp_max = QDoubleSpinBox()
        amp_step = QDoubleSpinBox()
        amp_min.setRange(-100, 100)
        amp_max.setRange(-100, 100)
        amp_step.setRange(0, 100)  # Allow step=0
        amp_step.setSingleStep(0.1)
        param_layout.addRow("Amplitude Min (V):", amp_min)
        param_layout.addRow("Amplitude Max (V):", amp_max)
        param_layout.addRow("Amplitude Step (V):", amp_step)

        # Bias configuration
        bias_min = QDoubleSpinBox()
        bias_max = QDoubleSpinBox()
        bias_step = QDoubleSpinBox()
        bias_min.setRange(-100, 100)
        bias_max.setRange(-100, 100)
        bias_step.setRange(0, 100)  # Allow step=0
        bias_step.setSingleStep(0.1)
        param_layout.addRow("Bias Min (V):", bias_min)
        param_layout.addRow("Bias Max (V):", bias_max)
        param_layout.addRow("Bias Step (V):", bias_step)

        # Frequency configuration
        freq_min = QDoubleSpinBox()
        freq_max = QDoubleSpinBox()
        freq_step = QDoubleSpinBox()
        freq_min.setRange(0, 1000)  # Allow 0 Hz to disable channel
        freq_max.setRange(0, 1000)
        freq_step.setRange(0, 100)  # Allow step=0
        freq_step.setSingleStep(0.1)
        param_layout.addRow("Frequency Min (Hz):", freq_min)
        param_layout.addRow("Frequency Max (Hz):", freq_max)
        param_layout.addRow("Frequency Step (Hz):", freq_step)

        # Waveform type
        waveform_type = QComboBox()
        waveform_type.addItems(["Sine (Z)", "Square (F)", "Triangle (S)", "Sawtooth (J)"])
        param_layout.addRow("Waveform Type:", waveform_type)

        # Store widgets for this channel
        setattr(self, f'ch{channel}_amp_min', amp_min)
        setattr(self, f'ch{channel}_amp_max', amp_max)
        setattr(self, f'ch{channel}_amp_step', amp_step)
        setattr(self, f'ch{channel}_bias_min', bias_min)
        setattr(self, f'ch{channel}_bias_max', bias_max)
        setattr(self, f'ch{channel}_bias_step', bias_step)
        setattr(self, f'ch{channel}_freq_min', freq_min)
        setattr(self, f'ch{channel}_freq_max', freq_max)
        setattr(self, f'ch{channel}_freq_step', freq_step)
        setattr(self, f'ch{channel}_waveform', waveform_type)

        param_group.setLayout(param_layout)
        return param_group

    def setup_connections(self):
        """Set up signal connections for automatic saving."""
        try:
            # Connect serial port changes
            self.port_input.textChanged.connect(self.save_current_config)
            
            # Connect DAS configuration changes
            self.prefix_input.textChanged.connect(self.save_current_config)
            self.nfiles_input.valueChanged.connect(self.save_current_config)
            self.nrefls_input.valueChanged.connect(self.save_current_config)

            # Connect all value change signals for each channel
            for ch in range(1, 4):
                for param in ['amp', 'bias', 'freq']:
                    for suffix in ['min', 'max', 'step']:
                        widget = getattr(self, f'ch{ch}_{param}_{suffix}')
                        if isinstance(widget, QSpinBox):
                            widget.valueChanged.connect(self.save_current_config)
                        elif isinstance(widget, QDoubleSpinBox):
                            widget.valueChanged.connect(self.save_current_config)

                # Connect step value changes to handle step=0
                amp_step = getattr(self, f'ch{ch}_amp_step')
                amp_min = getattr(self, f'ch{ch}_amp_min')
                amp_max = getattr(self, f'ch{ch}_amp_max')
                amp_step.valueChanged.connect(lambda v, min_w=amp_min, max_w=amp_max: self.handle_step_change(v, min_w, max_w))

                bias_step = getattr(self, f'ch{ch}_bias_step')
                bias_min = getattr(self, f'ch{ch}_bias_min')
                bias_max = getattr(self, f'ch{ch}_bias_max')
                bias_step.valueChanged.connect(lambda v, min_w=bias_min, max_w=bias_max: self.handle_step_change(v, min_w, max_w))

                freq_step = getattr(self, f'ch{ch}_freq_step')
                freq_min = getattr(self, f'ch{ch}_freq_min')
                freq_max = getattr(self, f'ch{ch}_freq_max')
                freq_step.valueChanged.connect(lambda v, min_w=freq_min, max_w=freq_max: self.handle_step_change(v, min_w, max_w))

                # Connect waveform changes
                waveform = getattr(self, f'ch{ch}_waveform')
                waveform.currentTextChanged.connect(self.save_current_config)

            # Connect experiment control signals
            self.start_button.clicked.connect(self.start_experiment)
            self.stop_button.clicked.connect(self.stop_experiment)
            logging.info("Signal connections set up successfully")
        except Exception as e:
            error_msg = f"Error setting up connections: {str(e)}\n{traceback.format_exc()}"
            logging.error(error_msg)
            raise

    def save_current_config(self):
        """Save current configuration to file."""
        try:
            config = self.get_config()
            self.config_manager.save_config(config)
            logging.debug("Configuration saved successfully")
        except Exception as e:
            error_msg = f"Error saving configuration: {str(e)}\n{traceback.format_exc()}"
            logging.error(error_msg)
            QMessageBox.warning(self, "Warning", f"Failed to save configuration: {str(e)}")

    def load_config(self):
        """Load saved configuration into UI"""
        try:
            config = self.config_manager.config
            
            # Load serial port
            if "serial_port" in config:
                self.port_input.setText(config["serial_port"])

            # Load DAS configuration
            if "prefix" in config:
                self.prefix_input.setText(config["prefix"])
            if "nfiles" in config:
                self.nfiles_input.setValue(config["nfiles"])
            if "nrefls" in config:
                self.nrefls_input.setValue(config["nrefls"])

            # Load channel configurations
            for ch in range(1, 4):
                ch_key = f"ch{ch}"
                if ch_key in config:
                    ch_config = config[ch_key]
                    
                    # Load amplitude
                    if "amplitude" in ch_config:
                        amp = ch_config["amplitude"]
                        getattr(self, f'ch{ch}_amp_min').setValue(amp["min"])
                        getattr(self, f'ch{ch}_amp_max').setValue(amp["max"])
                        getattr(self, f'ch{ch}_amp_step').setValue(amp["step"])
                    
                    # Load bias
                    if "bias" in ch_config:
                        bias = ch_config["bias"]
                        getattr(self, f'ch{ch}_bias_min').setValue(bias["min"])
                        getattr(self, f'ch{ch}_bias_max').setValue(bias["max"])
                        getattr(self, f'ch{ch}_bias_step').setValue(bias["step"])
                    
                    # Load frequency
                    if "frequency" in ch_config:
                        freq = ch_config["frequency"]
                        getattr(self, f'ch{ch}_freq_min').setValue(freq["min"])
                        getattr(self, f'ch{ch}_freq_max').setValue(freq["max"])
                        getattr(self, f'ch{ch}_freq_step').setValue(freq["step"])
                    
                    # Load waveform
                    if "waveform_type" in ch_config:
                        waveform = getattr(self, f'ch{ch}_waveform')
                        waveform.setCurrentText(f"{ch_config['waveform_type']} ({ch_config['waveform_type']})")
            
            logging.info("Configuration loaded successfully")
        except Exception as e:
            error_msg = f"Error loading configuration: {str(e)}\n{traceback.format_exc()}"
            logging.error(error_msg)
            QMessageBox.warning(self, "Warning", f"Failed to load configuration: {str(e)}")

    def get_config(self):
        """Get current configuration from UI"""
        try:
            config = {
                "serial_port": self.port_input.text(),
                "parallel_sweep": True,
                "prefix": self.prefix_input.text(),
                "nfiles": self.nfiles_input.value(),
                "nrefls": self.nrefls_input.value()
            }

            # Get configuration for each channel
            for ch in range(1, 4):
                ch_key = f"ch{ch}"
                config[ch_key] = {
                    "amplitude": {
                        "min": getattr(self, f'ch{ch}_amp_min').value(),
                        "max": getattr(self, f'ch{ch}_amp_max').value(),
                        "step": getattr(self, f'ch{ch}_amp_step').value()
                    },
                    "bias": {
                        "min": getattr(self, f'ch{ch}_bias_min').value(),
                        "max": getattr(self, f'ch{ch}_bias_max').value(),
                        "step": getattr(self, f'ch{ch}_bias_step').value()
                    },
                    "frequency": {
                        "min": getattr(self, f'ch{ch}_freq_min').value(),
                        "max": getattr(self, f'ch{ch}_freq_max').value(),
                        "step": getattr(self, f'ch{ch}_freq_step').value()
                    },
                    "waveform_type": getattr(self, f'ch{ch}_waveform').currentText()[0]
                }

            return config
        except Exception as e:
            error_msg = f"Error getting configuration: {str(e)}\n{traceback.format_exc()}"
            logging.error(error_msg)
            raise

    def handle_step_change(self, step_value: float, min_widget: QDoubleSpinBox, max_widget: QDoubleSpinBox):
        """Handle step value changes, auto-copy max to min when step=0."""
        try:
            if step_value == 0:
                min_widget.setValue(max_widget.value())
            self.save_current_config()
        except Exception as e:
            error_msg = f"Error handling step change: {str(e)}\n{traceback.format_exc()}"
            logging.error(error_msg)
            QMessageBox.warning(self, "Warning", f"Failed to handle step change: {str(e)}")

    def ensure_safe_shutdown(self):
        """Ensure all channels are set to 0 in case of any error or shutdown."""
        try:
            if self.serial_controller:
                # Create zero configuration for all channels
                zero_config = {
                    'wave_type': 'Z',
                    'ch1': {'v': 0.0, 'b': 0.0, 'f': 0.0},
                    'ch2': {'v': 0.0, 'b': 0.0, 'f': 0.0},
                    'ch3': {'v': 0.0, 'b': 0.0, 'f': 0.0}
                }
                try:
                    self.serial_controller.configure_channels(zero_config)
                    logging.info("Successfully set all channels to zero")
                except Exception as e:
                    logging.error(f"Failed to set channels to zero: {str(e)}")
                finally:
                    self.serial_controller.close()
                    self.serial_controller = None
        except Exception as e:
            logging.error(f"Error during safe shutdown: {str(e)}")

    def start_experiment(self):
        """Start the experiment"""
        try:
            config = self.get_config()
            if not self.config_manager.validate_config(config):
                QMessageBox.critical(self, "Error", "Invalid configuration")
                return

            # Validate serial port
            if not config["serial_port"]:
                QMessageBox.critical(self, "Error", "Please enter a serial port")
                return

            # Check if read_udp_das.exe exists
            exe_path = os.path.join("Alinx C Interrogate programm tool", "read_udp_das.exe")
            if not os.path.exists(exe_path):
                QMessageBox.critical(self, "Error", f"read_udp_das.exe not found at {exe_path}")
                return

            # Copy executable if needed
            if not os.path.exists("read_udp_das.exe"):
                try:
                    import shutil
                    shutil.copy2(exe_path, "read_udp_das.exe")
                except Exception as e:
                    error_msg = f"Failed to copy read_udp_das.exe: {str(e)}\n{traceback.format_exc()}"
                    logging.error(error_msg)
                    QMessageBox.critical(self, "Error", error_msg)
                    return

            # Initialize serial controller
            try:
                self.serial_controller = SerialConfigurator(port=config["serial_port"])
            except Exception as e:
                error_msg = f"Failed to initialize serial controller: {str(e)}"
                logging.error(error_msg)
                QMessageBox.critical(self, "Error", error_msg)
                return

            self.experiment_controller = ParameterSweepController(config, self)
            self.experiment_thread = ExperimentThread(self.experiment_controller)
            self.experiment_thread.error.connect(self.handle_error)
            self.experiment_thread.finished.connect(self.experiment_finished)
            self.experiment_thread.start()

            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            self.status_label.setText("Experiment running...")
            logging.info("Experiment started successfully")
        except Exception as e:
            error_msg = f"Error starting experiment: {str(e)}\n{traceback.format_exc()}"
            logging.error(error_msg)
            QMessageBox.critical(self, "Error", f"Failed to start experiment: {str(e)}")
            self.ensure_safe_shutdown()

    def stop_experiment(self):
        """Stop the experiment"""
        try:
            if self.experiment_controller:
                self.experiment_controller.stop_experiment()
                self.stop_button.setEnabled(False)
                self.status_label.setText("Stopping experiment...")
                logging.info("Experiment stop requested")
        except Exception as e:
            error_msg = f"Error stopping experiment: {str(e)}\n{traceback.format_exc()}"
            logging.error(error_msg)
            QMessageBox.critical(self, "Error", f"Failed to stop experiment: {str(e)}")
            self.ensure_safe_shutdown()

    def handle_error(self, error_msg):
        """Handle experiment error"""
        logging.error(f"Experiment error: {error_msg}")
        QMessageBox.critical(self, "Error", f"Experiment failed: {error_msg}")
        self.ensure_safe_shutdown()
        self.experiment_finished()

    def experiment_finished(self):
        """Handle experiment completion"""
        try:
            if self.experiment_controller:
                self.experiment_controller.cleanup()
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.progress_bar.setVisible(False)
            self.status_label.setText("Ready")
            logging.info("Experiment finished")
        except Exception as e:
            error_msg = f"Error handling experiment completion: {str(e)}\n{traceback.format_exc()}"
            logging.error(error_msg)
            QMessageBox.critical(self, "Error", f"Error during experiment completion: {str(e)}")
            self.ensure_safe_shutdown()

    def on_progress(self, current: int, total: int):
        """Handle progress updates."""
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)

    def on_error(self, error: str):
        """Handle error updates."""
        self.handle_error(error)

    def on_complete(self):
        """Handle experiment completion."""
        self.experiment_finished()

    def closeEvent(self, event):
        """Handle window close"""
        try:
            if self.experiment_controller:
                reply = QMessageBox.question(
                    self, 'Confirm Exit',
                    "Experiment is running. Are you sure you want to exit?",
                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No
                )
                if reply == QMessageBox.Yes:
                    self.experiment_controller.stop_experiment()
                    self.experiment_controller.cleanup()
                    self.ensure_safe_shutdown()
                    event.accept()
                else:
                    event.ignore()
            else:
                self.ensure_safe_shutdown()
                event.accept()
            logging.info("Application closed")
        except Exception as e:
            error_msg = f"Error during application close: {str(e)}\n{traceback.format_exc()}"
            logging.error(error_msg)
            self.ensure_safe_shutdown()
            event.accept()  # Force close on error 
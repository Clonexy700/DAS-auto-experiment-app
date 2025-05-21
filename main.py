import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                            QHBoxLayout, QLabel, QLineEdit, QComboBox,
                            QPushButton, QFileDialog, QMessageBox, QGroupBox,
                            QFormLayout, QSpinBox, QDoubleSpinBox, QProgressBar)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from src.config.config_manager import JsonConfigManager
from src.experiment.experiment_controller import ParameterSweepController

class ExperimentThread(QThread):
    error = pyqtSignal(str)
    progress = pyqtSignal(int, int)  # current, total
    finished = pyqtSignal()

    def __init__(self, controller):
        super().__init__()
        self.controller = controller

    def run(self):
        try:
            self.controller.start_experiment()
        except Exception as e:
            self.error.emit(str(e))
        finally:
            self.finished.emit()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config_manager = JsonConfigManager()
        self.experiment_controller = None
        self.experiment_thread = None
        self.init_ui()
        self.setup_connections()

    def init_ui(self):
        self.setWindowTitle('Piezo Experiment Controller')
        self.setMinimumWidth(600)

        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Parameter configuration group
        param_group = QGroupBox("Parameter Configuration")
        param_layout = QFormLayout()

        # Amplitude configuration
        self.amp_min = QDoubleSpinBox()
        self.amp_max = QDoubleSpinBox()
        self.amp_step = QDoubleSpinBox()
        self.amp_min.setRange(-100, 100)
        self.amp_max.setRange(-100, 100)
        self.amp_step.setRange(0, 100)
        self.amp_step.setSingleStep(0.1)
        param_layout.addRow("Amplitude Min (V):", self.amp_min)
        param_layout.addRow("Amplitude Max (V):", self.amp_max)
        param_layout.addRow("Amplitude Step (V):", self.amp_step)

        # Bias configuration
        self.bias_min = QDoubleSpinBox()
        self.bias_max = QDoubleSpinBox()
        self.bias_step = QDoubleSpinBox()
        self.bias_min.setRange(-100, 100)
        self.bias_max.setRange(-100, 100)
        self.bias_step.setRange(0, 100)
        self.bias_step.setSingleStep(0.1)
        param_layout.addRow("Bias Min (V):", self.bias_min)
        param_layout.addRow("Bias Max (V):", self.bias_max)
        param_layout.addRow("Bias Step (V):", self.bias_step)

        # Frequency configuration
        self.freq_min = QDoubleSpinBox()
        self.freq_max = QDoubleSpinBox()
        self.freq_step = QDoubleSpinBox()
        self.freq_min.setRange(0.1, 1000)
        self.freq_max.setRange(0.1, 1000)
        self.freq_step.setRange(0, 100)
        self.freq_step.setSingleStep(0.1)
        param_layout.addRow("Frequency Min (Hz):", self.freq_min)
        param_layout.addRow("Frequency Max (Hz):", self.freq_max)
        param_layout.addRow("Frequency Step (Hz):", self.freq_step)

        # Waveform type
        self.waveform_type = QComboBox()
        self.waveform_type.addItems(["Sine (Z)", "Square (F)", "Triangle (S)", "Sawtooth (J)"])
        param_layout.addRow("Waveform Type:", self.waveform_type)

        # Prefix
        self.prefix = QLineEdit()
        param_layout.addRow("Prefix:", self.prefix)

        # Data acquisition parameters
        self.nfiles = QSpinBox()
        self.nfiles.setRange(1, 100)
        self.nrefls = QSpinBox()
        self.nrefls.setRange(1000, 100000)
        self.nrefls.setSingleStep(1000)
        param_layout.addRow("Number of Files:", self.nfiles)
        param_layout.addRow("Number of Reflectograms:", self.nrefls)

        param_group.setLayout(param_layout)
        layout.addWidget(param_group)

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

    def setup_connections(self):
        """Set up signal connections for automatic saving."""
        # Connect all value change signals
        for widget in [self.amp_min, self.amp_max, self.amp_step,
                      self.bias_min, self.bias_max, self.bias_step,
                      self.freq_min, self.freq_max, self.freq_step,
                      self.nfiles, self.nrefls]:
            if isinstance(widget, QSpinBox):
                widget.valueChanged.connect(self.save_current_config)
            elif isinstance(widget, QDoubleSpinBox):
                widget.valueChanged.connect(self.save_current_config)

        # Connect step value changes to handle step=0
        self.amp_step.valueChanged.connect(lambda v: self.handle_step_change(v, self.amp_min, self.amp_max))
        self.bias_step.valueChanged.connect(lambda v: self.handle_step_change(v, self.bias_min, self.bias_max))
        self.freq_step.valueChanged.connect(lambda v: self.handle_step_change(v, self.freq_min, self.freq_max))

        # Connect text change signals
        self.prefix.textChanged.connect(self.save_current_config)
        self.waveform_type.currentTextChanged.connect(self.save_current_config)

        # Connect experiment control signals
        self.start_button.clicked.connect(self.start_experiment)
        self.stop_button.clicked.connect(self.stop_experiment)

    def save_current_config(self):
        """Save current configuration to file."""
        try:
            config = self.get_config()
            self.config_manager.save_config(config)
        except Exception as e:
            print(f"Error saving configuration: {e}")

    def load_config(self):
        """Load saved configuration into UI"""
        config = self.config_manager.config
        self.amp_min.setValue(config["amplitude"]["min"])
        self.amp_max.setValue(config["amplitude"]["max"])
        self.amp_step.setValue(config["amplitude"]["step"])
        self.bias_min.setValue(config["bias"]["min"])
        self.bias_max.setValue(config["bias"]["max"])
        self.bias_step.setValue(config["bias"]["step"])
        self.freq_min.setValue(config["frequency"]["min"])
        self.freq_max.setValue(config["frequency"]["max"])
        self.freq_step.setValue(config["frequency"]["step"])
        self.waveform_type.setCurrentText(f"{config['waveform_type']} ({config['waveform_type']})")
        self.prefix.setText(config["prefix"])
        self.nfiles.setValue(config["nfiles"])
        self.nrefls.setValue(config["nrefls"])

    def get_config(self):
        """Get current configuration from UI"""
        return {
            "amplitude": {
                "min": self.amp_min.value(),
                "max": self.amp_max.value(),
                "step": self.amp_step.value()
            },
            "bias": {
                "min": self.bias_min.value(),
                "max": self.bias_max.value(),
                "step": self.bias_step.value()
            },
            "frequency": {
                "min": self.freq_min.value(),
                "max": self.freq_max.value(),
                "step": self.freq_step.value()
            },
            "waveform_type": self.waveform_type.currentText()[0],
            "prefix": self.prefix.text(),
            "nfiles": self.nfiles.value(),
            "nrefls": self.nrefls.value(),
            "parallel_sweep": True
        }

    def start_experiment(self):
        """Start the experiment"""
        config = self.get_config()
        if not self.config_manager.validate_config(config):
            QMessageBox.critical(self, "Error", "Invalid configuration")
            return

        # Validate prefix
        if not config["prefix"]:
            QMessageBox.critical(self, "Error", "Prefix cannot be empty")
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
                QMessageBox.critical(self, "Error", f"Failed to copy read_udp_das.exe: {str(e)}")
                return

        self.experiment_controller = ParameterSweepController(config)
        self.experiment_thread = ExperimentThread(self.experiment_controller)
        self.experiment_thread.error.connect(self.handle_error)
        self.experiment_thread.finished.connect(self.experiment_finished)
        self.experiment_thread.start()

        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("Experiment running...")

    def stop_experiment(self):
        """Stop the experiment"""
        if self.experiment_controller:
            self.experiment_controller.stop_experiment()
            self.stop_button.setEnabled(False)
            self.status_label.setText("Stopping experiment...")

    def handle_error(self, error_msg):
        """Handle experiment error"""
        QMessageBox.critical(self, "Error", f"Experiment failed: {error_msg}")
        self.experiment_finished()

    def experiment_finished(self):
        """Handle experiment completion"""
        if self.experiment_controller:
            self.experiment_controller.cleanup()
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.status_label.setText("Ready")

    def closeEvent(self, event):
        """Handle window close"""
        if self.experiment_controller:
            reply = QMessageBox.question(
                self, 'Confirm Exit',
                "Experiment is running. Are you sure you want to exit?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.experiment_controller.stop_experiment()
                self.experiment_controller.cleanup()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

    def handle_step_change(self, step_value: float, min_widget: QDoubleSpinBox, max_widget: QDoubleSpinBox):
        """Handle step value changes, auto-copy max to min when step=0."""
        if step_value == 0:
            min_widget.setValue(max_widget.value())
        self.save_current_config()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())



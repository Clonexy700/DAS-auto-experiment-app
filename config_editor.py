import sys
import json
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QDoubleSpinBox, QComboBox, 
                            QGroupBox, QLineEdit, QGridLayout, QFrame, QScrollArea, QPushButton)
from PyQt5.QtCore import Qt, QSettings, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QIcon
from piezo_control_service import run_piezo_experiment

class ExperimentThread(QThread):
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, sleep_time=1.0):
        super().__init__()
        self.sleep_time = sleep_time

    def run(self):
        try:
            run_piezo_experiment(sleep_time=self.sleep_time)
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))

class ConfigEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DAS Configuration Editor")
        self.setWindowIcon(QIcon.fromTheme("preferences-system"))
        self.settings = QSettings("DAS", "ConfigEditor")
        self.default_font = QFont("Segoe UI", 12)
        self.header_font = QFont("Segoe UI", 14, QFont.Bold)
        self.section_font = QFont("Segoe UI", 12, QFont.Bold)

        # Extended dark/gray modern stylesheet
        self.setStyleSheet('''
            QMainWindow, QWidget {
                background: #23272e;
            }
            QScrollArea {
                background: #23272e;
                border: none;
            }
            QGroupBox {
                border: 1.5px solid #3a3f4b;
                border-radius: 16px;
                margin-top: 18px;
                background: #2d313a;
                box-shadow: 0 2px 8px rgba(0,0,0,0.10);
            }
            QGroupBox:title {
                subcontrol-origin: margin;
                left: 16px;
                top: 8px;
                padding: 0 4px 0 4px;
                color: #e0e6f0;
                font-size: 15px;
                font-weight: bold;
            }
            QLabel {
                font-size: 14px;
                color: #e0e6f0;
            }
            QDoubleSpinBox, QLineEdit, QComboBox {
                font-size: 15px;
                min-height: 38px;
                border-radius: 8px;
                border: 1.5px solid #3a3f4b;
                background: #23272e;
                padding: 4px 12px;
                color: #f8fafc;
                selection-background-color: #4f8cff;
            }
            QDoubleSpinBox:focus, QLineEdit:focus, QComboBox:focus {
                border: 1.5px solid #4f8cff;
                background: #232e3c;
            }
            QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
                width: 24px;
                height: 24px;
                background: #23272e;
                border-radius: 6px;
            }
            QDoubleSpinBox::up-arrow, QDoubleSpinBox::down-arrow {
                border: none;
                background: none;
            }
            QComboBox QAbstractItemView {
                border-radius: 8px;
                background: #23272e;
                selection-background-color: #4f8cff;
                color: #f8fafc;
                border: 1.5px solid #3a3f4b;
            }
            QComboBox::drop-down {
                background: #23272e;
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border: none;
            }
            QFrame#TopBar {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4f8cff, stop:1 #232e3c);
                border-radius: 12px;
                min-height: 54px;
                margin-bottom: 18px;
            }
            QLabel#TitleLabel {
                color: white;
                font-size: 22px;
                font-weight: bold;
                padding-left: 18px;
            }
            QScrollBar:vertical, QScrollBar:horizontal {
                background: #23272e;
                width: 16px;
                height: 16px;
                margin: 16px 0 16px 0;
                border-radius: 8px;
            }
            QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
                background: #4f8cff;
                min-height: 32px;
                min-width: 32px;
                border-radius: 8px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                background: none;
                height: 0px;
                width: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical,
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                background: none;
            }
            QToolTip {
                background-color: #232e3c;
                color: #f8fafc;
                border: 1.5px solid #4f8cff;
                border-radius: 8px;
                font-size: 14px;
            }
            QPushButton {
                background: #4f8cff;
                color: white;
                border-radius: 8px;
                font-size: 16px;
                min-height: 40px;
                padding: 8px 24px;
            }
            QPushButton:disabled {
                background: #444a5a;
                color: #888;
            }
        ''')

        # Main scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        self.setCentralWidget(scroll)

        main_widget = QWidget()
        scroll.setWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setSpacing(18)
        main_layout.setContentsMargins(24, 24, 24, 24)

        # Top bar with title
        top_bar = QFrame()
        top_bar.setObjectName("TopBar")
        top_bar_layout = QHBoxLayout(top_bar)
        top_bar_layout.setContentsMargins(0, 0, 0, 0)
        title_label = QLabel("DAS Configuration Editor")
        title_label.setObjectName("TitleLabel")
        title_label.setFont(QFont("Segoe UI", 22, QFont.Bold))
        top_bar_layout.addWidget(title_label)
        top_bar_layout.addStretch()
        main_layout.addWidget(top_bar)

        self.channel_widgets = {}
        for ch in ['ch1', 'ch2', 'ch3']:
            group = self.create_channel_group(ch)
            main_layout.addWidget(group)

        # Wave type selection
        wave_group = QGroupBox("Wave Type")
        wave_group.setFont(self.section_font)
        wave_layout = QHBoxLayout()
        wave_layout.setSpacing(10)
        wave_layout.setContentsMargins(18, 12, 18, 12)
        self.wave_combo = QComboBox()
        self.wave_combo.setFont(self.default_font)
        self.wave_combo.setMinimumHeight(38)
        self.wave_combo.setFixedWidth(140)
        self.wave_combo.addItems(['Z', 'S', 'T'])
        self.wave_combo.setToolTip("Select the waveform type for the experiment.")
        self.wave_combo.currentTextChanged.connect(self.save_config)
        wave_layout.addWidget(QLabel("Type:"))
        wave_layout.addWidget(self.wave_combo)
        wave_layout.addStretch()
        wave_group.setLayout(wave_layout)
        main_layout.addWidget(wave_group)

        # Prefix input
        prefix_group = QGroupBox("Prefix")
        prefix_group.setFont(self.section_font)
        prefix_layout = QHBoxLayout()
        prefix_layout.setSpacing(10)
        prefix_layout.setContentsMargins(18, 12, 18, 12)
        self.prefix_input = QLineEdit()
        self.prefix_input.setFont(self.default_font)
        self.prefix_input.setMinimumHeight(38)
        self.prefix_input.setFixedWidth(260)
        self.prefix_input.setToolTip("Prefix for experiment file names.")
        self.prefix_input.textChanged.connect(self.save_config)
        prefix_layout.addWidget(QLabel("Prefix:"))
        prefix_layout.addWidget(self.prefix_input)
        prefix_layout.addStretch()
        prefix_group.setLayout(prefix_layout)
        main_layout.addWidget(prefix_group)

        # Port input
        port_group = QGroupBox("Port")
        port_group.setFont(self.section_font)
        port_layout = QHBoxLayout()
        port_layout.setSpacing(10)
        port_layout.setContentsMargins(18, 12, 18, 12)
        self.port_input = QLineEdit()
        self.port_input.setFont(self.default_font)
        self.port_input.setMinimumHeight(38)
        self.port_input.setFixedWidth(180)
        self.port_input.setToolTip("Serial port for the experiment (e.g., COM4, /dev/ttyUSB0)")
        self.port_input.textChanged.connect(self.save_config)
        port_layout.addWidget(QLabel("Port:"))
        port_layout.addWidget(self.port_input)
        port_layout.addStretch()
        port_group.setLayout(port_layout)
        main_layout.addWidget(port_group)

        # Start Experiment button and status
        button_layout = QHBoxLayout()
        self.start_button = QPushButton("Start Experiment")
        self.start_button.clicked.connect(self.on_start_experiment)
        self.status_label = QLabel("")
        self.status_label.setFont(self.default_font)
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.status_label)
        button_layout.addStretch()
        main_layout.addLayout(button_layout)

        main_layout.addStretch(1)
        self.load_config()
        self.resize(900, 1050)

    def create_channel_group(self, channel):
        group = QGroupBox(f"Channel {channel[-1]}")
        group.setFont(self.section_font)
        vbox = QVBoxLayout()
        vbox.setSpacing(12)
        vbox.setContentsMargins(16, 12, 16, 12)
        params = {}
        for param, param_label, tooltip in zip(
            ['v', 'b', 'f'],
            ['Voltage (V)', 'Bias (B)', 'Frequency (F)'],
            ["Voltage sweep settings.", "Bias sweep settings.", "Frequency sweep settings."]):
            param_group = QGroupBox(param_label)
            param_group.setFont(self.default_font)
            param_group.setToolTip(tooltip)
            grid = QGridLayout()
            grid.setSpacing(10)
            grid.setContentsMargins(10, 10, 10, 10)
            for i, (limit, limit_label, limit_tip) in enumerate([
                ('min', 'Min', 'Minimum value'),
                ('max', 'Max', 'Maximum value'),
                ('step', 'Step', 'Step size (0 = fixed value)')]):
                label = QLabel(limit_label+":")
                label.setFont(self.default_font)
                label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                grid.addWidget(label, 0, i)
                widget = QDoubleSpinBox()
                widget.setFont(self.default_font)
                widget.setMinimumHeight(38)
                widget.setFixedWidth(130)
                widget.setRange(-1000, 1000)
                widget.setDecimals(3)
                widget.setSingleStep(0.1)
                widget.setToolTip(f"{limit_tip} for {param_label.lower()}.")
                if limit == 'step':
                    widget.valueChanged.connect(lambda value, ch=channel, p=param: self.on_step_changed(ch, p, value))
                widget.valueChanged.connect(self.save_config)
                grid.addWidget(widget, 1, i)
                params[f"{limit}_{param}"] = widget
            param_group.setLayout(grid)
            vbox.addWidget(param_group)
        group.setLayout(vbox)
        self.channel_widgets[channel] = params
        return group

    def on_step_changed(self, channel, param, value):
        if value == 0:
            widgets = self.channel_widgets[channel]
            min_widget = widgets[f"min_{param}"]
            max_widget = widgets[f"max_{param}"]
            max_widget.setValue(min_widget.value())

    def load_config(self):
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
            for channel, widgets in self.channel_widgets.items():
                if channel in config:
                    for param in ['v', 'b', 'f']:
                        for limit in ['min', 'max', 'step']:
                            key = f"{limit}_{param}"
                            if key in config[channel]:
                                widgets[key].setValue(config[channel][key])
            if 'wave_type' in config:
                self.wave_combo.setCurrentText(config['wave_type'])
            if 'prefix' in config:
                self.prefix_input.setText(config['prefix'])
            if 'port' in config:
                self.port_input.setText(config['port'])
        except Exception as e:
            print(f"Error loading configuration: {e}")

    def save_config(self):
        config = {}
        for channel, widgets in self.channel_widgets.items():
            config[channel] = {}
            for param in ['v', 'b', 'f']:
                for limit in ['min', 'max', 'step']:
                    key = f"{limit}_{param}"
                    config[channel][key] = widgets[key].value()
        config['wave_type'] = self.wave_combo.currentText()
        config['prefix'] = self.prefix_input.text()
        config['port'] = self.port_input.text()
        try:
            with open('config.json', 'w') as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            print(f"Error saving configuration: {e}")

    def on_start_experiment(self):
        self.start_button.setEnabled(False)
        self.status_label.setText("Running...")
        self.thread = ExperimentThread(sleep_time=1.0)
        self.thread.finished.connect(self.on_experiment_finished)
        self.thread.error.connect(self.on_experiment_error)
        self.thread.start()

    def on_experiment_finished(self):
        self.status_label.setText("Finished")
        self.start_button.setEnabled(True)

    def on_experiment_error(self, msg):
        self.status_label.setText(f"Error: {msg}")
        self.start_button.setEnabled(True)

# Force Fusion style for full dark theme support
if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = ConfigEditor()
    window.show()
    sys.exit(app.exec_())
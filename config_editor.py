import sys
import json
import threading
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QDoubleSpinBox, QComboBox, 
                            QGroupBox, QLineEdit, QGridLayout, QFrame, QScrollArea, QPushButton, QFormLayout,
                            QTextEdit, QTableWidget, QTableWidgetItem, QAbstractItemView, QHeaderView, QSizePolicy)
from PyQt5.QtCore import Qt, QSettings, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QIcon, QColor
from piezo_control_service import run_piezo_experiment
import os

class ExperimentThread(QThread):
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, sleep_time=1.0, stop_event=None):
        super().__init__()
        self.sleep_time = sleep_time
        self.stop_event = stop_event

    def run(self):
        try:
            run_piezo_experiment(sleep_time=self.sleep_time, stop_event=self.stop_event)
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))

class ConfigEditor(QMainWindow):
    INIT_KEYS = ["Ng", "line_length", "len_udp_pack", "freq_send_data", "pulse_width"]

    STEP_COLUMNS = [
        ("step", "Step"),
        ("ch1_v", "Ch1 V"), ("ch1_b", "Ch1 B"), ("ch1_f", "Ch1 F"),
        ("spacer1", ""),
        ("ch2_v", "Ch2 V"), ("ch2_b", "Ch2 B"), ("ch2_f", "Ch2 F"),
        ("spacer2", ""),
        ("ch3_v", "Ch3 V"), ("ch3_b", "Ch3 B"), ("ch3_f", "Ch3 F")
    ]

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

        # Subtle dark header instead of blue bar
        header_frame = QFrame()
        header_frame.setStyleSheet('''
            QFrame { background: #23272e; border-radius: 12px; min-height: 54px; margin-bottom: 18px; }
        ''')
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 0, 0, 0)
        title_label = QLabel("DAS Configuration Editor")
        title_label.setFont(QFont("Segoe UI", 22, QFont.Bold))
        title_label.setStyleSheet('color: #e0e6f0; padding-left: 18px;')
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        main_layout.addWidget(header_frame)

        self.channel_widgets = {}  # No longer used for per-channel param editing
        # --- Step Table ---
        step_group = QGroupBox("Experiment Steps")
        step_group.setFont(self.section_font)
        step_layout = QVBoxLayout()
        step_layout.setSpacing(10)
        step_layout.setContentsMargins(12, 12, 12, 12)
        # Buttons for add/remove/move (now above table)
        btn_layout = QHBoxLayout()
        self.add_step_btn = QPushButton("Add Step")
        self.add_step_btn.clicked.connect(self.add_step)
        self.remove_step_btn = QPushButton("Remove Step")
        self.remove_step_btn.clicked.connect(self.remove_step)
        self.move_up_btn = QPushButton("Move Up")
        self.move_up_btn.clicked.connect(self.move_step_up)
        self.move_down_btn = QPushButton("Move Down")
        self.move_down_btn.clicked.connect(self.move_step_down)
        btn_layout.addWidget(self.add_step_btn)
        btn_layout.addWidget(self.remove_step_btn)
        btn_layout.addWidget(self.move_up_btn)
        btn_layout.addWidget(self.move_down_btn)
        btn_layout.addStretch()
        step_layout.addLayout(btn_layout)
        # Step Table
        self.step_table = QTableWidget()
        self.step_table.setColumnCount(len(self.STEP_COLUMNS))
        self.step_table.setHorizontalHeaderLabels([label for _, label in self.STEP_COLUMNS])
        self.step_table.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.SelectedClicked | QAbstractItemView.EditKeyPressed)
        self.step_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.step_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.step_table.setMinimumHeight(320)
        self.step_table.setFont(QFont("Segoe UI", 14))
        self.step_table.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)
        for col, (key, _) in enumerate(self.STEP_COLUMNS):
            if key == "step":
                self.step_table.setColumnWidth(col, 60)
            elif key.startswith("spacer"):
                self.step_table.setColumnWidth(col, 2)
            else:
                self.step_table.setColumnWidth(col, 110)
        self.step_table.horizontalHeader().setStretchLastSection(False)
        self.step_table.verticalHeader().setVisible(False)
        self.step_table.setAlternatingRowColors(True)
        # Tooltips for headers
        for col, (key, label) in enumerate(self.STEP_COLUMNS):
            if key == "step":
                tip = "Step number (auto)"
            elif key.startswith("spacer"):
                tip = ""
            else:
                ch, param = key.split('_')
                tip = f"Channel {ch[-1]} {param.upper()}"
            self.step_table.horizontalHeaderItem(col).setToolTip(tip)
        self.step_table.itemChanged.connect(self.save_config)
        self.step_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        step_layout.addWidget(self.step_table)
        step_group.setLayout(step_layout)
        main_layout.addWidget(step_group)
        # --- End Step Table ---
        main_layout.addSpacing(18)
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
        self.step_table.horizontalHeader().setStyleSheet('''
            QHeaderView::section {
                background: #232e3c;
                color: #f8fafc;
                font-weight: bold;
                font-size: 15px;
                padding: 8px 0px;
                border: 1px solid #3a3f4b;
            }
        ''')
        self.step_table.setStyleSheet('''
            QTableWidget {
                background: #23272e;
                color: #e0e6f0;
                gridline-color: #3a3f4b;
                selection-background-color: #4f8cff;
                selection-color: #fff;
                alternate-background-color: #262b33;
                font-size: 15px;
            }
            QTableWidget::item:selected {
                background: #4f8cff;
                color: #fff;
            }
        ''')
        self.step_table.setAlternatingRowColors(True)
        self.step_table.itemChanged.connect(self.save_config)
        step_layout.addWidget(self.step_table)
        # Buttons for add/remove/move
        btn_layout = QHBoxLayout()
        button_style = '''
            QPushButton {
                background: #353a45;
                color: #e0e6f0;
                border-radius: 8px;
                font-size: 15px;
                min-width: 110px;
                min-height: 36px;
                padding: 6px 18px;
                border: 1.5px solid #3a3f4b;
            }
            QPushButton:hover {
                background: #4f8cff;
                color: #fff;
                border: 1.5px solid #4f8cff;
            }
            QPushButton:pressed {
                background: #232e3c;
                color: #fff;
            }
        '''
        self.add_step_btn = QPushButton("Add Step")
        self.add_step_btn.setStyleSheet(button_style)
        self.add_step_btn.clicked.connect(self.add_step)
        self.remove_step_btn = QPushButton("Remove Step")
        self.remove_step_btn.setStyleSheet(button_style)
        self.remove_step_btn.clicked.connect(self.remove_step)
        self.move_up_btn = QPushButton("Move Up")
        self.move_up_btn.setStyleSheet(button_style)
        self.move_up_btn.clicked.connect(self.move_step_up)
        self.move_down_btn = QPushButton("Move Down")
        self.move_down_btn.setStyleSheet(button_style)
        self.move_down_btn.clicked.connect(self.move_step_down)
        btn_layout.addWidget(self.add_step_btn)
        btn_layout.addWidget(self.remove_step_btn)
        btn_layout.addWidget(self.move_up_btn)
        btn_layout.addWidget(self.move_down_btn)
        btn_layout.addStretch()
        step_layout.addLayout(btn_layout)
        step_group.setLayout(step_layout)
        main_layout.addWidget(step_group)
        # --- End Step Table ---

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

        # Start/Stop Experiment button and status
        button_layout = QHBoxLayout()
        self.start_button = QPushButton("Start Experiment")
        self.start_button.clicked.connect(self.on_start_experiment)
        self.stop_button = QPushButton("Stop Experiment")
        self.stop_button.clicked.connect(self.on_stop_experiment)
        self.stop_button.setEnabled(False)
        self.status_label = QLabel("")
        self.status_label.setFont(self.default_font)
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(self.status_label)
        button_layout.addStretch()
        main_layout.addLayout(button_layout)

        # Ensure INIT and UDP_DAS params are present in config.json (import from INIT or set defaults if missing)
        self.ensure_init_params_in_config()
        self.ensure_udp_params_in_config()

        # INIT parameters section (from config.json, not INIT file)
        self.init_param_widgets = {}
        init_group = QGroupBox("INIT Parameters (for udp_das_cringe.exe)")
        init_group.setFont(self.section_font)
        init_layout = QFormLayout()
        for key in self.INIT_KEYS:
            value = self.load_init_param_from_config(key)
            widget = QLineEdit(str(value))
            widget.setFont(self.default_font)
            widget.setMinimumHeight(32)
            widget.editingFinished.connect(self.save_init_params)
            init_layout.addRow(QLabel(key), widget)
            self.init_param_widgets[key] = widget
        init_group.setLayout(init_layout)
        main_layout.addWidget(init_group)

        # udp_das_cringe.exe parameters section
        self.udp_params = self.load_udp_params()
        udp_group = QGroupBox("UDP DAS Cringe Parameters (for udp_das_cringe.exe)")
        udp_group.setFont(self.section_font)
        udp_layout = QFormLayout()
        self.udp_param_widgets = {}
        for key in ['dir', 'nfiles', 'nrefls']:
            widget = QLineEdit(str(self.udp_params.get(key, '')))
            widget.setFont(self.default_font)
            widget.setMinimumHeight(32)
            widget.editingFinished.connect(self.save_udp_params)
            udp_layout.addRow(QLabel(key), widget)
            self.udp_param_widgets[key] = widget
        udp_group.setLayout(udp_layout)
        main_layout.addWidget(udp_group)

        main_layout.addStretch(1)
        self.load_config()
        self.resize(1100, 1050)

    def add_step(self):
        row = self.step_table.rowCount()
        self.step_table.insertRow(row)
        for col, (key, _) in enumerate(self.STEP_COLUMNS):
            if key == "step":
                item = QTableWidgetItem(str(row + 1))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            elif key.startswith("spacer"):
                item = QTableWidgetItem("")
                item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            else:
                item = QTableWidgetItem("")
                item.setTextAlignment(Qt.AlignCenter)
            self.step_table.setItem(row, col, item)
        self.renumber_steps()
        self.style_step_table()
        self.save_config()

    def remove_step(self):
        row = self.step_table.currentRow()
        if row >= 0:
            self.step_table.removeRow(row)
            self.renumber_steps()
            self.style_step_table()
            self.save_config()

    def move_step_up(self):
        row = self.step_table.currentRow()
        if row > 0:
            self.swap_rows(row, row - 1)
            self.step_table.selectRow(row - 1)
            self.renumber_steps()
            self.style_step_table()
            self.save_config()

    def move_step_down(self):
        row = self.step_table.currentRow()
        if row < self.step_table.rowCount() - 1 and row >= 0:
            self.swap_rows(row, row + 1)
            self.step_table.selectRow(row + 1)
            self.renumber_steps()
            self.style_step_table()
            self.save_config()

    def swap_rows(self, row1, row2):
        for col, (key, _) in enumerate(self.STEP_COLUMNS):
            item1 = self.step_table.item(row1, col)
            item2 = self.step_table.item(row2, col)
            text1 = item1.text() if item1 else ""
            text2 = item2.text() if item2 else ""
            new_item1 = QTableWidgetItem(text2)
            new_item2 = QTableWidgetItem(text1)
            if key == "step":
                new_item1.setFlags(new_item1.flags() & ~Qt.ItemIsEditable)
                new_item2.setFlags(new_item2.flags() & ~Qt.ItemIsEditable)
            elif key.startswith("spacer"):
                new_item1.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                new_item2.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            else:
                new_item1.setTextAlignment(Qt.AlignCenter)
                new_item2.setTextAlignment(Qt.AlignCenter)
            self.step_table.setItem(row1, col, new_item1)
            self.step_table.setItem(row2, col, new_item2)
        self.style_step_table()

    def renumber_steps(self):
        for row in range(self.step_table.rowCount()):
            item = self.step_table.item(row, 0)
            if not item:
                item = QTableWidgetItem(str(row + 1))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.step_table.setItem(row, 0, item)
            else:
                item.setText(str(row + 1))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        self.style_step_table()

    def load_config(self):
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
            # --- Load steps table ---
            self.step_table.blockSignals(True)
            self.step_table.setRowCount(0)
            steps = config.get('steps', [])
            for i, step in enumerate(steps):
                row = self.step_table.rowCount()
                self.step_table.insertRow(row)
                for col, (key, _) in enumerate(self.STEP_COLUMNS):
                    if key == "step":
                        item = QTableWidgetItem(str(row + 1))
                        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    elif key.startswith("spacer"):
                        item = QTableWidgetItem("")
                        item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                    else:
                        # Only split if not step or spacer
                        if '_' in key:
                            ch, param = key.split('_')
                            value = step.get(ch, {}).get(param, "")
                        else:
                            value = ""
                        item = QTableWidgetItem(str(value))
                        item.setTextAlignment(Qt.AlignCenter)
                    self.step_table.setItem(row, col, item)
            self.step_table.blockSignals(False)
            self.style_step_table()
            # --- Load other params ---
            if 'wave_type' in config:
                self.wave_combo.setCurrentText(config['wave_type'])
            if 'prefix' in config:
                self.prefix_input.setText(config['prefix'])
            if 'port' in config:
                self.port_input.setText(config['port'])
        except Exception as e:
            print(f"Error loading configuration: {e}")

    def save_config(self):
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
        except Exception:
            config = {}
        # --- Save steps table ---
        steps = []
        for row in range(self.step_table.rowCount()):
            step = {"ch1": {}, "ch2": {}, "ch3": {}}
            for col, (key, _) in enumerate(self.STEP_COLUMNS):
                if key == "step" or key.startswith("spacer"):
                    continue
                # Only split if not step or spacer
                if '_' in key:
                    ch, param = key.split('_')
                    item = self.step_table.item(row, col)
                    try:
                        value = float(item.text()) if item and item.text().strip() != '' else 0.0
                    except ValueError:
                        value = 0.0
                    step[ch][param] = value
            steps.append(step)
        config['steps'] = steps
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
        self.stop_button.setEnabled(True)
        self.status_label.setText("Running...")
        self.stop_event = threading.Event()
        self.thread = ExperimentThread(sleep_time=5.0, stop_event=self.stop_event)
        self.thread.finished.connect(self.on_experiment_finished)
        self.thread.error.connect(self.on_experiment_error)
        self.thread.start()

    def on_stop_experiment(self):
        if hasattr(self, 'stop_event') and self.stop_event is not None:
            self.stop_event.set()
        self.status_label.setText("Stopping...")
        self.stop_button.setEnabled(False)

    def on_experiment_finished(self):
        self.status_label.setText("Finished")
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    def on_experiment_error(self, msg):
        self.status_label.setText(f"Error: {msg}")
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    def load_init_param_from_config(self, key):
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
            return config.get(key, '')
        except Exception:
            return ''

    def save_init_params(self):
        # Save to config.json and INIT file (always keep in sync)
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
        except Exception:
            config = {}
        for k, w in self.init_param_widgets.items():
            config[k] = w.text()
        with open('config.json', 'w') as f:
            json.dump(config, f, indent=4)
        # Also sync to INIT file
        with open('INIT', 'w') as f:
            for k in self.INIT_KEYS:
                v = self.init_param_widgets[k].text()
                f.write(f'{k} = {v}\n')

    def load_udp_params(self):
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
            return {k: config.get(k, '') for k in ['dir', 'nfiles', 'nrefls']}
        except Exception:
            return {'dir': '', 'nfiles': '', 'nrefls': ''}

    def save_udp_params(self):
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
        except Exception:
            config = {}
        for k, w in self.udp_param_widgets.items():
            config[k] = w.text()
        with open('config.json', 'w') as f:
            json.dump(config, f, indent=4)

    def ensure_init_params_in_config(self):
        """Ensure all INIT_KEYS are present in config.json, importing from INIT file if missing."""
        config = {}
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
        except Exception:
            config = {}
        # Read INIT file if present
        init_values = {}
        if os.path.exists('INIT'):
            with open('INIT', 'r') as f:
                for line in f:
                    if '=' in line:
                        k, v = line.strip().split('=', 1)
                        init_values[k.strip()] = v.strip()
        changed = False
        for k in self.INIT_KEYS:
            if k not in config or config[k] == '':
                config[k] = init_values.get(k, '')
                changed = True
        if changed:
            with open('config.json', 'w') as f:
                json.dump(config, f, indent=4)

    def ensure_udp_params_in_config(self):
        """Ensure UDP_DAS params are present in config.json, set defaults if missing."""
        config = {}
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
        except Exception:
            config = {}
        defaults = {'dir': 'refls1', 'nfiles': 3, 'nrefls': 10000}
        changed = False
        for k, v in defaults.items():
            if k not in config or config[k] == '':
                config[k] = v
                changed = True
        if changed:
            with open('config.json', 'w') as f:
                json.dump(config, f, indent=4)

    def style_step_table(self):
        # Define colors for each channel group
        ch1_bg = QColor('#232b36')  # blueish dark
        ch2_bg = QColor('#233026')  # greenish dark
        ch3_bg = QColor('#2b2323')  # reddish dark
        step_bg = QColor('#22232a')  # Step column
        spacer_bg = QColor('#18191c')
        for row in range(self.step_table.rowCount()):
            for col, (key, _) in enumerate(self.STEP_COLUMNS):
                item = self.step_table.item(row, col)
                if not item:
                    continue
                # Step column
                if key == 'step':
                    item.setBackground(step_bg)
                    item.setForeground(QColor('#b0b0b0'))
                    item.setFont(QFont("Segoe UI", 13, QFont.Bold))
                elif key.startswith('spacer'):
                    item.setBackground(spacer_bg)
                    item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                # Channel 1
                elif key.startswith('ch1_'):
                    item.setBackground(ch1_bg)
                # Channel 2
                elif key.startswith('ch2_'):
                    item.setBackground(ch2_bg)
                # Channel 3
                elif key.startswith('ch3_'):
                    item.setBackground(ch3_bg)

# Force Fusion style for full dark theme support
if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = ConfigEditor()
    window.show()
    sys.exit(app.exec_())
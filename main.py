import sys
from PyQt5.QtWidgets import QApplication
from config_editor import ConfigEditor
import os

def main():
    app = QApplication(sys.argv)
    # Load and apply stylesheet from style.qss
    style_path = os.path.join(os.path.dirname(__file__), 'style.qss')
    if os.path.exists(style_path):
        with open(style_path, 'r', encoding='utf-8') as f:
            app.setStyleSheet(f.read())
    window = ConfigEditor()
    window.resize(1200, 800)
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()

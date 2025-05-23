import sys
from PyQt5.QtWidgets import QApplication
from config_editor import ConfigEditor

def main():
    app = QApplication(sys.argv)
    window = ConfigEditor()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()

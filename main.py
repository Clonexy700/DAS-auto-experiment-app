"""
Main entry point for the DAS Auto Experiment Application.
"""
import sys
import logging
import traceback
from PyQt5.QtWidgets import QApplication, QMessageBox
from src.gui.main_window import MainWindow

# Set up logging
logging.basicConfig(
    filename='app.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def exception_hook(exctype, value, tb):
    """Global exception handler."""
    error_msg = ''.join(traceback.format_exception(exctype, value, tb))
    logging.error(f"Unhandled exception:\n{error_msg}")
    sys.__excepthook__(exctype, value, tb)  # Call default handler

sys.excepthook = exception_hook

def main():
    """Main entry point for the application."""
    try:
        app = QApplication(sys.argv)
        window = MainWindow()
        window.show()
        sys.exit(app.exec_())
    except Exception as e:
        error_msg = f"Fatal error: {str(e)}\n{traceback.format_exc()}"
        logging.critical(error_msg)
        QMessageBox.critical(None, "Fatal Error", f"Application crashed: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()



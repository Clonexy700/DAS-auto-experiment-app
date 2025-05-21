"""
Experiment thread implementation for running experiments in the background.
"""
import logging
import traceback
from PyQt5.QtCore import QThread, pyqtSignal

class ExperimentThread(QThread):
    """Thread for running experiments in the background."""
    
    error = pyqtSignal(str)
    progress = pyqtSignal(int, int)  # current, total
    finished = pyqtSignal()

    def __init__(self, controller):
        super().__init__()
        self.controller = controller

    def run(self):
        """Run the experiment in the background."""
        try:
            self.controller.start_experiment()
        except Exception as e:
            error_msg = f"Experiment error: {str(e)}\n{traceback.format_exc()}"
            logging.error(error_msg)
            self.error.emit(str(e))
        finally:
            self.finished.emit() 
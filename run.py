"""
Entry point script for the DAS Auto Experiment Application.
"""
import os
import sys
import shutil

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Ensure read_udp_das.exe is in the correct location
exe_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "read_udp_das.exe")
alinx_exe_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                            "Alinx C Interrogate programm tool", "read_udp_das.exe")

if not os.path.exists(exe_path) and os.path.exists(alinx_exe_path):
    shutil.copy2(alinx_exe_path, exe_path)

from src.main import main

if __name__ == "__main__":
    main() 
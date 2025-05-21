# DAS Auto Experiment Application

An automated experiment application for controlling piezo actuators and performing data acquisition.

## Features

- Configurable parameter sweeps for amplitude, bias, and frequency
- Support for multiple waveform types (Sine, Square, Triangle, Sawtooth)
- Real-time progress tracking
- Automatic data acquisition using external executable
- Configuration persistence
- Error handling and cleanup

## Requirements

- Python 3.7+
- PyQt5
- pyserial
- pztlibrary
- read_udp_das.exe (data acquisition executable)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd DAS-auto-experiment-app
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Place `read_udp_das.exe` in the project root directory.

## Usage

1. Run the application:
```bash
python src/main.py
```

2. Configure experiment parameters:
   - Set amplitude range (min, max, step)
   - Set bias range (min, max, step)
   - Set frequency range (min, max, step)
   - Select waveform type
   - Enter prefix for output files
   - Set number of files and reflectograms

3. Click "Start Experiment" to begin the parameter sweep.

4. Monitor progress using the progress bar and status label.

5. Click "Stop Experiment" to abort the experiment if needed.

## Configuration

The application saves the last used configuration in `config.json`. This file is automatically loaded when the application starts.

## Error Handling

The application includes comprehensive error handling:
- Input validation
- Device communication errors
- Data acquisition errors
- Resource cleanup on exit

## Project Structure

```
DAS-auto-experiment-app/
├── src/
│   ├── core/
│   │   └── interfaces.py
│   ├── config/
│   │   └── config_manager.py
│   ├── devices/
│   │   └── piezo_controller.py
│   ├── acquisition/
│   │   └── data_acquisition.py
│   ├── experiment/
│   │   └── experiment_controller.py
│   ├── gui/
│   │   └── main_window.py
│   └── main.py
├── requirements.txt
└── README.md
```

## License

[Your License Here] 
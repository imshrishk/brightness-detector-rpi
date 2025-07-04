#!/usr/bin/env python3
"""
Main application for Brightness Detector
Initializes the GUI and connects to the camera module
"""

import sys
import os
import platform
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox
from PyQt5.QtGui import QIcon

# Import our modules
from ui.main_window import MainWindow
from utils.config import load_config


def setup_environment():
    """Set up environment variables and paths"""
    # Set up base directories
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.environ['APP_BASE_DIR'] = base_dir
    
    # Create output directories if they don't exist
    output_dir = os.path.join(base_dir, 'output')
    images_dir = os.path.join(output_dir, 'images')
    videos_dir = os.path.join(output_dir, 'videos')
    
    for directory in [output_dir, images_dir, videos_dir]:
        if not os.path.exists(directory):
            os.makedirs(directory)
    
    # Detect system for camera functionality
    system = platform.system()
    is_rpi = platform.machine().startswith('arm') or os.path.exists('/sys/firmware/devicetree/base/model')
    os.environ['IS_RPI'] = str(is_rpi)
    
    # Check for simulation mode flag
    if '--sim' in sys.argv or '-s' in sys.argv or os.environ.get('SIMULATION_MODE', 'False').lower() == 'true':
        os.environ['SIMULATION_MODE'] = 'True'
        print("Simulation mode enabled: Using virtual camera for testing")
        
    return base_dir


def main():
    """Main function to run the application"""
    # Set base directory for the application
    if getattr(sys, 'frozen', False):
        # The application is frozen
        base_dir = os.path.dirname(sys.executable)
    else:
        # The application is not frozen
        base_dir = os.path.dirname(os.path.abspath(__file__))
    
    os.environ['APP_BASE_DIR'] = base_dir

    # Check for simulation mode argument
    if '--sim' in sys.argv or '-s' in sys.argv:
        os.environ['SIMULATION_MODE'] = 'True'

    # Load configuration from file
    config = load_config()

    # Create and run the application
    app = QApplication(sys.argv)
    
    main_win = MainWindow(config)
    main_win.show()

    if os.environ.get('SIMULATION_MODE') == 'True':
        QMessageBox.information(main_win, "Simulation Mode", "Running in simulation mode.")
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

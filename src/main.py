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
    """Main application entry point"""
    # Set up environment
    base_dir = setup_environment()
    
    # Parse command line arguments
    args = sys.argv[1:]
    
    # Check for help flag
    if '--help' in args or '-h' in args:
        print("Brightness Detector Usage:")
        print("  --sim, -s         : Enable simulation mode (use virtual camera)")
        print("  --help, -h        : Show this help message")
        return
    
    # Load configuration
    config = load_config()
    
    # Initialize application
    app = QApplication(sys.argv)
    app.setApplicationName("Brightness Detector")
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create main window
    window = MainWindow(config)
    window.setWindowTitle("Brightness Detector for Raspberry Pi")
    window.resize(1024, 768)
    
    # Show simulation mode notification if enabled
    if os.environ.get('SIMULATION_MODE', 'False').lower() == 'true':
        QMessageBox.information(window, "Simulation Mode", 
                              "Running in simulation mode with virtual camera.\n"
                              "This mode allows testing without physical camera hardware.")
    
    # Show the window
    window.show()
    
    # Start application event loop
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

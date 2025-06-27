"""
Camera capture tab for the Brightness Detector application
"""

import os
import time
import platform
import threading
from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QComboBox, QSlider, QGroupBox, QGridLayout,
    QCheckBox, QMessageBox, QFileDialog, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot, QTimer
from PyQt5.QtGui import QImage, QPixmap
from utils.config import update_config

# Determine if running in simulation mode
IS_SIM_MODE = os.environ.get("SIMULATION_MODE", "False").lower() == "true"

def is_raspberry_pi():
    """Checks if the code is running on a Raspberry Pi."""
    try:
        with open('/sys/firmware/devicetree/base/model', 'r') as f:
            if 'raspberry pi' in f.read().lower():
                return True
    except Exception:
        pass
    return False

# Import camera module based on platform
try:
    if IS_SIM_MODE:
        print("INFO: Simulation mode enabled. Using simulated camera.")
        from camera.sim_camera import SimCamera as Camera
    elif is_raspberry_pi():
        print("INFO: Raspberry Pi detected. Using picamera2 backend.")
        # Import Raspberry Pi specific camera module
        from camera.rpi_camera import RPiCamera as Camera
    else:
        print("INFO: Not a Raspberry Pi. Using OpenCV backend.")
        # Use OpenCV for other platforms
        from camera.cv_camera import CVCamera as Camera
except ImportError as e:
    print(f"Error importing camera module: {e}")


class CaptureTab(QWidget):
    """Camera capture tab UI"""
    
    # Define signals
    image_captured = pyqtSignal(object)  # Signal emitted when image is captured
    
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.camera = None
        self.stream_active = False
        self.recording = False
        self.recording_path = None
        self.init_ui()
        self.init_camera()
        
    def init_ui(self):
        """Initialize user interface"""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # --- Camera View ---
        camera_container = QFrame()
        camera_container.setFrameShape(QFrame.StyledPanel)
        camera_layout = QVBoxLayout(camera_container)
        
        self.camera_view = QLabel("Camera not available")
        self.camera_view.setAlignment(Qt.AlignCenter)
        self.camera_view.setMinimumSize(640, 480)
        camera_layout.addWidget(self.camera_view)
        main_layout.addWidget(camera_container)
        
        # --- Control Panel ---
        control_panel = QGroupBox("Camera Controls")
        control_layout = QGridLayout(control_panel)
        control_layout.setSpacing(15)
        
        # Camera selection
        self.camera_selector = QComboBox()
        self.camera_selector.currentIndexChanged.connect(self.change_camera)
        control_layout.addWidget(QLabel("Camera:"), 0, 0)
        control_layout.addWidget(self.camera_selector, 0, 1)
        
        # Resolution selection
        self.resolution_selector = QComboBox()
        self.resolution_selector.addItems(["640x480", "1280x720", "1920x1080"])
        self.resolution_selector.currentIndexChanged.connect(self.change_resolution)
        control_layout.addWidget(QLabel("Resolution:"), 0, 2)
        control_layout.addWidget(self.resolution_selector, 0, 3)
        
        # Brightness control
        self.brightness_slider = QSlider(Qt.Horizontal)
        self.brightness_slider.setRange(0, 100)
        self.brightness_slider.setValue(self.config["camera"]["brightness"])
        self.brightness_slider.valueChanged.connect(self.change_brightness)
        control_layout.addWidget(QLabel("Brightness:"), 1, 0)
        control_layout.addWidget(self.brightness_slider, 1, 1)
        
        # Contrast control
        self.contrast_slider = QSlider(Qt.Horizontal)
        self.contrast_slider.setRange(-100, 100)
        self.contrast_slider.setValue(self.config["camera"]["contrast"])
        self.contrast_slider.valueChanged.connect(self.change_contrast)
        control_layout.addWidget(QLabel("Contrast:"), 1, 2)
        control_layout.addWidget(self.contrast_slider, 1, 3)
        
        main_layout.addWidget(control_panel)
        
        # --- Action Buttons ---
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(15)
        
        self.stream_button = QPushButton("Start Stream")
        self.stream_button.clicked.connect(self.toggle_stream)
        buttons_layout.addWidget(self.stream_button)
        
        self.capture_button = QPushButton("Capture Image")
        self.capture_button.clicked.connect(self.capture_image)
        buttons_layout.addWidget(self.capture_button)
        
        self.record_button = QPushButton("Start Recording")
        self.record_button.clicked.connect(self.toggle_recording)
        buttons_layout.addWidget(self.record_button)
        
        main_layout.addLayout(buttons_layout)
        
        # Timer for camera updates
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        
    def init_camera(self):
        """Initialize the camera"""
        try:
            self.camera = Camera(self.config["camera"])

            # Block signals from the camera selector while we modify it
            self.camera_selector.blockSignals(True)
            
            # Get the list of available cameras and populate the dropdown
            cam_list = self.camera.list_cameras()
            self.camera_selector.clear()
            if cam_list:
                for i, cam_name in enumerate(cam_list):
                    self.camera_selector.addItem(cam_name, i)
            
            # Set the camera selector to the index from the config
            saved_index = self.config["camera"].get("index", 0)
            for i in range(self.camera_selector.count()):
                if self.camera_selector.itemData(i) == saved_index:
                    self.camera_selector.setCurrentIndex(i)
                    break
            
            # Re-enable signals
            self.camera_selector.blockSignals(False)

            # Manually select the initial camera
            self.camera.select_camera(self.camera_selector.currentData())

        except Exception as e:
            QMessageBox.warning(self, "Camera Error", f"Error initializing camera: {e}")
            print(f"Camera initialization error: {e}")
    
    @pyqtSlot()
    def toggle_stream(self):
        """Toggle camera stream on/off"""
        if self.stream_active:
            self.stream_active = False
            self.timer.stop()
            self.stream_button.setText("Start Stream")
            self.stream_button.setStyleSheet("") # Reset style
            self.camera_view.setText("Camera stream stopped.")
        else:
            if self.camera is not None and self.camera.start_stream():
                self.stream_active = True
                self.timer.start(30)  # Update every 30ms
                self.stream_button.setText("Stop Stream")
                self.stream_button.setStyleSheet("background-color: #e74c3c;") # Red color
            else:
                QMessageBox.warning(self, "Stream Error", "Could not start camera stream.")
    
    @pyqtSlot()
    def update_frame(self):
        """Update the camera frame in the UI"""
        if not self.camera or not self.stream_active:
            return
        
        try:
            frame = self.camera.get_frame()
            if frame is not None:
                # Write video frame if recording
                if self.recording:
                    self.camera.write_video_frame(frame)
                # Convert frame to QImage
                height, width, channel = frame.shape
                bytes_per_line = channel * width
                q_image = QImage(frame.data, width, height, bytes_per_line, QImage.Format_RGB888)
                # Display the QImage in the QLabel
                self.camera_view.setPixmap(QPixmap.fromImage(q_image).scaled(
                    self.camera_view.width(), 
                    self.camera_view.height(),
                    Qt.KeepAspectRatio
                ))
        except Exception as e:
            print(f"Error updating frame: {e}")
            self.stream_active = False
            self.timer.stop()
            self.stream_button.setText("Start Stream")
    
    @pyqtSlot()
    def capture_image(self):
        """Capture a still image from the camera"""
        if not self.camera:
            QMessageBox.warning(self, "Camera Error", "Camera not available")
            return None
        
        try:
            # If stream is not active, start it temporarily
            temp_stream = False
            if not self.stream_active:
                self.camera.start_stream()
                temp_stream = True
            
            # Capture image
            image = self.camera.capture_image()
            
            if temp_stream:
                self.camera.stop_stream()
            
            if image is not None:
                # Save the image
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"image_{timestamp}.{self.config['output']['image_format']}"
                file_path = os.path.join(
                    os.environ.get('APP_BASE_DIR', ''), 
                    'output', 
                    'images', 
                    filename
                )
                
                self.camera.save_image(image, file_path)
                
                # Emit signal with the captured image
                self.image_captured.emit(image)
                
                # Show confirmation
                QMessageBox.information(
                    self, 
                    "Image Captured", 
                    f"Image saved to:\n{file_path}"
                )
                
                return image
            else:
                QMessageBox.warning(self, "Capture Error", "Failed to capture image")
                return None
                
        except Exception as e:
            QMessageBox.warning(self, "Capture Error", f"Error capturing image: {e}")
            return None
    
    @pyqtSlot()
    def toggle_recording(self):
        """Toggle video recording on/off"""
        if self.recording:
            self.recording = False
            self.camera.stop_recording()
            self.record_button.setText("Start Recording")
            self.record_button.setStyleSheet("") # Reset style
            QMessageBox.information(self, "Recording Stopped", f"Video saved to: {self.recording_path}")
        else:
            if not self.stream_active:
                QMessageBox.warning(self, "Recording Error", "Please start the camera stream first.")
                return

            save_dir = os.path.join(os.environ.get('APP_BASE_DIR', ''), 'output', 'videos')
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.recording_path = os.path.join(save_dir, f"rec_{timestamp}.mp4")
            
            self.recording = self.camera.start_recording(self.recording_path)
            if self.recording:
                self.record_button.setText("Stop Recording")
                self.record_button.setStyleSheet("background-color: #e74c3c;") # Red color
            else:
                QMessageBox.critical(self, "Recording Error", "Failed to start recording.")
    
    @pyqtSlot(int)
    def change_camera(self, index):
        """Change the active camera"""
        if self.camera:
            # Stop any active stream/recording
            was_streaming = self.stream_active
            was_recording = self.recording
            if self.stream_active:
                self.toggle_stream()
            if self.recording:
                self.toggle_recording()
            # Switch camera
            try:
                selected_index = self.camera_selector.currentData()
                self.camera.select_camera(selected_index)
                # Update config with new camera index
                self.config["camera"]["index"] = selected_index
                update_config({"camera": {"index": selected_index}})
                # Restore previous state
                if was_streaming:
                    self.toggle_stream()
                if was_recording:
                    self.toggle_recording()
            except Exception as e:
                QMessageBox.warning(self, "Camera Error", f"Error switching camera: {e}")
    
    @pyqtSlot(int)
    def change_resolution(self, index):
        """Change camera resolution"""
        resolution_text = self.resolution_selector.itemText(index)
        width, height = map(int, resolution_text.split('x'))
        
        if self.camera:
            self.camera.set_resolution((width, height))
        
        update_config({"camera": {"resolution": [width, height]}})
    
    @pyqtSlot(int)
    def change_brightness(self, value):
        """Change camera brightness"""
        if self.camera:
            try:
                self.camera.set_brightness(value)
            except Exception as e:
                print(f"Error setting brightness: {e}")
    
    @pyqtSlot(int)
    def change_contrast(self, value):
        """Change camera contrast"""
        if self.camera:
            try:
                self.camera.set_contrast(value)
            except Exception as e:
                print(f"Error setting contrast: {e}")
    
    def closeEvent(self, event):
        """Handle widget close event"""
        if self.stream_active:
            self.toggle_stream()
        
        if self.recording:
            self.toggle_recording()
        
        if self.camera:
            self.camera.release()
            
        event.accept()

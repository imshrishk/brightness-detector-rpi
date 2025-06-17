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
    QCheckBox, QMessageBox, QFileDialog
)
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot, QTimer
from PyQt5.QtGui import QImage, QPixmap

# Import camera module based on platform
try:
    is_rpi = os.environ.get('IS_RPI', 'False').lower() == 'true'
    if is_rpi:
        # Import Raspberry Pi specific camera module
        from camera.rpi_camera import RPiCamera as Camera
    else:
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
        
        # Camera view
        self.camera_view = QLabel("Camera not available")
        self.camera_view.setAlignment(Qt.AlignCenter)
        self.camera_view.setMinimumSize(640, 480)
        self.camera_view.setStyleSheet("background-color: #222; color: white;")
        main_layout.addWidget(self.camera_view)
        
        # Control panel
        control_panel = QGroupBox("Camera Controls")
        control_layout = QGridLayout(control_panel)
        
        # Camera selection
        camera_label = QLabel("Camera:")
        self.camera_selector = QComboBox()
        self.camera_selector.addItem("Default Camera", 0)
        self.camera_selector.currentIndexChanged.connect(self.change_camera)
        control_layout.addWidget(camera_label, 0, 0)
        control_layout.addWidget(self.camera_selector, 0, 1)
        
        # Resolution selection
        resolution_label = QLabel("Resolution:")
        self.resolution_selector = QComboBox()
        self.resolution_selector.addItem("640x480", (640, 480))
        self.resolution_selector.addItem("1280x720", (1280, 720))
        self.resolution_selector.addItem("1920x1080", (1920, 1080))
        self.resolution_selector.currentIndexChanged.connect(self.change_resolution)
        control_layout.addWidget(resolution_label, 0, 2)
        control_layout.addWidget(self.resolution_selector, 0, 3)
        
        # Brightness control
        brightness_label = QLabel("Brightness:")
        self.brightness_slider = QSlider(Qt.Horizontal)
        self.brightness_slider.setMinimum(0)
        self.brightness_slider.setMaximum(100)
        self.brightness_slider.setValue(self.config["camera"]["brightness"])
        self.brightness_slider.valueChanged.connect(self.change_brightness)
        control_layout.addWidget(brightness_label, 1, 0)
        control_layout.addWidget(self.brightness_slider, 1, 1)
        
        # Contrast control
        contrast_label = QLabel("Contrast:")
        self.contrast_slider = QSlider(Qt.Horizontal)
        self.contrast_slider.setMinimum(-100)
        self.contrast_slider.setMaximum(100)
        self.contrast_slider.setValue(self.config["camera"]["contrast"])
        self.contrast_slider.valueChanged.connect(self.change_contrast)
        control_layout.addWidget(contrast_label, 1, 2)
        control_layout.addWidget(self.contrast_slider, 1, 3)
        
        # Add control panel to main layout
        main_layout.addWidget(control_panel)
        
        # Buttons layout
        buttons_layout = QHBoxLayout()
        
        # Start/Stop stream button
        self.stream_button = QPushButton("Start Stream")
        self.stream_button.clicked.connect(self.toggle_stream)
        buttons_layout.addWidget(self.stream_button)
        
        # Capture button
        self.capture_button = QPushButton("Capture Image")
        self.capture_button.clicked.connect(self.capture_image)
        buttons_layout.addWidget(self.capture_button)
        
        # Record button
        self.record_button = QPushButton("Start Recording")
        self.record_button.clicked.connect(self.toggle_recording)
        buttons_layout.addWidget(self.record_button)
        
        # Add buttons layout to main layout
        main_layout.addLayout(buttons_layout)
        
        # Create timer for camera updates
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        
    def init_camera(self):
        """Initialize the camera"""
        try:
            self.camera = Camera(self.config["camera"])
            
            # Try to get a list of available cameras
            cam_list = self.camera.list_cameras()
            if cam_list:
                self.camera_selector.clear()
                for i, cam_name in enumerate(cam_list):
                    self.camera_selector.addItem(cam_name, i)
        except Exception as e:
            QMessageBox.warning(self, "Camera Error", f"Error initializing camera: {e}")
            print(f"Camera initialization error: {e}")
    
    @pyqtSlot()
    def toggle_stream(self):
        """Toggle camera stream on/off"""
        if self.stream_active:
            # Stop the stream
            self.stream_active = False
            self.timer.stop()
            if self.camera:
                self.camera.stop_stream()
            self.stream_button.setText("Start Stream")
        else:
            # Start the stream
            if not self.camera:
                self.init_camera()
            
            if self.camera:
                try:
                    self.camera.start_stream()
                    self.stream_active = True
                    self.timer.start(30)  # Update at approximately 33 fps
                    self.stream_button.setText("Stop Stream")
                except Exception as e:
                    QMessageBox.warning(self, "Camera Error", f"Error starting camera stream: {e}")
    
    @pyqtSlot()
    def update_frame(self):
        """Update the camera frame in the UI"""
        if not self.camera or not self.stream_active:
            return
        
        try:
            frame = self.camera.get_frame()
            if frame is not None:
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
        """Start or stop video recording"""
        if not self.camera:
            QMessageBox.warning(self, "Camera Error", "Camera not available")
            return
            
        if self.recording:
            # Stop recording
            try:
                self.camera.stop_recording()
                self.recording = False
                self.record_button.setText("Start Recording")
                
                # Show confirmation
                QMessageBox.information(
                    self, 
                    "Recording Complete", 
                    f"Video saved to:\n{self.recording_path}"
                )
            except Exception as e:
                QMessageBox.warning(self, "Recording Error", f"Error stopping recording: {e}")
        else:
            # Start recording
            try:
                # Create filename with timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"video_{timestamp}.{self.config['output']['video_format']}"
                self.recording_path = os.path.join(
                    os.environ.get('APP_BASE_DIR', ''), 
                    'output', 
                    'videos', 
                    filename
                )
                
                # Ensure stream is active
                if not self.stream_active:
                    self.toggle_stream()
                
                # Start recording
                self.camera.start_recording(self.recording_path)
                self.recording = True
                self.record_button.setText("Stop Recording")
            except Exception as e:
                QMessageBox.warning(self, "Recording Error", f"Error starting recording: {e}")
    
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
                self.camera.select_camera(self.camera_selector.currentData())
                
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
        if self.camera:
            resolution = self.resolution_selector.currentData()
            try:
                self.camera.set_resolution(resolution)
            except Exception as e:
                QMessageBox.warning(self, "Camera Error", f"Error changing resolution: {e}")
    
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

"""
Camera module for Raspberry Pi camera access using picamera2
"""

import os
import time
import threading
import cv2
import numpy as np
from datetime import datetime

try:
    # Import picamera2 for Raspberry Pi
    from picamera2 import Picamera2
    from picamera2.encoders import H264Encoder, MJPEGEncoder, Quality
    from picamera2.outputs import FileOutput
    PICAMERA_AVAILABLE = True
except ImportError:
    PICAMERA_AVAILABLE = False
    print("Warning: picamera2 not available. RPi camera features will be limited.")


class RPiCamera:
    """Raspberry Pi camera implementation using picamera2"""
    
    def __init__(self, config):
        """Initialize the camera with configuration"""
        self.config = config
        self.camera = None
        self.resolution = config.get("resolution", (1280, 720))
        self.stream_active = False
        self.recording = False
        self.encoder = None
        self.output = None
        self.latest_frame = None
        self.frame_lock = threading.Lock()
        
        # Try to initialize the camera
        self._init_camera()
    
    def _init_camera(self):
        """Initialize the picamera2 instance"""
        if not PICAMERA_AVAILABLE:
            raise ImportError("picamera2 is not available")
        
        try:
            self.camera = Picamera2()
            
            # Configure the camera
            config = self.camera.create_still_configuration(
                main={"size": self.resolution},
                lores={"size": (640, 480)},
                display="lores"
            )
            self.camera.configure(config)
            
            # Set camera controls based on config
            self.set_brightness(self.config.get("brightness", 50))
            self.set_contrast(self.config.get("contrast", 0))
            
            # Set rotation if needed
            rotation = self.config.get("rotation", 0)
            if rotation > 0:
                self.camera.set_controls({"RotationDegrees": rotation})
            
        except Exception as e:
            print(f"Error initializing RPi camera: {e}")
            self.camera = None
            raise
    
    def list_cameras(self):
        """List available camera devices"""
        if not PICAMERA_AVAILABLE:
            return []
        
        try:
            # Get a list of available cameras
            cameras = Picamera2.global_camera_info()
            return [f"Camera {i} ({camera.get('Model', 'Unknown')})" 
                   for i, camera in enumerate(cameras)]
        except Exception as e:
            print(f"Error listing cameras: {e}")
            return ["Default RPi Camera"]
    
    def select_camera(self, camera_index):
        """Select camera by index"""
        if not PICAMERA_AVAILABLE:
            return False
        
        try:
            # Close current camera if open
            if self.camera is not None:
                self.release()
            
            # Initialize new camera with index
            self.camera = Picamera2(camera_index)
            
            # Configure the camera
            config = self.camera.create_still_configuration(
                main={"size": self.resolution},
                lores={"size": (640, 480)},
                display="lores"
            )
            self.camera.configure(config)
            
            # Apply settings
            self.set_brightness(self.config.get("brightness", 50))
            self.set_contrast(self.config.get("contrast", 0))
            
            return True
        except Exception as e:
            print(f"Error selecting camera: {e}")
            return False
    
    def _frame_callback(self, request):
        """Callback for new frames"""
        with self.frame_lock:
            # Get the RGB image from the request
            buffer = request.make_array("main")
            self.latest_frame = buffer.copy()
            
            # Record the frame if recording
            if self.recording and self.encoder is not None:
                self.encoder.encode(request)
    
    def start_stream(self):
        """Start camera stream"""
        if not self.camera:
            self._init_camera()
        
        if not self.camera:
            raise Exception("Camera is not available")
        
        try:
            # Start the camera
            self.camera.start()
            
            # Setup the callback
            self.camera.set_image_callback(self._frame_callback)
            
            self.stream_active = True
        except Exception as e:
            print(f"Error starting stream: {e}")
            self.stream_active = False
            raise
    
    def stop_stream(self):
        """Stop camera stream"""
        if not self.camera or not self.stream_active:
            return
        
        try:
            self.camera.stop()
            self.stream_active = False
        except Exception as e:
            print(f"Error stopping stream: {e}")
    
    def get_frame(self):
        """Get the latest frame from the camera"""
        if not self.camera or not self.stream_active:
            return None
        
        with self.frame_lock:
            if self.latest_frame is not None:
                return self.latest_frame.copy()
        
        return None
    
    def capture_image(self):
        """Capture a still image"""
        if not self.camera:
            self._init_camera()
        
        if not self.camera:
            raise Exception("Camera is not available")
        
        try:
            # If streaming, use the latest frame
            if self.stream_active and self.latest_frame is not None:
                with self.frame_lock:
                    return self.latest_frame.copy()
            
            # Otherwise take a photo
            if not self.stream_active:
                self.camera.start()
            
            # Capture an image
            metadata = self.camera.capture_array("main")
            
            if not self.stream_active:
                self.camera.stop()
            
            return metadata
        except Exception as e:
            print(f"Error capturing image: {e}")
            return None
    
    def save_image(self, image, file_path):
        """Save image to file"""
        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Save the image
        if isinstance(image, np.ndarray):
            cv2.imwrite(file_path, cv2.cvtColor(image, cv2.COLOR_RGB2BGR))
        else:
            # If it's a direct output from picamera, save it directly
            self.camera.capture_file(file_path)
        
        return file_path
    
    def start_recording(self, file_path):
        """Start video recording"""
        if not self.camera or self.recording:
            return False
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        try:
            # Create encoder based on file extension
            _, ext = os.path.splitext(file_path)
            
            if ext.lower() == '.mp4' or ext.lower() == '.h264':
                # H.264 video
                self.encoder = H264Encoder(Quality.HIGH)
            else:
                # Default to MJPEG
                self.encoder = MJPEGEncoder()
            
            # Create file output
            self.output = FileOutput(file_path)
            
            # Start recording
            if not self.stream_active:
                self.start_stream()
            
            self.encoder.output = self.output
            self.camera.start_encoder(self.encoder)
            
            self.recording = True
            return True
        except Exception as e:
            print(f"Error starting recording: {e}")
            self.recording = False
            return False
    
    def stop_recording(self):
        """Stop video recording"""
        if not self.camera or not self.recording:
            return False
        
        try:
            # Stop the encoder
            self.camera.stop_encoder()
            
            # Close the output
            if self.output:
                self.output.close()
            
            self.recording = False
            self.encoder = None
            self.output = None
            
            return True
        except Exception as e:
            print(f"Error stopping recording: {e}")
            return False
    
    def set_resolution(self, resolution):
        """Set camera resolution"""
        if not self.camera:
            self.resolution = resolution
            return False
        
        try:
            # Need to reconfigure camera for resolution change
            streaming = self.stream_active
            recording = self.recording
            
            if streaming:
                self.stop_stream()
            
            if recording:
                self.stop_recording()
            
            # Update resolution
            self.resolution = resolution
            
            # Reconfigure
            config = self.camera.create_still_configuration(
                main={"size": self.resolution},
                lores={"size": (640, 480)},
                display="lores"
            )
            self.camera.configure(config)
            
            # Restart if needed
            if streaming:
                self.start_stream()
            
            return True
        except Exception as e:
            print(f"Error setting resolution: {e}")
            return False
    
    def set_brightness(self, value):
        """Set camera brightness"""
        if not self.camera:
            return False
        
        try:
            # Convert 0-100 to -1.0 to 1.0
            normalized = (value - 50) / 50.0
            
            # Set brightness
            self.camera.set_controls({"Brightness": normalized})
            return True
        except Exception as e:
            print(f"Error setting brightness: {e}")
            return False
    
    def set_contrast(self, value):
        """Set camera contrast"""
        if not self.camera:
            return False
        
        try:
            # Convert -100 to 100 to 0.0 to 2.0
            normalized = (value + 100) / 100.0
            
            # Set contrast
            self.camera.set_controls({"Contrast": normalized})
            return True
        except Exception as e:
            print(f"Error setting contrast: {e}")
            return False
    
    def release(self):
        """Release camera resources"""
        if self.recording:
            self.stop_recording()
        
        if self.stream_active:
            self.stop_stream()
        
        if self.camera is not None:
            try:
                self.camera.close()
            except:
                pass
            
            self.camera = None

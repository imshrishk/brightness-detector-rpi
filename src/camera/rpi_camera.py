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
    from picamera2.encoders import H264Encoder, MJPEGEncoder
    from picamera2.outputs import FfmpegOutput
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
        self.video_writer = None  # For OpenCV-based recording fallback
        self.recording_path = None
        self.using_picamera_recording = False  # Flag to track recording mode
        
        # Try to initialize the camera
        self._init_camera()
    
    def _init_camera(self):
        """Initialize the picamera2 instance"""
        if not PICAMERA_AVAILABLE:
            print("Warning: picamera2 not available, RPi camera will use fallback mode")
            self.camera = None
            return
        
        try:
            self.camera = Picamera2()
            
            # Configure the camera for video recording
            config = self.camera.create_video_configuration(
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
            
            # Configure the camera for video recording
            config = self.camera.create_video_configuration(
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
    
    def start_stream(self):
        """Start camera stream"""
        if not self.camera:
            self._init_camera()
        
        if not self.camera:
            print("[DEBUG] rpi_camera.py: start_stream failed, camera is not available")
            return False
        
        try:
            # Start the camera
            self.camera.start()
            self.stream_active = True
            print("[DEBUG] rpi_camera.py: start_stream succeeded")
            return True
        except Exception as e:
            print(f"Error starting stream: {e}")
            self.stream_active = False
            print("[DEBUG] rpi_camera.py: start_stream failed with exception")
            return False
    
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
        
        try:
            # capture_array is a blocking call, which is what we want
            # for the QTimer-based update mechanism.
            return self.camera.capture_array("main")
        except Exception as e:
            print(f"Error capturing frame: {e}")
            return None
    
    def capture_image(self):
        """Capture a still image"""
        if not self.camera:
            self._init_camera()
        
        if not self.camera:
            raise Exception("Camera is not available")
        
        try:
            # Capture a new array directly. This ensures we get a fresh frame.
            return self.camera.capture_array("main")
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
        
        self.recording_path = file_path
        
        try:
            # Try using picamera2's built-in recording first
            # Create encoder based on file extension
            _, ext = os.path.splitext(file_path)
            
            if ext.lower() == '.mp4' or ext.lower() == '.h264':
                # Use lower bitrate for RPi to avoid performance issues
                encoder = H264Encoder(5000000)  # 5Mbps bitrate (reduced from 10Mbps)
            else:
                # Default to MJPEG for other formats like .avi
                encoder = MJPEGEncoder()
            
            # Use FfmpegOutput for robust container handling
            output = FfmpegOutput(file_path)
            
            # Ensure camera is started before recording
            if not self.stream_active:
                self.camera.start()
                self.stream_active = True
            
            # start_recording is a robust, high-level call
            self.camera.start_recording(encoder, output)
            
            self.recording = True
            self.using_picamera_recording = True  # Flag to indicate picamera2 recording mode
            print(f"[DEBUG] RPi camera recording started (picamera2 mode): {file_path}")
            return True
        except Exception as e:
            print(f"Error starting picamera2 recording: {e}")
            print("Falling back to OpenCV-based recording...")
            
            # Fallback to OpenCV-based recording
            return self._start_opencv_recording(file_path)
    
    def _start_opencv_recording(self, file_path):
        """Start recording using OpenCV as fallback"""
        try:
            # Get video properties
            width, height = self.resolution
            fps = 30
            
            # Get video format from file extension
            _, ext = os.path.splitext(file_path)
            
            # Choose codec based on extension
            if ext.lower() == '.mp4':
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            elif ext.lower() == '.avi':
                fourcc = cv2.VideoWriter_fourcc(*'XVID')
            else:
                # Default to MP4
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            
            # Create video writer
            self.video_writer = cv2.VideoWriter(
                file_path,
                fourcc,
                fps,
                (width, height)
            )
            
            self.recording = True
            self.using_picamera_recording = False  # Flag to indicate OpenCV recording mode
            print(f"[DEBUG] OpenCV recording started: {file_path}")
            return True
        except Exception as e:
            print(f"Error starting OpenCV recording: {e}")
            self.recording = False
            return False
    
    def stop_recording(self):
        """Stop video recording"""
        if not self.recording:
            return False
        
        try:
            # Stop picamera2 recording if active
            if hasattr(self, 'using_picamera_recording') and self.using_picamera_recording:
                if self.camera and hasattr(self.camera, 'stop_recording'):
                    try:
                        self.camera.stop_recording()
                        print("[DEBUG] picamera2 recording stopped")
                    except Exception as e:
                        print(f"Error stopping picamera2 recording: {e}")
            else:
                # Stop OpenCV recording if active
                if self.video_writer is not None:
                    self.video_writer.release()
                    self.video_writer = None
                    print("[DEBUG] OpenCV recording stopped")
            
            self.recording = False
            self.using_picamera_recording = False
            print(f"[DEBUG] Recording stopped: {self.recording_path}")
            return True
        except Exception as e:
            print(f"Error stopping recording: {e}")
            return False
    
    def write_video_frame(self, frame):
        """Write a frame to the video file if recording is active."""
        if not self.recording:
            return
        
        try:
            # Only write frames manually if using OpenCV recording (fallback mode)
            # For picamera2 recording, frames are automatically written by the camera
            if hasattr(self, 'using_picamera_recording') and not self.using_picamera_recording:
                if self.video_writer is not None:
                    # Convert RGB to BGR for OpenCV
                    if len(frame.shape) == 3 and frame.shape[2] == 3:
                        bgr_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                    else:
                        bgr_frame = frame
                    self.video_writer.write(bgr_frame)
            else:
                # For picamera2 recording, frames are handled automatically
                # No manual frame writing needed
                pass
            
        except Exception as e:
            print(f"Error writing video frame: {e}")
    
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
            config = self.camera.create_video_configuration(
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
        
        # Release video writer if it exists
        if self.video_writer is not None:
            try:
                self.video_writer.release()
            except:
                pass
            self.video_writer = None
        
        if self.camera is not None:
            try:
                self.camera.close()
            except:
                pass
            
            self.camera = None

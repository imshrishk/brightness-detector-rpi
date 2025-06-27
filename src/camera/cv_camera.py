"""
Camera module for OpenCV-based camera access on non-Raspberry Pi systems
"""

import os
import time
import cv2
import numpy as np
from datetime import datetime


class CVCamera:
    """OpenCV camera implementation for non-Raspberry Pi systems"""
    
    def __init__(self, config):
        """Initialize the camera with configuration"""
        self.config = config
        self.camera = None
        self.camera_index = config.get("index", 0)  # Use index from config
        self.resolution = config.get("resolution", (1280, 720))
        self.stream_active = False
        self.recording = False
        self.video_writer = None
        
        # Simulation mode
        self.simulation_mode = os.environ.get('SIMULATION_MODE', 'False').lower() == 'true'
        self.sim_frame_count = 0
        self.sim_brightness = 50
        self.sim_contrast = 0
        
    def list_cameras(self):
        """List available camera devices"""
        if self.simulation_mode:
            return ["Simulated Camera"]
            
        available_cameras = []
        
        # Try checking several indices to find connected cameras
        for i in range(10):
            cap = cv2.VideoCapture(i)
            if cap is not None and cap.isOpened():
                # Get camera name if possible
                if hasattr(cap, 'getBackendName'):
                    name = f"Camera {i} ({cap.getBackendName()})"
                else:
                    name = f"Camera {i}"
                
                available_cameras.append(name)
                cap.release()
            else:
                break
        
        if not available_cameras:
            # If no cameras found, add simulation option
            available_cameras.append("Simulated Camera")
            self.simulation_mode = True
            
        return available_cameras
    
    def _create_simulated_frame(self):
        """Create a simulated camera frame with patterns"""
        width, height = self.resolution
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Create a moving gradient
        t = self.sim_frame_count / 30.0  # Time variable
        
        # Draw a moving circle
        center_x = int(width/2 + width/4 * np.sin(t * 0.5))
        center_y = int(height/2 + height/4 * np.cos(t * 0.7))
        radius = 50 + 20 * np.sin(t * 2)
        
        # Draw background gradient
        for y in range(height):
            for x in range(width):
                # Create moving patterns
                pattern = (np.sin(x * 0.01 + t) + np.cos(y * 0.01 + t * 1.5)) * 20 + 128
                
                # Apply brightness and contrast
                brightness_factor = self.sim_brightness / 50.0  # 0 to 2
                contrast_factor = (self.sim_contrast + 100) / 100.0  # 0 to 2
                
                r = max(0, min(255, pattern * brightness_factor))
                g = max(0, min(255, pattern * brightness_factor))
                b = max(0, min(255, pattern * brightness_factor))
                
                frame[y, x] = [r, g, b]
        
        # Draw the circle with increased brightness
        cv2.circle(frame, (center_x, center_y), int(radius), (200, 230, 255), -1)
        
        # Add a very bright spot that moves around
        bright_x = int(width/2 + width/3 * np.sin(t * 1.1))
        bright_y = int(height/2 + height/3 * np.cos(t * 0.8))
        cv2.circle(frame, (bright_x, bright_y), 20, (255, 255, 255), -1)
        
        # Add timestamp text
        time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(frame, time_str, (20, height - 20), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 2)
        cv2.putText(frame, "SIMULATED CAMERA", (width - 300, height - 20), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 2)
        
        self.sim_frame_count += 1
        return frame
    
    def select_camera(self, camera_index=None):
        """Select camera by index"""
        if self.camera is not None:
            self.release()
        if camera_index is None:
            camera_index = self.config.get("index", 0)
        self.camera_index = camera_index
        
        # Enable simulation mode if the special index is selected
        if camera_index == "Simulated Camera" or (isinstance(camera_index, (int, float)) and camera_index >= 100):
            self.simulation_mode = True
            return True
            
        if self.simulation_mode:
            return True
            
        # Initialize the camera
        self.camera = cv2.VideoCapture(camera_index)
        
        if not self.camera.isOpened():
            print(f"Could not open camera index {camera_index}, falling back to simulation mode")
            self.simulation_mode = True
            return True
        
        # Set resolution
        self.set_resolution(self.resolution)
        
        # Apply other settings
        self.set_brightness(self.config.get("brightness", 50))
        self.set_contrast(self.config.get("contrast", 0))
        
        return True
    
    def start_stream(self):
        """Start camera stream"""
        if self.simulation_mode:
            self.stream_active = True
            return
            
        if self.camera is None:
            # Try to initialize the default camera
            try:
                self.select_camera(self.camera_index)
            except Exception as e:
                print(f"Error selecting camera: {e}")
                self.simulation_mode = True
                self.stream_active = True
                return
        
        if not self.camera.isOpened():
            print("Camera could not be opened, falling back to simulation mode")
            self.simulation_mode = True
            self.stream_active = True
            return
        
        self.stream_active = True
    
    def stop_stream(self):
        """Stop camera stream"""
        self.stream_active = False
        
        if self.simulation_mode:
            return
            
        if self.camera is not None:
            pass  # No special actions needed to stop OpenCV camera stream
    
    def get_frame(self):
        """Get the next frame from the camera"""
        if not self.stream_active:
            return None
            
        if self.simulation_mode:
            return self._create_simulated_frame()
        
        if self.camera is None:
            return None
        
        ret, frame = self.camera.read()
        
        if not ret:
            # If capture fails, switch to simulation mode
            print("Camera capture failed, switching to simulation mode")
            self.simulation_mode = True
            return self._create_simulated_frame()
        
        # Convert BGR to RGB for display
        return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    def capture_image(self):
        """Capture a still image"""
        if self.simulation_mode:
            return self._create_simulated_frame()
            
        if self.camera is None:
            # Try to initialize the default camera
            try:
                self.select_camera(self.camera_index)
            except Exception as e:
                print(f"Error selecting camera: {e}")
                self.simulation_mode = True
                return self._create_simulated_frame()
        
        # Make sure the camera is open
        if not self.camera.isOpened():
            print("Camera could not be opened, falling back to simulation mode")
            self.simulation_mode = True
            return self._create_simulated_frame()
        
        # Read frame
        ret, frame = self.camera.read()
        
        if not ret:
            print("Camera capture failed, switching to simulation mode")
            self.simulation_mode = True
            return self._create_simulated_frame()
        
        # Convert BGR to RGB
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        return rgb_image
    
    def save_image(self, image, file_path):
        """Save image to file"""
        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Convert RGB to BGR for OpenCV
        if len(image.shape) == 3 and image.shape[2] == 3:
            bgr_image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        else:
            bgr_image = image
        
        # Save the image
        cv2.imwrite(file_path, bgr_image)
        
        return file_path
    
    def start_recording(self, file_path):
        """Start video recording"""
        if self.recording:
            return False
            
        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Get video properties
        if self.simulation_mode:
            width, height = self.resolution
            fps = 30
        else:
            if self.camera is None or not self.camera.isOpened():
                self.simulation_mode = True
                width, height = self.resolution
                fps = 30
            else:
                width = int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fps = self.camera.get(cv2.CAP_PROP_FPS)
                
                # Use a reasonable framerate if not detected
                if fps <= 0:
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
        
        # Make sure streaming is active
        if not self.stream_active:
            self.start_stream()
        
        return True
    
    def stop_recording(self):
        """Stop video recording"""
        if not self.recording or self.video_writer is None:
            return False
        
        self.recording = False
        
        # Release the video writer
        if self.video_writer is not None:
            # If in simulation mode, write some frames to ensure a valid video file
            if self.simulation_mode:
                for _ in range(30):  # Add 1 second of footage
                    frame = self._create_simulated_frame()
                    # Convert RGB to BGR for OpenCV
                    bgr_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                    self.video_writer.write(bgr_frame)
            
            self.video_writer.release()
            self.video_writer = None
        
        return True
    
    def set_resolution(self, resolution):
        """Set camera resolution"""
        self.resolution = resolution
        
        if self.simulation_mode:
            return True
            
        if self.camera is None:
            return False
        
        width, height = resolution
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        return True
    
    def set_brightness(self, value):
        """Set camera brightness"""
        # Store for simulation mode
        self.sim_brightness = value
        
        if self.simulation_mode:
            return True
            
        if self.camera is None:
            return False
        
        # OpenCV brightness range is usually 0-100
        self.camera.set(cv2.CAP_PROP_BRIGHTNESS, value / 100.0)
        return True
    
    def set_contrast(self, value):
        """Set camera contrast"""
        # Store for simulation mode
        self.sim_contrast = value
        
        if self.simulation_mode:
            return True
            
        if self.camera is None:
            return False
        
        # OpenCV contrast range is usually -100 to 100
        normalized_value = value / 100.0
        self.camera.set(cv2.CAP_PROP_CONTRAST, normalized_value)
        return True
    
    def release(self):
        """Release camera resources"""
        if self.recording:
            self.stop_recording()
        
        if self.camera is not None:
            self.camera.release()
            self.camera = None
    
    def write_video_frame(self, frame):
        """Write a frame to the video file if recording is active."""
        if self.recording and self.video_writer is not None:
            # Convert RGB to BGR for OpenCV
            if len(frame.shape) == 3 and frame.shape[2] == 3:
                bgr_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            else:
                bgr_frame = frame
            self.video_writer.write(bgr_frame)

import numpy as np
import time
from datetime import datetime
import cv2

class SimCamera:
    """A simulated camera for testing without actual hardware."""
    
    def __init__(self, config=None):
        self.config = config or {}
        self.width = self.config.get("resolution", [640, 480])[0]
        self.height = self.config.get("resolution", [640, 480])[1]
        self.is_streaming = False
        self.is_recording = False
        self.frame = self._create_dummy_frame("Camera is OFF")

    def start_stream(self):
        print("[DEBUG] sim_camera.py: start_stream called.")
        self.is_streaming = True
        print("[DEBUG] sim_camera.py: start_stream returning True")
        return True

    def stop_stream(self):
        self.is_streaming = False

    def capture_frame(self):
        if not self.is_streaming:
            return self.frame
        return self._create_dummy_frame(f"{datetime.now():%H:%M:%S}")

    def capture_image(self):
        return self._create_dummy_frame("Captured Image")

    def start_recording(self, path):
        self.is_recording = True
        self.recording_path = path
        # Create a video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.video_writer = cv2.VideoWriter(
            path, fourcc, 30, (self.width, self.height)
        )
        return True

    def write_video_frame(self, frame):
        if self.is_recording and hasattr(self, 'video_writer') and self.video_writer is not None:
            if len(frame.shape) == 3 and frame.shape[2] == 3:
                bgr_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            else:
                bgr_frame = frame
            self.video_writer.write(bgr_frame)

    def stop_recording(self):
        self.is_recording = False
        if hasattr(self, 'video_writer') and self.video_writer is not None:
            self.video_writer.release()
            self.video_writer = None

    def list_cameras(self):
        return ["Simulated Camera"]

    def set_resolution(self, resolution):
        self.width, self.height = resolution

    def set_brightness(self, value):
        pass # Not applicable for sim

    def set_contrast(self, value):
        pass # Not applicable for sim

    def release(self):
        self.stop_stream()
        self.stop_recording()

    def _create_dummy_frame(self, text):
        """Creates a black frame with text."""
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        
        # Simple pulsating background to simulate activity
        gray_value = int(10 + (np.sin(time.time()) + 1) * 15)
        frame[:] = (gray_value, gray_value, gray_value)

        # Add text
        font = 0 # cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 1.2
        thickness = 2
        text_size = (len(text) * 20, 20) # A rough estimation of text size
        text_x = (self.width - text_size[0]) // 2
        text_y = (self.height + text_size[1]) // 2
        
        # A simple white text display
        # In a real OpenCV environment, you'd use cv2.putText
        # This is a simplified placeholder
        # For this to work without cv2, we will just return the frame
        cv2.putText(frame, text, (text_x, text_y), font, font_scale, (255, 255, 255), thickness)
        return frame 
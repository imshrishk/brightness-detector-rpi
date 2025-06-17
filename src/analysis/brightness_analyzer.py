"""
Brightness analyzer for detecting the brightest points in images and videos
"""

import os
import time
import numpy as np
import cv2


class BrightnessAnalyzer:
    """
    Class to analyze brightness in images and videos
    Uses weighted RGB algorithm to calculate perceived brightness
    """
    
    def __init__(self, config):
        """Initialize the analyzer with configuration"""
        self.config = config
        self.progress = 0
    
    def calculate_brightness(self, image):
        """
        Calculate brightness using simple average formula:
        brightness = (R + G + B) / 3
        
        Args:
            image: Input image (RGB or grayscale)
            
        Returns:
            Brightness matrix with same dimensions as input
        """
        if len(image.shape) == 3:  # Color image
            # Extract RGB channels
            r, g, b = cv2.split(image)
            
            # Apply simple average formula
            brightness = (r.astype(np.float32) + 
                         g.astype(np.float32) + 
                         b.astype(np.float32)) / 3.0
            
            return brightness
        else:  # Grayscale image
            return image.astype(np.float32)
    
    def find_brightest_point(self, brightness):
        """
        Find coordinates of the brightest point in the brightness matrix
        
        Args:
            brightness: Brightness matrix
            
        Returns:
            (x, y) coordinates of the brightest point
        """
        # Find the maximum brightness value
        max_val = np.max(brightness)
        
        # Get coordinates of the brightest point (y, x)
        y, x = np.where(brightness == max_val)
        
        # If multiple points have the same brightness, take the first one
        if len(x) > 0 and len(y) > 0:
            return (int(x[0]), int(y[0]))
        else:
            return (0, 0)
    
    def calculate_average_brightness(self, brightness, point, radius=10):
        """
        Calculate average brightness in the area surrounding a point
        
        Args:
            brightness: Brightness matrix
            point: (x, y) coordinates of the center
            radius: Radius of the area to average
            
        Returns:
            Average brightness value in the surrounding area
        """
        x, y = point
        height, width = brightness.shape
        
        # Define region boundaries with bounds checking
        x_min = max(0, x - radius)
        x_max = min(width, x + radius + 1)
        y_min = max(0, y - radius)
        y_max = min(height, y + radius + 1)
        
        # Extract region and calculate average
        region = brightness[y_min:y_max, x_min:x_max]
        avg_brightness = np.mean(region)
        
        return avg_brightness
    
    def calculate_histogram(self, brightness):
        """
        Calculate brightness histogram
        
        Args:
            brightness: Brightness matrix
            
        Returns:
            Histogram of brightness values (256 bins)
        """
        # Normalize brightness to 0-255 range
        brightness_norm = cv2.normalize(
            brightness, 
            None, 
            alpha=0, 
            beta=255, 
            norm_type=cv2.NORM_MINMAX, 
            dtype=cv2.CV_8U
        )
        
        # Calculate histogram
        hist = cv2.calcHist([brightness_norm], [0], None, [256], [0, 256])
        
        # Convert to list
        hist_list = [h[0] for h in hist]
        
        return hist_list
    
    def enhance_contrast(self, image, contrast_factor=1.5):
        """
        Enhance contrast of the image
        
        Args:
            image: Input image
            contrast_factor: Factor to increase contrast (default 1.5)
            
        Returns:
            Image with enhanced contrast
        """
        # Convert to float32 for calculations
        img_float = image.astype(np.float32)
        
        # Calculate mean brightness
        mean_brightness = np.mean(img_float)
        
        # Apply contrast enhancement
        enhanced = mean_brightness + contrast_factor * (img_float - mean_brightness)
        
        # Clip values to valid range
        enhanced = np.clip(enhanced, 0, 255)
        
        return enhanced.astype(np.uint8)

    def analyze_image(self, image):
        """
        Analyze a single image for brightness
        
        Args:
            image: Input image (RGB or grayscale)
            
        Returns:
            Dictionary with analysis results
        """
        # Calculate brightness matrix
        brightness = self.calculate_brightness(image)
        
        # Find the brightest point
        brightest_point = self.find_brightest_point(brightness)
        
        # Get maximum brightness value
        max_brightness = np.max(brightness)
        
        # Calculate average brightness around the brightest point
        average_brightness = self.calculate_average_brightness(
            brightness, 
            brightest_point, 
            radius=self.config.get("average_area_size", 10)
        )
        
        # Calculate brightness histogram
        histogram = self.calculate_histogram(brightness)
        
        # Enhance contrast of the image
        enhanced_image = self.enhance_contrast(image.copy())
        
        # Create marked image for visualization
        brightest_frame_marked = self.draw_markers(
            enhanced_image,
            brightest_point,
            max_brightness,
            average_brightness
        )
        
        # Return analysis results
        return {
            'brightest_point': brightest_point,
            'max_brightness': float(max_brightness),
            'average_brightness': float(average_brightness),
            'brightness_histogram': histogram,
            'brightest_frame': enhanced_image,
            'brightest_frame_marked': brightest_frame_marked,
            'is_video': False,
            'frame_number': 0,
            'metadata': {
                'image_shape': image.shape,
                'analysis_time': time.strftime('%Y-%m-%d %H:%M:%S')
            }
        }
    
    def analyze_video(self, video_capture, sample_rate=5):
        """
        Analyze a video to find the brightest point across all frames
        
        Args:
            video_capture: OpenCV VideoCapture object
            sample_rate: Sample every N frames for better performance
            
        Returns:
            Dictionary with analysis results
        """
        # Get video properties
        total_frames = int(video_capture.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = video_capture.get(cv2.CAP_PROP_FPS)
        
        # Initialize variables
        global_max_brightness = 0
        global_brightest_point = (0, 0)
        global_brightest_frame = None
        global_frame_number = 0
        frame_count = 0
        
        # Reset video to beginning
        video_capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
        
        # Process every Nth frame based on sample_rate
        while True:
            # Read the frame
            ret, frame = video_capture.read()
            
            if not ret:  # End of video
                break
            
            # Update progress
            self.progress = int((frame_count / total_frames) * 100)
            
            # Process only every sample_rate frames
            if frame_count % sample_rate == 0:
                # Convert to RGB for consistent processing
                if len(frame.shape) == 3:
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                else:
                    frame_rgb = frame
                
                # Calculate brightness
                brightness = self.calculate_brightness(frame_rgb)
                
                # Find max brightness in this frame
                max_brightness = np.max(brightness)
                
                # If brighter than previous max, update
                if max_brightness > global_max_brightness:
                    global_max_brightness = max_brightness
                    global_brightest_point = self.find_brightest_point(brightness)
                    global_brightest_frame = frame_rgb.copy()
                    global_frame_number = frame_count
            
            frame_count += 1
        
        # Reset video position
        video_capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
        
        # Calculate average brightness around brightest point
        if global_brightest_frame is not None:
            brightness = self.calculate_brightness(global_brightest_frame)
            average_brightness = self.calculate_average_brightness(
                brightness, 
                global_brightest_point,
                radius=self.config.get("average_area_size", 10)
            )
            
            # Calculate histogram for the brightest frame
            histogram = self.calculate_histogram(brightness)
            
            # Create marked image for visualization
            brightest_frame_marked = self.draw_markers(
                global_brightest_frame.copy(),
                global_brightest_point,
                global_max_brightness,
                average_brightness
            )
        else:
            average_brightness = 0
            histogram = [0] * 256
            brightest_frame_marked = None
        
        # Return analysis results
        return {
            'brightest_point': global_brightest_point,
            'max_brightness': float(global_max_brightness),
            'average_brightness': float(average_brightness),
            'brightness_histogram': histogram,
            'brightest_frame': global_brightest_frame,
            'brightest_frame_marked': brightest_frame_marked,
            'is_video': True,
            'frame_number': global_frame_number,
            'total_frames': total_frames,
            'fps': fps,
            'sample_rate': sample_rate,
            'metadata': {
                'video_fps': fps,
                'video_frames': total_frames,
                'video_duration': total_frames / fps if fps > 0 else 0,
                'analysis_time': time.strftime('%Y-%m-%d %H:%M:%S')
            }
        }
    
    def analyze_gif(self, frames, sample_rate=1):
        """
        Analyze a GIF to find the brightest point across all frames
        
        Args:
            frames: List of numpy arrays containing the GIF frames
            sample_rate: Sample every N frames for better performance
            
        Returns:
            Dictionary with analysis results
        """
        # Get basic properties
        total_frames = len(frames)
        
        if total_frames == 0:
            raise ValueError("No frames provided for GIF analysis")
        
        # Initialize variables
        global_max_brightness = 0
        global_brightest_point = (0, 0)
        global_brightest_frame = None
        global_frame_number = 0
        
        # Process each frame in the GIF
        for frame_number, frame in enumerate(frames):
            # Update progress
            self.progress = int((frame_number / total_frames) * 100)
            
            # Process only every sample_rate frames
            if frame_number % sample_rate == 0:
                # Calculate brightness
                brightness = self.calculate_brightness(frame)
                
                # Find max brightness in this frame
                max_brightness = np.max(brightness)
                
                # If brighter than previous max, update
                if max_brightness > global_max_brightness:
                    global_max_brightness = max_brightness
                    global_brightest_point = self.find_brightest_point(brightness)
                    global_brightest_frame = frame.copy()
                    global_frame_number = frame_number
        
        # Calculate average brightness around brightest point
        if global_brightest_frame is not None:
            brightness = self.calculate_brightness(global_brightest_frame)
            average_brightness = self.calculate_average_brightness(
                brightness, 
                global_brightest_point,
                radius=self.config.get("average_area_size", 10)
            )
            
            # Calculate histogram for the brightest frame
            histogram = self.calculate_histogram(brightness)
            
            # Create marked image for visualization
            brightest_frame_marked = self.draw_markers(
                global_brightest_frame.copy(),
                global_brightest_point,
                global_max_brightness,
                average_brightness
            )
        else:
            average_brightness = 0
            histogram = [0] * 256
            brightest_frame_marked = None
        
        # Return analysis results
        return {
            'brightest_point': global_brightest_point,
            'max_brightness': float(global_max_brightness),
            'average_brightness': float(average_brightness),
            'brightness_histogram': histogram,
            'brightest_frame': global_brightest_frame,
            'brightest_frame_marked': brightest_frame_marked,
            'is_video': True,
            'frame_number': global_frame_number,
            'total_frames': total_frames,
            # Use a default FPS for GIFs since they don't have a consistent frame rate
            'fps': 10,
            'sample_rate': sample_rate,
            'metadata': {
                'image_type': 'GIF',
                'frames': total_frames,
                'analysis_time': time.strftime('%Y-%m-%d %H:%M:%S')
            }
        }
    
    def draw_markers(self, image, point, max_brightness, avg_brightness):
        """
        Draw markers on the image to highlight the brightest point
        
        Args:
            image: Input image
            point: (x, y) coordinates of the brightest point
            max_brightness: Maximum brightness value
            avg_brightness: Average brightness around the point
            
        Returns:
            Marked image
        """
        # Get highlight color and radius from config
        highlight_color = self.config.get("highlight_color", (255, 0, 0))
        highlight_radius = self.config.get("highlight_radius", 5)
        
        # Draw crosshair
        x, y = point
        cv2.line(image, (x-10, y), (x+10, y), highlight_color, 2)
        cv2.line(image, (x, y-10), (x, y+10), highlight_color, 2)
        
        # Draw circle
        cv2.circle(image, (x, y), highlight_radius, highlight_color, 2)
        
        # Add text with brightness values
        cv2.putText(
            image,
            f"Max: {max_brightness:.2f}",
            (x+15, y+15),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            highlight_color,
            1
        )
        
        cv2.putText(
            image,
            f"Avg: {avg_brightness:.2f}",
            (x+15, y+35),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            highlight_color,
            1
        )
        
        return image

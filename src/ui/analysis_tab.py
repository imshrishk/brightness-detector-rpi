"""
Analysis tab for the Brightness Detector application
"""

import os
import time
import threading
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QComboBox, QProgressBar, QGroupBox, 
    QCheckBox, QSpinBox, QMessageBox, QFileDialog,
    QFrame, QGridLayout
)
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot, QTimer
from PyQt5.QtGui import QImage, QPixmap, QPainter, QPen, QColor
import numpy as np
import cv2
from PIL import Image, ImageSequence
import logging

# Import our modules
from analysis.brightness_analyzer import BrightnessAnalyzer

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class AnalysisTab(QWidget):
    """Analysis tab UI"""
    
    # Define signals
    analysis_complete = pyqtSignal(dict)  # Signal emitted when analysis completes
    
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.media_path = None
        self.current_image = None
        self.current_video = None
        self.is_gif = False
        self.gif_frames = []
        self.video_player = None
        self.analyzer = BrightnessAnalyzer(config["analysis"])
        self.analysis_thread = None
        self.analysis_results = None
        self.init_ui()
    
    def init_ui(self):
        """Initialize user interface"""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # --- Media Preview ---
        preview_container = QFrame()
        preview_container.setFrameShape(QFrame.StyledPanel)
        preview_layout = QVBoxLayout(preview_container)
        
        self.media_preview = QLabel("No media loaded")
        self.media_preview.setAlignment(Qt.AlignCenter)
        self.media_preview.setMinimumSize(640, 480)
        preview_layout.addWidget(self.media_preview)
        main_layout.addWidget(preview_container)
        
        # --- Analysis Settings ---
        settings_group = QGroupBox("Analysis Settings")
        settings_layout = QGridLayout(settings_group)
        settings_layout.setSpacing(15)
        
        # Analysis Type
        self.analyze_option = QComboBox()
        self.analyze_option.addItems(["Analyze Frame", "Analyze Video"])
        settings_layout.addWidget(QLabel("Analysis Type:"), 0, 0)
        settings_layout.addWidget(self.analyze_option, 0, 1)

        # Sample Rate
        self.sample_rate = QSpinBox()
        self.sample_rate.setRange(1, 30)
        self.sample_rate.setValue(self.config["analysis"]["sample_rate"])
        self.sample_rate.setSuffix(" frames")
        settings_layout.addWidget(QLabel("Sample Rate:"), 0, 2)
        settings_layout.addWidget(self.sample_rate, 0, 3)

        # Highlight Radius
        self.highlight_radius = QSpinBox()
        self.highlight_radius.setRange(5, 50)
        self.highlight_radius.setValue(self.config["analysis"]["highlight_radius"])
        self.highlight_radius.setSuffix(" px")
        settings_layout.addWidget(QLabel("Highlight Radius:"), 1, 0)
        settings_layout.addWidget(self.highlight_radius, 1, 1)

        # Average Brightness Checkbox
        self.include_avg = QCheckBox("Include Average Brightness")
        self.include_avg.setChecked(True)
        settings_layout.addWidget(self.include_avg, 1, 2, 1, 2)

        main_layout.addWidget(settings_group)
        
        # --- Progress and Buttons ---
        progress_layout = QVBoxLayout()
        progress_layout.setSpacing(10)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        progress_layout.addWidget(self.progress_bar)
        
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(15)
        
        self.load_button = QPushButton("Load Media")
        self.load_button.clicked.connect(self.load_media_dialog)
        buttons_layout.addWidget(self.load_button)
        
        self.analyze_button = QPushButton("Run Analysis")
        self.analyze_button.clicked.connect(self.run_analysis)
        self.analyze_button.setEnabled(False)
        buttons_layout.addWidget(self.analyze_button)
        
        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self.clear)
        buttons_layout.addWidget(self.clear_button)

        progress_layout.addLayout(buttons_layout)
        main_layout.addLayout(progress_layout)
    
    @pyqtSlot()
    def load_media_dialog(self):
        """Open file dialog to load media"""
        # Create file filters with GIF files first
        file_filters = [
            "GIF Files (*.gif)",
            "Image Files (*.jpg *.jpeg *.png *.bmp)",
            "Video Files (*.mp4 *.avi *.mov *.h264 *.mjpeg *.mjpg)",
            "All Files (*.*)"
        ]
        
        try:
            # Get the default directory, fallback to current directory if not set
            default_dir = os.path.join(os.environ.get('APP_BASE_DIR', os.getcwd()), 'output')
            
            logger.debug(f"Opening file dialog with default directory: {default_dir}")
            logger.debug(f"Available file filters: {file_filters}")
            
            file_path, selected_filter = QFileDialog.getOpenFileName(
                self,
                "Open Media File",
                default_dir,
                ";;".join(file_filters)
            )
            
            logger.debug(f"Selected file: {file_path}")
            logger.debug(f"Selected filter: {selected_filter}")
            
            if file_path:
                # Verify file exists before proceeding
                if not os.path.exists(file_path):
                    logger.error(f"Selected file does not exist: {file_path}")
                    QMessageBox.warning(self, "File Error", f"File not found: {file_path}")
                    return
                
                # Get file extension
                file_ext = os.path.splitext(file_path)[1].lower()
                logger.debug(f"File extension: {file_ext}")
                
                # Load the media file
                self.load_media(file_path)
                
        except Exception as e:
            logger.error(f"Error in file dialog: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Error opening file dialog: {str(e)}")
    
    def load_media(self, file_path):
        """Load media from file path"""
        try:
            if not os.path.exists(file_path):
                logger.error(f"File does not exist: {file_path}")
                QMessageBox.warning(self, "File Error", f"File not found: {file_path}")
                return
            
            # Clear any previous media
            self.clear()
            
            # Check file type (case insensitive)
            file_ext = os.path.splitext(file_path)[1].lower()
            is_video = file_ext in ('.mp4', '.avi', '.mov', '.h264', '.mjpeg', '.mjpg')
            self.is_gif = file_ext == '.gif'
            
            logger.debug(f"Loading media file: {file_path}")
            logger.debug(f"File extension: {file_ext}")
            logger.debug(f"Is GIF: {self.is_gif}")
            logger.debug(f"File size: {os.path.getsize(file_path)} bytes")
            
            if self.is_gif:
                # Load GIF using PIL
                self.media_path = file_path
                self.gif_frames = []
                
                try:
                    logger.debug("Attempting to load GIF file...")
                    # Verify file is actually a GIF
                    with Image.open(file_path) as test_img:
                        if test_img.format != 'GIF':
                            raise ValueError("File is not a valid GIF image")
                        logger.debug(f"GIF format verified. Image mode: {test_img.mode}")
                    
                    # Now load the GIF for processing
                    gif = Image.open(file_path)
                    logger.debug(f"GIF loaded successfully. Size: {gif.size}, Mode: {gif.mode}")
                    logger.debug(f"Number of frames: {getattr(gif, 'n_frames', 'unknown')}")
                    
                    # Extract frames
                    frame_count = 0
                    for frame in ImageSequence.Iterator(gif):
                        logger.debug(f"Processing frame {frame_count + 1}")
                        # Convert PIL image to RGB mode
                        rgb_frame = frame.convert('RGB')
                        # Convert to numpy array
                        np_frame = np.array(rgb_frame)
                        logger.debug(f"Frame shape: {np_frame.shape}")
                        # Append to frames list
                        self.gif_frames.append(np_frame)
                        frame_count += 1
                    
                    # Set the first frame as current image
                    if self.gif_frames:
                        logger.debug(f"Successfully extracted {len(self.gif_frames)} frames from GIF")
                        self.current_image = self.gif_frames[0]
                        self.update_preview(self.current_image)
                        
                        print(f"Loaded GIF: {file_path}")
                        print(f"Frames: {len(self.gif_frames)}")
                        
                        # Set analyze option to video since GIF has multiple frames
                        self.analyze_option.setCurrentIndex(1)
                        # Enable analysis button
                        self.analyze_button.setEnabled(True)
                        
                        # Show success message
                        QMessageBox.information(
                            self,
                            "GIF Loaded",
                            f"Successfully loaded GIF with {len(self.gif_frames)} frames"
                        )
                    else:
                        raise ValueError("No frames were extracted from the GIF")
                    
                except Exception as e:
                    logger.error(f"Error loading GIF: {str(e)}", exc_info=True)
                    QMessageBox.warning(self, "GIF Error", f"Error loading GIF: {str(e)}")
                    self.clear()
                    return
            
            elif is_video:
                # Load video
                self.media_path = file_path
                self.current_video = cv2.VideoCapture(file_path)
                
                # Check if the video was opened successfully
                if not self.current_video.isOpened():
                    # Try with additional OpenCV options for special formats
                    if file_ext == '.h264':
                        # Try with FFMPEG backend specifically for h264
                        self.current_video = cv2.VideoCapture(file_path, cv2.CAP_FFMPEG)
                    elif file_ext in ('.mjpeg', '.mjpg'):
                        # Try with specific MJPEG settings
                        self.current_video = cv2.VideoCapture(file_path)
                        # Set MJPEG codec explicitly
                        self.current_video.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
                
                # Read first frame for preview
                ret, frame = self.current_video.read()
                if ret:
                    # Convert BGR to RGB for display
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    self.current_image = frame
                    self.update_preview(frame)
                    
                    # Get video properties
                    fps = self.current_video.get(cv2.CAP_PROP_FPS)
                    frame_count = int(self.current_video.get(cv2.CAP_PROP_FRAME_COUNT))
                    duration = frame_count / fps if fps > 0 else 0
                    
                    print(f"Loaded video: {file_path}")
                    print(f"Format: {file_ext}, Frames: {frame_count}, FPS: {fps}, Duration: {duration:.2f}s")
                    
                    # Set analyze option to video
                    self.analyze_option.setCurrentIndex(1)
                    # Enable analysis button
                    self.analyze_button.setEnabled(True)
                else:
                    QMessageBox.warning(self, "Video Error", "Could not read video file")
                    self.clear()
                    return
            
            else:
                # Load image
                self.media_path = file_path
                self.current_image = cv2.imread(file_path)
                if self.current_image is not None:
                    # Convert BGR to RGB for display
                    self.current_image = cv2.cvtColor(self.current_image, cv2.COLOR_BGR2RGB)
                    self.update_preview(self.current_image)
                    
                    print(f"Loaded image: {file_path}")
                    print(f"Size: {self.current_image.shape[1]}x{self.current_image.shape[0]}")
                    
                    # Set analyze option to frame
                    self.analyze_option.setCurrentIndex(0)
                    # Enable analysis button
                    self.analyze_button.setEnabled(True)
                else:
                    QMessageBox.warning(self, "Image Error", "Could not read image file")
                    self.clear()
                    return
            
            # Enable analysis button
            self.analyze_button.setEnabled(True)
            
            # Show media info in status bar (if available)
            if hasattr(self, 'parent') and hasattr(self.parent(), 'statusBar'):
                filename = os.path.basename(file_path)
                self.parent().statusBar().showMessage(f"Loaded {filename}")
            
        except Exception as e:
            logger.error(f"Error loading media: {str(e)}", exc_info=True)
            QMessageBox.warning(self, "Error", f"Error loading media: {str(e)}")
            self.clear()
    
    def set_image(self, image):
        """Set current image from numpy array"""
        if image is not None:
            self.clear()
            self.current_image = image.copy()
            self.update_preview(image)
            self.analyze_button.setEnabled(True)
            # Set analyze option to frame
            self.analyze_option.setCurrentIndex(0)
    
    def update_preview(self, frame):
        """Update the media preview with the given frame"""
        height, width, channel = frame.shape
        bytes_per_line = channel * width
        q_image = QImage(frame.data, width, height, bytes_per_line, QImage.Format_RGB888)
        
        # Display the QImage in the QLabel
        self.media_preview.setPixmap(QPixmap.fromImage(q_image).scaled(
            self.media_preview.width(),
            self.media_preview.height(),
            Qt.KeepAspectRatio
        ))
    
    def draw_brightest_point(self, img, point, avg_brightness):
        """Draw markers for the brightest point on the image"""
        # Make a copy to avoid modifying the original
        marked_img = img.copy()
        
        # Get highlight color and radius from config
        highlight_color = self.config["analysis"]["highlight_color"]
        highlight_radius = self.config["analysis"]["highlight_radius"]
        
        # Draw crosshair
        x, y = point
        cv2.line(marked_img, (x-10, y), (x+10, y), highlight_color, 2)
        cv2.line(marked_img, (x, y-10), (x, y+10), highlight_color, 2)
        
        # Draw circle
        cv2.circle(marked_img, (x, y), highlight_radius, highlight_color, 2)
        
        # Draw text with brightness value
        text = f"Brightness: {avg_brightness:.2f}"
        cv2.putText(
            marked_img, 
            text, 
            (x+15, y+15), 
            cv2.FONT_HERSHEY_SIMPLEX, 
            0.5, 
            highlight_color, 
            1
        )
        
        return marked_img
    
    @pyqtSlot()
    def run_analysis(self):
        """Run brightness analysis on the current media"""
        # Fix for the numpy array boolean check issue
        has_image = self.current_image is not None and isinstance(self.current_image, np.ndarray)
        has_video = self.current_video is not None
        has_gif = self.is_gif and len(self.gif_frames) > 0
        
        if not (has_image or has_video or has_gif):
            QMessageBox.warning(self, "Analysis Error", "No media loaded")
            return
        
        # Update config with current settings
        self.config["analysis"]["sample_rate"] = self.sample_rate.value()
        self.config["analysis"]["highlight_radius"] = self.highlight_radius.value()
        # Update average area size to match highlight radius
        self.config["analysis"]["average_area_size"] = self.highlight_radius.value()
        
        # Update analyzer config
        self.analyzer.config.update(self.config["analysis"])
        
        # Get analysis type
        analysis_type = "video" if self.analyze_option.currentIndex() == 1 else "frame"
        
        # Show progress bar
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0) # Indeterminate progress
        
        # Disable buttons during analysis
        self.load_button.setEnabled(False)
        self.analyze_button.setEnabled(False)
        self.clear_button.setEnabled(False)
        
        # Start analysis in a thread
        self.analysis_thread = threading.Thread(
            target=self._run_analysis_thread,
            args=(analysis_type,),
            daemon=True
        )
        self.analysis_thread.start()
    
    def _run_analysis_thread(self, analysis_type):
        """Run analysis in background thread"""
        try:
            if analysis_type == "frame":
                # Analyze single frame
                if self.current_image is not None:
                    # Run the analysis
                    self.analyzer.progress = 0
                    result = self.analyzer.analyze_image(self.current_image)
                    self.analyzer.progress = 100
                    
                    # Store results
                    self.analysis_results = result
            else:
                # Analyze video
                if self.current_video is not None:
                    # Make sure video is at the start
                    self.current_video.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    
                    # Run the analysis
                    self.analyzer.progress = 0
                    result = self.analyzer.analyze_video(
                        self.current_video,
                        sample_rate=self.config["analysis"]["sample_rate"]
                    )
                    self.analyzer.progress = 100
                    
                    # Store results
                    self.analysis_results = result
                
                # Analyze GIF
                elif self.is_gif and self.gif_frames:
                    # Run the analysis
                    self.analyzer.progress = 0
                    result = self.analyzer.analyze_gif(
                        self.gif_frames,
                        sample_rate=self.config["analysis"]["sample_rate"]
                    )
                    self.analyzer.progress = 100
                    
                    # Store results
                    self.analysis_results = result
                    
                    # Update preview with the brightest frame
                    if result and 'brightest_frame' in result:
                        self.update_preview(result['brightest_frame'])
        
            self.progress_bar.setRange(0, 100) # Set to determinate
            self.analysis_results = result
            
            logger.info("Analysis finished.")
            
            # Re-enable UI elements on the main thread
            QTimer.singleShot(0, self.on_analysis_finished)
        
        except Exception as e:
            # Log error and show message box from main thread
            logger.error(f"Analysis error: {str(e)}", exc_info=True)
            QTimer.singleShot(0, lambda: QMessageBox.warning(
                self, 
                "Analysis Error", 
                f"Error during analysis: {str(e)}"
            ))
    
    def on_analysis_finished(self):
        """Called when analysis is complete."""
        self.progress_bar.setVisible(False)
        self.progress_bar.setValue(0)
        
        # Re-enable buttons
        self.load_button.setEnabled(True)
        self.analyze_button.setEnabled(True)
        self.clear_button.setEnabled(True)
        
        if self.analysis_results:
            self.analysis_complete.emit(self.analysis_results)
            QMessageBox.information(self, "Analysis Complete", "Analysis finished successfully.")
        else:
            QMessageBox.warning(self, "Analysis Error", "Analysis failed or returned no results.")
    
    @pyqtSlot()
    def clear(self):
        """Clear the analysis tab"""
        # Clear media
        self.media_path = None
        self.current_image = None
        self.is_gif = False
        self.gif_frames = []
        
        if self.current_video is not None:
            self.current_video.release()
            self.current_video = None
        
        # Clear UI
        self.media_preview.setText("No media loaded")
        self.media_preview.setPixmap(QPixmap())
        self.analyze_button.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.analysis_results = None
    
    def closeEvent(self, event):
        """Handle widget close event"""
        # Clean up video resources
        if self.current_video is not None:
            self.current_video.release()
            
        event.accept()

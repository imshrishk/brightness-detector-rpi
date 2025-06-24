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
    QFrame
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
        
        # Media preview container
        preview_container = QFrame()
        preview_container.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        preview_container.setStyleSheet("""
            QFrame {
                background-color: #1a1a1a;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        preview_layout = QVBoxLayout(preview_container)
        preview_layout.setContentsMargins(10, 10, 10, 10)
        
        # Media preview
        self.media_preview = QLabel("No media loaded")
        self.media_preview.setAlignment(Qt.AlignCenter)
        self.media_preview.setMinimumSize(640, 480)
        self.media_preview.setStyleSheet("""
            QLabel {
                background-color: #222;
                color: #666;
                border-radius: 4px;
                font-size: 14px;
            }
        """)
        preview_layout.addWidget(self.media_preview)
        main_layout.addWidget(preview_container)
        
        # Analysis settings
        settings_group = QGroupBox("Analysis Settings")
        settings_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #dcdde1;
                border-radius: 6px;
                margin-top: 1em;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 5px;
                color: #2c3e50;
            }
        """)
        settings_layout = QVBoxLayout(settings_group)
        settings_layout.setContentsMargins(15, 15, 15, 15)
        settings_layout.setSpacing(15)
        
        # Analysis controls
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(20)
        
        # Analysis type selector
        type_label = QLabel("Analysis Type:")
        type_label.setStyleSheet("color: #2c3e50;")
        self.analyze_option = QComboBox()
        self.analyze_option.addItem("Analyze Frame", "frame")
        self.analyze_option.addItem("Analyze Video", "video")
        controls_layout.addWidget(type_label)
        controls_layout.addWidget(self.analyze_option)
        
        # Sample rate for video analysis
        rate_label = QLabel("Sample Rate:")
        rate_label.setStyleSheet("color: #2c3e50;")
        self.sample_rate = QSpinBox()
        self.sample_rate.setMinimum(1)
        self.sample_rate.setMaximum(30)
        self.sample_rate.setValue(self.config["analysis"]["sample_rate"])
        self.sample_rate.setPrefix("Every ")
        self.sample_rate.setSuffix(" frames")
        controls_layout.addWidget(rate_label)
        controls_layout.addWidget(self.sample_rate)
        
        # Highlight radius control
        radius_label = QLabel("Highlight Radius:")
        radius_label.setStyleSheet("color: #2c3e50;")
        self.highlight_radius = QSpinBox()
        self.highlight_radius.setMinimum(5)
        self.highlight_radius.setMaximum(50)
        self.highlight_radius.setValue(self.config["analysis"]["highlight_radius"])
        self.highlight_radius.setSuffix(" px")
        controls_layout.addWidget(radius_label)
        controls_layout.addWidget(self.highlight_radius)
        
        # Include Average Brightness option
        self.include_avg = QCheckBox("Include Average Brightness")
        self.include_avg.setChecked(True)
        self.include_avg.setStyleSheet("""
            QCheckBox {
                color: #2c3e50;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
            QCheckBox::indicator:unchecked {
                border: 2px solid #dcdde1;
                border-radius: 3px;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                border: 2px solid #3498db;
                border-radius: 3px;
                background-color: #3498db;
            }
        """)
        controls_layout.addWidget(self.include_avg)
        
        # Add controls to settings layout
        settings_layout.addLayout(controls_layout)
        
        # Progress bar for analysis
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #dcdde1;
                border-radius: 4px;
                text-align: center;
                background-color: #f5f6fa;
            }
            QProgressBar::chunk {
                background-color: #3498db;
                border-radius: 3px;
            }
        """)
        settings_layout.addWidget(self.progress_bar)
        
        # Add settings group to main layout
        main_layout.addWidget(settings_group)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(15)
        
        # Load media button
        self.load_button = QPushButton("Load Media")
        self.load_button.setMinimumWidth(120)
        self.load_button.clicked.connect(self.load_media_dialog)
        buttons_layout.addWidget(self.load_button)
        
        # Run analysis button
        self.analyze_button = QPushButton("Run Analysis")
        self.analyze_button.setMinimumWidth(120)
        self.analyze_button.clicked.connect(self.run_analysis)
        self.analyze_button.setEnabled(False)
        buttons_layout.addWidget(self.analyze_button)
        
        # Clear button
        self.clear_button = QPushButton("Clear")
        self.clear_button.setMinimumWidth(120)
        self.clear_button.clicked.connect(self.clear)
        buttons_layout.addWidget(self.clear_button)
        
        # Add buttons layout to main layout
        main_layout.addLayout(buttons_layout)
    
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
        analysis_type = self.analyze_option.currentData()
        
        # Show progress bar
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        
        # Disable buttons during analysis
        self.analyze_button.setEnabled(False)
        self.load_button.setEnabled(False)
        
        # Start analysis in a thread
        self.analysis_thread = threading.Thread(
            target=self._run_analysis_thread,
            args=(analysis_type,)
        )
        self.analysis_thread.daemon = True
        self.analysis_thread.start()
        
        # Start timer to update progress
        self.progress_timer = QTimer(self)
        self.progress_timer.timeout.connect(self.update_progress)
        self.progress_timer.start(100)
    
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
        
        except Exception as e:
            # Log error and show message box from main thread
            logger.error(f"Analysis error: {str(e)}", exc_info=True)
            QTimer.singleShot(0, lambda: QMessageBox.warning(
                self, 
                "Analysis Error", 
                f"Error during analysis: {str(e)}"
            ))
    
    @pyqtSlot()
    def update_progress(self):
        """Update the progress bar"""
        if self.analyzer is None:
            return
        
        current_progress = self.analyzer.progress
        self.progress_bar.setValue(current_progress)
        
        # Check if analysis is complete
        if current_progress >= 100:
            self.progress_timer.stop()
            self.progress_bar.setVisible(False)
            
            # Re-enable buttons
            self.analyze_button.setEnabled(True)
            self.load_button.setEnabled(True)
            
            # Display results
            if self.analysis_results:
                # Update the preview with marked image
                brightest_point = self.analysis_results["brightest_point"]
                brightest_frame = self.analysis_results["brightest_frame"]
                avg_brightness = self.analysis_results["average_brightness"]
                frame_number = self.analysis_results.get("frame_number", 1)
                
                # Draw the brightest point on the frame
                marked_frame = self.draw_brightest_point(
                    brightest_frame, 
                    brightest_point, 
                    avg_brightness
                )
                self.update_preview(marked_frame)
                
                # Emit signal with results
                self.analysis_complete.emit(self.analysis_results)
                
                # Show success message with frame number
                frame_info = f"Frame #{frame_number}" if frame_number > 1 else "Current frame"
                QMessageBox.information(
                    self,
                    "Analysis Complete",
                    f"Brightness analysis complete.\n"
                    f"{frame_info}\n"
                    f"Brightest point: {brightest_point}\n"
                    f"Brightness value: {self.analysis_results['max_brightness']:.2f}\n"
                    f"Average surrounding brightness: {avg_brightness:.2f}"
                )
    
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

"""
Results tab for the Brightness Detector application
"""

import os
import json
from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QTableWidget, QTableWidgetItem, QGroupBox, 
    QTextEdit, QFileDialog, QMessageBox, QSplitter,
    QFrame
)
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtGui import QImage, QPixmap, QPainter, QPen, QColor
import numpy as np
import cv2
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import pandas as pd


class ResultsTab(QWidget):
    """Results tab UI"""
    
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.current_image = None
        self.current_analysis = None
        self.analysis_data = None
        self.init_ui()
    
    def init_ui(self):
        """Initialize user interface"""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Create splitter for resizable sections
        splitter = QSplitter(Qt.Vertical)
        splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #dcdde1;
                height: 2px;
            }
            QSplitter::handle:hover {
                background-color: #3498db;
            }
        """)
        
        # Image preview section
        image_group = QGroupBox("Image Preview")
        image_group.setStyleSheet("""
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
        image_layout = QVBoxLayout(image_group)
        image_layout.setContentsMargins(15, 15, 15, 15)
        
        # Image preview container
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
        
        self.image_preview = QLabel("No results to display")
        self.image_preview.setAlignment(Qt.AlignCenter)
        self.image_preview.setMinimumSize(640, 360)
        self.image_preview.setStyleSheet("""
            QLabel {
                background-color: #222;
                color: #666;
                border-radius: 4px;
                font-size: 14px;
            }
        """)
        preview_layout.addWidget(self.image_preview)
        image_layout.addWidget(preview_container)
        
        splitter.addWidget(image_group)
        
        # Details section
        details_group = QGroupBox("Analysis Details")
        details_group.setStyleSheet("""
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
        details_layout = QVBoxLayout(details_group)
        details_layout.setContentsMargins(15, 15, 15, 15)
        details_layout.setSpacing(15)
        
        # Create details panel with information
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #dcdde1;
                border-radius: 4px;
                padding: 8px;
                background-color: white;
            }
        """)
        details_layout.addWidget(self.details_text)
        
        # Create visualization area (for brightness histogram, etc.)
        self.figure = Figure(facecolor='white')
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setStyleSheet("""
            FigureCanvas {
                border: 1px solid #dcdde1;
                border-radius: 4px;
                background-color: white;
            }
        """)
        details_layout.addWidget(self.canvas)
        
        splitter.addWidget(details_group)
        
        # Add splitter to main layout
        main_layout.addWidget(splitter)
        
        # Buttons layout
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(15)
        
        # Save image button
        self.save_image_button = QPushButton("Save Image")
        self.save_image_button.setMinimumWidth(120)
        self.save_image_button.clicked.connect(self.save_image)
        self.save_image_button.setEnabled(False)
        buttons_layout.addWidget(self.save_image_button)
        
        # Save data button
        self.save_data_button = QPushButton("Save Analysis Data")
        self.save_data_button.setMinimumWidth(120)
        self.save_data_button.clicked.connect(self.save_data)
        self.save_data_button.setEnabled(False)
        buttons_layout.addWidget(self.save_data_button)
        
        # Export button
        self.export_button = QPushButton("Export to Excel")
        self.export_button.setMinimumWidth(120)
        self.export_button.clicked.connect(self.export_to_excel)
        self.export_button.setEnabled(False)
        buttons_layout.addWidget(self.export_button)
        
        # Clear button
        self.clear_button = QPushButton("Clear Results")
        self.clear_button.setMinimumWidth(120)
        self.clear_button.clicked.connect(self.clear)
        buttons_layout.addWidget(self.clear_button)
        
        # Add buttons layout to main layout
        main_layout.addLayout(buttons_layout)
    
    @pyqtSlot(object)
    def display_image(self, image):
        """Display an image in the preview"""
        if image is None:
            return
        
        # Store the image
        self.current_image = image.copy()
        
        # Convert to proper format for display
        if len(image.shape) == 3 and image.shape[2] == 3:
            # RGB image
            height, width, channel = image.shape
            bytes_per_line = channel * width
            q_image = QImage(image.data, width, height, bytes_per_line, QImage.Format_RGB888)
        else:
            # Try to handle grayscale image
            height, width = image.shape
            q_image = QImage(image.data, width, height, width, QImage.Format_Grayscale8)
        
        # Display the QImage in the QLabel
        self.image_preview.setPixmap(QPixmap.fromImage(q_image).scaled(
            self.image_preview.width(),
            self.image_preview.height(),
            Qt.KeepAspectRatio
        ))
        
        # Enable save buttons
        self.save_image_button.setEnabled(True)
    
    @pyqtSlot(dict)
    def display_analysis(self, analysis_data):
        """Display analysis results"""
        if not analysis_data:
            return
        
        # Store the analysis data
        self.current_analysis = analysis_data
        
        # Display the brightest frame with highlight
        if 'brightest_frame_marked' in analysis_data:
            marked_frame = analysis_data['brightest_frame_marked']
        else:
            marked_frame = analysis_data['brightest_frame']
        
        # Display the image
        self.display_image(marked_frame)
        
        # Update details text
        self.update_details_text(analysis_data)
        
        # Update visualization
        self.update_visualization(analysis_data)
        
        # Enable save buttons
        self.save_image_button.setEnabled(True)
        self.save_data_button.setEnabled(True)
    
    def update_details_text(self, analysis_data):
        """Update the details text with analysis information"""
        self.analysis_data = analysis_data  # Store the data for export
        self.export_button.setEnabled(True)  # Enable export button
        
        # Extract data from the analysis results
        max_brightness = analysis_data.get('max_brightness', 0)
        brightest_point = analysis_data.get('brightest_point', (0, 0))
        average_brightness = analysis_data.get('average_brightness', 0)
        frame_number = analysis_data.get('frame_number', 0)
        
        # Format the details text
        details = f"""
        <h3>Brightness Analysis Results</h3>
        <p><b>Maximum Brightness:</b> {max_brightness:.2f}</p>
        <p><b>Brightest Point:</b> x={brightest_point[0]}, y={brightest_point[1]}</p>
        <p><b>Average Brightness (surrounding area):</b> {average_brightness:.2f}</p>
        """
        
        if 'is_video' in analysis_data and analysis_data['is_video']:
            details += f"<p><b>Frame Number:</b> {frame_number}</p>"
            
            if 'total_frames' in analysis_data:
                details += f"<p><b>Total Frames:</b> {analysis_data['total_frames']}</p>"
                details += f"<p><b>Frame Time:</b> {frame_number / analysis_data['fps']:.2f} seconds</p>"
        
        # Add metadata if available
        if 'metadata' in analysis_data:
            details += "<h3>Metadata</h3>"
            for key, value in analysis_data['metadata'].items():
                details += f"<p><b>{key}:</b> {value}</p>"
        
        # Set the details text
        self.details_text.setHtml(details)
    
    def update_visualization(self, analysis_data):
        """Update the visualization with brightness data"""
        # Clear previous plots
        self.figure.clear()
        
        # Create brightness histogram if data is available
        if 'brightness_histogram' in analysis_data:
            # Plot histogram from data
            ax = self.figure.add_subplot(111)
            ax.bar(
                range(len(analysis_data['brightness_histogram'])),
                analysis_data['brightness_histogram'],
                color='blue',
                alpha=0.7
            )
            ax.set_title('Brightness Distribution')
            ax.set_xlabel('Brightness Level')
            ax.set_ylabel('Pixel Count')
            ax.grid(True, alpha=0.3)
        else:
            # Calculate histogram from the brightest frame
            if 'brightest_frame' in analysis_data:
                frame = analysis_data['brightest_frame']
                
                # Convert to grayscale if RGB
                if len(frame.shape) == 3:
                    # Use weighted brightness conversion
                    r, g, b = cv2.split(frame)
                    gray = cv2.addWeighted(
                        cv2.addWeighted(r, 0.299, g, 0.587, 0), 
                        1.0, 
                        b, 
                        0.114, 
                        0
                    )
                else:
                    gray = frame
                
                # Calculate histogram
                hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
                hist = [h[0] for h in hist]  # Convert to list
                
                # Plot histogram
                ax = self.figure.add_subplot(111)
                ax.bar(range(256), hist, color='blue', alpha=0.7, width=1)
                ax.set_title('Brightness Distribution')
                ax.set_xlabel('Brightness Level')
                ax.set_ylabel('Pixel Count')
                ax.grid(True, alpha=0.3)
                
                # Highlight the max brightness value
                max_brightness = int(analysis_data.get('max_brightness', 0))
                if 0 <= max_brightness < 256:
                    ax.axvline(x=max_brightness, color='red', linestyle='--', linewidth=1)
                    ax.text(
                        max_brightness + 5, 
                        max(hist) * 0.9, 
                        f'Max: {max_brightness}', 
                        color='red'
                    )
        
        # Refresh the canvas
        self.canvas.draw()
    
    @pyqtSlot()
    def save_image(self):
        """Save the current image to a file"""
        if self.current_image is None:
            QMessageBox.warning(self, "Save Error", "No image to save")
            return
        
        # Get current datetime for filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"brightness_analysis_{timestamp}.{self.config['output']['image_format']}"
        
        # Open file dialog
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Image",
            os.path.join(os.environ.get('APP_BASE_DIR', ''), 'output', 'images', default_name),
            f"Images (*.{self.config['output']['image_format']})"
        )
        
        if file_path:
            try:
                # Save the image
                if len(self.current_image.shape) == 3:
                    # RGB image
                    cv2.imwrite(file_path, cv2.cvtColor(self.current_image, cv2.COLOR_RGB2BGR))
                else:
                    # Grayscale image
                    cv2.imwrite(file_path, self.current_image)
                
                QMessageBox.information(self, "Save Complete", f"Image saved to:\n{file_path}")
            except Exception as e:
                QMessageBox.warning(self, "Save Error", f"Error saving image: {e}")
    
    @pyqtSlot()
    def save_data(self):
        """Save the analysis data to a JSON file"""
        if self.current_analysis is None:
            QMessageBox.warning(self, "Save Error", "No analysis data to save")
            return
        
        # Get current datetime for filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"brightness_analysis_{timestamp}.json"
        
        # Open file dialog
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Analysis Data",
            os.path.join(os.environ.get('APP_BASE_DIR', ''), 'output', default_name),
            "JSON Files (*.json)"
        )
        
        if file_path:
            try:
                # Create a copy of the data, removing non-serializable items
                data_to_save = self.current_analysis.copy()
                
                # Remove numpy arrays and other non-serializable objects
                keys_to_remove = []
                for key, value in data_to_save.items():
                    if isinstance(value, np.ndarray):
                        keys_to_remove.append(key)
                
                for key in keys_to_remove:
                    data_to_save.pop(key)
                
                # Convert tuple coordinates to lists for JSON serialization
                if 'brightest_point' in data_to_save:
                    data_to_save['brightest_point'] = list(data_to_save['brightest_point'])
                
                # Add timestamp and metadata
                data_to_save['timestamp'] = timestamp
                data_to_save['app_version'] = "1.0.0"
                
                # Save to JSON file
                with open(file_path, 'w') as f:
                    json.dump(data_to_save, f, indent=4)
                
                QMessageBox.information(self, "Save Complete", f"Analysis data saved to:\n{file_path}")
            except Exception as e:
                QMessageBox.warning(self, "Save Error", f"Error saving data: {e}")
    
    @pyqtSlot()
    def save_results(self):
        """Save both image and data"""
        self.save_image()
        self.save_data()
    
    @pyqtSlot()
    def clear(self):
        """Clear the results tab"""
        self.current_image = None
        self.current_analysis = None
        
        # Clear UI elements
        self.image_preview.setText("No results to display")
        self.image_preview.setPixmap(QPixmap())
        self.details_text.clear()
        self.figure.clear()
        self.canvas.draw()
        
        # Disable save buttons
        self.save_image_button.setEnabled(False)
        self.save_data_button.setEnabled(False)
        self.export_button.setEnabled(False)
    
    def export_to_excel(self):
        """Export analysis data to Excel"""
        if not self.analysis_data:
            return
            
        try:
            # Create a DataFrame with the analysis data
            data = {
                'Metric': [
                    'Maximum Brightness',
                    'Average Brightness',
                    'Brightest Point X',
                    'Brightest Point Y',
                    'Frame Number',
                    'Analysis Time'
                ],
                'Value': [
                    self.analysis_data.get('max_brightness', 0),
                    self.analysis_data.get('average_brightness', 0),
                    self.analysis_data.get('brightest_point', (0, 0))[0],
                    self.analysis_data.get('brightest_point', (0, 0))[1],
                    self.analysis_data.get('frame_number', 0),
                    self.analysis_data.get('metadata', {}).get('analysis_time', '')
                ]
            }
            
            # Add video-specific data if available
            if self.analysis_data.get('is_video', False):
                data['Metric'].extend([
                    'Total Frames',
                    'FPS',
                    'Frame Time (seconds)'
                ])
                data['Value'].extend([
                    self.analysis_data.get('total_frames', 0),
                    self.analysis_data.get('fps', 0),
                    self.analysis_data.get('frame_number', 0) / self.analysis_data.get('fps', 1)
                ])
            
            # Create DataFrame
            df = pd.DataFrame(data)
            
            # Get save file path
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            default_name = f'brightness_analysis_{timestamp}.xlsx'
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save Excel File",
                default_name,
                "Excel Files (*.xlsx)"
            )
            
            if file_path:
                # Save to Excel
                df.to_excel(file_path, index=False, sheet_name='Brightness Analysis')
                
                # Add histogram data to a new sheet
                if 'brightness_histogram' in self.analysis_data:
                    hist_df = pd.DataFrame({
                        'Brightness Level': range(256),
                        'Pixel Count': self.analysis_data['brightness_histogram']
                    })
                    
                    with pd.ExcelWriter(file_path, engine='openpyxl', mode='a') as writer:
                        hist_df.to_excel(writer, index=False, sheet_name='Histogram')
                
                QMessageBox.information(
                    self,
                    "Export Successful",
                    f"Data has been exported to:\n{file_path}"
                )
                
        except Exception as e:
            QMessageBox.critical(
                self,
                "Export Error",
                f"Failed to export data: {str(e)}"
            )

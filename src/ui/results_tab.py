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
    QFrame, QSlider, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem
)
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtGui import QImage, QPixmap, QPainter, QPen, QColor
import numpy as np
import cv2
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import pandas as pd


class PhotoViewer(QGraphicsView):
    """A QGraphicsView for displaying and interacting with images."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.photo_item = QGraphicsPixmapItem()
        self.scene.addItem(self.photo_item)
        
        # Placeholder text
        self.placeholder = self.scene.addSimpleText("No results to display")
        self.placeholder.setBrush(Qt.lightGray)
        self.placeholder.setPos(0, 0)
        
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setDragMode(QGraphicsView.NoDrag)
        self.setMinimumSize(640, 360)
        self._zoom = 0

    def set_photo(self, pixmap=None):
        if pixmap and not pixmap.isNull():
            self.placeholder.setVisible(False)
            self.setDragMode(QGraphicsView.ScrollHandDrag)
            self.photo_item.setPixmap(pixmap)
            self.setSceneRect(self.photo_item.boundingRect())
            self.fitInView(self.photo_item, Qt.KeepAspectRatio)
            self._zoom = 0
        else:
            self.placeholder.setVisible(True)
            self.setDragMode(QGraphicsView.NoDrag)
            self.photo_item.setPixmap(QPixmap())
            self.setSceneRect(self.placeholder.boundingRect())

    def wheelEvent(self, event):
        if not self.photo_item.pixmap().isNull():
            if event.angleDelta().y() > 0:
                factor = 1.25
                self._zoom += 1
            else:
                factor = 0.8
                self._zoom -= 1
            
            if self._zoom > 0:
                self.scale(factor, factor)
            elif self._zoom == 0:
                self.fitInView(self.photo_item, Qt.KeepAspectRatio)
            else:
                self._zoom = 0

    def resizeEvent(self, event):
        if self._zoom == 0 and not self.photo_item.pixmap().isNull():
            self.fitInView(self.photo_item, Qt.KeepAspectRatio)
        super().resizeEvent(event)


class ResultsTab(QWidget):
    """Results tab UI"""
    
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.current_image = None
        self.adjusted_image = None
        self.current_analysis = None
        self.analysis_data = None
        self.init_ui()
    
    def init_ui(self):
        """Initialize user interface"""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Splitter for resizable sections
        splitter = QSplitter(Qt.Vertical)
        
        # --- Image Preview Section ---
        image_group = QGroupBox("Image Preview")
        image_layout = QVBoxLayout(image_group)
        
        self.image_preview = PhotoViewer()
        image_layout.addWidget(self.image_preview)
        
        # Brightness and Contrast controls
        adj_layout = QHBoxLayout()
        
        # Brightness
        bright_label = QLabel("Brightness:")
        self.brightness_slider = QSlider(Qt.Horizontal)
        self.brightness_slider.setRange(-100, 100)
        self.brightness_slider.setValue(0)
        self.brightness_slider.valueChanged.connect(self.apply_brightness_contrast)
        self.brightness_slider.setEnabled(False)
        adj_layout.addWidget(bright_label)
        adj_layout.addWidget(self.brightness_slider)

        # Contrast
        contrast_label = QLabel("Contrast:")
        self.contrast_slider = QSlider(Qt.Horizontal)
        self.contrast_slider.setRange(-100, 100)
        self.contrast_slider.setValue(0)
        self.contrast_slider.valueChanged.connect(self.apply_brightness_contrast)
        self.contrast_slider.setEnabled(False)
        adj_layout.addWidget(contrast_label)
        adj_layout.addWidget(self.contrast_slider)

        image_layout.addLayout(adj_layout)
        
        splitter.addWidget(image_group)
        
        # --- Details Section ---
        details_group = QGroupBox("Analysis Details")
        details_layout = QHBoxLayout(details_group)
        details_layout.setSpacing(15)

        # Details Text
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        details_layout.addWidget(self.details_text, 1) # Give more space to text

        # Visualization
        self.figure = Figure(facecolor='#2c3e50')
        self.canvas = FigureCanvas(self.figure)
        details_layout.addWidget(self.canvas, 2) # And to the plot

        splitter.addWidget(details_group)
        main_layout.addWidget(splitter)
        
        # --- Buttons ---
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(15)
        
        self.save_image_button = QPushButton("Save Image")
        self.save_image_button.clicked.connect(self.save_image)
        self.save_image_button.setEnabled(False)
        buttons_layout.addWidget(self.save_image_button)
        
        self.save_data_button = QPushButton("Save Analysis Data")
        self.save_data_button.clicked.connect(self.save_data)
        self.save_data_button.setEnabled(False)
        buttons_layout.addWidget(self.save_data_button)
        
        self.export_button = QPushButton("Export to Excel")
        self.export_button.clicked.connect(self.export_to_excel)
        self.export_button.setEnabled(False)
        buttons_layout.addWidget(self.export_button)
        
        self.clear_button = QPushButton("Clear Results")
        self.clear_button.clicked.connect(self.clear)
        buttons_layout.addWidget(self.clear_button)
        
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
        self.image_preview.set_photo(QPixmap.fromImage(q_image))
        
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
        self.current_image = marked_frame.copy()
        self.update_image_preview(self.current_image)
        
        # Update details text
        self.update_details_text(analysis_data)
        
        # Update visualization
        self.update_visualization(analysis_data)
        
        # Enable save buttons
        self.save_image_button.setEnabled(True)
        self.save_data_button.setEnabled(True)

        # Reset and enable sliders
        self.brightness_slider.setEnabled(True)
        self.brightness_slider.setValue(0)
        self.contrast_slider.setEnabled(True)
        self.contrast_slider.setValue(0)
    
    def update_details_text(self, analysis_data):
        """Update the details text with analysis information"""
        self.analysis_data = analysis_data  # Store the data for export
        self.export_button.setEnabled(True)  # Enable export button
        
        details = f"""
        <b>Analysis Results</b>
        <hr>
        <b>Timestamp:</b> {analysis_data.get('timestamp', 'N/A')}
        <br>
        <b>Media Path:</b> {analysis_data.get('media_path', 'N/A')}
        <br>
        <br>
        <b>Brightest Point (X, Y):</b> {analysis_data.get('brightest_point', 'N/A')}
        <br>
        <b>Max Brightness (0-255):</b> {analysis_data.get('max_brightness', 'N/A'):.2f}
        <br>
        <b>Average Brightness:</b> {analysis_data.get('average_brightness', 'N/A'):.2f}
        """
        
        if 'frame_number' in analysis_data:
            details += f"<br><b>Frame Number:</b> {analysis_data.get('frame_number', 'N/A')}"
            
        self.details_text.setHtml(details)
    
    def update_visualization(self, analysis_data):
        """Update the visualization with brightness histogram"""
        self.figure.clear()
        
        if 'histogram' in analysis_data and analysis_data['histogram'] is not None:
            hist = analysis_data['histogram']
            
            ax = self.figure.add_subplot(111)
            ax.plot(hist, color='#3498db')
            ax.set_title("Brightness Histogram", color='white')
            ax.set_xlabel("Brightness Level", color='white')
            ax.set_ylabel("Pixel Count", color='white')
            ax.grid(True, linestyle='--', alpha=0.6)
            ax.set_facecolor('#34495e')

            # Change tick colors
            ax.tick_params(axis='x', colors='white')
            ax.tick_params(axis='y', colors='white')

            # Change spine colors
            for spine in ax.spines.values():
                spine.set_edgecolor('white')

            self.canvas.draw()
    
    def apply_brightness_contrast(self):
        """Apply brightness and contrast to the current image."""
        if self.current_image is None:
            return

        brightness = self.brightness_slider.value()
        contrast = self.contrast_slider.value()

        # Contrast is a multiplier (alpha), brightness is an offset (beta)
        # Convert slider range to appropriate alpha and beta values
        alpha = 1.0 + (contrast / 100.0)
        beta = brightness

        # Apply the transformation
        self.adjusted_image = cv2.convertScaleAbs(self.current_image, alpha=alpha, beta=beta)
        
        # Update the preview with the adjusted image
        self.update_image_preview(self.adjusted_image)

    def update_image_preview(self, image_to_display):
        """Helper to update the image preview label."""
        if image_to_display is None:
            self.image_preview.set_photo(None)
            return

        if len(image_to_display.shape) == 3 and image_to_display.shape[2] == 3:
            h, w, ch = image_to_display.shape
            q_img = QImage(image_to_display.data, w, h, ch * w, QImage.Format_RGB888)
        else:
            h, w = image_to_display.shape
            q_img = QImage(image_to_display.data, w, h, w, QImage.Format_Grayscale8)
        
        self.image_preview.set_photo(QPixmap.fromImage(q_img))

    @pyqtSlot()
    def save_image(self):
        """Save the current image to a file"""
        image_to_save = self.adjusted_image if self.adjusted_image is not None else self.current_image
        if image_to_save is None:
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
                if len(image_to_save.shape) == 3:
                    # RGB image
                    cv2.imwrite(file_path, cv2.cvtColor(image_to_save, cv2.COLOR_RGB2BGR))
                else:
                    # Grayscale image
                    cv2.imwrite(file_path, image_to_save)
                
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
        """Clear the current results"""
        self.current_image = None
        self.adjusted_image = None
        self.current_analysis = None
        self.image_preview.set_photo(None)
        self.details_text.clear()
        self.figure.clear()
        self.canvas.draw()
        
        # Disable buttons
        self.save_image_button.setEnabled(False)
        self.save_data_button.setEnabled(False)
        self.export_button.setEnabled(False)

        # Disable and reset sliders
        self.brightness_slider.setEnabled(False)
        self.brightness_slider.setValue(0)
        self.contrast_slider.setEnabled(False)
        self.contrast_slider.setValue(0)
    
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
                if 'histogram' in self.analysis_data and self.analysis_data['histogram'] is not None:
                    hist_df = pd.DataFrame({
                        'Brightness Level': range(256),
                        'Pixel Count': self.analysis_data['histogram']
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

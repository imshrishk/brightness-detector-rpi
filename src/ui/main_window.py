"""
Main window interface for the Brightness Detector application
"""

import os
import sys
from PyQt5.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QFileDialog, QMessageBox, QSplitter,
    QAction, QToolBar, QStatusBar, QComboBox, QApplication
)
from PyQt5.QtCore import Qt, QSize, pyqtSlot, QTimer
from PyQt5.QtGui import QIcon, QPixmap

# Import application-specific modules
from ui.capture_tab import CaptureTab
from ui.analysis_tab import AnalysisTab
from ui.results_tab import ResultsTab
from ui.styles import MAIN_STYLE
from utils.config import update_config


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self, config):
        super().__init__()
        
        self.config = config
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface"""
        # Set window properties
        self.setWindowTitle("Brightness Detector")
        self.setMinimumSize(1200, 800)
        
        # Apply stylesheet
        self.setStyleSheet(MAIN_STYLE)
        
        # Create central widget and layout
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Create tab widget for different functions
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)  # Modern look for tabs
        
        # Create tabs
        self.capture_tab = CaptureTab(self.config)
        self.analysis_tab = AnalysisTab(self.config)
        self.results_tab = ResultsTab(self.config)
        
        # Add tabs to tab widget
        self.tabs.addTab(self.capture_tab, "Capture")
        self.tabs.addTab(self.analysis_tab, "Analysis")
        self.tabs.addTab(self.results_tab, "Results")
        
        # Add tab widget to main layout
        main_layout.addWidget(self.tabs)
        
        # Connect signals
        self.capture_tab.image_captured.connect(self.results_tab.display_image)
        self.analysis_tab.analysis_complete.connect(self.results_tab.display_analysis)
        
        # Set central widget
        self.setCentralWidget(central_widget)
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
        # Create toolbar
        self.create_toolbar()
        
        # Center window on screen
        self.center_window()
    
    def center_window(self):
        """Center the window on the screen"""
        screen = QApplication.primaryScreen().geometry()
        size = self.geometry()
        self.move(
            (screen.width() - size.width()) // 2,
            (screen.height() - size.height()) // 2
        )
    
    def create_menu_bar(self):
        """Create the application menu bar"""
        # File menu
        file_menu = self.menuBar().addMenu("&File")
        
        # Open file action
        open_action = QAction("&Open Media", self)
        open_action.setShortcut("Ctrl+O")
        open_action.setStatusTip("Open an image or video file")
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)
        
        # Save results action
        save_action = QAction("&Save Results", self)
        save_action.setShortcut("Ctrl+S")
        save_action.setStatusTip("Save analysis results")
        save_action.triggered.connect(self.save_results)
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        
        # Exit action
        exit_action = QAction("&Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.setStatusTip("Exit the application")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Tools menu
        tools_menu = self.menuBar().addMenu("&Tools")
        
        # Settings action
        settings_action = QAction("&Settings", self)
        settings_action.setStatusTip("Configure application settings")
        settings_action.triggered.connect(self.show_settings)
        tools_menu.addAction(settings_action)
        
        # Help menu
        help_menu = self.menuBar().addMenu("&Help")
        
        # About action
        about_action = QAction("&About", self)
        about_action.setStatusTip("Show the application's About box")
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def create_toolbar(self):
        """Create the main toolbar"""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setIconSize(QSize(24, 24))
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        
        # Add toolbar buttons
        # Open button
        open_action = QAction("Open", self)
        open_action.setStatusTip("Open an image or video file")
        open_action.triggered.connect(self.open_file)
        toolbar.addAction(open_action)
        
        # Camera capture button
        capture_action = QAction("Capture", self)
        capture_action.setStatusTip("Capture an image from camera")
        capture_action.triggered.connect(self.capture_tab.capture_image)
        toolbar.addAction(capture_action)
        
        toolbar.addSeparator()
        
        # Analyze button
        analyze_action = QAction("Analyze", self)
        analyze_action.setStatusTip("Analyze current media")
        analyze_action.triggered.connect(self.analyze_current)
        toolbar.addAction(analyze_action)
        
        toolbar.addSeparator()
        
        # Save button
        save_action = QAction("Save", self)
        save_action.setStatusTip("Save analysis results")
        save_action.triggered.connect(self.save_results)
        toolbar.addAction(save_action)
    
    @pyqtSlot()
    def open_file(self):
        """Open a media file for analysis"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Image or Video",
            os.path.join(os.environ.get('APP_BASE_DIR', ''), 'output'),
            "Media Files (*.jpg *.jpeg *.png *.bmp *.mp4 *.avi *.mov)"
        )
        
        if file_path:
            # Switch to analysis tab
            self.tabs.setCurrentIndex(1)
            
            # Load the file
            self.analysis_tab.load_media(file_path)
            
            # Update recent files in config
            recent = self.config["ui"].get("recent_files", [])
            if file_path in recent:
                recent.remove(file_path)
            recent.insert(0, file_path)
            recent = recent[:10]  # Keep only 10 most recent
            
            update_config({"ui": {"recent_files": recent}})
    
    @pyqtSlot()
    def analyze_current(self):
        """Analyze the current media"""
        if self.tabs.currentIndex() == 0:
            # If on capture tab, capture image first then analyze
            image = self.capture_tab.capture_image()
            if image is not None:
                self.analysis_tab.set_image(image)
                self.analysis_tab.run_analysis()
        else:
            # Otherwise run analysis on what's in the analysis tab
            self.analysis_tab.run_analysis()
    
    @pyqtSlot()
    def save_results(self):
        """Save the current analysis results"""
        self.results_tab.save_results()
    
    @pyqtSlot()
    def show_settings(self):
        """Show the settings dialog"""
        # TODO: Implement settings dialog
        QMessageBox.information(self, "Settings", "Settings dialog not yet implemented")
    
    @pyqtSlot()
    def show_about(self):
        """Show the about dialog"""
        QMessageBox.about(self, "About Brightness Detector", 
                         "Brightness Detector for Raspberry Pi\n\n"
                         "A cross-platform GUI application for capturing, recording, "
                         "and analyzing video/images from a Raspberry Pi camera.\n\n"
                         "Version: 1.0.0")

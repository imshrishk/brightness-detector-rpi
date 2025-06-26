"""
Modern dark theme styling for the Brightness Detector application
"""

DARK_THEME_STYLE = """
/* General Window */
QMainWindow {
    background-color: #2c3e50; /* Dark blue-grey background */
}

/* Tab Widgets */
QTabWidget::pane {
    border: 1px solid #34495e; /* Slightly lighter border */
    border-radius: 5px;
    background-color: #34495e; /* Slightly lighter tab content area */
}

QTabBar::tab {
    background-color: #2c3e50;
    color: #ecf0f1; /* Light grey text */
    border: 1px solid #34495e;
    border-bottom: none;
    border-top-left-radius: 5px;
    border-top-right-radius: 5px;
    padding: 10px 20px;
    margin-right: 2px;
    font-size: 14px;
}

QTabBar::tab:selected {
    background-color: #3498db; /* Bright blue for selected tab */
    color: white;
    border-bottom: 2px solid #3498db;
}

QTabBar::tab:hover:!selected {
    background-color: #4c5d6e;
}

/* Buttons */
QPushButton {
    background-color: #3498db;
    color: white;
    border: none;
    padding: 10px 20px;
    border-radius: 5px;
    min-width: 90px;
    font-size: 14px;
}

QPushButton:hover {
    background-color: #2980b9;
}

QPushButton:pressed {
    background-color: #2472a4;
}

QPushButton:disabled {
    background-color: #7f8c8d;
    color: #bdc3c7;
}

/* Input Fields */
QLineEdit, QTextEdit, QComboBox {
    border: 1px solid #34495e;
    border-radius: 5px;
    padding: 8px;
    background-color: #ecf0f1;
    color: #2c3e50;
    font-size: 14px;
}

QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
    border: 2px solid #3498db;
}

/* ComboBox Dropdown */
QComboBox::drop-down {
    border: none;
    width: 25px;
}

/* Sliders */
QSlider::groove:horizontal {
    border: 1px solid #34495e;
    height: 10px;
    background: #2c3e50;
    margin: 2px 0;
    border-radius: 5px;
}

QSlider::handle:horizontal {
    background: #3498db;
    border: none;
    width: 20px;
    margin: -5px 0;
    border-radius: 10px;
}

QSlider::handle:horizontal:hover {
    background: #2980b9;
}

/* ScrollBars */
QScrollBar:vertical {
    border: none;
    background-color: #2c3e50;
    width: 14px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background-color: #3498db;
    border-radius: 7px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background-color: #2980b9;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    border: none;
    background-color: #2c3e50;
    height: 14px;
    margin: 0px;
}

QScrollBar::handle:horizontal {
    background-color: #3498db;
    border-radius: 7px;
    min-width: 30px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #2980b9;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}

/* Status Bar */
QStatusBar {
    background-color: #2c3e50;
    color: #ecf0f1;
    border-top: 1px solid #34495e;
}

/* Menu Bar */
QMenuBar {
    background-color: #34495e;
    color: #ecf0f1;
    border-bottom: 1px solid #2c3e50;
}

QMenuBar::item {
    padding: 8px 12px;
    background-color: transparent;
}

QMenuBar::item:selected {
    background-color: #3498db;
    color: white;
}

/* Menu Dropdowns */
QMenu {
    background-color: #34495e;
    color: #ecf0f1;
    border: 1px solid #2c3e50;
    border-radius: 5px;
}

QMenu::item {
    padding: 8px 30px 8px 25px;
}

QMenu::item:selected {
    background-color: #3498db;
    color: white;
}

/* Toolbar */
QToolBar {
    background-color: #34495e;
    border-bottom: 1px solid #2c3e50;
    spacing: 8px;
    padding: 5px;
}

QToolBar::separator {
    width: 1px;
    background-color: #2c3e50;
    margin: 0px 8px;
}

/* Labels */
QLabel {
    color: #ecf0f1;
    font-size: 14px;
}

/* GroupBox */
QGroupBox {
    border: 1px solid #34495e;
    border-radius: 5px;
    margin-top: 1.5em;
    padding: 15px;
    font-size: 14px;
    font-weight: bold;
    color: #ecf0f1;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top center;
    padding: 0 8px;
    color: #ecf0f1;
    background-color: #34495e;
    border-radius: 5px;
}

/* MessageBox */
QMessageBox {
    background-color: #34495e;
}

QMessageBox QLabel {
    color: #ecf0f1;
    font-size: 14px;
}

QMessageBox QPushButton {
    min-width: 100px;
    background-color: #3498db;
}

QMessageBox QPushButton:hover {
    background-color: #2980b9;
}

/* ProgressBar */
QProgressBar {
    border: 1px solid #34495e;
    border-radius: 5px;
    text-align: center;
    color: #ecf0f1;
    background-color: #2c3e50;
}

QProgressBar::chunk {
    background-color: #3498db;
    border-radius: 5px;
}

/* CheckBox */
QCheckBox {
    color: #ecf0f1;
    font-size: 14px;
}

QCheckBox::indicator {
    width: 20px;
    height: 20px;
}

QCheckBox::indicator:unchecked {
    border: 2px solid #34495e;
    border-radius: 5px;
    background-color: #2c3e50;
}

QCheckBox::indicator:checked {
    border: 2px solid #3498db;
    border-radius: 5px;
    background-color: #3498db;
}

/* Splitter */
QSplitter::handle {
    background-color: #34495e;
    height: 4px;
}

QSplitter::handle:hover {
    background-color: #3498db;
}
""" 
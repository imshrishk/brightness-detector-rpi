"""
Modern styling for the Brightness Detector application
"""

MAIN_STYLE = """
QMainWindow {
    background-color: #f5f6fa;
}

QTabWidget::pane {
    border: 1px solid #dcdde1;
    border-radius: 4px;
    background-color: white;
}

QTabBar::tab {
    background-color: #f5f6fa;
    border: 1px solid #dcdde1;
    border-bottom: none;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    padding: 8px 16px;
    margin-right: 2px;
}

QTabBar::tab:selected {
    background-color: white;
    border-bottom: 2px solid #3498db;
}

QTabBar::tab:hover:!selected {
    background-color: #e8e8e8;
}

QPushButton {
    background-color: #3498db;
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 4px;
    min-width: 80px;
}

QPushButton:hover {
    background-color: #2980b9;
}

QPushButton:pressed {
    background-color: #2472a4;
}

QPushButton:disabled {
    background-color: #bdc3c7;
}

QLineEdit, QTextEdit, QComboBox {
    border: 1px solid #dcdde1;
    border-radius: 4px;
    padding: 6px;
    background-color: white;
}

QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
    border: 2px solid #3498db;
}

QComboBox::drop-down {
    border: none;
    width: 20px;
}

QComboBox::down-arrow {
    image: url(resources/down-arrow.png);
    width: 12px;
    height: 12px;
}

QScrollBar:vertical {
    border: none;
    background-color: #f5f6fa;
    width: 12px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background-color: #bdc3c7;
    border-radius: 6px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background-color: #95a5a6;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    border: none;
    background-color: #f5f6fa;
    height: 12px;
    margin: 0px;
}

QScrollBar::handle:horizontal {
    background-color: #bdc3c7;
    border-radius: 6px;
    min-width: 30px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #95a5a6;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}

QStatusBar {
    background-color: #f5f6fa;
    color: #2c3e50;
}

QMenuBar {
    background-color: #f5f6fa;
    border-bottom: 1px solid #dcdde1;
}

QMenuBar::item {
    padding: 6px 10px;
    background-color: transparent;
}

QMenuBar::item:selected {
    background-color: #3498db;
    color: white;
}

QMenu {
    background-color: white;
    border: 1px solid #dcdde1;
    border-radius: 4px;
}

QMenu::item {
    padding: 6px 25px 6px 20px;
}

QMenu::item:selected {
    background-color: #3498db;
    color: white;
}

QToolBar {
    background-color: #f5f6fa;
    border-bottom: 1px solid #dcdde1;
    spacing: 6px;
    padding: 4px;
}

QToolBar::separator {
    width: 1px;
    background-color: #dcdde1;
    margin: 0px 6px;
}

QLabel {
    color: #2c3e50;
}

QGroupBox {
    border: 1px solid #dcdde1;
    border-radius: 4px;
    margin-top: 1em;
    padding-top: 10px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top center;
    padding: 0 5px;
    color: #2c3e50;
}

QMessageBox {
    background-color: white;
}

QMessageBox QPushButton {
    min-width: 100px;
}
""" 
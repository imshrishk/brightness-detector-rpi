# Brightness Detector for Raspberry Pi

A cross-platform GUI application for capturing, recording, and analyzing video/images from a Raspberry Pi camera. This application provides a complete solution for:

- Capturing images and recording videos from the Raspberry Pi camera
- Uploading and analyzing existing media files
- Detecting the brightest points in images/videos
- Displaying analysis results with visualization

## Features

- Cross-platform compatibility (works on both Raspberry Pi and Windows)
- Real-time video streaming from the Raspberry Pi camera
- Brightness analysis using weighted RGB algorithm
- Visual representation of the brightest points
- Analysis metrics including maximum brightness value and coordinates
- User-friendly GUI interface
- Support for multiple media formats:
  - Images: JPG, JPEG, PNG, BMP
  - Videos: MP4, AVI, MOV, H264, MJPEG
  - Animations: GIF

## Requirements

- Python 3.7 or higher
- Raspberry Pi with camera module (for capture features)
- Dependencies listed in requirements.txt

## Installation

1. Clone this repository:
```
git clone https://github.com/imshrishk/brightness-detector-rpi.git
cd brightness-detector-rpi
```

2. Install dependencies:
```
pip install -r requirements.txt
```

3. On Raspberry Pi, ensure the camera interface is enabled:
```
sudo raspi-config
```
Navigate to "Interface Options" > "Camera" and enable it.

## Usage

Run the application:
```
python src/main.py
```

With simulation mode (for testing without camera hardware):
```
python src/main.py --sim
```

- Use the "Capture" tab to take photos or record videos
- Use the "Analysis" tab to analyze captured or uploaded media
- Results will be displayed in the "Results" panel

### Supported Media Formats

- **Images**: JPG, JPEG, PNG, BMP
- **Videos**: MP4, AVI, MOV, H264, MJPEG/MJPG
- **Animations**: GIF

## How Brightness Detection Works

The brightness detection algorithm uses a weighted RGB formula to calculate perceived brightness:

```
brightness = (0.299 * Red) + (0.587 * Green) + (0.114 * Blue)
```

This formula accounts for human perception of different colors, where green appears brighter than red, and red appears brighter than blue. 
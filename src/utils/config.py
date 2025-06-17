"""
Configuration utilities for the Brightness Detector application
"""

import os
import json
import platform


DEFAULT_CONFIG = {
    "camera": {
        "resolution": (1280, 720),
        "framerate": 30,
        "rotation": 0,
        "brightness": 50,
        "contrast": 0,
        "saturation": 0,
        "sharpness": 0,
        "auto_exposure": True,
        "exposure_compensation": 0
    },
    "analysis": {
        "analyze_full_video": True,
        "sample_rate": 5,  # Sample every N frames
        "highlight_color": (255, 0, 0),  # RGB for highlight points
        "highlight_radius": 5,  # Size of highlight circle
        "average_area_size": 10  # Radius for calculating average brightness
    },
    "output": {
        "image_format": "jpg",
        "video_format": "mp4",
        "image_quality": 95
    },
    "ui": {
        "theme": "light",
        "recent_files": []
    }
}


def get_config_path():
    """Get the path to the config file"""
    # Get appropriate config directory for platform
    system = platform.system()
    if system == "Windows":
        config_dir = os.path.join(os.environ.get("APPDATA"), "BrightnessDetector")
    elif system == "Darwin":  # macOS
        config_dir = os.path.join(os.path.expanduser("~"), "Library", "Application Support", "BrightnessDetector")
    else:  # Linux and others
        config_dir = os.path.join(os.path.expanduser("~"), ".config", "BrightnessDetector")
    
    # Ensure directory exists
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)
    
    return os.path.join(config_dir, "config.json")


def load_config():
    """Load configuration from file or create default if not exists"""
    config_path = get_config_path()
    
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                
            # Merge with default to ensure all keys exist
            merged_config = DEFAULT_CONFIG.copy()
            for section, values in config.items():
                if section in merged_config:
                    merged_config[section].update(values)
            
            return merged_config
        except Exception as e:
            print(f"Error loading config: {e}")
    
    # If no config or error, create and return default
    save_config(DEFAULT_CONFIG)
    return DEFAULT_CONFIG


def save_config(config):
    """Save configuration to file"""
    config_path = get_config_path()
    
    try:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False


def update_config(updates):
    """Update specific config values"""
    config = load_config()
    
    for section, values in updates.items():
        if section in config:
            config[section].update(values)
    
    save_config(config)
    return config

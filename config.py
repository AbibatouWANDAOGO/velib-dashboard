"""
Configuration file for the Velib Dashboard project.
Contains all constants and configuration parameters.
"""

from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
CLEANED_DATA_DIR = DATA_DIR / "cleaned"
IMAGES_DIR = PROJECT_ROOT / "images"

# Data files
STATION_INFO_FILE = RAW_DATA_DIR / "station_information.csv"
STATION_STATUS_FILE = RAW_DATA_DIR / "station_statut.csv"
CLEANED_DATA_FILE = CLEANED_DATA_DIR / "velib_merged_data.csv"

# API URLs (for future updates)
VELIB_API_BASE_URL = "https://velib-metropole-opendata.smovengo.cloud/opendata/Velib_Metropole"
STATION_INFO_URL = f"{VELIB_API_BASE_URL}/station_information.json"
STATION_STATUS_URL = f"{VELIB_API_BASE_URL}/station_status.json"

# Dashboard configuration
DASHBOARD_TITLE = "Vélib' Métropole - Analyse des Stations"
DASHBOARD_HOST = "127.0.0.1"
DASHBOARD_PORT = 8060
DEBUG_MODE = False  # Set to False for production

# Database configuration
USE_DATABASE = True  # Use SQLite database for data storage
USE_LIVE_DATA = True  # Fetch real-time data from the Vélib' API at startup (falls back to local data if offline)
DATABASE_FILE = DATA_DIR / "velib_data.db"

# Cache configuration
ENABLE_CACHE = True
CACHE_TIMEOUT = 300  # 5 minutes

# Map configuration
DEFAULT_MAP_CENTER = [48.8566, 2.3522]  # Paris center
DEFAULT_MAP_ZOOM = 12
MAP_STYLE = "open-street-map"

# Color schemes for visualizations
COLORS = {
    'primary': '#1f77b4',
    'secondary': '#ff7f0e',
    'success': '#2ca02c',
    'danger': '#d62728',
    'warning': '#ff9800',
    'info': '#17a2b8',
    'mechanical': '#2196F3',
    'ebike': '#4CAF50',
    'available': '#4CAF50',
    'low': '#FF9800',
    'empty': '#F44336'
}

# Thresholds
LOW_AVAILABILITY_THRESHOLD = 5  # Number of bikes below which station is considered "low"
EMPTY_THRESHOLD = 0

# CSV delimiters
INFO_DELIMITER = ';'
STATUS_DELIMITER = ','

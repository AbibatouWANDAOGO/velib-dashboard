"""
Module for fetching Velib data from API or local files.
Handles data retrieval and initial loading.
"""

import requests
import pandas as pd
from pathlib import Path
from typing import Optional
import logging

from config import (
    STATION_INFO_URL,
    STATION_STATUS_URL,
    STATION_INFO_FILE,
    STATION_STATUS_FILE,
    INFO_DELIMITER,
    STATUS_DELIMITER
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def fetch_data_from_api(url: str, timeout: int = 10) -> Optional[dict]:
    """
    Fetch data from Velib API.
    
    Args:
        url: API endpoint URL
        timeout: Request timeout in seconds
        
    Returns:
        JSON data as dictionary or None if request fails
    """
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching data from {url}: {e}")
        return None


def count_bike_type(types: object, bike_type: str) -> int:
    """
    Count the bikes of one type in the API's num_bikes_available_types field.

    Args:
        types: List of single-key dicts, e.g. [{"mechanical": 4}, {"ebike": 2}]
        bike_type: Key to sum ("mechanical" or "ebike")

    Returns:
        Number of bikes of that type (0 if the field is missing)
    """
    if not isinstance(types, list):
        return 0
    return sum(int(t.get(bike_type, 0)) for t in types if isinstance(t, dict))


def load_station_information(use_local: bool = True) -> pd.DataFrame:
    """
    Load station information data.
    
    Args:
        use_local: If True, load from local CSV file. If False, fetch from API.
        
    Returns:
        DataFrame containing station information
    """
    if use_local:
        logger.info(f"Loading station information from {STATION_INFO_FILE}")
        try:
            df = pd.read_csv(STATION_INFO_FILE, delimiter=INFO_DELIMITER)
            logger.info(f"Loaded {len(df)} stations from local file")
            return df
        except Exception as e:
            logger.error(f"Error loading local file: {e}")
            raise
    else:
        logger.info("Fetching station information from API")
        data = fetch_data_from_api(STATION_INFO_URL)
        if data and 'data' in data and 'stations' in data['data']:
            df = pd.DataFrame(data['data']['stations'])
            logger.info(f"Fetched {len(df)} stations from API")
            return df
        else:
            raise ValueError("Failed to fetch data from API")


def load_station_status(use_local: bool = True) -> pd.DataFrame:
    """
    Load station status data.
    
    Args:
        use_local: If True, load from local CSV file. If False, fetch from API.
        
    Returns:
        DataFrame containing station status
    """
    if use_local:
        logger.info(f"Loading station status from {STATION_STATUS_FILE}")
        try:
            df = pd.read_csv(STATION_STATUS_FILE, delimiter=STATUS_DELIMITER)
            logger.info(f"Loaded status for {len(df)} stations from local file")
            return df
        except Exception as e:
            logger.error(f"Error loading local file: {e}")
            raise
    else:
        logger.info("Fetching station status from API")
        data = fetch_data_from_api(STATION_STATUS_URL)
        if data and 'data' in data and 'stations' in data['data']:
            df = pd.DataFrame(data['data']['stations'])
            # The API nests bike types as [{"mechanical": n}, {"ebike": m}]:
            # flatten them into the same columns as the local CSV export
            if 'num_bikes_available_types' in df.columns:
                types = df.pop('num_bikes_available_types')
                df['num_bikes_available_types/0/mechanical'] = types.map(lambda t: count_bike_type(t, 'mechanical'))
                df['num_bikes_available_types/1/ebike'] = types.map(lambda t: count_bike_type(t, 'ebike'))
            logger.info(f"Fetched status for {len(df)} stations from API")
            return df
        else:
            raise ValueError("Failed to fetch data from API")


def save_data_to_csv(df: pd.DataFrame, filepath: Path, delimiter: str = ',') -> None:
    """
    Save DataFrame to CSV file.
    
    Args:
        df: DataFrame to save
        filepath: Path where to save the file
        delimiter: CSV delimiter character
    """
    try:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(filepath, index=False, sep=delimiter)
        logger.info(f"Data saved to {filepath}")
    except Exception as e:
        logger.error(f"Error saving data to {filepath}: {e}")
        raise


def get_all_data(use_local: bool = True) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load both station information and status data.
    
    Args:
        use_local: If True, load from local files. If False, fetch from API.
        
    Returns:
        Tuple of (station_info_df, station_status_df)
    """
    station_info = load_station_information(use_local=use_local)
    station_status = load_station_status(use_local=use_local)

    return station_info, station_status


if __name__ == "__main__":
    # Test the module
    print("Testing data loading...")
    info_df, status_df = get_all_data(use_local=True)
    print(f"\nStation Information shape: {info_df.shape}")
    print(f"Station Status shape: {status_df.shape}")
    print("\nFirst rows of Station Information:")
    print(info_df.head())
    print("\nFirst rows of Station Status:")
    print(status_df.head())

"""Data extraction module for Satisfactory CommunityResources."""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import requests


logger = logging.getLogger(__name__)


class DataExtractor:
    """Extracts and processes Satisfactory game data from community resources."""
    
    def __init__(self, source_url: Optional[str] = None):
        """Initialize the data extractor.
        
        Args:
            source_url: URL to the fr.json community resources file
        """
        self.source_url = source_url or (
            "https://github.com/ficsit-felix/satisfactory-community-resources/"
            "raw/main/GameData/fr.json"
        )
        
    def fetch_data(self) -> Dict[str, Any]:
        """Fetch raw game data from the community resources.
        
        Returns:
            Raw game data as a dictionary
            
        Raises:
            requests.RequestException: If data fetching fails
        """
        logger.info(f"Fetching data from {self.source_url}")
        
        try:
            response = requests.get(self.source_url, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to fetch data: {e}")
            raise
            
    def save_data(self, data: Dict[str, Any], filepath: Path) -> None:
        """Save extracted data to file.
        
        Args:
            data: Game data dictionary
            filepath: Path to save the data
        """
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
        logger.info(f"Data saved to {filepath}")
        
    def load_data(self, filepath: Path) -> Dict[str, Any]:
        """Load game data from file.
        
        Args:
            filepath: Path to the data file
            
        Returns:
            Game data dictionary
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
            
    def extract_and_save(self, filepath: Path) -> Dict[str, Any]:
        """Extract data from source and save to file.
        
        Args:
            filepath: Path to save the extracted data
            
        Returns:
            Extracted game data
        """
        data = self.fetch_data()
        self.save_data(data, filepath)
        return data
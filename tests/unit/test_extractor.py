"""Unit tests for the data extractor module."""

import pytest
import json
from unittest.mock import Mock, patch
from pathlib import Path

from satisgraph.extractor import DataExtractor


class TestDataExtractor:
    """Test cases for DataExtractor class."""
    
    def test_init_default_url(self):
        """Test initialization with default URL."""
        extractor = DataExtractor()
        assert "satisfactory-community-resources" in extractor.source_url
        assert extractor.source_url.endswith("fr.json")
        
    def test_init_custom_url(self):
        """Test initialization with custom URL."""
        custom_url = "https://example.com/test.json"
        extractor = DataExtractor(custom_url)
        assert extractor.source_url == custom_url
        
    @patch('satisgraph.extractor.requests.get')
    def test_fetch_data_success(self, mock_get):
        """Test successful data fetching."""
        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = {"test": "data"}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        extractor = DataExtractor()
        data = extractor.fetch_data()
        
        assert data == {"test": "data"}
        mock_get.assert_called_once_with(extractor.source_url, timeout=30)
        
    @patch('satisgraph.extractor.requests.get')
    def test_fetch_data_failure(self, mock_get):
        """Test data fetching failure."""
        mock_get.side_effect = Exception("Network error")
        
        extractor = DataExtractor()
        with pytest.raises(Exception, match="Network error"):
            extractor.fetch_data()
            
    def test_save_and_load_data(self, temp_dir, sample_game_data):
        """Test saving and loading data."""
        extractor = DataExtractor()
        filepath = temp_dir / "test_data.json"
        
        # Save data
        extractor.save_data(sample_game_data, filepath)
        assert filepath.exists()
        
        # Load data
        loaded_data = extractor.load_data(filepath)
        assert loaded_data == sample_game_data
        
    @patch('satisgraph.extractor.DataExtractor.fetch_data')
    def test_extract_and_save(self, mock_fetch, temp_dir, sample_game_data):
        """Test extract and save workflow."""
        mock_fetch.return_value = sample_game_data
        
        extractor = DataExtractor()
        filepath = temp_dir / "extracted_data.json"
        
        result = extractor.extract_and_save(filepath)
        
        assert result == sample_game_data
        assert filepath.exists()
        
        # Verify saved content
        with open(filepath, 'r') as f:
            saved_data = json.load(f)
        assert saved_data == sample_game_data
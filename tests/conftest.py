"""Test configuration and utilities."""

import pytest
import tempfile
from pathlib import Path


@pytest.fixture
def temp_dir():
    """Provide a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture  
def sample_game_data():
    """Provide sample game data for testing."""
    return {
        "items": [
            {
                "name": "iron_ore",
                "displayName": "Iron Ore",
                "category": "resources",
                "stackSize": 100
            },
            {
                "name": "iron_ingot", 
                "displayName": "Iron Ingot",
                "category": "ingots",
                "stackSize": 100
            }
        ],
        "buildings": [
            {
                "name": "smelter",
                "displayName": "Smelter",
                "category": "smelting",
                "powerConsumption": 4.0
            }
        ],
        "recipes": [
            {
                "name": "iron_ingot_recipe",
                "inputs": {"iron_ore": 1.0},
                "outputs": {"iron_ingot": 1.0},
                "building": "smelter",
                "time": 2.0
            }
        ]
    }
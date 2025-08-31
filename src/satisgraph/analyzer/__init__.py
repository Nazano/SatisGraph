"""Data analysis modules for Satisfactory game data."""

import logging
from typing import Dict, Any, List, Set
from dataclasses import dataclass


logger = logging.getLogger(__name__)


@dataclass
class Recipe:
    """Represents a Satisfactory recipe."""
    name: str
    inputs: Dict[str, float]
    outputs: Dict[str, float]
    building: str
    time: float


@dataclass
class Item:
    """Represents a Satisfactory item."""
    name: str
    display_name: str
    category: str
    stack_size: int


@dataclass
class Building:
    """Represents a Satisfactory building."""
    name: str
    display_name: str
    category: str
    power_consumption: float


class RecipeAnalyzer:
    """Analyzes recipes and production chains."""
    
    def __init__(self, game_data: Dict[str, Any]):
        """Initialize with game data."""
        self.game_data = game_data
        self._recipes = None
        
    @property
    def recipes(self) -> List[Recipe]:
        """Get all recipes from game data."""
        if self._recipes is None:
            self._recipes = self._parse_recipes()
        return self._recipes
        
    def _parse_recipes(self) -> List[Recipe]:
        """Parse recipes from raw game data."""
        recipes = []
        
        # This is a placeholder - actual parsing would depend on fr.json structure
        if 'recipes' in self.game_data:
            for recipe_data in self.game_data['recipes']:
                recipe = Recipe(
                    name=recipe_data.get('name', ''),
                    inputs=recipe_data.get('inputs', {}),
                    outputs=recipe_data.get('outputs', {}),
                    building=recipe_data.get('building', ''),
                    time=recipe_data.get('time', 0.0)
                )
                recipes.append(recipe)
                
        return recipes
        
    def find_production_chain(self, target_item: str) -> List[Recipe]:
        """Find the production chain for a target item."""
        chain = []
        
        # Simple implementation - find recipes that produce the target item
        for recipe in self.recipes:
            if target_item in recipe.outputs:
                chain.append(recipe)
                
        return chain


class ItemAnalyzer:
    """Analyzes items and their properties."""
    
    def __init__(self, game_data: Dict[str, Any]):
        """Initialize with game data."""
        self.game_data = game_data
        self._items = None
        
    @property  
    def items(self) -> List[Item]:
        """Get all items from game data."""
        if self._items is None:
            self._items = self._parse_items()
        return self._items
        
    def _parse_items(self) -> List[Item]:
        """Parse items from raw game data."""
        items = []
        
        # Placeholder parsing logic
        if 'items' in self.game_data:
            for item_data in self.game_data['items']:
                item = Item(
                    name=item_data.get('name', ''),
                    display_name=item_data.get('displayName', ''),
                    category=item_data.get('category', ''),
                    stack_size=item_data.get('stackSize', 1)
                )
                items.append(item)
                
        return items


class BuildingAnalyzer:
    """Analyzes buildings and their capabilities."""
    
    def __init__(self, game_data: Dict[str, Any]):
        """Initialize with game data."""
        self.game_data = game_data
        self._buildings = None
        
    @property
    def buildings(self) -> List[Building]:
        """Get all buildings from game data."""
        if self._buildings is None:
            self._buildings = self._parse_buildings()
        return self._buildings
        
    def _parse_buildings(self) -> List[Building]:
        """Parse buildings from raw game data."""
        buildings = []
        
        # Placeholder parsing logic  
        if 'buildings' in self.game_data:
            for building_data in self.game_data['buildings']:
                building = Building(
                    name=building_data.get('name', ''),
                    display_name=building_data.get('displayName', ''),
                    category=building_data.get('category', ''),
                    power_consumption=building_data.get('powerConsumption', 0.0)
                )
                buildings.append(building)
                
        return buildings
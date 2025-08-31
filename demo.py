#!/usr/bin/env python3
"""Demo script showing SatisGraph functionality."""

import sys
import json
from pathlib import Path

# Add src to path for demo
sys.path.insert(0, str(Path(__file__).parent / "src"))

from satisgraph.extractor import DataExtractor
from satisgraph.analyzer import RecipeAnalyzer, ItemAnalyzer, BuildingAnalyzer


def main():
    """Run SatisGraph demo."""
    print("🎮 SatisGraph Demo")
    print("==================")
    
    # Sample Satisfactory-like game data
    sample_data = {
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
            },
            {
                "name": "iron_plate",
                "displayName": "Iron Plate",
                "category": "parts",
                "stackSize": 200
            }
        ],
        "buildings": [
            {
                "name": "smelter",
                "displayName": "Smelter",
                "category": "smelting",
                "powerConsumption": 4.0
            },
            {
                "name": "constructor",
                "displayName": "Constructor", 
                "category": "assembly",
                "powerConsumption": 8.0
            }
        ],
        "recipes": [
            {
                "name": "iron_ingot_recipe",
                "inputs": {"iron_ore": 1.0},
                "outputs": {"iron_ingot": 1.0},
                "building": "smelter",
                "time": 2.0
            },
            {
                "name": "iron_plate_recipe",
                "inputs": {"iron_ingot": 3.0},
                "outputs": {"iron_plate": 2.0},
                "building": "constructor", 
                "time": 6.0
            }
        ]
    }
    
    print("📊 Analyzing sample game data...")
    
    # Test data analyzers
    recipe_analyzer = RecipeAnalyzer(sample_data)
    item_analyzer = ItemAnalyzer(sample_data)
    building_analyzer = BuildingAnalyzer(sample_data)
    
    recipes = recipe_analyzer.recipes
    items = item_analyzer.items
    buildings = building_analyzer.buildings
    
    print(f"\n✅ Analysis Results:")
    print(f"   • Items: {len(items)}")
    print(f"   • Buildings: {len(buildings)}")
    print(f"   • Recipes: {len(recipes)}")
    
    print(f"\n🏭 Buildings Found:")
    for building in buildings:
        print(f"   • {building.display_name} ({building.name}) - {building.power_consumption}MW")
        
    print(f"\n📦 Items Found:")
    for item in items:
        print(f"   • {item.display_name} ({item.name}) - Stack: {item.stack_size}")
        
    print(f"\n⚙️ Recipes Found:")
    for recipe in recipes:
        inputs_str = ", ".join([f"{amt} {item}" for item, amt in recipe.inputs.items()])
        outputs_str = ", ".join([f"{amt} {item}" for item, amt in recipe.outputs.items()])
        print(f"   • {recipe.name}: {inputs_str} → {outputs_str} ({recipe.time}s)")
        
    print(f"\n🔍 Production Chain Analysis:")
    chain = recipe_analyzer.find_production_chain("iron_plate")
    if chain:
        print(f"   Iron Plate can be produced by:")
        for recipe in chain:
            print(f"     - {recipe.name} using {recipe.building}")
    else:
        print("   No production chain found for iron_plate")
        
    print(f"\n🎯 Demo completed successfully!")
    print(f"   Next steps: Set up Neo4j and run 'satisgraph extract' with real data")


if __name__ == "__main__":
    main()
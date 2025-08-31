"""Neo4j graph database integration module."""

import logging
from typing import Dict, Any, List, Optional
from neo4j import GraphDatabase, Session
from ..analyzer import Recipe, Item, Building


logger = logging.getLogger(__name__)


class Neo4jConnector:
    """Manages Neo4j database connections."""
    
    def __init__(self, uri: str, username: str, password: str, database: str = "neo4j"):
        """Initialize Neo4j connector.
        
        Args:
            uri: Neo4j database URI
            username: Database username
            password: Database password  
            database: Database name
        """
        self.uri = uri
        self.username = username
        self.password = password
        self.database = database
        self._driver = None
        
    def connect(self) -> None:
        """Establish connection to Neo4j."""
        try:
            self._driver = GraphDatabase.driver(
                self.uri, 
                auth=(self.username, self.password)
            )
            # Test connection
            with self._driver.session() as session:
                session.run("RETURN 1")
            logger.info("Connected to Neo4j database")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise
            
    def close(self) -> None:
        """Close Neo4j connection."""
        if self._driver:
            self._driver.close()
            logger.info("Closed Neo4j connection")
            
    def get_session(self) -> Session:
        """Get a Neo4j session."""
        if not self._driver:
            self.connect()
        return self._driver.session(database=self.database)
        
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


class GraphLoader:
    """Loads game data into Neo4j graph database."""
    
    def __init__(self, connector: Neo4jConnector):
        """Initialize with Neo4j connector."""
        self.connector = connector
        
    def create_constraints(self) -> None:
        """Create database constraints and indexes."""
        constraints = [
            "CREATE CONSTRAINT item_name IF NOT EXISTS FOR (i:Item) REQUIRE i.name IS UNIQUE",
            "CREATE CONSTRAINT recipe_name IF NOT EXISTS FOR (r:Recipe) REQUIRE r.name IS UNIQUE",
            "CREATE CONSTRAINT building_name IF NOT EXISTS FOR (b:Building) REQUIRE b.name IS UNIQUE"
        ]
        
        with self.connector.get_session() as session:
            for constraint in constraints:
                try:
                    session.run(constraint)
                    logger.info(f"Created constraint: {constraint}")
                except Exception as e:
                    logger.warning(f"Constraint already exists or failed: {e}")
                    
    def clear_data(self) -> None:
        """Clear all existing data from the database."""
        with self.connector.get_session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            logger.info("Cleared all existing data")
            
    def load_items(self, items: List[Item]) -> None:
        """Load items into the graph."""
        query = """
        UNWIND $items AS item
        MERGE (i:Item {name: item.name})
        SET i.displayName = item.display_name,
            i.category = item.category,
            i.stackSize = item.stack_size
        """
        
        items_data = [
            {
                "name": item.name,
                "display_name": item.display_name,
                "category": item.category,
                "stack_size": item.stack_size
            }
            for item in items
        ]
        
        with self.connector.get_session() as session:
            session.run(query, items=items_data)
            logger.info(f"Loaded {len(items)} items")
            
    def load_buildings(self, buildings: List[Building]) -> None:
        """Load buildings into the graph."""
        query = """
        UNWIND $buildings AS building
        MERGE (b:Building {name: building.name})
        SET b.displayName = building.display_name,
            b.category = building.category,
            b.powerConsumption = building.power_consumption
        """
        
        buildings_data = [
            {
                "name": building.name,
                "display_name": building.display_name,
                "category": building.category,
                "power_consumption": building.power_consumption
            }
            for building in buildings
        ]
        
        with self.connector.get_session() as session:
            session.run(query, buildings=buildings_data)
            logger.info(f"Loaded {len(buildings)} buildings")
            
    def load_recipes(self, recipes: List[Recipe]) -> None:
        """Load recipes and their relationships into the graph."""
        # Create recipe nodes
        recipe_query = """
        UNWIND $recipes AS recipe
        MERGE (r:Recipe {name: recipe.name})
        SET r.time = recipe.time
        """
        
        # Create relationships for inputs
        input_query = """
        UNWIND $recipe_inputs AS ri
        MATCH (r:Recipe {name: ri.recipe_name})
        MATCH (i:Item {name: ri.item_name})
        MERGE (i)-[rel:INPUT_TO]->(r)
        SET rel.amount = ri.amount
        """
        
        # Create relationships for outputs
        output_query = """
        UNWIND $recipe_outputs AS ro
        MATCH (r:Recipe {name: ro.recipe_name})
        MATCH (i:Item {name: ro.item_name})
        MERGE (r)-[rel:PRODUCES]->(i)
        SET rel.amount = ro.amount
        """
        
        # Create relationships to buildings
        building_query = """
        UNWIND $recipe_buildings AS rb
        MATCH (r:Recipe {name: rb.recipe_name})
        MATCH (b:Building {name: rb.building_name})
        MERGE (r)-[:REQUIRES_BUILDING]->(b)
        """
        
        with self.connector.get_session() as session:
            # Load recipes
            recipes_data = [
                {"name": recipe.name, "time": recipe.time}
                for recipe in recipes
            ]
            session.run(recipe_query, recipes=recipes_data)
            
            # Load input relationships
            recipe_inputs = []
            for recipe in recipes:
                for item_name, amount in recipe.inputs.items():
                    recipe_inputs.append({
                        "recipe_name": recipe.name,
                        "item_name": item_name,
                        "amount": amount
                    })
            if recipe_inputs:
                session.run(input_query, recipe_inputs=recipe_inputs)
                
            # Load output relationships
            recipe_outputs = []
            for recipe in recipes:
                for item_name, amount in recipe.outputs.items():
                    recipe_outputs.append({
                        "recipe_name": recipe.name,
                        "item_name": item_name,
                        "amount": amount
                    })
            if recipe_outputs:
                session.run(output_query, recipe_outputs=recipe_outputs)
                
            # Load building relationships
            recipe_buildings = [
                {"recipe_name": recipe.name, "building_name": recipe.building}
                for recipe in recipes if recipe.building
            ]
            if recipe_buildings:
                session.run(building_query, recipe_buildings=recipe_buildings)
                
            logger.info(f"Loaded {len(recipes)} recipes with relationships")
            
    def load_all(self, items: List[Item], buildings: List[Building], recipes: List[Recipe]) -> None:
        """Load all game data into the graph."""
        self.create_constraints()
        self.load_items(items)
        self.load_buildings(buildings)
        self.load_recipes(recipes)
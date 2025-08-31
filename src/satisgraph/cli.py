"""Command line interface for SatisGraph."""

import click
import logging
from pathlib import Path
from .utils import load_config, setup_logging, get_default_config_path
from .extractor import DataExtractor
from .analyzer import RecipeAnalyzer, ItemAnalyzer, BuildingAnalyzer
from .graph import Neo4jConnector, GraphLoader


logger = logging.getLogger(__name__)


@click.group()
@click.option('--config', '-c', type=click.Path(exists=True), 
              help='Configuration file path')
@click.pass_context
def cli(ctx, config):
    """SatisGraph: Satisfactory game data pipeline and analysis tool."""
    ctx.ensure_object(dict)
    
    # Load configuration
    if config:
        config_path = Path(config)
    else:
        config_path = get_default_config_path()
        
    ctx.obj['config'] = load_config(config_path)
    setup_logging(ctx.obj['config'])


@cli.command()
@click.option('--output', '-o', type=click.Path(), default='data/raw/fr.json',
              help='Output file path for extracted data')
@click.pass_context
def extract(ctx, output):
    """Extract Satisfactory game data from community resources."""
    config = ctx.obj['config']
    data_sources = config.get('data_sources', {})
    source_url = data_sources.get('satisfactory_community_resources')
    
    extractor = DataExtractor(source_url)
    output_path = Path(output)
    
    try:
        data = extractor.extract_and_save(output_path)
        click.echo(f"Successfully extracted data to {output_path}")
        click.echo(f"Data contains {len(data)} top-level keys")
    except Exception as e:
        click.echo(f"Error extracting data: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.option('--input', '-i', type=click.Path(exists=True), 
              default='data/raw/fr.json', help='Input data file path')
@click.pass_context
def analyze(ctx, input):
    """Analyze extracted game data."""
    input_path = Path(input)
    
    try:
        extractor = DataExtractor()
        data = extractor.load_data(input_path)
        
        recipe_analyzer = RecipeAnalyzer(data)
        item_analyzer = ItemAnalyzer(data)
        building_analyzer = BuildingAnalyzer(data)
        
        recipes = recipe_analyzer.recipes
        items = item_analyzer.items
        buildings = building_analyzer.buildings
        
        click.echo(f"Analysis complete:")
        click.echo(f"  Recipes: {len(recipes)}")
        click.echo(f"  Items: {len(items)}")
        click.echo(f"  Buildings: {len(buildings)}")
        
    except Exception as e:
        click.echo(f"Error analyzing data: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.option('--input', '-i', type=click.Path(exists=True),
              default='data/raw/fr.json', help='Input data file path')
@click.option('--clear', is_flag=True, help='Clear existing data before loading')
@click.pass_context
def load(ctx, input, clear):
    """Load analyzed data into Neo4j graph database."""
    config = ctx.obj['config']
    neo4j_config = config.get('neo4j', {})
    
    input_path = Path(input)
    
    try:
        # Extract and analyze data
        extractor = DataExtractor()
        data = extractor.load_data(input_path)
        
        recipe_analyzer = RecipeAnalyzer(data)
        item_analyzer = ItemAnalyzer(data)
        building_analyzer = BuildingAnalyzer(data)
        
        recipes = recipe_analyzer.recipes
        items = item_analyzer.items
        buildings = building_analyzer.buildings
        
        # Connect to Neo4j and load data
        connector = Neo4jConnector(
            uri=neo4j_config.get('uri', 'bolt://localhost:7687'),
            username=neo4j_config.get('username', 'neo4j'),
            password=neo4j_config.get('password', 'password'),
            database=neo4j_config.get('database', 'neo4j')
        )
        
        loader = GraphLoader(connector)
        
        with connector:
            if clear:
                loader.clear_data()
                click.echo("Cleared existing data")
                
            loader.load_all(items, buildings, recipes)
            click.echo("Successfully loaded data into Neo4j")
            
    except Exception as e:
        click.echo(f"Error loading data: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.argument('item_name')
@click.pass_context
def chain(ctx, item_name):
    """Find production chain for an item."""
    config = ctx.obj['config']
    neo4j_config = config.get('neo4j', {})
    
    try:
        connector = Neo4jConnector(
            uri=neo4j_config.get('uri', 'bolt://localhost:7687'),
            username=neo4j_config.get('username', 'neo4j'),
            password=neo4j_config.get('password', 'password'),
            database=neo4j_config.get('database', 'neo4j')
        )
        
        with connector:
            with connector.get_session() as session:
                # Simple query to find recipes that produce the item
                query = """
                MATCH (i:Item {name: $item_name})<-[p:PRODUCES]-(r:Recipe)
                RETURN r.name as recipe, p.amount as amount
                """
                result = session.run(query, item_name=item_name)
                
                recipes = list(result)
                if recipes:
                    click.echo(f"Production recipes for {item_name}:")
                    for record in recipes:
                        click.echo(f"  - {record['recipe']}: {record['amount']} units")
                else:
                    click.echo(f"No production recipes found for {item_name}")
                    
    except Exception as e:
        click.echo(f"Error querying production chain: {e}", err=True)
        raise click.Abort()


def main():
    """Main entry point."""
    cli()
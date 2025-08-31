# SatisGraph

A lightweight data pipeline that extracts Satisfactory CommunityResources (fr.json), analyzes recipes, items, and buildings, and loads a Neo4j graph to enable graph queries and production‑chain analysis.

## Features

- **Data Extraction**: Automatically fetches and processes Satisfactory game data from community resources
- **Data Analysis**: Analyzes recipes, items, and buildings with comprehensive parsing and validation
- **Graph Database**: Loads data into Neo4j for powerful graph queries and relationship analysis
- **Production Chains**: Query and analyze production chains and dependencies
- **CLI Interface**: Easy-to-use command line interface for all operations

## Quick Start

### Prerequisites

- Python 3.8+
- Neo4j Database (optional, for graph features)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/Nazano/SatisGraph.git
cd SatisGraph
```

2. Run the setup script:
```bash
./setup.sh
```

### Usage

#### Extract Game Data
```bash
satisgraph extract --output data/raw/fr.json
```

#### Analyze Data
```bash
satisgraph analyze --input data/raw/fr.json
```

#### Load into Neo4j
```bash
satisgraph load --input data/raw/fr.json --clear
```

#### Query Production Chains
```bash
satisgraph chain "iron_ingot"
```

### Configuration

Edit `config/default.yaml` to configure:
- Neo4j connection settings
- Data source URLs
- Logging preferences
- Processing options

## Development

### Project Structure

```
SatisGraph/
├── src/satisgraph/          # Main package
│   ├── extractor/           # Data extraction modules
│   ├── analyzer/            # Data analysis modules
│   ├── graph/               # Neo4j integration
│   ├── utils/               # Utility functions
│   └── cli.py              # Command line interface
├── tests/                   # Test suite
├── config/                  # Configuration files
├── docs/                    # Documentation
└── data/                    # Data directories
```

### Running Tests

```bash
pytest tests/
```

### Code Formatting

```bash
black src/ tests/
flake8 src/ tests/
```

## Project Milestones

See [project_todo_milestones.md](project_todo_milestones.md) for detailed development milestones and progress tracking.

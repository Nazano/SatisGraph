#!/bin/bash

# SatisGraph Setup Script
echo "Setting up SatisGraph development environment..."

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Install package in development mode
pip install -e .

# Create data directories
mkdir -p data/{raw,processed,cache}
mkdir -p logs

echo "Setup complete!"
echo "To activate the environment, run: source venv/bin/activate"
echo "To run the CLI, use: satisgraph --help"
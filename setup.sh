#!/bin/bash
echo "Setting up virtual environment..."
python3 -m venv .venv
source .venv/bin/activate
echo "Installing requirements..."
pip install -r requirements.txt
echo ""
echo "Setup complete!"
echo ""
echo "To activate the environment, run: source .venv/bin/activate"
echo "To run the visualizer, run: python main.py"
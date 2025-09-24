@echo off
echo Setting up virtual environment...
python -m venv .venv
call .venv\Scripts\activate
echo Installing requirements...
pip install -r requirements.txt
echo.
echo Setup complete!
echo.
echo To activate the environment, run: .venv\Scripts\activate
echo To run the visualizer, run: python main.py
#!/usr/bin/env python
"""
Main entry point for the Trading Bot application.
Run this script from the project root directory.
"""

import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import and run the trading bot
from trading_bot.bot import main

if __name__ == "__main__":
    main()

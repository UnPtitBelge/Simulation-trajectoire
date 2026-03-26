#!/usr/bin/env python3
"""Main entry point for Simulation Trajectoire application.

Usage:
    python main.py [mode]

Available modes:
    normal      - Default mode (no argument)
    presentation - Presentation mode
    libre       - Libre mode
"""

import sys
from src.application.app import MainApplication

if __name__ == "__main__":
    # Get mode from command line arguments
    mode = sys.argv[1] if len(sys.argv) > 1 else "normal"
    
    # Validate mode
    valid_modes = ["normal", "presentation", "libre"]
    if mode not in valid_modes:
        print(f"Error: Invalid mode '{mode}'")
        print(f"Valid modes are: {', '.join(valid_modes)}")
        sys.exit(1)
    
    # Create and run application
    app = MainApplication(mode=mode)
    app.run()
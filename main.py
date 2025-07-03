#!/usr/bin/env python3
"""
SSH Client - Professional Terminal Application
Main entry point for the desktop application
"""

import sys
import os
import logging
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('ssh_client.log')
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Main application entry point"""
    try:
        logger.info("Starting SSH Client...")
        
        # Import here to avoid circular imports
        from gui.main_window import MainWindow
        
        # Create and run the main window
        app = MainWindow()
        
        # Set up closing handler
        app.protocol("WM_DELETE_WINDOW", app.on_closing)
        
        # Start the application
        app.mainloop()
        
    except Exception as e:
        logger.error(f"Application failed to start: {e}")
        sys.exit(1)
    finally:
        logger.info("SSH Client stopped")

if __name__ == "__main__":
    main() 
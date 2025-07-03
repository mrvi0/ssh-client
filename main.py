#!/usr/bin/env python3
"""
SSH Client Desktop Application

A simple SSH client with local data storage and command management.
"""

import sys
import os
import signal
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from gui.main_window import MainWindow


def signal_handler(signum, frame):
    """Handle system signals for graceful shutdown"""
    print("\nShutting down SSH Client...")
    sys.exit(0)


def main():
    """Main application entry point"""
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Create and run main window
        app = MainWindow()
        
        # Set up cleanup on exit
        def cleanup():
            app.cleanup()
            
        app.root.protocol("WM_DELETE_WINDOW", lambda: [cleanup(), app.root.quit()])
        
        print("Starting SSH Client...")
        app.run()
        
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
    except Exception as e:
        print(f"Error starting application: {e}")
        sys.exit(1)
    finally:
        print("SSH Client stopped")


if __name__ == "__main__":
    main() 
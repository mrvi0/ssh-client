#!/usr/bin/env python3
"""
Installation script for SSH Client application
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(command, description):
    """Run a command and handle errors"""
    print(f"Running: {description}")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✓ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False


def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("✗ Python 3.8 or higher is required")
        return False
    print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    return True


def install_dependencies():
    """Install required dependencies"""
    print("\n=== Installing Dependencies ===")
    
    # Check if pip is available
    if not run_command("python -m pip --version", "Checking pip"):
        print("✗ pip is not available. Please install pip first.")
        return False
    
    # Install desktop dependencies
    if not run_command("python -m pip install -r requirements.txt", "Installing desktop dependencies"):
        return False
    
    # Install web dependencies (optional)
    if os.path.exists("requirements_web.txt"):
        print("\nWeb dependencies found. Install them? (y/n): ", end="")
        if input().lower().startswith('y'):
            if not run_command("python -m pip install -r requirements_web.txt", "Installing web dependencies"):
                print("Warning: Web dependencies installation failed, but desktop app should still work")
    
    return True


def setup_directories():
    """Setup application directories"""
    print("\n=== Setting up Directories ===")
    
    # Create necessary directories
    directories = [
        "logs",
        "backups",
        "keys"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✓ Created directory: {directory}")
    
    return True


def create_config():
    """Create default configuration"""
    print("\n=== Creating Configuration ===")
    
    config_content = '''{
  "app": {
    "name": "SSH Client",
    "version": "1.0.0",
    "theme": "default",
    "language": "en"
  },
  "database": {
    "path": "ssh_client.db",
    "encryption_enabled": true
  },
  "ssh": {
    "default_port": 22,
    "timeout": 30,
    "keepalive_interval": 60
  },
  "ui": {
    "window_width": 1200,
    "window_height": 800,
    "font_size": 10,
    "font_family": "Consolas"
  },
  "security": {
    "auto_lock_timeout": 300,
    "require_password_on_startup": false
  }
}'''
    
    try:
        with open("config.json", "w") as f:
            f.write(config_content)
        print("✓ Created default configuration file")
        return True
    except Exception as e:
        print(f"✗ Failed to create configuration: {e}")
        return False


def test_installation():
    """Test if the application can be imported"""
    print("\n=== Testing Installation ===")
    
    try:
        # Test imports
        import tkinter
        print("✓ tkinter available")
        
        import paramiko
        print("✓ paramiko available")
        
        import cryptography
        print("✓ cryptography available")
        
        # Test application modules
        sys.path.insert(0, str(Path(__file__).parent))
        
        from models.database import DatabaseManager
        print("✓ Database module imported")
        
        from ssh.ssh_client import SSHClient
        print("✓ SSH client module imported")
        
        from gui.main_window import MainWindow
        print("✓ GUI module imported")
        
        return True
        
    except ImportError as e:
        print(f"✗ Import test failed: {e}")
        return False


def main():
    """Main installation function"""
    print("SSH Client Installation Script")
    print("=" * 40)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print("\n✗ Installation failed. Please check the errors above.")
        sys.exit(1)
    
    # Setup directories
    if not setup_directories():
        print("\n✗ Directory setup failed.")
        sys.exit(1)
    
    # Create configuration
    if not create_config():
        print("\n✗ Configuration creation failed.")
        sys.exit(1)
    
    # Test installation
    if not test_installation():
        print("\n✗ Installation test failed.")
        sys.exit(1)
    
    print("\n" + "=" * 40)
    print("✓ Installation completed successfully!")
    print("\nTo run the application:")
    print("  python main.py")
    print("\nTo run the web server (optional):")
    print("  python app.py")
    print("\nFor more information, see README.md")


if __name__ == "__main__":
    main() 
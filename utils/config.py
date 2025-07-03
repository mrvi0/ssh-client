"""
Configuration utilities for SSH Client application
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ConfigManager:
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default"""
        default_config = {
            "app": {
                "name": "SSH Client",
                "version": "1.0.0",
                "theme": "default",
                "language": "en"
            },
            "database": {
                "path": "ssh_client.db",
                "encryption_enabled": True
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
                "auto_lock_timeout": 300,  # 5 minutes
                "require_password_on_startup": False
            }
        }
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                logger.info("Loaded configuration from file")
                
                # Merge with default config to ensure all keys exist
                merged_config = self._merge_configs(default_config, config)
                return merged_config
            else:
                # Create default config file
                self._save_config(default_config)
                logger.info("Created default configuration file")
                return default_config
                
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            return default_config
            
    def _merge_configs(self, default: Dict[str, Any], user: Dict[str, Any]) -> Dict[str, Any]:
        """Merge user config with default config"""
        merged = default.copy()
        
        def merge_dicts(d1: Dict[str, Any], d2: Dict[str, Any]) -> Dict[str, Any]:
            result = d1.copy()
            for key, value in d2.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = merge_dicts(result[key], value)
                else:
                    result[key] = value
            return result
            
        return merge_dicts(merged, user)
        
    def _save_config(self, config: Dict[str, Any]):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key (supports dot notation)"""
        keys = key.split('.')
        value = self.config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
            
    def set(self, key: str, value: Any):
        """Set configuration value by key (supports dot notation)"""
        keys = key.split('.')
        config = self.config
        
        # Navigate to the parent of the target key
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
            
        # Set the value
        config[keys[-1]] = value
        
        # Save to file
        self._save_config(self.config)
        
    def save(self):
        """Save current configuration to file"""
        self._save_config(self.config)
        
    def reset_to_defaults(self):
        """Reset configuration to default values"""
        self.config = self._load_config()
        self._save_config(self.config)
        logger.info("Configuration reset to defaults")


class AppPaths:
    """Manage application paths and directories"""
    
    def __init__(self):
        self.app_name = "ssh-client"
        self.setup_paths()
        
    def setup_paths(self):
        """Setup application paths"""
        # Get user home directory
        home = Path.home()
        
        # Application data directory
        if os.name == 'nt':  # Windows
            self.data_dir = home / "AppData" / "Local" / self.app_name
        elif os.name == 'posix':  # Unix/Linux/macOS
            self.data_dir = home / ".config" / self.app_name
        else:
            self.data_dir = home / f".{self.app_name}"
            
        # Create directories if they don't exist
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Subdirectories
        self.logs_dir = self.data_dir / "logs"
        self.logs_dir.mkdir(exist_ok=True)
        
        self.keys_dir = self.data_dir / "keys"
        self.keys_dir.mkdir(exist_ok=True)
        
        self.backups_dir = self.data_dir / "backups"
        self.backups_dir.mkdir(exist_ok=True)
        
    def get_database_path(self) -> Path:
        """Get database file path"""
        return self.data_dir / "ssh_client.db"
        
    def get_config_path(self) -> Path:
        """Get configuration file path"""
        return self.data_dir / "config.json"
        
    def get_log_path(self) -> Path:
        """Get log file path"""
        return self.logs_dir / "ssh_client.log"
        
    def get_key_path(self) -> Path:
        """Get encryption key file path"""
        return self.data_dir / "encryption.key"
        
    def get_backup_path(self, filename: str) -> Path:
        """Get backup file path"""
        return self.backups_dir / filename


# Global instances
config_manager = ConfigManager()
app_paths = AppPaths() 
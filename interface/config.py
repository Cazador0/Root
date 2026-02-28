"""
Configuration management for managers and application settings.
"""
import json
import os
from utils.logger import get_logger


class Config:
    """Manage application and model configurations."""
    
    DEFAULT_CONFIG = {
        "o3": {
            "path": "./gpt-oss-20b-Q5_K_M.gguf",
            "n_ctx": 4096,
            "n_gpu_layers": -1,
            "n_threads": 8
        }
    }
    
    def __init__(self, config_file="models_config.json"):
        self.config_file = config_file
        self.logger = get_logger("Config")
        self.model_configs = {}
        self.load()
    
    def load(self):
        """Load configuration from JSON file."""
        try:
            with open(self.config_file, 'r') as f:
                self.model_configs = json.load(f)
            self.logger.info(f"Loaded config from {self.config_file}")
        except FileNotFoundError:
            self.logger.warning(f"Config file {self.config_file} not found, using defaults")
            self.model_configs = self.DEFAULT_CONFIG.copy()
            self.save()
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in {self.config_file}: {str(e)}")
            self.model_configs = self.DEFAULT_CONFIG.copy()
    
    def save(self):
        """Save configuration to JSON file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.model_configs, f, indent=2)
            self.logger.info(f"Saved config to {self.config_file}")
        except Exception as e:
            self.logger.error(f"Failed to save config: {str(e)}")
    
    def get_model_config(self, model_name):
        """Get configuration for a specific model."""
        return self.model_configs.get(model_name, {})
    
    def get_model_names(self):
        """Get list of all configured model names."""
        return list(self.model_configs.keys())
    
    def get_model_path(self, model_name):
        """Get the file path for a specific model."""

        config = self.get_model_config(model_name)
        return config.get("path", "")
    
    def add_model(self, model_name, config):
        """Add a new model configuration."""
        self.model_configs[model_name] = config
        self.save()
        self.logger.info(f"Added model: {model_name}")
    
    def remove_model(self, model_name):
        """Remove a model configuration."""
        if model_name in self.model_configs:
            del self.model_configs[model_name]
            self.save()
            self.logger.info(f"Removed model: {model_name}")
    
    def update_model(self, model_name, config):
        """Update an existing model configuration."""
        if model_name in self.model_configs:
            self.model_configs[model_name].update(config)
            self.save()
            self.logger.info(f"Updated model: {model_name}")

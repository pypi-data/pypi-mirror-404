import yaml
import os
from typing import Dict, Any

class ConfigLoader:
    def __init__(self, config_path: str = "sentinel.yaml"):
        # We store the settings in this dictionary
        self._settings: Dict[str, Any] = {}
        self.config_path = config_path

    def load(self) -> Dict[str, Any]:
        """
        Reads the YAML file and converts it into a Python Dictionary.
        """
        if not os.path.exists(self.config_path):
            # If file is missing, return empty defaults to avoid crashing
            print(f"Warning: {self.config_path} not found. Using defaults.")
            return self._settings

        with open(self.config_path, "r") as file:
            # safe_load is a security best practice to prevent code injection
            self._settings = yaml.safe_load(file) or {}
            
        return self._settings

    def get(self, key: str, default: Any = None) -> Any:
        """
        A helper to get a setting safely. 
        Example: config.get('app_name', 'My App')
        """
        return self._settings.get(key, default)
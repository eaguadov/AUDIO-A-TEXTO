import json
import os
import logging

CONFIG_FILE = 'config.json'
logger = logging.getLogger(__name__)

class ConfigManager:
    _instance = None
    _config = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance.load_config()
        return cls._instance

    def load_config(self):
        """Carga la configuración desde el archivo JSON"""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    self._config = json.load(f)
            except Exception as e:
                logger.error(f"Error cargando config: {e}")
                self._config = {}
        else:
            self._config = {}

    def save_config(self):
        """Guarda la configuración en el archivo JSON"""
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self._config, f, indent=4)
        except Exception as e:
            logger.error(f"Error guardando config: {e}")

    def get_hf_token(self):
        return self._config.get('hf_token')

    def set_hf_token(self, token):
        self._config['hf_token'] = token
        self.save_config()

# Instancia global
config_manager = ConfigManager()

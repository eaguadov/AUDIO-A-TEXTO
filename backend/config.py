import json
import os
import logging

# Resolver ruta absoluta correcta
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, 'config.json')
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
        logger.info(f"Cargando configuración desde: {CONFIG_FILE}")
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    self._config = json.load(f)
                logger.info(f"Configuración cargada. Keys: {list(self._config.keys())}")
            except Exception as e:
                logger.error(f"Error cargando config: {e}")
                self._config = {}
        else:
            logger.warning(f"No se encontró el archivo de configuración en: {CONFIG_FILE}")
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

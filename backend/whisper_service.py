import whisper
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WhisperService:
    """Servicio para transcribir audio usando Whisper de OpenAI"""
    
    def __init__(self, model_name="base"):
        """
        Inicializa el servicio de Whisper
        
        Args:
            model_name: Nombre del modelo ('tiny', 'base', 'small', 'medium', 'large')
        """
        self.model_name = model_name
        self.model = None
        self.current_language = "es"  # Español por defecto
        
    def load_model(self):
        """Carga el modelo de Whisper en memoria"""
        if self.model is None:
            logger.info(f"Cargando modelo Whisper '{self.model_name}'...")
            try:
                self.model = whisper.load_model(self.model_name)
                logger.info(f"Modelo '{self.model_name}' cargado exitosamente")
            except Exception as e:
                logger.error(f"Error al cargar el modelo: {e}")
                raise
    
    def set_language(self, language_code):
        """
        Configura el idioma de transcripción
        
        Args:
            language_code: Código de idioma ('es', 'en', 'fr', etc.) o 'auto' para detección automática
        """
        self.current_language = language_code
        logger.info(f"Idioma configurado a: {language_code}")
    
    def transcribe(self, audio_path, include_timestamps=False):
        """
        Transcribe un archivo de audio
        
        Args:
            audio_path: Ruta al archivo de audio
            include_timestamps: Si se deben devolver timestamps
            
        Returns:
            str o dict: Texto transcrito o dict con texto y segments
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Archivo de audio no encontrado: {audio_path}")
        
        # Asegurar que el modelo esté cargado
        if self.model is None:
            self.load_model()
        
        try:
            logger.info(f"Transcribiendo: {audio_path}")
            
            # Realizar transcripción
            logger.info(f"Running Whisper: timestamps={include_timestamps}, model={self.model_name}")
            
            # NOTA CRÍTICA: Para que Whisper devuelva segmentos, 'verbose' no debe ser None a veces, 
            # pero lo más importante es que devolvamos el objeto completo
            result = self.model.transcribe(
                audio_path, 
                language=self.current_language if self.current_language != "auto" else None,
                verbose=False, # Importante para evitar spam en consola pero obtener resultado estructurado
                word_timestamps=include_timestamps # Precisión a nivel de palabra para mejorar diarización
            )
            
            logger.info(f"Whisper result obtained. Keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")

            # Si se piden timestamps, devolver el objeto completo (que incluye 'segments')
            # Si se piden timestamps, devolver el objeto completo (que incluye 'segments')
            if include_timestamps:
                logger.info(f"Returning full result with {len(result.get('segments', []))} segments")
                return result
            else:
                # Extraer solo el texto transcrito
                transcribed_text = result["text"].strip()
                logger.info(f"Transcription completed: {len(transcribed_text)} chars")
                return transcribed_text
            
        except Exception as e:
            logger.error(f"Error durante la transcripción: {e}")
            raise

# Instancia global del servicio
whisper_service = WhisperService(model_name="small")

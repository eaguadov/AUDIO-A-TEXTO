
import logging
import torch
import torchaudio
import os
import subprocess
from pyannote.audio import Pipeline
from config import config_manager

logger = logging.getLogger(__name__)

class DiarizationService:
    def __init__(self):
        self.pipeline = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    def load_pipeline(self):
        """Carga el pipeline de diarización si no está cargado"""
        token = config_manager.get_hf_token()
        
        if not token:
            logger.warning("No Hugging Face token found. Diarization disabled.")
            return False

        if self.pipeline is None:
            try:
                logger.info(f"Cargando Pyannote Pipeline en {self.device}...")
                self.pipeline = Pipeline.from_pretrained(
                    "pyannote/speaker-diarization-3.1", 
                    token=token
                ).to(self.device)
                logger.info("✅ Pipeline de diarización cargado correctamente")
            except Exception as e:
                logger.error(f"Error cargando Pyannote: {e}")
                return False
        
        return True

    def diarize(self, audio_path, num_speakers=None):
        """
        Ejecuta la diarización en el archivo de audio
        
        Args:
            audio_path: Ruta al archivo de audio
            num_speakers: (Opcional) Número exacto de hablantes si se conoce
        """
        if not self.load_pipeline():
            raise Exception("No se pudo cargar el modelo de diarización (¿Token inválido?)")

        logger.info(f"🎤 Ejecutando diarización en: {audio_path} (Hablantes esperados: {num_speakers if num_speakers else 'Auto'})")
        temp_wav = None
        try:
            # FIX: Usar FFmpeg para convertir a WAV estándar (16kHz mono)
            # Esto evita problemas de codecs corruptos o no soportados por torchaudio/torchcodec
            temp_wav = f"{audio_path}_temp_16k.wav"
            logger.info(f"Convirtiendo a WAV temporal: {temp_wav}")
            
            # Ejecutar ffmpeg (asumiendo que está en PATH, igual que Whisper)
            subprocess.run([
                "ffmpeg", "-i", audio_path, 
                "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le", 
                temp_wav, "-y"
            ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # Cargar el WAV limpio
            waveform, sample_rate = torchaudio.load(temp_wav)
            
            # Pasar diccionario al pipeline
            # Si se especificó número de hablantes, lo pasamos
            run_opts = {"waveform": waveform, "sample_rate": sample_rate}
            kwargs = {}
            if num_speakers:
                try:
                    kwargs["num_speakers"] = int(num_speakers)
                except:
                    logger.warning(f"Número de hablantes inválido: {num_speakers}")

            diarization_result = self.pipeline(run_opts, **kwargs)
            
            # LOG DEBUG: Inspeccionar el tipo de resultado
            logger.info(f"Tipo de resultado de diarización: {type(diarization_result)}")
            
            # Manejar 'DiarizeOutput', tupla o atributo 'speaker_diarization'
            diarization = diarization_result
            
            # Caso 1: Pyannote 3.1+ DiarizeOutput (tiene 'speaker_diarization')
            if hasattr(diarization_result, 'speaker_diarization'):
                diarization = diarization_result.speaker_diarization
            # Caso 2: Objeto genérico con 'annotation'
            elif hasattr(diarization_result, 'annotation'):
                diarization = diarization_result.annotation
            # Caso 3: Tupla (annotation, vector, etc)
            elif isinstance(diarization_result, tuple):
                diarization = diarization_result[0]

            logger.info(f"Objeto a iterar (Annotation): {type(diarization)}")
            
            # Convertir a lista de segmentos simple
            segments = []
            if hasattr(diarization, 'itertracks'):
                for turn, _, speaker in diarization.itertracks(yield_label=True):
                    segments.append({
                        "start": turn.start,
                        "end": turn.end,
                        "speaker": speaker
                    })
            else:
                 logger.error(f"El objeto resultante no tiene itertracks. Atributos: {dir(diarization_result)}")
                 raise Exception(f"Formato de diarización inesperado: {type(diarization_result)}")
            
            logger.info(f"Diarización completada: {len(segments)} segmentos de hablantes detectados")
            return segments
            
        except Exception as e:
            logger.error(f"Error durante diarización: {e}")
            raise
        finally:
            # Limpiar archivo temporal
            if temp_wav and os.path.exists(temp_wav):
                try:
                    os.remove(temp_wav)
                except:
                    pass

# Instancia global
diarization_service = DiarizationService()

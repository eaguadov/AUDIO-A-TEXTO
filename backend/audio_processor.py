import os
import subprocess
import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AudioProcessor:
    """Procesador de audio con división automática y transcripción"""
    
    def __init__(self, whisper_service, max_duration_minutes=20):
        """
        Inicializa el procesador de audio
        
        Args:
            whisper_service: Instancia del servicio de Whisper
            max_duration_minutes: Duración máxima por segmento (minutos)
        """
        self.whisper_service = whisper_service
        self.max_duration_seconds = max_duration_minutes * 60
    
    def get_audio_duration(self, audio_path):
        """
        Obtiene la duración de un archivo de audio usando ffprobe
        
        Args:
            audio_path: Ruta al archivo de audio
            
        Returns:
            float: Duración en segundos
        """
        try:
            cmd = [
                'ffprobe',
                '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'json',
                audio_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            duration_info = json.loads(result.stdout)
            duration = float(duration_info['format']['duration'])
            
            logger.info(f"Duración del audio: {duration:.2f} segundos ({duration/60:.2f} minutos)")
            return duration
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Error al obtener duración del audio: {e}")
            raise
        except (KeyError, ValueError, json.JSONDecodeError) as e:
            logger.error(f"Error al parsear duración: {e}")
            raise
    
    def split_audio(self, audio_path, output_dir):
        """
        Divide un archivo de audio en segmentos usando ffmpeg
        
        Args:
            audio_path: Ruta al archivo de audio original
            output_dir: Directorio donde guardar los segmentos
            
        Returns:
            list: Lista de rutas a los archivos de audio segmentados
        """
        duration = self.get_audio_duration(audio_path)
        
        # Si el audio es menor a la duración máxima, no dividir
        if duration <= self.max_duration_seconds:
            logger.info("El audio no necesita ser dividido")
            return [audio_path]
        
        # Calcular número de segmentos necesarios
        num_segments = int(duration / self.max_duration_seconds) + 1
        segment_duration = self.max_duration_seconds
        
        logger.info(f"Dividiendo audio en {num_segments} segmentos de {segment_duration/60:.2f} minutos")
        
        # Preparar nombres de archivo
        audio_filename = Path(audio_path).stem
        audio_extension = Path(audio_path).suffix
        
        segment_paths = []
        
        for i in range(num_segments):
            start_time = i * segment_duration
            segment_name = f"{audio_filename}_parte{i+1}{audio_extension}"
            segment_path = os.path.join(output_dir, segment_name)
            
            # Comando ffmpeg para extraer el segmento
            cmd = [
                'ffmpeg',
                '-i', audio_path,
                '-ss', str(start_time),
                '-t', str(segment_duration),
                '-c', 'copy',  # Copiar sin recodificar (más rápido)
                '-y',  # Sobrescribir si existe
                segment_path
            ]
            
            try:
                subprocess.run(cmd, capture_output=True, check=True)
                segment_paths.append(segment_path)
                logger.info(f"Segmento creado: {segment_name}")
            except subprocess.CalledProcessError as e:
                logger.error(f"Error al crear segmento {i+1}: {e}")
                # Si falla la copia sin recodificar, intentar recodificando
                cmd = [
                    'ffmpeg',
                    '-i', audio_path,
                    '-ss', str(start_time),
                    '-t', str(segment_duration),
                    '-y',
                    segment_path
                ]
                subprocess.run(cmd, capture_output=True, check=True)
                segment_paths.append(segment_path)
                logger.info(f"Segmento creado (recodificado): {segment_name}")
        
        return segment_paths
    
    def process_audio(self, audio_path, output_dir, original_filename=None, include_timestamps=False):
        """
        Procesa un archivo de audio: divide si es necesario y transcribe
        
        Args:
            audio_path: Ruta al archivo de audio
            output_dir: Directorio donde guardar las transcripciones
            original_filename: Nombre original del archivo (opcional)
            include_timestamps: Si se deben incluir timestamps en la transcripción
            
        Returns:
            dict: Información sobre los archivos generados
        """
        # Usar el nombre original si se proporciona, sino extraer del path
        if original_filename:
            audio_filename = Path(original_filename).stem
        else:
            audio_filename = Path(audio_path).stem
        
        # Crear directorio temporal para segmentos si no existe
        temp_dir = os.path.join(output_dir, "temp")
        os.makedirs(temp_dir, exist_ok=True)
        
        # Dividir el audio si es necesario
        segment_paths = self.split_audio(audio_path, temp_dir)
        
        transcriptions = []
        output_files = []
        
        # Transcribir cada segmento
        for i, segment_path in enumerate(segment_paths):
            logger.info(f"Transcribiendo segmento {i+1}/{len(segment_paths)}")
            
            try:
                # Transcribir
                # Transcribir
                logger.info(f"Transcribing segment {i+1} with timestamps={include_timestamps}")
                transcription_result = self.whisper_service.transcribe(segment_path, include_timestamps=include_timestamps)
                
                # Format transcription with timestamps if requested
                if include_timestamps and isinstance(transcription_result, dict):
                    logger.info(f"Formatting {len(transcription_result.get('segments', []))} segments with timestamps")
                    transcription = self._format_with_timestamps(transcription_result)
                else:
                    transcription = transcription_result if isinstance(transcription_result, str) else transcription_result.get('text', '')
                
                transcriptions.append(transcription)
                
                # Guardar transcripción del segmento
                if len(segment_paths) > 1:
                    segment_txt_name = f"{audio_filename}_parte{i+1}.txt"
                else:
                    segment_txt_name = f"{audio_filename}.txt"
                
                segment_txt_path = os.path.join(output_dir, segment_txt_name)
                
                with open(segment_txt_path, 'w', encoding='utf-8') as f:
                    f.write(transcription)
                
                output_files.append(segment_txt_path)
                logger.info(f"Transcripción guardada: {segment_txt_name}")
                
            except Exception as e:
                logger.error(f"Error transcribiendo segmento {i+1}: {e}")
                raise
        
        # Si hubo múltiples segmentos, crear archivo consolidado
        if len(segment_paths) > 1:
            consolidated_txt_name = f"{audio_filename}_completo.txt"
            consolidated_txt_path = os.path.join(output_dir, consolidated_txt_name)
            
            with open(consolidated_txt_path, 'w', encoding='utf-8') as f:
                for i, transcription in enumerate(transcriptions):
                    if i > 0:
                        f.write("\n\n")  # Separador entre segmentos
                    f.write(f"--- Parte {i+1} ---\n\n")
                    f.write(transcription)
            
            output_files.append(consolidated_txt_path)
            logger.info(f"Transcripción consolidada guardada: {consolidated_txt_name}")
        
        # Limpiar archivos temporales de segmentos (solo si fueron divididos)
        if len(segment_paths) > 1:
            for segment_path in segment_paths:
                try:
                    os.remove(segment_path)
                except:
                    pass
        
        return {
            'original_file': original_filename if original_filename else audio_filename,
            'num_segments': len(segment_paths),
            'output_files': output_files,
            'success': True
        }
    
    def _format_with_timestamps(self, result):
        """
        Formatea la transcripción con timestamps en formato [HH:MM:SS]
        
        Args:
            result: Resultado de Whisper con segments
            
        Returns:
            str: Texto formateado con timestamps
        """
        formatted_lines = []
        
        for segment in result.get('segments', []):
            start_time = segment.get('start', 0)
            text = segment.get('text', '').strip()
            
            if text:
                # Convert seconds to HH:MM:SS
                hours = int(start_time // 3600)
                minutes = int((start_time % 3600) // 60)
                seconds = int(start_time % 60)
                
                timestamp = f"[{hours:02d}:{minutes:02d}:{seconds:02d}]"
                formatted_lines.append(f"{timestamp} {text}")
        
        return "\n".join(formatted_lines)

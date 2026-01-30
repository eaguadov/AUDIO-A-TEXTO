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
    
    def process_audio(self, audio_path, output_dir, original_filename=None, include_timestamps=False, perform_diarization=False, num_speakers=None):
        """
        Procesa un archivo de audio: divide si es necesario y transcribe
        
        Args:
            audio_path: Ruta al archivo de audio
            output_dir: Directorio donde guardar las transcripciones
            original_filename: Nombre original del archivo (opcional)
            include_timestamps: Si se deben incluir timestamps en la transcripción
            num_speakers: Número esperado de hablantes (opcional, para diarización)
            
        Returns:
            dict: Información sobre los archivos generados
        """
        # IMPORT LOGIC
        from diarization_service import diarization_service

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
                # SIEMPRE pedir timestamps si hay diarización, para poder alinear
                force_timestamps = include_timestamps or perform_diarization
                
                logger.info(f"Transcribing segment {i+1} with timestamps={force_timestamps}")
                transcription_result = self.whisper_service.transcribe(segment_path, include_timestamps=force_timestamps)
                
                # Diarización (Identificación de hablantes)
                speaker_segments = []
                if perform_diarization:
                    try:
                        logger.info(f"Iniciando diarización para segmento {i+1}...")
                        speaker_segments = diarization_service.diarize(segment_path, num_speakers=num_speakers)
                    except Exception as e:
                        logger.error(f"Fallo en diarización: {e}. Se continuará sin speaker ID.")
                        perform_diarization = False # Desactivar para este segmento si falla

                # Format transcription
                if force_timestamps and isinstance(transcription_result, dict):
                    num_segments = len(transcription_result.get('segments', []))
                    logger.info(f"Formatting {num_segments} segments. Diarization enabled: {perform_diarization}")
                    
                    if perform_diarization and speaker_segments:
                         transcription = self._format_with_speakers(transcription_result, speaker_segments)
                    elif include_timestamps:
                         transcription = self._format_with_timestamps(transcription_result)
                    else:
                         # Si forzamos timestamps solo por diarización pero falló, devolvemos texto plano
                         transcription = transcription_result.get('text', '').strip()
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
        """
        formatted_lines = []
        
        for segment in result.get('segments', []):
            start_time = segment.get('start', 0)
            text = segment.get('text', '').strip()
            
            if text:
                hours = int(start_time // 3600)
                minutes = int((start_time % 3600) // 60)
                seconds = int(start_time % 60)
                
                timestamp = f"[{hours:02d}:{minutes:02d}:{seconds:02d}]"
                formatted_lines.append(f"{timestamp} {text}")
        
        return "\n".join(formatted_lines)

    def _format_with_speakers(self, result, speaker_segments):
        """
        Formatea la transcripción asignando hablantes a cada segmento.
        Si hay timestamps a nivel de palabra, usa alineación fina.
        """
        # Chequear si tenemos timestamps de palabras (Whisper con word_timestamps=True)
        has_word_timestamps = False
        if result.get('segments') and len(result['segments']) > 0:
            if 'words' in result['segments'][0]:
                has_word_timestamps = True
        
        if has_word_timestamps:
            logger.info("Usando alineación a nivel de PALABRA (Alta precisión)")
            return self._format_with_word_alignment(result, speaker_segments)
        else:
            logger.info("Usando alineación a nivel de SEGMENTO (Baja precisión)")
            return self._format_with_segment_alignment(result, speaker_segments)

    def _format_with_segment_alignment(self, result, speaker_segments):
        """Método clásico: Alineación por segmentos de Whisper"""
        formatted_lines = []
        
        # Helper para convertir segundos a HH:MM:SS
        def secs_to_str(seconds_float):
            hours = int(seconds_float // 3600)
            minutes = int((seconds_float % 3600) // 60)
            seconds = int(seconds_float % 60)
            return f"[{hours:02d}:{minutes:02d}:{seconds:02d}]"

        for segment in result.get('segments', []):
            start = segment.get('start', 0)
            end = segment.get('end', 0)
            text = segment.get('text', '').strip()
            
            if not text:
                continue

            # Encontrar el hablante que más se solapa con este segmento
            best_speaker = "Unknown"
            max_overlap = 0

            for spk_seg in speaker_segments:
                # Calcular intersección de tiempos
                seg_start = max(start, spk_seg['start'])
                seg_end = min(end, spk_seg['end'])
                overlap = max(0, seg_end - seg_start)
                
                if overlap > max_overlap:
                    max_overlap = overlap
                    best_speaker = spk_seg['speaker']
            
            # Formato: [HH:MM:SS] [SPEAKER_01]: Texto
            timestamp = secs_to_str(start)
            speaker_label = f"[{best_speaker}]"
            formatted_lines.append(f"{timestamp} {speaker_label}: {text}")

        return "\n".join(formatted_lines)

    def _format_with_word_alignment(self, result, speaker_segments):
        """
        Alineación híbrida v2: 
        1. Asigna hablantes a palabras (con tolerancia para palabras en los bordes).
        2. Suaviza asignaciones incorrectas (palabras sueltas).
        3. Mantiene la estructura de frases original de Whisper.
        """
        lines = []
        
        # Optimizacion: Ordenar segmentos de hablantes por tiempo
        speaker_segments.sort(key=lambda x: x['start'])
        
        def secs_to_str(seconds_float):
            hours = int(seconds_float // 3600)
            minutes = int((seconds_float % 3600) // 60)
            seconds = int(seconds_float % 60)
            return f"[{hours:02d}:{minutes:02d}:{seconds:02d}]"

        for segment in result.get('segments', []):
            words = segment.get('words', [])
            if not words:
                continue
                
            # 1. Asignar hablante a cada palabra del segmento
            words_with_speaker = []
            for word in words:
                w_start = word['start']
                w_end = word['end']
                w_center = (w_start + w_end) / 2
                
                best_speaker = None
                
                # A) Búsqueda exacta (centro de la palabra dentro del segmento)
                for spk in speaker_segments:
                    if spk['start'] <= w_center <= spk['end']:
                        best_speaker = spk['speaker']
                        break 
                
                # B) Búsqueda por proximidad (si no hay exacto)
                # Muchas veces la palabra empieza milisegundos antes que la diarización
                if not best_speaker:
                    closest_dist = float('inf')
                    for spk in speaker_segments:
                        # Distancia al segmento (0 si está dentro)
                        dist = 0
                        if w_center < spk['start']:
                            dist = spk['start'] - w_center
                        elif w_center > spk['end']:
                            dist = w_center - spk['end']
                        
                        # Si está muy cerca (< 0.5s), es candidato
                        if dist < 0.5 and dist < closest_dist:
                            closest_dist = dist
                            best_speaker = spk['speaker']
                
                words_with_speaker.append({
                    'word': word['word'],
                    'start': w_start,
                    'end': w_end,
                    'speaker': best_speaker if best_speaker else "Unknown"
                })
            
            # 2. Suavizado de hablantes (Voting / Smoothing)
            # Evita que una palabra suelta rompa la frase: A A B A A -> A A A A A
            for i in range(1, len(words_with_speaker) - 1):
                prev_spk = words_with_speaker[i-1]['speaker']
                curr_spk = words_with_speaker[i]['speaker']
                next_spk = words_with_speaker[i+1]['speaker']
                
                # Si la palabra actual es diferente a las de los lados, corregirla
                if prev_spk == next_spk and curr_spk != prev_spk:
                    words_with_speaker[i]['speaker'] = prev_spk
                
                # Si la actual es Unknown, heredar del anterior (flujo continuo)
                if curr_spk == "Unknown" and prev_spk != "Unknown":
                    words_with_speaker[i]['speaker'] = prev_spk

            # Corrección de inicio si es Unknown (heredar del siguiente)
            if words_with_speaker[0]['speaker'] == "Unknown" and len(words_with_speaker) > 1:
                if words_with_speaker[1]['speaker'] != "Unknown":
                    words_with_speaker[0]['speaker'] = words_with_speaker[1]['speaker']

            # 3. Agrupar palabras consecutivas del MISMO hablante DENTRO del segmento
            if not words_with_speaker:
                continue

            current_speaker = words_with_speaker[0]['speaker']
            current_group_words = []
            current_group_start = words_with_speaker[0]['start']
            
            for w in words_with_speaker:
                # Cambio de hablante solo si no es Unknown (para evitar fragmentación por silencios)
                if w['speaker'] != "Unknown" and w['speaker'] != current_speaker:
                    
                    # Guardar grupo anterior
                    if current_group_words:
                        text = "".join([w['word'] for w in current_group_words]).strip()
                        text = text.replace(" ,", ",").replace(" .", ".").replace(" ?", "?").replace(" !", "!")
                        if text:
                            lines.append(f"{secs_to_str(current_group_start)} [{current_speaker}]: {text}")
                    
                    # Iniciar nuevo grupo
                    current_speaker = w['speaker']
                    current_group_words = [w]
                    current_group_start = w['start']
                else:
                    current_group_words.append(w)
                    # Si veníamos de Unknown y ahora tenemos hablante, actualizar el label del grupo actual
                    if current_speaker == "Unknown" and w['speaker'] != "Unknown":
                        current_speaker = w['speaker']
            
            # Guardar el último grupo del segmento
            if current_group_words:
                text = "".join([w['word'] for w in current_group_words]).strip()
                text = text.replace(" ,", ",").replace(" .", ".").replace(" ?", "?").replace(" !", "!")
                if text:
                    lines.append(f"{secs_to_str(current_group_start)} [{current_speaker}]: {text}")
            
        return "\n".join(lines)

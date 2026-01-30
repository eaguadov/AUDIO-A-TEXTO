
# VERSIÓN DEL BACKEND: v2.1-clean-logs
# VERSION LIMPIA SIN EMOJIS PARA EVITAR ERRORES DE ENCODING EN WINDOWS
"""
Flask backend for Audio to Text transcription
VERSION: 2.1-clean-logs
"""
import os
import uuid
import logging
import threading
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
from logging.handlers import RotatingFileHandler

# Configuración de logging ROBUSTA
# Crear formatters y handlers
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# Handler de archivo (SIEMPRE FUNCIONA)
file_handler = RotatingFileHandler('app.log', maxBytes=1024*1024, backupCount=5, encoding='utf-8')
file_handler.setFormatter(log_formatter)
file_handler.setLevel(logging.INFO)

# Handler de consola
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)
console_handler.setLevel(logging.INFO)

# Configurar logger raíz
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addHandler(file_handler)
root_logger.addHandler(console_handler)

# Logger específico (sin duplicar)
logger = logging.getLogger(__name__)

# Importar servicios
try:
    from whisper_service import whisper_service
    from audio_processor import AudioProcessor
    from diarization_service import diarization_service
    from config import config_manager
except ImportError as e:
    logger.error(f"Error importando servicios: {e}")
    raise

# Configuración
UPLOAD_DIR = 'uploads'
TRANSCRIPTION_DIR = 'transcriptions'
ALLOWED_EXTENSIONS = {'.mp3', '.wav', '.m4a', '.flac', '.ogg', '.wma', '.aac', '.mpeg'}

# Crear directorios si no existen
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(TRANSCRIPTION_DIR, exist_ok=True)

# Inicializar Flask
app = Flask(__name__)
CORS(app)

# Inicializar procesador de audio
audio_processor = AudioProcessor(whisper_service)

# Almacenar tareas en memoria
tasks = {}

def allowed_file(filename):
    """Verifica si el archivo tiene una extensión permitida"""
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS

# Global Lock for processing (Sequencing)
processing_lock = threading.Lock()

def process_audio_task(task_id, audio_path, filename, model='small', timestamps=False, diarization=False, num_speakers=None):
    """Función que se ejecuta en un hilo separado para procesar el audio SECUENCIALMENTE"""
    try:
        # Actualizar estado inicial (En cola, pero 'processing' para la UI)
        tasks[task_id]['status'] = 'processing'
        tasks[task_id]['progress'] = 5
        
        logger.info(f"THREAD START: {filename} esperando turno... (Lock)")
        
        # --- AQUÍ ESTÁ LA MAGIA: Esperar turno (Semáforo) ---
        with processing_lock:
            logger.info(f"LOCK ACQUIRED: Iniciando procesamiento real de {filename}")
            tasks[task_id]['progress'] = 10
            
            # Cambiar modelo de Whisper si es necesario
            old_model = whisper_service.model_name
            if old_model != model:
                whisper_service.model_name = model
                whisper_service.model = None  # Forzar recarga del modelo
                logger.info(f"MODEL CHANGE: {old_model} -> {model}")
            
            # Cargar modelo de Whisper si no está cargado
            tasks[task_id]['progress'] = 20
            whisper_service.load_model()
            logger.info(f"MODEL READY: {whisper_service.model_name}")
            
            # Procesar audio (dividir y transcribir)
            tasks[task_id]['progress'] = 30
            logger.info(f"PROCESSING START: Timestamps={timestamps}, Diarization={diarization}")
            
            result = audio_processor.process_audio(audio_path, TRANSCRIPTION_DIR, original_filename=filename, include_timestamps=timestamps, perform_diarization=diarization, num_speakers=num_speakers)
            
            # Actualizar tarea con resultados
            tasks[task_id]['status'] = 'completed'
            tasks[task_id]['progress'] = 100
            tasks[task_id]['result'] = result
            tasks[task_id]['output_files'] = [os.path.basename(f) for f in result['output_files']]
            tasks[task_id]['original_file'] = filename
            
            logger.info(f"TASK COMPLETED: {filename}")
            logger.info(f"LOCK RELEASED: Fin de {filename}")
            
    except Exception as e:
        logger.error(f"TASK ERROR in {filename}: {e}", exc_info=True)
        tasks[task_id]['status'] = 'error'
        tasks[task_id]['error'] = str(e)
    finally:
        # Limpiar archivo de audio temporal
        try:
            if os.path.exists(audio_path):
                os.remove(audio_path)
        except:
            pass

@app.route('/upload', methods=['POST'])
def upload_file():
    """Endpoint para subir archivos de audio"""
    try:
        if 'files' not in request.files:
            return jsonify({'error': 'No se enviaron archivos'}), 400
        
        files = request.files.getlist('files')
        
        if not files or files[0].filename == '':
            return jsonify({'error': 'No se seleccionaron archivos'}), 400
        
        # Get configuration from request
        model = request.form.get('model', 'small')
        timestamps_value = request.form.get('timestamps', 'false')
        
        # Parse timestamps
        if isinstance(timestamps_value, bool):
            timestamps = timestamps_value
        else:
            timestamps = str(timestamps_value).lower() in ['true', '1', 'yes']
            
        # Parse diarization
        diarization_value = request.form.get('diarization', 'false')
        if isinstance(diarization_value, bool):
            diarization = diarization_value
        else:
            diarization = str(diarization_value).lower() in ['true', '1', 'yes']
        
        # Parse num_speakers
        num_speakers = request.form.get('speakers', '')
        if num_speakers and num_speakers.strip().isdigit():
            num_speakers = int(num_speakers)
        else:
            num_speakers = None
        
        # LOG CRITICO
        logger.info(f"UPLOAD REQUEST: Files={len(files)}, Model={model}, Timestamps={timestamps}, Diarization={diarization}, Speakers={num_speakers}")
        
        task_ids = []
        
        # Procesar cada archivo
        for file in files:
            if file and allowed_file(file.filename):
                # Generar ID único para la tarea
                task_id = str(uuid.uuid4())
                
                # Guardar archivo temporalmente
                filename = file.filename
                safe_filename = f"{task_id}_{filename}"
                filepath = os.path.join(UPLOAD_DIR, safe_filename)
                file.save(filepath)
                
                # Crear tarea
                tasks[task_id] = {
                    'id': task_id,
                    'filename': filename,
                    'status': 'queued',
                    'progress': 0,
                    'output_files': []
                }
                
                # Iniciar procesamiento en hilo separado
                thread = threading.Thread(
                    target=process_audio_task,
                    args=(task_id, filepath, filename, model, timestamps, diarization, num_speakers)
                )
                thread.start()
                
                task_ids.append(task_id)
                logger.info(f"QUEUED: {filename} -> TaskID: {task_id}")
                
            else:
                logger.warning(f"IGNORED: Archivo no permitido {file.filename}")
        
        if not task_ids:
            return jsonify({'error': 'No se procesaron archivos válidos'}), 400
        
        return jsonify({
            'message': f'{len(task_ids)} archivo(s) en cola',
            'task_ids': task_ids
        }), 200
        
    except Exception as e:
        logger.error(f"UPLOAD ERROR: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/status/<task_id>', methods=['GET'])
def get_status(task_id):
    """Endpoint para obtener el estado de una tarea"""
    if task_id not in tasks:
        return jsonify({'error': 'Tarea no encontrada'}), 404
    
    task = tasks[task_id]
    
    response = {
        'id': task['id'],
        'filename': task['filename'],
        'status': task['status'],
        'progress': task['progress']
    }
    
    if task['status'] == 'completed':
        response['output_files'] = task['output_files']
        response['original_file'] = task.get('original_file', task['filename'])
        if 'result' in task:
            response['num_segments'] = task['result'].get('num_segments', 1)
    
    if task['status'] == 'error':
        response['error'] = task.get('error', 'Error desconocido')
    
    return jsonify(response)

@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    """Endpoint para descargar archivos transcriptados"""
    try:
        return send_from_directory(TRANSCRIPTION_DIR, filename, as_attachment=True)
    except FileNotFoundError:
        return jsonify({'error': 'Archivo no encontrado'}), 404

@app.route('/language', methods=['POST'])
def set_language():
    """Endpoint para cambiar el idioma de transcripción"""
    try:
        data = request.get_json()
        language = data.get('language', 'es')
        whisper_service.set_language(language)
        return jsonify({'message': f'Idioma configurado a: {language}'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """Endpoint para verificar el estado del servidor"""
    return jsonify({
        'status': 'ok',
        'version': '2.1-clean-logs',
        'model': whisper_service.model_name,
        'model_loaded': whisper_service.model is not None
    })

@app.route('/config', methods=['POST'])
def save_config():
    """Endpoint para guardar configuración (Token HF)"""
    try:
        data = request.get_json()
        token = data.get('hf_token')
        if token:
            config_manager.set_hf_token(token)
            return jsonify({'message': 'Token guardado correctamente'}), 200
        return jsonify({'error': 'Token no proporcionado'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/config', methods=['GET'])
def get_config():
    """Endpoint para obtener estado de la configuración"""
    token = config_manager.get_hf_token()
    return jsonify({
        'has_token': bool(token),
        'token_masked': f"{token[:4]}...{token[-4:]}" if token else None
    })

if __name__ == '__main__':
    logger.info("=" * 70)
    logger.info("SERVER STARTING - VERSION 2.2-diarization")
    logger.info("=" * 70)
    logger.info(f"Uploads Dir: {os.path.abspath(UPLOAD_DIR)}")
    logger.info(f"Transcriptions Dir: {os.path.abspath(TRANSCRIPTION_DIR)}")
    logger.info(f"Whisper Model: {whisper_service.model_name}")
    logger.info("=" * 70)
    app.run(debug=True, host='0.0.0.0', port=5000)

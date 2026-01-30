# Test para verificar que whisper devuelve segments con timestamps
import sys
sys.path.append('backend')

from whisper_service import whisper_service
import os

# Buscar un archivo de audio de prueba
upload_dir = "backend/uploads"
transcriptions_dir = "backend/transcriptions"

# Buscar archivos de audio
audio_files = []
if os.path.exists(upload_dir):
    audio_files = [f for f in os.listdir(upload_dir) if f.endswith(('.mp3', '.wav', '.m4a', '.flac'))]

# Si no hay archivos en uploads, buscar en transcriptions para al menos saber que tenemos archivos procesados
if not audio_files and os.path.exists(transcriptions_dir):
    txt_files = [f for f in os.listdir(transcriptions_dir) if f.endswith('.txt')]
    if txt_files:
        print(f"No hay archivos de audio en uploads/, pero hay {len(txt_files)} transcripciones existentes")
        print("\nContenido del archivo mas reciente (primeras 300 caracteres):")
        latest_txt = sorted([os.path.join(transcriptions_dir, f) for f in txt_files], 
                          key=os.path.getmtime, reverse=True)[0]
        with open(latest_txt, 'r', encoding='utf-8') as f:
            content = f.read()
            print(content[:300])
            print(f"\n\n¿Tiene timestamps? {('[00:' in content or '[01:' in content)}")
            if '[00:' in content or '[01:' in content:
                print("✅ SI tiene timestamps")
            else:
                print("❌ NO tiene timestamps")
else:
    print(f"❌ No hay archivos de audio en {upload_dir}/")

print("\n" + "="*60)
print(f"Modelo whisper_service: {whisper_service.model_name}")
print(f"¿Modelo cargado?: {whisper_service.model is not None}")

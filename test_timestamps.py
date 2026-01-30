"""
Script de diagnóstico para verificar que los timestamps funcionan
"""
import sys
sys.path.append('backend')

from whisper_service import whisper_service
from audio_processor import AudioProcessor
import os

# Test 1: Verificar que whisper_service puede devolver timestamps
print("=" * 60)
print("TEST 1: Verificar configuración de whisper_service")
print("=" * 60)
print(f"Modelo configurado: {whisper_service.model_name}")
print(f"Modelo cargado: {whisper_service.model is not None}")

# Test 2: Buscar un archivo de audio de prueba
print("\n" + "=" * 60)
print("TEST 2: Buscar archivos de audio en uploads")
print("=" * 60)

upload_dir = "backend/uploads"
if os.path.exists(upload_dir):
    audio_files = [f for f in os.listdir(upload_dir) if f.endswith(('.mp3', '.wav', '.m4a', '.flac'))]
    if audio_files:
        test_file = os.path.join(upload_dir, audio_files[0])
        print(f"✅ Archivo encontrado para test: {audio_files[0]}")
        
        # Test 3: Transcribir CON timestamps
        print("\n" + "=" * 60)
        print("TEST 3: Transcribir CON timestamps")
        print("=" * 60)
        
        whisper_service.load_model()
        result = whisper_service.transcribe(test_file, include_timestamps=True)
        
        if isinstance(result, dict):
            print(f"✅ Resultado es dict (correcto)")
            print(f"   - Tiene 'text': {'text' in result}")
            print(f"   - Tiene 'segments': {'segments' in result}")
            if 'segments' in result:
                print(f"   - Número de segmentos: {len(result['segments'])}")
                if len(result['segments']) > 0:
                    first_seg = result['segments'][0]
                    print(f"   - Primer segmento:")
                    print(f"     * start: {first_seg.get('start')}")
                    print(f"     * text: {first_seg.get('text')[:50]}...")
        else:
            print("❌ Resultado NO es dict (error - debería ser dict con timestamps=True)")
            
        # Test 4: Probar formateo de timestamps
        print("\n" + "=" * 60)
        print("TEST 4: Probar formateo de timestamps")
        print("=" * 60)
        
        processor = AudioProcessor(whisper_service)
        if isinstance(result, dict) and 'segments' in result:
            formatted = processor._format_with_timestamps(result)
            print("Primeras 5 líneas del texto formateado:")
            lines = formatted.split('\n')[:5]
            for line in lines:
                print(f"  {line}")
        
    else:
        print("❌ No se encontraron archivos de audio en uploads/")
else:
    print("❌ Directorio uploads/ no existe")

print("\n" + "=" * 60)
print("FIN DE DIAGNÓSTICO")
print("=" * 60)

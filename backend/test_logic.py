import sys
import os

# Asegurar que podemos importar los módulos del backend
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from audio_processor import AudioProcessor
except ImportError:
    # Si falla, intentar agregar el directorio actual al path
    sys.path.append('.')
    from audio_processor import AudioProcessor

class MockWhisper:
    def transcribe(self, path, include_timestamps=False):
        return {} 

# Crear instancia con mock
processor = AudioProcessor(MockWhisper())

# Simular resultado de Whisper con segmentos
mock_result = {
    "text": "Texto completo ignorado",
    "segments": [
        {"start": 0.0, "end": 2.5, "text": " Hola mundo"},
        {"start": 2.5, "end": 5.0, "text": " Esto es una prueba de timestamps"},
        {"start": 65.0, "end": 68.0, "text": " Más de un minuto después"}
    ]
}

print("="*50)
print("TEST DE LÓGICA DE TIMESTAMPS")
print("="*50)

try:
    # Probar la función de formateo
    formatted = processor._format_with_timestamps(mock_result)
    
    print("\n--- Resultado Generado ---")
    print(formatted)
    print("--------------------------")

    # Verificaciones
    has_start = "[00:00:00]" in formatted
    has_mid = "[00:00:02]" in formatted
    has_min = "[00:01:05]" in formatted
    
    if has_start and has_min:
        print("\n✅ ÉXITO: La lógica de formateo funciona correctamente.")
        print("   El código sabe generar [00:00:00] si recibe los datos correctos.")
    else:
        print("\n❌ FALLO: No se generaron los timestamps esperados.")

except Exception as e:
    print(f"\n❌ ERROR DE EJECUCIÓN: {e}")
    import traceback
    traceback.print_exc()

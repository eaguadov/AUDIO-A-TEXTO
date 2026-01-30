# Registro de Cambios

Todos los cambios notables en este proyecto se documentarán en este archivo.

## [1.1.0] - 2026-01-30

### 🚀 Añadido
- **Diarización de Hablantes**: Soporte añadido para identificar hablantes usando `pyannote.audio`.
- **Contador de Hablantes**: Nuevo campo en el Frontend para especificar el número exacto de hablantes (mejora la precisión).
- **Alineación a Nivel de Palabra**: Implementada alineación quirúrgica para asignar cada palabra a su hablante, mejorando turnos rápidos de diálogo.
- **Gestión de Tokens**: Modal en la UI para gestionar de forma segura los tokens de autenticación de Hugging Face.

### 🛠 Cambiado
- **Motor de Alineación Híbrido**: 
    - Cambio de alineación por segmentos a alineación por palabras.
    - Lógica "Imán": Las palabras ligeramente fuera de los segmentos de hablante ahora se ajustan al más cercano (tolerancia < 0.5s).
    - Pasada de "Suavizado": Evita la fragmentación arreglando palabras aisladas marcadas como `Unknown` (ej: `A -> Unknown -> A` se convierte en `A -> A -> A`).
- **Procesamiento de Audio**: Pre-conversiónde audio a WAV 16kHz usando FFmpeg para evitar problemas de compatibilidad con `torchcodec` en Windows.

### 🐛 Corregido
- Solucionado cierre inesperado al cargar `pyannote/speaker-diarization-3.1` en Windows.
- Resuelto problema de "palabras colgantes" donde palabras iniciales cortas (como "A ver...") se marcaban como Unknown.
- Corregido error `AttributeError` con versiones nuevas de los objetos de salida de `pyannote`.

### 📦 Dependencias
- Añadido `pyannote.audio`, `huggingface_hub`, `torchaudio`.

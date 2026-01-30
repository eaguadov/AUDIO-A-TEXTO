# Registro de Cambios

Todos los cambios notables en este proyecto se documentarán en este archivo.

## [2.0.0] - 2026-01-30

### ⭐ Principales Mejoras
- **Estabilidad Total en Lotes**: Implementado sistema de "Semáforo" (Lock) que procesa los archivos uno por uno. Esto elimina los errores de `Torch Runtime Error` (tensor size mismatch) al subir muchos archivos a la vez.
- **Persistencia de Token**: Arreglado el problema donde la aplicación olvidaba el Token de Hugging Face al reiniciar. Ahora se guarda de forma segura en `config.json` y se carga con logs de confirmación.
- **Interfaz UI Pulida**: Solucionado el error visual donde la ventana de configuración aparecía "rota" al final de la página. Ahora es un modal oculto correctamente.

### 🚀 Añadido
- **Sufijo Automático**: Todos los archivos generados ahora terminan en `_Transcrito.txt` para facilitar su identificación.
- **Launcher Optimizado**: `start_app.bat` ahora abre el navegador automáticamente tras verificar que los servidores están listos.
- **Guía de Instalación**: Añadido `INSTALL_GUIDE.md` para facilitar la migración a otros equipos.

### 🐛 Corregido
- Race conditions en el frontend al comprobar el estado del token.
- Errores 404 en el bucle de estado tras reinicios del servidor (ahora el frontend maneja mejor estas desconexiones).

---

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

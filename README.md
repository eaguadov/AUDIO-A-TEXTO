# Audio a Texto - Transcriptor Automático 🎵📝

Aplicación web local para transcribir archivos de audio a texto usando **Whisper de OpenAI** (open source). 100% gratuito y sin límites.

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Python](https://img.shields.io/badge/python-3.8+-blue)

## ✨ Características

- 🎯 **Transcripción automática** de audio a texto
- 🔄 **División inteligente** de archivos grandes (>20 min)
- 🌍 **Multi-idioma** (español, inglés, francés, alemán, italiano, portugués, etc.)
- 📦 **Procesamiento por lotes** (múltiples archivos simultáneamente)
- 💾 **100% local** - tus datos no salen de tu PC
- 🎨 **Interfaz moderna** con drag & drop
- 📊 **Seguimiento en tiempo real** del progreso
- 📝 **Archivos consolidados** para audios divididos

## 🎬 Formatos Soportados

- MP3
- WAV
- M4A
- FLAC
- OGG
- WMA
- AAC

## 🚀 Instalación

### Requisitos Previos

1. **Python 3.8 o superior**
   - Descargar desde [python.org](https://www.python.org/downloads/)

2. **ffmpeg** (requerido para procesamiento de audio)
   
   **Windows:**
   - Descarga ffmpeg desde [ffmpeg.org](https://ffmpeg.org/download.html)
   - Extrae el archivo ZIP
   - Agrega la carpeta `bin` al PATH del sistema
   - Verificar: `ffmpeg -version`

   **Alternativa fácil para Windows:**
   ```powershell
   # Usando Chocolatey
   choco install ffmpeg
   
   # O usando winget
   winget install ffmpeg
   ```

### Instalación de la Aplicación

1. **Clonar o descargar el proyecto**
   ```bash
   cd "c:\Proyectos Antigravity\AUDIO A TXT"
   ```

2. **Instalar dependencias de Python**
   ```bash
   pip install -r requirements.txt
   ```

   > ⚠️ **Nota**: La primera instalación descargará PyTorch (~2GB) y puede tardar varios minutos.

3. **Verificar instalación**
   ```bash
   python -c "import whisper; print('Whisper instalado correctamente')"
   ```

## 🎯 Uso

### Método Rápido (Recomendado) ⚡

**¡Inicia todo con un solo doble-clic!**

1. Haz doble clic en `start_app.bat` en la raíz del proyecto
2. ¡Listo! Se abrirán automáticamente:
   - Servidor Backend (puerto 5000)
   - Servidor Frontend (puerto 8080)
   - Navegador web con la aplicación

> 💡 **Nota**: NO cierres las ventanas de comandos que se abren. Son los servidores ejecutándose.

---

### Método Manual (Alternativo)

Si prefieres iniciar los servidores manualmente:

### 1. Iniciar el Servidor Backend

```bash
cd backend
python app.py
```

Verás un mensaje como:
```
Cargando modelo Whisper 'base'...
Modelo 'base' cargado exitosamente
* Running on http://127.0.0.1:5000
```

### 2. Abrir la Interfaz Web

Simplemente abre el archivo `frontend/index.html` en tu navegador web.

O usa un servidor local:
```bash
cd frontend
python -m http.server 8080 --bind 127.0.0.1
```

Luego abre: `http://127.0.0.1:8080`

### 3. ¡Usa la aplicación!

1. 🌍 **Selecciona el idioma** (español por defecto)
2. 📁 **Arrastra archivos de audio** o haz clic para seleccionar
3. ⏳ **Espera** mientras se procesan
4. 💾 **Descarga** las transcripciones en formato TXT

## 📋 Ejemplos de Uso

### Archivo Pequeño (<20 minutos)
```
Input:  entrevista.mp3 (15 minutos)
Output: entrevista.txt
```

### Archivo Grande (>20 minutos)
```
Input:  conferencia.mp3 (60 minutos)
Output: 
  - conferencia_parte1.txt
  - conferencia_parte2.txt
  - conferencia_parte3.txt
  - conferencia_completo.txt  ← Consolidado
```

### Múltiples Archivos
```
Input:  
  - reunion1.mp3
  - reunion2.mp3
  - entrevista.wav
  
Output:
  - reunion1.txt
  - reunion2.txt
  - entrevista.txt
```

## ⚙️ Configuración Avanzada

### Cambiar Modelo de Whisper

En `backend/whisper_service.py`, línea ~78:

```python
# Opciones disponibles:
whisper_service = WhisperService(model_name="tiny")    # Más rápido, menos preciso (39MB)
whisper_service = WhisperService(model_name="base")    # ✅ Recomendado (74MB)
whisper_service = WhisperService(model_name="small")   # Más preciso (244MB)
whisper_service = WhisperService(model_name="medium")  # Muy preciso (769MB)
whisper_service = WhisperService(model_name="large")   # Máxima precisión (1550MB)
```

### Cambiar Duración de Segmentos

En `backend/audio_processor.py`, línea ~87:

```python
audio_processor = AudioProcessor(whisper_service, max_duration_minutes=20)  # Por defecto
audio_processor = AudioProcessor(whisper_service, max_duration_minutes=30)  # Segmentos más largos
```

## 🔧 Estructura del Proyecto

```
AUDIO A TXT/
├── backend/
│   ├── app.py                 # Servidor Flask
│   ├── audio_processor.py     # Lógica de división de audio
│   ├── whisper_service.py     # Servicio de transcripción
│   ├── uploads/               # Carpeta temporal
│   └── transcriptions/        # Transcripciones generadas
├── frontend/
│   ├── index.html            # Interfaz web
│   ├── styles.css            # Estilos
│   └── script.js             # Lógica del cliente
├── requirements.txt          # Dependencias Python
└── README.md                # Este archivo
```

## 🐛 Solución de Problemas

### Error: "ffmpeg no encontrado"
- Asegúrate de que ffmpeg está instalado y en el PATH
- Verifica: `ffmpeg -version`

### Error: "ModuleNotFoundError: No module named 'whisper'"
- Instala las dependencias: `pip install -r requirements.txt`

### Error: "CORS policy"
- Asegúrate de que el servidor backend está ejecutándose
- Verifica que `flask-cors` está instalado

### El procesamiento es muy lento
- Usa un modelo más pequeño (`tiny` o `base`)
- Si tienes GPU NVIDIA, instala PyTorch con soporte CUDA

### Error de memoria RAM
- Reduce el tamaño del modelo (usa `tiny` o `base`)
- Reduce la duración de los segmentos (15 min en lugar de 20)

## 📊 Rendimiento

| Modelo  | Tamaño | Velocidad     | Precisión | Recomendado para |
|---------|--------|---------------|-----------|------------------|
| tiny    | 39MB   | ~5x más rápido| ⭐⭐      | Testing rápido   |
| base    | 74MB   | ~3x más rápido| ⭐⭐⭐    | ✅ Uso general   |
| small   | 244MB  | Normal        | ⭐⭐⭐⭐  | Alta precisión   |
| medium  | 769MB  | Lento         | ⭐⭐⭐⭐⭐| Profesional      |
| large   | 1550MB | Muy lento     | ⭐⭐⭐⭐⭐| Máxima calidad   |

## 🌟 Características Futuras

- [ ] Soporte para subtítulos (SRT, VTT)
- [ ] Detección automática de hablantes
- [ ] Exportar a Word/PDF
- [ ] Corrección ortográfica automática
- [ ] Interfaz para editar transcripciones

## 📝 Licencia

MIT License - Siente libre de usar, modificar y distribuir.

## 🙏 Créditos

- **OpenAI Whisper** - Modelo de transcripción
- **Flask** - Framework web
- **FFmpeg** - Procesamiento de audio

---

**Hecho con ❤️ para facilitar la transcripción de audio**

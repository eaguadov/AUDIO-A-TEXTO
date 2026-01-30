# Guía de Instalación y Migración (Audio a Texto)

Esta guía te explica cómo instalar esta aplicación en otro ordenador desde cero.

## 1. Requisitos Previos
Necesitas instalar dos cosas en el nuevo ordenador antes de empezar:

1.  **Python 3.10 o superior** (Importante: Marca la casilla "Add Python to PATH" durante la instalación).
2.  **FFmpeg**: Necesario para procesar audio.
    *   Descárgalo de https://ffmpeg.org/download.html
    *   O instálalo usando `winget install ffmpeg` en la terminal (CMD).
    *   **Git** (Opcional, pero recomendado): https://git-scm.com/downloads

## 2. Descargar la Aplicación
Tienes dos opciones:

### Opción A (Recomendado - Usando Git)
Abre una terminal (CMD o PowerShell) y escribe:
```bash
git clone https://github.com/Start-App-2/Audio-Transcriber-v2.git
cd Audio-Transcriber-v2
```

### Opción B (Sin Git)
1. Ve a la página de GitHub del proyecto.
2. Pulsa el botón verde **CODE** > **Download ZIP**.
3. Descomprime el archivo ZIP en una carpeta (ej: `C:\AudioTranscriptor`).

## 3. Instalación Automática
Hemos incluido un script que hace todo el trabajo sucio.

1. Abre la carpeta del proyecto.
2. Abre una terminal en esa carpeta.
3. Ejecuta: `pip install -r requirements.txt`

(Opcional: Puedes crear un archivo `install.bat` con ese comando para hacerlo con doble click).

## 4. Iniciar la App
Haz doble click en **`start_app.bat`**.
¡Listo! Se abrirá el servidor y tu navegador.

## 5. Migrar tus Datos (Opcional)
Si quieres conservar tu historial de transcripciones:
*   Copia la carpeta `backend/transcriptions` de tu ordenador viejo al nuevo.
*   Copia el archivo `backend/config.json` si quieres mantener tu Token guardado.

# Changelog

All notable changes to this project will be documented in this file.

## [1.1.0] - 2026-01-30

### 🚀 Added
- **Speaker Diarization**: Added support for identifying valid speakers using `pyannote.audio`.
- **Speaker Counter**: New input field in Frontend to specify exact number of speakers (improves model accuracy).
- **Word-Level Alignment**: Implemented surgical alignment matching each word to its speaker for handling rapid dialogue turns.
- **Token Management**: UI modal to safely manage Hugging Face authentication tokens.

### 🛠 Changed
- **Hybrid Alignment Engine**: 
    - Moved from segment-level to word-level alignment.
    - Implemented "Magnet" logic: Words slightly outside speaker segments now snap to the nearest speaker (tolerance < 0.5s).
    - Added "Smoothing" pass: Prevents fragmentation by fixing isolated `Unknown` words (e.g., `A -> Unknown -> A` becomes `A -> A -> A`).
- **Audio Processing**: Now pre-converts audio to 16kHz WAV using FFmpeg to avoid `torchcodec` compatibility issues on Windows.

### 🐛 Fixed
- Fixed crash when loading `pyannote/speaker-diarization-3.1` on Windows.
- Resolved "dangling words" issue where short initial words (like "A ver...") were marked as Unknown.
- Fixed `AttributeError` with newer versions of `pyannote` output objects.

### 📦 Dependencies
- Added `pyannote.audio`, `huggingface_hub`, `torchaudio`.

// Configuration
const API_BASE_URL = 'http://127.0.0.1:5000';
const POLL_INTERVAL = 2000; // Poll every 2 seconds

// DOM Elements
// DOM Elements
const uploadZone = document.getElementById('uploadZone');
const fileInput = document.getElementById('fileInput');
const languageSelect = document.getElementById('language');
const modelSelect = document.getElementById('model');
const timestampsCheckbox = document.getElementById('timestamps');
const diarizationCheckbox = document.getElementById('diarization'); // NEW
const settingsBtn = document.getElementById('settingsBtn'); // NEW
const configModal = document.getElementById('configModal'); // NEW
const hfTokenInput = document.getElementById('hfToken'); // NEW
const saveConfigBtn = document.getElementById('saveConfig'); // NEW
const cancelConfigBtn = document.getElementById('cancelConfig'); // NEW
const closeModalBtn = document.querySelector('.close-modal'); // NEW
const timeEstimate = document.getElementById('timeEstimate');
const timeEstimateText = document.getElementById('timeEstimateText');
const filesQueue = document.getElementById('filesQueue');
const filesList = document.getElementById('filesList');
const resultsSection = document.getElementById('resultsSection');
const resultsList = document.getElementById('resultsList');

// State
const activeTasks = new Map();
const completedTasks = new Set();
let hasValidToken = false;

// Preferences key
const PREFS_KEY = 'audioToTextPrefs';

// Model speed multipliers (relative to real-time)
const MODEL_SPEEDS = {
    'small': 1.5,   // ~1.5x faster than real-time
    'medium': 0.8   // ~0.8x (slightly slower than real-time)
};

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadPreferences();
    checkTokenStatus(); // Check if backend has token
    setupEventListeners();
});

function setupEventListeners() {
    // Check if critical elements exist
    if (!uploadZone || !fileInput) return;

    // Click to upload
    uploadZone.addEventListener('click', () => {
        fileInput.click();
    });

    // File input change
    fileInput.addEventListener('change', (e) => {
        handleFiles(e.target.files);
        fileInput.value = ''; // Reset input
    });

    // Drag and drop
    uploadZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadZone.classList.add('dragover');
    });

    uploadZone.addEventListener('dragleave', () => {
        uploadZone.classList.remove('dragover');
    });

    uploadZone.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadZone.classList.remove('dragover');
        handleFiles(e.dataTransfer.files);
    });

    // Language change
    languageSelect.addEventListener('change', async (e) => {
        const language = e.target.value;
        await setLanguage(language);
        savePreferences();
    });

    // Model change
    modelSelect.addEventListener('change', () => {
        savePreferences();
    });

    // Timestamps change
    timestampsCheckbox.addEventListener('change', () => {
        savePreferences();
    });

    // Diarization change
    diarizationCheckbox.addEventListener('change', () => {
        const isChecked = diarizationCheckbox.checked;

        // Toggle speakers input visibility
        if (isChecked) {
            speakersInputContainer.style.display = 'flex';
        } else {
            speakersInputContainer.style.display = 'none';
        }

        if (isChecked && !hasValidToken) {
            // If checking box but no token, open modal
            openModal();
            diarizationCheckbox.checked = false; // Cancel check until token saved
            speakersInputContainer.style.display = 'none'; // Hide back
        } else {
            savePreferences();
        }
    });

    // Settings Modal interactions
    settingsBtn.addEventListener('click', openModal);
    closeModalBtn.addEventListener('click', closeModal);
    cancelConfigBtn.addEventListener('click', closeModal);

    // Close modal if clicking outside
    window.addEventListener('click', (e) => {
        if (e.target === configModal) {
            closeModal();
        }
    });

    // Save Token
    saveConfigBtn.addEventListener('click', async () => {
        const token = hfTokenInput.value.trim();
        if (!token) return;

        try {
            const response = await fetch(`${API_BASE_URL}/config`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ hf_token: token })
            });

            if (response.ok) {
                hasValidToken = true;
                diarizationCheckbox.disabled = false;
                diarizationCheckbox.checked = true; // Auto-enable if user was trying to enable it
                speakersInputContainer.style.display = 'flex'; // Show speakers input
                savePreferences();
                closeModal();
                alert('Token guardado correctamente ✅');
            } else {
                alert('Error guardando token ❌');
            }
        } catch (error) {
            console.error('Error config:', error);
            alert('Error de conexión');
        }
    });
}

function openModal() {
    configModal.style.display = 'block';
    // Fetch current token status/preview
    fetch(`${API_BASE_URL}/config`)
        .then(r => r.json())
        .then(data => {
            if (data.token_masked) {
                hfTokenInput.placeholder = `Actual: ${data.token_masked}`;
            }
        });
}

function closeModal() {
    configModal.style.display = 'none';
}

async function checkTokenStatus() {
    try {
        const response = await fetch(`${API_BASE_URL}/config`);
        const data = await response.json();
        hasValidToken = data.has_token;

        if (!hasValidToken && diarizationCheckbox.checked) {
            diarizationCheckbox.checked = false; // Uncheck if no token actually exists
            speakersInputContainer.style.display = 'none';
        } else if (hasValidToken && diarizationCheckbox.checked) {
            speakersInputContainer.style.display = 'flex';
        }
    } catch (e) {
        console.error("Could not check token status", e);
    }
}

// Preferences Management
function savePreferences() {
    const prefs = {
        language: languageSelect.value,
        model: modelSelect.value,
        timestamps: timestampsCheckbox.checked,
        diarization: diarizationCheckbox.checked
    };
    localStorage.setItem(PREFS_KEY, JSON.stringify(prefs));
}

function loadPreferences() {
    try {
        const saved = localStorage.getItem(PREFS_KEY);
        if (saved) {
            const prefs = JSON.parse(saved);
            if (prefs.language) languageSelect.value = prefs.language;
            if (prefs.model) modelSelect.value = prefs.model;
            if (typeof prefs.timestamps === 'boolean') timestampsCheckbox.checked = prefs.timestamps;
            if (typeof prefs.diarization === 'boolean') {
                diarizationCheckbox.checked = prefs.diarization;
                if (prefs.diarization) speakersInputContainer.style.display = 'flex';
            }
        }
    } catch (error) {
        console.error('Error loading preferences:', error);
    }
}

// Time Estimation
function estimateProcessingTime(files, model) {
    if (!files || files.length === 0) return null;

    const speedMultiplier = MODEL_SPEEDS[model] || 1;

    // Estimate based on file count and average size
    // Rough estimate: 1MB ≈ 30 seconds of audio
    let estimatedAudioSeconds = 0;
    for (const file of files) {
        const fileSizeMB = file.size / (1024 * 1024);
        const approxDurationSeconds = fileSizeMB * 30; // 1MB ≈ 30 sec
        estimatedAudioSeconds += approxDurationSeconds;
    }

    // Processing time = audio duration / speed multiplier
    const processingSeconds = estimatedAudioSeconds / speedMultiplier;

    return processingSeconds;
}

function formatTime(seconds) {
    if (seconds < 60) {
        return `${Math.round(seconds)} segundos`;
    }
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.round(seconds % 60);
    if (minutes < 60) {
        return remainingSeconds > 0
            ? `${minutes} min ${remainingSeconds} seg`
            : `${minutes} minutos`;
    }
    const hours = Math.floor(minutes / 60);
    const remainingMinutes = minutes % 60;
    return `${hours}h ${remainingMinutes}min`;
}

function showTimeEstimate(files) {
    const model = modelSelect.value;
    const timestamps = timestampsCheckbox.checked;
    const estimatedSeconds = estimateProcessingTime(files, model);

    if (estimatedSeconds) {
        const formattedTime = formatTime(estimatedSeconds);
        const modelName = model === 'small' ? 'Small' : 'Medium';
        const timestampsText = timestamps ? ' con timestamps' : '';
        timeEstimateText.textContent = `⚙️  Modelo: ${modelName}${timestampsText} | Tiempo estimado: ~${formattedTime}`;
        timeEstimate.style.display = 'flex';

        // Hide after 15 seconds
        setTimeout(() => {
            timeEstimate.style.display = 'none';
        }, 15000);
    }
}

async function handleFiles(files) {
    if (!files || files.length === 0) return;

    // Show time estimate
    showTimeEstimate(files);

    const formData = new FormData();
    const filesArray = Array.from(files);

    // Add all files to FormData
    filesArray.forEach(file => {
        formData.append('files', file);
    });


    // Add configuration
    formData.append('model', modelSelect.value);
    formData.append('timestamps', timestampsCheckbox.checked ? 'true' : 'false');
    formData.append('diarization', diarizationCheckbox.checked ? 'true' : 'false');

    // Add number of speakers
    const numSpeakers = document.getElementById('numSpeakers').value;
    if (numSpeakers && diarizationCheckbox.checked) {
        formData.append('speakers', numSpeakers);
    }

    console.log('📤 Enviando configuración:', {
        model: modelSelect.value,
        timestamps: timestampsCheckbox.checked ? 'true' : 'false',
        diarization: diarizationCheckbox.checked ? 'true' : 'false',
        speakers: numSpeakers,
        numFiles: filesArray.length
    });

    console.log('🌐 Iniciando petición a:', `${API_BASE_URL}/upload`);

    try {
        console.log('⏳ Ejecutando fetch...');
        // Upload files
        const response = await fetch(`${API_BASE_URL}/upload`, {
            method: 'POST',
            body: formData
        });

        console.log('✅ Respuesta recibida:', response.status, response.statusText);

        if (!response.ok) {
            console.error('❌ Respuesta no OK:', response.status);
            const errorData = await response.json().catch(() => ({ error: 'Error desconocido' }));
            throw new Error(errorData.error || `Error del servidor: ${response.status}`);
        }

        const data = await response.json();
        console.log('📦 Datos recibidos:', data);

        // Validate response data
        if (!data || !data.task_ids || !Array.isArray(data.task_ids)) {
            throw new Error('Respuesta inválida del servidor');
        }

        // Start tracking each task
        data.task_ids.forEach((taskId, index) => {
            const file = filesArray[index];
            if (file && taskId) {
                trackTask(taskId, file.name);
            }
        });

        // Show files queue
        filesQueue.style.display = 'block';

    } catch (error) {
        console.error('Error completo:', error);
        let errorMessage = `Error: ${error.message}`;

        // Check if backend is not running
        if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
            errorMessage = '❌ No se puede conectar al servidor backend.\n\n¿El backend está corriendo?\n\nPara iniciar el backend:\n1. Abre una terminal\n2. cd "c:\\Proyectos Antigravity\\AUDIO A TXT\\backend"\n3. python app.py';
        }

        alert(errorMessage);
        // Hide time estimate on error
        timeEstimate.style.display = 'none';
    }
}

function trackTask(taskId, filename) {
    // Add to active tasks
    activeTasks.set(taskId, { filename, pollInterval: null });

    // Create UI element
    createFileItem(taskId, filename);

    // Start polling
    startPolling(taskId);
}

function createFileItem(taskId, filename) {
    const fileItem = document.createElement('div');
    fileItem.className = 'file-item';
    fileItem.id = `file-${taskId}`;
    fileItem.innerHTML = `
        <div class="file-header">
            <div class="file-info">
                <div class="file-icon">🎵</div>
                <div class="file-name">${filename}</div>
            </div>
            <div class="file-status status-queued" id="status-${taskId}">En cola</div>
        </div>
        <div class="progress-container">
            <div class="progress-bar">
                <div class="progress-fill" id="progress-${taskId}" style="width: 0%"></div>
            </div>
            <div class="progress-text" id="progress-text-${taskId}">0%</div>
        </div>
    `;

    filesList.appendChild(fileItem);
}

async function startPolling(taskId) {
    const task = activeTasks.get(taskId);

    if (!task) return;

    const poll = async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/status/${taskId}`);

            if (!response.ok) {
                throw new Error('Error al obtener estado');
            }

            const data = await response.json();

            // Update UI
            updateTaskUI(taskId, data);

            // Check if completed or error
            if (data.status === 'completed') {
                stopPolling(taskId);
                moveToResults(taskId, data);
            } else if (data.status === 'error') {
                stopPolling(taskId);
                showError(taskId, data.error);
            }

        } catch (error) {
            console.error('Polling error:', error);
        }
    };

    // Poll immediately
    poll();

    // Then poll every interval
    task.pollInterval = setInterval(poll, POLL_INTERVAL);
}

function stopPolling(taskId) {
    const task = activeTasks.get(taskId);

    if (task && task.pollInterval) {
        clearInterval(task.pollInterval);
        task.pollInterval = null;
    }
}

function updateTaskUI(taskId, data) {
    const statusElement = document.getElementById(`status-${taskId}`);
    const progressFill = document.getElementById(`progress-${taskId}`);
    const progressText = document.getElementById(`progress-text-${taskId}`);

    if (!statusElement) return;

    // Update status
    statusElement.className = 'file-status';

    if (data.status === 'queued') {
        statusElement.classList.add('status-queued');
        statusElement.textContent = 'En cola';
    } else if (data.status === 'processing') {
        statusElement.classList.add('status-processing');
        statusElement.textContent = 'Procesando...';
    } else if (data.status === 'completed') {
        statusElement.classList.add('status-completed');
        statusElement.textContent = 'Completado';
    } else if (data.status === 'error') {
        statusElement.classList.add('status-error');
        statusElement.textContent = 'Error';
    }

    // Update progress
    const progress = data.progress || 0;
    if (progressFill && progressText) {
        progressFill.style.width = `${progress}%`;
        progressText.textContent = `${progress}%`;
    }
}

function moveToResults(taskId, data) {
    // Remove from queue
    const fileItem = document.getElementById(`file-${taskId}`);
    if (fileItem) {
        fileItem.remove();
    }

    // Remove from active tasks
    activeTasks.delete(taskId);

    // Add to completed tasks
    completedTasks.add(taskId);

    // Create result item
    createResultItem(data);

    // Show results section
    resultsSection.style.display = 'block';

    // Hide queue if empty
    if (activeTasks.size === 0) {
        filesQueue.style.display = 'none';
    }
}

function createResultItem(data) {
    const resultItem = document.createElement('div');
    resultItem.className = 'result-item';

    const outputFiles = data.output_files || [];
    const consolidatedFile = outputFiles.find(f => f.includes('_completo.txt'));
    const partFiles = outputFiles.filter(f => !f.includes('_completo.txt'));

    let downloadButtons = '';

    if (consolidatedFile) {
        downloadButtons += `
            <button class="download-btn consolidated" onclick="downloadFile('${consolidatedFile}')">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                    <path d="M12 3V16M12 16L16 12M12 16L8 12M21 21H3" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                Descargar Completo
            </button>
        `;
    }

    partFiles.forEach(file => {
        const partNumber = file.match(/_parte(\d+)/)?.[1] || '';
        const label = partNumber ? `Parte ${partNumber}` : 'Descargar';
        downloadButtons += `
            <button class="download-btn" onclick="downloadFile('${file}')">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                    <path d="M12 3V16M12 16L16 12M12 16L8 12M21 21H3" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                ${label}
            </button>
        `;
    });

    // Get original filename with fallbacks
    const originalFile = data.original_file || data.result?.original_file || data.filename || 'Archivo procesado';
    const numSegments = data.num_segments || data.result?.num_segments || 1;

    resultItem.innerHTML = `
        <div class="result-header">
            <div class="result-title">✅ ${originalFile}</div>
        </div>
        ${numSegments > 1 ? `<p style="color: var(--text-secondary); margin-bottom: 1rem;">Dividido en ${numSegments} partes</p>` : ''}
        <div class="download-section">
            ${downloadButtons}
        </div>
    `;

    resultsList.insertBefore(resultItem, resultsList.firstChild);
}

function showError(taskId, errorMessage) {
    const fileItem = document.getElementById(`file-${taskId}`);
    if (fileItem) {
        fileItem.innerHTML += `
            <div style="color: #f44336; margin-top: 1rem; padding: 1rem; background: rgba(244, 67, 54, 0.1); border-radius: 12px; border: 1px solid rgba(244, 67, 54, 0.2);">
                <strong>Error:</strong> ${errorMessage}
            </div>
        `;
    }
}

async function setLanguage(language) {
    try {
        const response = await fetch(`${API_BASE_URL}/set-language`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ language })
        });

        if (!response.ok) {
            throw new Error('Error al configurar idioma');
        }

        console.log(`Idioma configurado a: ${language}`);

    } catch (error) {
        console.error('Error:', error);
    }
}

function downloadFile(filename) {
    window.open(`${API_BASE_URL}/download/${filename}`, '_blank');
}

// Global Browser Lock
window.addEventListener("dragover", function(e) { e.preventDefault(); }, false);
window.addEventListener("drop", function(e) { e.preventDefault(); }, false);

// DOM Elements
const dropzone = document.getElementById('dropzone');
const fileInput = document.getElementById('fileInput');
const uploadContent = document.getElementById('uploadContent');
const previewContainer = document.getElementById('previewContainer');
const imagePreview = document.getElementById('imagePreview');
const scannerLine = document.getElementById('scannerLine');
const scanningOverlay = document.getElementById('scanningOverlay');
const scanStatus = document.getElementById('scanStatus');
const resetBtn = document.getElementById('resetBtn');

const emptyState = document.getElementById('emptyState');
const resultsState = document.getElementById('resultsState');
const serverStatusDot = document.getElementById('serverStatusDot');
const serverStatusText = document.getElementById('serverStatusText');

// ==========================================
// WEBSOCKET INITIALIZATION
// ==========================================
const socket = io('http://127.0.0.1:5000');

socket.on('connect', () => {
    serverStatusDot.classList.replace('bg-red-500', 'bg-emerald-500');
    serverStatusText.innerText = "WebSocket Connected";
});

socket.on('disconnect', () => {
    serverStatusDot.classList.replace('bg-emerald-500', 'bg-red-500');
    serverStatusText.innerText = "WebSocket Offline";
});

// Real-time progress updates from Python
socket.on('progress', (data) => {
    scanStatus.innerText = data.step;
});

// Final results payload from Python
socket.on('analysis_complete', (data) => {
    scannerLine.style.display = 'none';
    scanningOverlay.classList.add('hidden');
    emptyState.classList.add('hidden');
    resultsState.classList.remove('hidden');

    try {
        populateDashboard(data);
    } catch(e) {
        console.error("UI Rendering Crash:", e);
        resultsState.innerHTML = `
            <div class="text-sky-400 p-4 font-mono h-full flex flex-col">
                <h3 class="text-xl font-bold mb-2 text-emerald-400">Analysis Complete!</h3>
                <textarea class="w-full flex-1 bg-slate-900 border border-slate-700 p-4 rounded text-xs text-slate-300" readonly>${JSON.stringify(data, null, 2)}</textarea>
            </div>
        `;
    }
});

// Error handling from Python
socket.on('analysis_error', (data) => {
    scannerLine.style.display = 'none';
    scanningOverlay.classList.add('hidden');
    emptyState.classList.remove('hidden');
    alert("Python Execution Error: " + data.error);
});

// ==========================================
// UPLOAD LOGIC
// ==========================================
dropzone.addEventListener('click', (e) => {
    // Prevent infinite clicking loops
    if (e.target === fileInput) return; 
    fileInput.click();
});

// 2. Drag and Drop styling
dropzone.addEventListener('dragover', (e) => { 
    e.preventDefault(); 
    dropzone.classList.add('border-sky-400', 'bg-sky-900/10'); 
});

dropzone.addEventListener('dragleave', (e) => { 
    e.preventDefault(); 
    dropzone.classList.remove('border-sky-400', 'bg-sky-900/10'); 
});

// 3. Drop action
dropzone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropzone.classList.remove('border-sky-400', 'bg-sky-900/10');
    if (e.dataTransfer.files.length > 0) {
        processFile(e.dataTransfer.files[0]);
    }
});

// 4. File input change (when user selects a file from the popup window)
fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        processFile(e.target.files[0]);
    }
});

resetBtn.addEventListener('click', (e) => {
    e.preventDefault();
    fileInput.value = '';
    previewContainer.classList.add('hidden');
    uploadContent.classList.remove('hidden');
    resultsState.classList.add('hidden');
    emptyState.classList.remove('hidden');
    resetBtn.classList.add('hidden');
    scannerLine.style.display = 'none';
});

function processFile(file) {
    if (!file.type.startsWith('image/')) {
        alert('Please upload an image file (JPG/JPEG/PNG).');
        return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
        // Show Image
        imagePreview.src = e.target.result;
        uploadContent.classList.add('hidden');
        previewContainer.classList.remove('hidden');
        resetBtn.classList.remove('hidden');

        // Setup UI for scanning
        scannerLine.style.display = 'block';
        scanningOverlay.classList.remove('hidden');
        emptyState.classList.add('hidden');
        resultsState.classList.add('hidden');
        scanStatus.innerText = "Transmitting image buffer to Python...";

        // Send payload via WebSocket
        socket.emit('analyze_image', { 
            file_data: e.target.result 
        });
    };
    reader.readAsDataURL(file); // This reads it as a Base64 string for safe WebSocket transmission
}

// --- Dynamic UI Population ---
function populateDashboard(data) {
    const isAuthentic = data.final_verdict && data.final_verdict.includes('Authentic');
    
    const finalVerdict = document.getElementById('finalVerdict');
    finalVerdict.innerText = data.final_verdict || "UNKNOWN";
    finalVerdict.className = `text-4xl font-bold uppercase tracking-wide ${isAuthentic ? 'text-emerald-400' : 'text-red-500'}`;
    
    const confText = document.getElementById('confidenceText');
    confText.className = `text-3xl font-mono font-light ${isAuthentic ? 'text-emerald-400' : 'text-red-500'}`;
    animateValue(confText, 0, data.joint_confidence || 0, 1500);

    const setTrace = (id, traceData, extra = "") => {
        if (!traceData) return; 
        const vEl = document.getElementById(`${id}Verdict`);
        const sEl = document.getElementById(`${id}Score`);
        
        if (traceData.status && traceData.status.includes('Bypassed')) {
            if(vEl) {
                vEl.innerText = 'BYPASSED';
                vEl.className = 'text-xs uppercase font-bold mb-1 text-slate-500';
            }
            if(sEl) sEl.innerText = traceData.status;
        } else {
            const traceAuth = traceData.verdict && traceData.verdict.includes('Authentic');
            if(vEl) {
                vEl.innerText = traceData.verdict || "UNKNOWN";
                vEl.className = `text-xs uppercase font-bold mb-1 ${traceAuth ? 'text-emerald-400' : 'text-red-400'}`;
            }
            if(sEl) sEl.innerText = `Conf: ${((traceData.score || 0) * 100).toFixed(1)}% ${extra}`;
        }
    };

    setTrace('prnu', data.breakdown.prnu);
    setTrace('cfa', data.breakdown.cfa);
    setTrace('jpeg', data.breakdown.jpeg);
    
    const devText = data.breakdown.lighting && data.breakdown.lighting.deviation !== undefined ? `(Dev: ${data.breakdown.lighting.deviation}°)` : "";
    setTrace('light', data.breakdown.lighting, devText);
}

function animateValue(obj, start, end, duration) {
    if(!obj) return;
    let startTimestamp = null;
    const step = (timestamp) => {
        if (!startTimestamp) startTimestamp = timestamp;
        const progress = Math.min((timestamp - startTimestamp) / duration, 1);
        obj.innerHTML = (progress * (end - start) + start).toFixed(2) + "%";
        if (progress < 1) window.requestAnimationFrame(step);
    };
    window.requestAnimationFrame(step);
}
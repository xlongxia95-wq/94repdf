/**
 * 94RePdf - 就是讓 PDF 重生
 * 前端主程式 - 支援三種 OCR 模式
 */

// API 位置
const API_BASE = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? '/api'
    : 'https://nine4repdf.onrender.com/api';

// Ollama 本地服務位置
const OLLAMA_BASE = 'http://localhost:11434';

// 狀態
let state = {
    authenticated: false,
    currentFeature: null,
    fileId: null,
    taskId: null,
    analysis: null,
    ocrMode: 'tesseract',  // 'ollama', 'tesseract', 'gemini'
    uploadedFile: null,
    ollamaAvailable: false,
    tesseractWorker: null
};

// DOM 元素
const elements = {
    authScreen: document.getElementById('auth-screen'),
    mainScreen: document.getElementById('main-screen'),
    passwordInput: document.getElementById('password-input'),
    authBtn: document.getElementById('auth-btn'),
    dropZone: document.getElementById('drop-zone'),
    fileInput: document.getElementById('file-input'),
    processBtn: document.getElementById('process-btn')
};

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    initAuth();
    initUpload();
    initFeatureCards();
    initProcess();
    initOcrModeSelector();
    checkOllamaAvailability();
});

// ===== Ollama 可用性檢查 =====
async function checkOllamaAvailability() {
    const statusEl = document.getElementById('ollama-status');
    const card = document.querySelector('.ocr-mode-card[data-mode="ollama"]');
    
    if (!statusEl || !card) return;
    
    try {
        // 嘗試連接 Ollama
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 3000);
        
        const res = await fetch(`${OLLAMA_BASE}/api/tags`, {
            signal: controller.signal
        });
        clearTimeout(timeout);
        
        if (res.ok) {
            const data = await res.json();
            // 檢查是否有 qwen3-vl 模型
            const hasQwen = data.models?.some(m => 
                m.name.includes('qwen') && m.name.includes('vl')
            );
            
            if (hasQwen) {
                statusEl.textContent = '✓ 可用';
                statusEl.className = 'mode-badge available';
                card.classList.remove('unavailable');
                state.ollamaAvailable = true;
                
                // 如果 Ollama 可用，設為預設
                selectOcrMode('ollama');
                return;
            } else {
                statusEl.textContent = '需安裝模型';
                statusEl.className = 'mode-badge unavailable';
                statusEl.title = '請執行: ollama pull qwen3-vl:8b';
            }
        }
    } catch (err) {
        console.log('Ollama not available:', err.message);
    }
    
    // Ollama 不可用
    statusEl.textContent = '未安裝';
    statusEl.className = 'mode-badge unavailable';
    card.classList.add('unavailable');
    state.ollamaAvailable = false;
}

// ===== OCR 模式選擇 =====
function initOcrModeSelector() {
    document.querySelectorAll('.ocr-mode-card').forEach(card => {
        card.addEventListener('click', () => {
            const mode = card.dataset.mode;
            
            // 檢查 Ollama 是否可用
            if (mode === 'ollama' && !state.ollamaAvailable) {
                alert('⚠️ 本地 AI 需要安裝 Ollama\n\n請先安裝：\n1. brew install ollama\n2. ollama serve\n3. ollama pull qwen3-vl:8b');
                return;
            }
            
            selectOcrMode(mode);
        });
    });
}

function selectOcrMode(mode) {
    // 移除其他選擇
    document.querySelectorAll('.ocr-mode-card').forEach(c => c.classList.remove('selected'));
    // 選擇當前
    const card = document.querySelector(`.ocr-mode-card[data-mode="${mode}"]`);
    if (card) card.classList.add('selected');
    
    state.ocrMode = mode;
    updateCostDisplay();
    updateHintText();
    
    console.log('OCR mode selected:', mode);
}

function updateCostDisplay() {
    const costEl = document.getElementById('cost');
    if (!costEl) return;
    
    const pages = state.analysis?.pages || 10;
    
    switch (state.ocrMode) {
        case 'ollama':
            costEl.innerHTML = `🆓 <span style="color: green;">完全免費</span>`;
            costEl.title = '本地 AI：使用你電腦的 GPU，完全免費無限制';
            break;
        case 'tesseract':
            costEl.innerHTML = `🆓 <span style="color: green;">完全免費</span>`;
            costEl.title = '本地 OCR：純瀏覽器運行，完全免費';
            break;
        case 'gemini':
            const costPerPage = 0.0004;
            const totalUSD = pages * costPerPage;
            const totalTWD = totalUSD * 31;
            costEl.innerHTML = 
                `🆓 <span style="color: green;">免費額度內</span><br>` +
                `<small style="color: #666;">超出：$${totalUSD.toFixed(4)} (NT$${totalTWD.toFixed(2)})</small>`;
            costEl.title = 'Gemini 2.0 Flash: 每頁約 NT$0.012，每日 500 免費請求';
            break;
    }
}

function updateHintText() {
    const hintEl = document.getElementById('ocr-mode-hint');
    if (!hintEl) return;
    
    const hints = {
        'ollama': '✨ 最佳選擇！使用本地 AI 模型，準確度高且完全免費',
        'tesseract': '📄 純瀏覽器運行，不需網路，適合簡單文件',
        'gemini': '☁️ 雲端 AI，最高準確度，適合複雜排版'
    };
    hintEl.textContent = hints[state.ocrMode] || '';
}

// ===== 密碼驗證 =====
function initAuth() {
    elements.authBtn.addEventListener('click', handleAuth);
    elements.passwordInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleAuth();
    });
    
    // 檢查是否已驗證
    if (getCookie('authenticated') === 'true') {
        showMainScreen();
    }
}

async function handleAuth() {
    const password = elements.passwordInput.value;
    if (!password) {
        alert('請輸入密碼');
        return;
    }
    
    try {
        const res = await fetch(`${API_BASE}/auth/verify`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ password })
        });
        
        if (res.ok) {
            setCookie('authenticated', 'true', 7);
            showMainScreen();
        } else {
            alert('密碼錯誤');
            elements.passwordInput.value = '';
        }
    } catch (err) {
        console.error('Auth error:', err);
        alert('連線錯誤: ' + err.message);
    }
}

function showMainScreen() {
    state.authenticated = true;
    elements.authScreen.classList.remove('active');
    elements.mainScreen.classList.add('active');
}

// ===== 功能卡片 =====
function initFeatureCards() {
    document.querySelectorAll('.feature-card').forEach(card => {
        card.addEventListener('click', () => {
            const feature = card.dataset.feature;
            state.currentFeature = feature;
            
            const titles = {
                'pptx': '上傳 PDF 轉 PPTX',
                'quick-edit': '上傳檔案進行快速編輯',
                'image': '上傳 PDF 轉圖片',
                'rotate': '上傳 PDF 進行旋轉',
                'resize': '上傳 PDF 調整尺寸',
                'page-number': '上傳 PDF 添加頁碼'
            };
            document.getElementById('upload-title').textContent = titles[feature] || '上傳檔案';
            
            showSection('upload-section');
        });
    });
}

// ===== 檔案上傳 =====
function initUpload() {
    const dropZone = elements.dropZone;
    const fileInput = elements.fileInput;
    
    dropZone.addEventListener('click', () => fileInput.click());
    
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });
    
    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('dragover');
    });
    
    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        if (e.dataTransfer.files.length > 0) {
            handleFile(e.dataTransfer.files[0]);
        }
    });
    
    fileInput.addEventListener('change', () => {
        if (fileInput.files.length > 0) {
            handleFile(fileInput.files[0]);
        }
    });
}

async function handleFile(file) {
    const validTypes = ['application/pdf', 'image/png', 'image/jpeg'];
    if (!validTypes.includes(file.type)) {
        alert('只支援 PDF、PNG、JPG 格式');
        return;
    }
    
    if (file.size > 50 * 1024 * 1024) {
        alert('檔案超過 50MB 限制');
        return;
    }
    
    state.uploadedFile = file;
    
    try {
        const formData = new FormData();
        formData.append('file', file);
        
        const uploadRes = await fetch(`${API_BASE}/upload`, {
            method: 'POST',
            body: formData
        });
        
        if (!uploadRes.ok) throw new Error('上傳失敗');
        
        const uploadData = await uploadRes.json();
        state.fileId = uploadData.file_id;
        
        const analyzeRes = await fetch(`${API_BASE}/analyze/${state.fileId}`);
        if (!analyzeRes.ok) throw new Error('分析失敗');
        const analyzeData = await analyzeRes.json();
        state.analysis = analyzeData.analysis;
        
        updateAnalyzeUI(file.name, file.size, analyzeData.analysis);
        showSection('analyze-section');
        
    } catch (err) {
        console.error('Upload error:', err);
        // 本地模式仍可用
        state.analysis = {
            pages: 1,
            original_size: { name: 'Unknown', width_mm: 0, height_mm: 0 },
            orientation: 'portrait',
            type: 'image_pdf'
        };
        updateAnalyzeUI(file.name, file.size, state.analysis);
        showSection('analyze-section');
    }
}

function updateAnalyzeUI(filename, size, analysis) {
    document.getElementById('file-name').textContent = filename;
    document.getElementById('file-meta').textContent = 
        `${analysis.pages} 頁 · ${formatSize(size)}`;
    
    document.getElementById('original-size').textContent = 
        `${analysis.original_size.name} (${analysis.original_size.width_mm} × ${analysis.original_size.height_mm} mm)`;
    
    document.getElementById('orientation').textContent = 
        analysis.orientation === 'portrait' ? '直向' : '橫向';
    
    const typeLabels = {
        'native_pdf': '原生 PDF（有文字層）',
        'image_pdf': '圖片式 PDF（需要 OCR）',
        'mixed': '混合型 PDF'
    };
    document.getElementById('pdf-type').textContent = typeLabels[analysis.type] || analysis.type;
    
    updateCostDisplay();
}

// ===== 處理 =====
function initProcess() {
    elements.processBtn.addEventListener('click', startProcess);
}

async function startProcess() {
    const outputRatio = document.getElementById('slide-ratio').value;
    const removeWatermark = document.getElementById('remove-watermark').checked;
    
    showSection('progress-section');
    
    switch (state.ocrMode) {
        case 'ollama':
            await processWithOllama();
            break;
        case 'tesseract':
            await processWithTesseract();
            break;
        case 'gemini':
            await processWithGemini(outputRatio, removeWatermark);
            break;
    }
}

// ===== Ollama 本地 AI 處理 =====
async function processWithOllama() {
    try {
        updateProgressUI(0, 1, 1, '連接本地 AI...');
        
        const file = state.uploadedFile;
        if (!file) {
            alert('請先上傳檔案');
            return;
        }
        
        // 檢查是否為圖片
        if (!file.type.startsWith('image/')) {
            alert('本地 AI 模式目前只支援圖片（PNG/JPG）。\nPDF 請使用雲端 AI 模式。');
            showSection('analyze-section');
            return;
        }
        
        // 轉換為 base64
        const base64 = await fileToBase64(file);
        
        updateProgressUI(10, 1, 1, 'Qwen3-VL 分析中...');
        
        // 呼叫 Ollama API
        const res = await fetch(`${OLLAMA_BASE}/api/generate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                model: 'qwen3-vl:8b',
                prompt: '請辨識這張圖片中的所有文字，保持原始排版格式。只輸出辨識結果，不要加其他說明。',
                images: [base64],
                stream: false
            })
        });
        
        if (!res.ok) {
            throw new Error('Ollama API 錯誤');
        }
        
        const data = await res.json();
        updateProgressUI(100, 1, 1, '完成！');
        
        // 顯示結果
        const imageData = await fileToDataURL(file);
        showOCRResult({
            text: data.response,
            confidence: 95,
            mode: 'Qwen3-VL (本地 AI)'
        }, imageData);
        
    } catch (err) {
        console.error('Ollama error:', err);
        alert('本地 AI 處理失敗：' + err.message + '\n\n請確認 Ollama 正在運行');
        showSection('analyze-section');
    }
}

// ===== Tesseract.js 本地 OCR 處理 =====
async function processWithTesseract() {
    try {
        updateProgressUI(0, 1, 1, '初始化 OCR 引擎...');
        
        const file = state.uploadedFile;
        if (!file) {
            alert('請先上傳檔案');
            return;
        }
        
        // 檢查是否為圖片
        if (!file.type.startsWith('image/')) {
            alert('本地 OCR 模式只支援圖片（PNG/JPG）。\n\nPDF 請選擇「雲端 AI」模式。');
            showSection('analyze-section');
            return;
        }
        
        updateProgressUI(5, 1, 1, '載入語言包...');
        
        // 初始化 Tesseract worker (中文繁體 + 英文)
        const worker = await Tesseract.createWorker('chi_tra+eng', 1, {
            logger: m => {
                if (m.status === 'recognizing text') {
                    const percent = Math.round(20 + m.progress * 70);
                    updateProgressUI(percent, 1, 1, '文字辨識中...');
                } else if (m.status === 'loading language traineddata') {
                    updateProgressUI(10, 1, 1, '載入語言包...');
                }
            }
        });
        
        const imageData = await fileToDataURL(file);
        
        updateProgressUI(20, 1, 1, '文字辨識中...');
        const { data } = await worker.recognize(imageData);
        
        await worker.terminate();
        
        updateProgressUI(100, 1, 1, '完成！');
        
        showOCRResult({
            text: data.text,
            confidence: data.confidence,
            mode: 'Tesseract.js (本地 OCR)'
        }, imageData);
        
    } catch (err) {
        console.error('Tesseract error:', err);
        alert('本地 OCR 處理失敗：' + err.message);
        showSection('analyze-section');
    }
}

// ===== Gemini 雲端 AI 處理 =====
async function processWithGemini(outputRatio, removeWatermark) {
    try {
        updateProgressUI(0, 1, 1, '連接雲端 AI...');
        
        const res = await fetch(`${API_BASE}/process/pptx`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                file_id: state.fileId,
                output_ratio: outputRatio,
                remove_watermark: removeWatermark,
                use_local: false  // 使用 Gemini
            })
        });
        
        if (!res.ok) {
            const error = await res.json().catch(() => ({}));
            throw new Error(error.detail || '處理請求失敗');
        }
        
        const data = await res.json();
        state.taskId = data.task_id;
        
        pollProgress();
        
    } catch (err) {
        console.error('Gemini process error:', err);
        alert('雲端 AI 處理失敗：' + err.message);
        showSection('analyze-section');
    }
}

async function pollProgress() {
    try {
        const res = await fetch(`${API_BASE}/process/status/${state.taskId}`);
        if (!res.ok) {
            throw new Error('狀態查詢失敗');
        }
        const data = await res.json();
        
        updateProgress(data.progress);
        
        if (data.status === 'done') {
            showSection('result-section');
            setupDownloadButtons();
        } else if (data.status === 'failed') {
            alert('處理失敗：' + (data.error || '未知錯誤'));
            showSection('analyze-section');
        } else {
            setTimeout(pollProgress, 1000);
        }
    } catch (err) {
        console.error('Poll error:', err);
        setTimeout(pollProgress, 2000);
    }
}

function updateProgress(progress) {
    document.getElementById('progress-fill').style.width = `${progress.percent}%`;
    document.getElementById('progress-text').textContent = `${progress.percent}%`;
    document.getElementById('current-page').textContent = progress.current_page;
    document.getElementById('total-pages').textContent = progress.total_pages;
    
    const stepLabels = {
        'ocr': 'Gemini AI 辨識中...',
        'inpainting': '背景重建...',
        'pptx': 'PPTX 生成中...'
    };
    document.getElementById('current-step').textContent = stepLabels[progress.current_step] || progress.current_step;
}

// ===== 結果顯示 =====
function showOCRResult(result, imageData) {
    showSection('result-section');
    
    const previewArea = document.getElementById('preview-area');
    previewArea.innerHTML = `
        <div style="width: 100%; padding: 1rem;">
            <img src="${imageData}" style="max-width: 100%; height: auto; border-radius: 0.5rem; margin-bottom: 1rem;" />
            <div style="padding: 1rem; background: var(--bg); border-radius: 0.5rem; border: 1px solid var(--border);">
                <h4 style="margin-bottom: 0.5rem;">📝 ${escapeHtml(result.mode)} 辨識結果</h4>
                <pre style="white-space: pre-wrap; font-size: 14px; max-height: 300px; overflow-y: auto; background: var(--card-bg); padding: 1rem; border-radius: 0.5rem;">${escapeHtml(result.text) || '(無辨識結果)'}</pre>
                <p style="margin-top: 0.5rem; color: var(--text-light); font-size: 0.875rem;">
                    信心度：${Math.round(result.confidence || 0)}%
                </p>
            </div>
        </div>
    `;
    
    // 更新按鈕
    const downloadPptx = document.getElementById('download-pptx');
    const downloadPdf = document.getElementById('download-pdf');
    
    downloadPptx.textContent = '📋 複製文字';
    downloadPptx.onclick = () => {
        navigator.clipboard.writeText(result.text);
        downloadPptx.textContent = '✅ 已複製！';
        setTimeout(() => downloadPptx.textContent = '📋 複製文字', 2000);
    };
    
    downloadPdf.textContent = '💾 下載原圖';
    downloadPdf.onclick = () => {
        const link = document.createElement('a');
        link.href = imageData;
        link.download = 'ocr-result.png';
        link.click();
    };
}

function setupDownloadButtons() {
    const downloadPptx = document.getElementById('download-pptx');
    const downloadPdf = document.getElementById('download-pdf');
    const reprocess = document.getElementById('reprocess');
    
    // PPTX 下載
    downloadPptx.textContent = '⬇️ 下載 PPTX';
    downloadPptx.onclick = async () => {
        window.location.href = `${API_BASE}/download/${state.taskId}`;
    };
    
    // PDF 下載（原始檔案）
    downloadPdf.textContent = '📄 下載原始 PDF';
    downloadPdf.onclick = async () => {
        if (state.uploadedFile) {
            const url = URL.createObjectURL(state.uploadedFile);
            const link = document.createElement('a');
            link.href = url;
            link.download = state.uploadedFile.name;
            link.click();
            URL.revokeObjectURL(url);
        } else {
            alert('原始檔案不可用');
        }
    };
    
    // 重新處理
    reprocess.onclick = () => {
        showSection('analyze-section');
    };
}

// ===== 工具函數 =====
function updateProgressUI(percent, current, total, step) {
    document.getElementById('progress-fill').style.width = `${percent}%`;
    document.getElementById('progress-text').textContent = `${percent}%`;
    document.getElementById('current-page').textContent = current;
    document.getElementById('total-pages').textContent = total;
    document.getElementById('current-step').textContent = step;
}

function fileToDataURL(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result);
        reader.onerror = reject;
        reader.readAsDataURL(file);
    });
}

function fileToBase64(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => {
            // 移除 data:image/xxx;base64, 前綴
            const base64 = reader.result.split(',')[1];
            resolve(base64);
        };
        reader.onerror = reject;
        reader.readAsDataURL(file);
    });
}

function showSection(sectionId) {
    document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
    document.getElementById(sectionId).classList.add('active');
}

function formatSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

function setCookie(name, value, days) {
    const expires = new Date(Date.now() + days * 864e5).toUTCString();
    document.cookie = `${name}=${value}; expires=${expires}; path=/`;
}

function getCookie(name) {
    return document.cookie.split('; ').reduce((r, v) => {
        const parts = v.split('=');
        return parts[0] === name ? parts[1] : r;
    }, '');
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

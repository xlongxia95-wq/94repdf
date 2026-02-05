/**
 * 94RePdf - 就是讓 PDF 重生
 * 前端主程式
 */

// API 位置（部署時會設定為雲端 URL）
const API_BASE = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? '/api'
    : 'https://steven-fame-pod-vacancies.trycloudflare.com/api';

// 狀態
let state = {
    authenticated: false,
    currentFeature: null,
    fileId: null,
    taskId: null,
    analysis: null,
    ocrMode: 'local',  // 'local' 或 'ai'
    uploadedFile: null  // 儲存上傳的檔案供本地處理
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
});

// ===== OCR 模式選擇 =====
function initOcrModeSelector() {
    document.querySelectorAll('.ocr-mode-card').forEach(card => {
        card.addEventListener('click', () => {
            // 移除其他選擇
            document.querySelectorAll('.ocr-mode-card').forEach(c => c.classList.remove('selected'));
            // 選擇當前
            card.classList.add('selected');
            state.ocrMode = card.dataset.mode;
            
            // 更新費用顯示
            updateCostDisplay();
            
            console.log('OCR mode selected:', state.ocrMode);
        });
    });
}

function updateCostDisplay() {
    const costEl = document.getElementById('cost');
    const pages = state.analysis?.pages || 10;
    
    if (state.ocrMode === 'local') {
        costEl.innerHTML = `🆓 <span style="color: green;">完全免費</span>`;
        costEl.title = '本地處理：在你的裝置上執行，完全免費';
    } else {
        const costPerPage = 0.0004;
        const totalUSD = pages * costPerPage;
        const totalTWD = totalUSD * 31;
        costEl.innerHTML = 
            `🆓 <span style="color: green;">免費額度內</span><br>` +
            `<small style="color: #666;">超出：$${totalUSD.toFixed(4)} (NT$${totalTWD.toFixed(2)})</small>`;
        costEl.title = 'AI 模式：Gemini 2.0 Flash，每頁約 NT$0.012';
    }
}

// ===== 密碼驗證 =====
function initAuth() {
    elements.authBtn.addEventListener('click', handleAuth);
    elements.passwordInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleAuth();
    });
    
    // 檢查是否已驗證（從 cookie）
    if (getCookie('authenticated') === 'true') {
        showMainScreen();
    }
}

async function handleAuth() {
    console.log('handleAuth called');
    const password = elements.passwordInput.value;
    console.log('Password entered:', password ? '***' : 'empty');
    if (!password) {
        alert('請輸入密碼');
        return;
    }
    
    try {
        console.log('Calling API:', API_BASE + '/auth/verify');
        const res = await fetch(`${API_BASE}/auth/verify`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ password })
        });
        
        console.log('API response:', res.status);
        if (res.ok) {
            setCookie('authenticated', 'true', 7);
            console.log('Showing main screen...');
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
            
            // 更新上傳標題
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
    
    // 點擊上傳
    dropZone.addEventListener('click', () => fileInput.click());
    
    // 拖放
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
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFile(files[0]);
        }
    });
    
    // 檔案選擇
    fileInput.addEventListener('change', () => {
        if (fileInput.files.length > 0) {
            handleFile(fileInput.files[0]);
        }
    });
}

async function handleFile(file) {
    // 檢查檔案類型
    const validTypes = ['application/pdf', 'image/png', 'image/jpeg'];
    if (!validTypes.includes(file.type)) {
        alert('只支援 PDF、PNG、JPG 格式');
        return;
    }
    
    // 檢查大小
    if (file.size > 50 * 1024 * 1024) {
        alert('檔案超過 50MB 限制');
        return;
    }
    
    // 儲存檔案供本地處理使用
    state.uploadedFile = file;
    
    try {
        // 上傳檔案到後端（AI 模式需要）
        const formData = new FormData();
        formData.append('file', file);
        
        const uploadRes = await fetch(`${API_BASE}/upload`, {
            method: 'POST',
            body: formData
        });
        
        if (!uploadRes.ok) throw new Error('上傳失敗');
        
        const uploadData = await uploadRes.json();
        state.fileId = uploadData.file_id;
        
        // 分析檔案
        const analyzeRes = await fetch(`${API_BASE}/analyze/${state.fileId}`);
        const analyzeData = await analyzeRes.json();
        state.analysis = analyzeData.analysis;
        
        // 更新 UI
        updateAnalyzeUI(file.name, file.size, analyzeData.analysis);
        showSection('analyze-section');
        
    } catch (err) {
        console.error('Upload error:', err);
        // 即使上傳失敗，本地模式仍可使用
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
        'image_pdf': '圖片式 PDF（需要 AI 辨識）',
        'mixed': '混合型 PDF'
    };
    document.getElementById('pdf-type').textContent = typeLabels[analysis.type] || analysis.type;
    
    // 費用計算：Gemini 2.0 Flash
    // 每頁約 $0.0004 USD = NT$0.012
    const pages = analysis.pages || 10;
    const costPerPage = 0.0004; // USD
    const totalUSD = pages * costPerPage;
    const totalTWD = totalUSD * 31;
    
    // 免費額度內（每日 500 請求）
    if (pages <= 500) {
        document.getElementById('cost').innerHTML = 
            `🆓 <span style="color: green;">免費額度內</span><br>` +
            `<small style="color: #666;">超出額度：約 $${totalUSD.toFixed(4)} USD (NT$${totalTWD.toFixed(2)})</small>`;
    } else {
        document.getElementById('cost').textContent = 
            `約 $${totalUSD.toFixed(4)} USD (NT$${totalTWD.toFixed(2)})`;
    }
    document.getElementById('cost').title = 
        `Gemini 2.0 Flash: 每頁約 NT$0.012\n免費額度：每日 500 請求`;
}

// ===== 處理 =====
function initProcess() {
    elements.processBtn.addEventListener('click', startProcess);
}

async function startProcess() {
    const outputRatio = document.getElementById('slide-ratio').value;
    const removeWatermark = document.getElementById('remove-watermark').checked;
    
    showSection('progress-section');
    
    // 兩種模式都用後端處理，差別在 use_local 參數
    // local = 後端 Ollama 視覺模型（完全免費）
    // ai = 後端 Gemini API
    const useLocal = state.ocrMode === 'local';
    await processWithBackend(outputRatio, removeWatermark, useLocal);
}

// ===== 本地 OCR 處理 =====
async function processWithLocalOCR() {
    try {
        updateProgressUI(0, 1, 1, 'initializing');
        
        const file = state.uploadedFile;
        if (!file) {
            alert('請先上傳檔案');
            return;
        }
        
        // 初始化 Tesseract worker
        updateProgressUI(5, 1, 1, 'loading');
        const worker = await Tesseract.createWorker('chi_tra+eng', 1, {
            logger: m => {
                if (m.status === 'recognizing text') {
                    const percent = Math.round(10 + m.progress * 80);
                    updateProgressUI(percent, 1, 1, 'ocr');
                }
            }
        });
        
        let imageData;
        
        // 如果是圖片，直接處理
        if (file.type.startsWith('image/')) {
            imageData = await fileToDataURL(file);
        } else {
            // PDF 需要轉成圖片（使用 canvas）
            // 簡化版：提示用戶先轉成圖片
            alert('本地模式目前只支援圖片（PNG/JPG）。\nPDF 請使用 AI 模式，或先將 PDF 轉成圖片。');
            await worker.terminate();
            showSection('analyze-section');
            return;
        }
        
        // 執行 OCR
        updateProgressUI(10, 1, 1, 'ocr');
        const { data } = await worker.recognize(imageData);
        
        updateProgressUI(90, 1, 1, 'generating');
        
        // 顯示 OCR 結果
        console.log('OCR Result:', data);
        
        // 儲存結果
        state.ocrResult = data;
        
        await worker.terminate();
        
        updateProgressUI(100, 1, 1, 'done');
        
        // 顯示結果
        setTimeout(() => {
            showOCRResult(data, imageData);
        }, 500);
        
    } catch (err) {
        console.error('Local OCR error:', err);
        alert('本地 OCR 處理失敗：' + err.message);
        showSection('analyze-section');
    }
}

function fileToDataURL(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result);
        reader.onerror = reject;
        reader.readAsDataURL(file);
    });
}

function showOCRResult(ocrData, imageData) {
    showSection('result-section');
    
    // 顯示預覽圖片
    const previewArea = document.getElementById('preview-area');
    previewArea.innerHTML = `
        <div style="position: relative; width: 100%;">
            <img src="${imageData}" style="max-width: 100%; height: auto;" />
            <div style="margin-top: 1rem; padding: 1rem; background: #f5f5f5; border-radius: 0.5rem;">
                <h4>📝 OCR 辨識結果</h4>
                <pre style="white-space: pre-wrap; font-size: 14px; max-height: 300px; overflow-y: auto;">${ocrData.text}</pre>
                <p style="margin-top: 0.5rem; color: #666;">信心度：${Math.round(ocrData.confidence)}%</p>
            </div>
        </div>
    `;
    
    // 更新下載按鈕
    document.getElementById('download-pptx').textContent = '複製文字';
    document.getElementById('download-pptx').onclick = () => {
        navigator.clipboard.writeText(ocrData.text);
        alert('已複製到剪貼簿！');
    };
    
    document.getElementById('download-pdf').textContent = '下載原圖';
    document.getElementById('download-pdf').onclick = () => {
        const link = document.createElement('a');
        link.href = imageData;
        link.download = 'result.png';
        link.click();
    };
}

function updateProgressUI(percent, current, total, step) {
    document.getElementById('progress-fill').style.width = `${percent}%`;
    document.getElementById('progress-text').textContent = `${percent}%`;
    document.getElementById('current-page').textContent = current;
    document.getElementById('total-pages').textContent = total;
    
    const stepLabels = {
        'initializing': '初始化中...',
        'loading': '載入 OCR 引擎...',
        'ocr': '文字辨識中...',
        'generating': '生成結果...',
        'done': '完成！'
    };
    document.getElementById('current-step').textContent = stepLabels[step] || step;
}

// ===== 後端處理（本地 Ollama 或 Gemini API）=====
async function processWithBackend(outputRatio, removeWatermark, useLocal = true) {
    try {
        const modeLabel = useLocal ? '本地 Ollama' : 'Gemini API';
        console.log(`Starting process with ${modeLabel} mode`);
        
        const res = await fetch(`${API_BASE}/process/pptx`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                file_id: state.fileId,
                output_ratio: outputRatio,
                remove_watermark: removeWatermark,
                use_local: useLocal  // true = Ollama, false = Gemini
            })
        });
        
        const data = await res.json();
        state.taskId = data.task_id;
        
        // 開始輪詢進度
        pollProgress();
        
    } catch (err) {
        console.error('Process error:', err);
        alert('處理失敗');
        showSection('analyze-section');
    }
}

async function pollProgress() {
    try {
        const res = await fetch(`${API_BASE}/process/status/${state.taskId}`);
        const data = await res.json();
        
        updateProgress(data.progress);
        
        if (data.status === 'done') {
            showSection('result-section');
        } else if (data.status === 'failed') {
            alert('處理失敗');
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
        'ocr': 'OCR 文字辨識',
        'inpainting': '背景重建',
        'pptx': 'PPTX 生成'
    };
    document.getElementById('current-step').textContent = stepLabels[progress.current_step] || progress.current_step;
}

// ===== 工具函數 =====
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

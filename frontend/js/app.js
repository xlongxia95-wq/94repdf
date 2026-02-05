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
    analysis: null
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
});

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
    
    try {
        // 上傳檔案
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
        alert('上傳失敗，請稍後再試');
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
    
    // 免費額度內不收費
    document.getElementById('cost').textContent = '🆓 免費';
    document.getElementById('cost').title = '使用 Gemini 免費額度，每日限處理約 1500 頁';
}

// ===== 處理 =====
function initProcess() {
    elements.processBtn.addEventListener('click', startProcess);
}

async function startProcess() {
    const outputRatio = document.getElementById('slide-ratio').value;
    const removeWatermark = document.getElementById('remove-watermark').checked;
    
    try {
        showSection('progress-section');
        
        const res = await fetch(`${API_BASE}/process/pptx`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                file_id: state.fileId,
                output_ratio: outputRatio,
                remove_watermark: removeWatermark
            })
        });
        
        const data = await res.json();
        state.taskId = data.task_id;
        
        // 開始輪詢進度
        pollProgress();
        
    } catch (err) {
        console.error('Process error:', err);
        alert('處理失敗');
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

import { CopilotClient } from '@github/copilot-sdk';
import fs from 'fs';

const TASK = `
你是一個專業的全端工程師。請在當前目錄建立 94RePdf 專案的完整檔案結構：

## 需要建立的檔案

### backend/main.py
FastAPI 入口，包含 CORS、健康檢查端點

### backend/requirements.txt
包含：fastapi, uvicorn, python-multipart, pypdf, pdf2image, Pillow, python-pptx, google-cloud-storage, google-generativeai, python-dotenv, aiofiles

### backend/Dockerfile
基於 python:3.11-slim，安裝 poppler-utils，暴露 8080 port

### backend/api/__init__.py
空檔案

### backend/api/auth.py
POST /api/auth/verify 端點骨架

### backend/api/upload.py
POST /api/upload 端點骨架

### backend/api/process.py
POST /api/process/pptx 和 /api/process/image 端點骨架

### backend/services/__init__.py
空檔案

### backend/services/pdf_service.py
PDF 處理服務類骨架

### backend/services/gemini_service.py
Gemini API 服務類骨架

### frontend/index.html
完整的 HTML 頁面，包含：
- 密碼驗證區塊
- 功能選擇卡片（轉 PPTX、轉圖片等）
- 檔案上傳區域（支援拖放）
- 處理進度顯示
- 結果預覽區域
使用現代化 CSS，響應式設計

### README.md
專案說明文件

請直接建立這些檔案，不要問問題。完成後說「任務完成！🥇」
`;

async function main() {
  const client = new CopilotClient({
    useLoggedInUser: true,
    logLevel: 'error'
  });
  
  try {
    console.log('🚀 Starting Copilot SDK...');
    await client.start();
    
    const session = await client.createSession({
      model: 'gpt-5'  // 用更強的模型
    });
    
    console.log('📝 Sending task to Copilot...');
    
    const done = new Promise((resolve, reject) => {
      let output = '';
      
      session.on('assistant.message.delta', (event) => {
        if (event.data?.content) {
          process.stdout.write(event.data.content);
          output += event.data.content;
        }
      });
      
      session.on('tool.call', (event) => {
        console.log('\\n🔧 Tool:', event.data?.name);
      });
      
      session.on('session.idle', () => {
        console.log('\\n✅ Task completed');
        resolve(output);
      });
      
      session.on('error', (event) => {
        reject(new Error(event.data?.message || 'Unknown error'));
      });
      
      // 超時保護
      setTimeout(() => {
        reject(new Error('Timeout after 5 minutes'));
      }, 5 * 60 * 1000);
    });
    
    await session.send({ prompt: TASK });
    await done;
    
    await session.destroy();
    await client.stop();
    
    console.log('\\n🎉 Done!');
    
  } catch (error) {
    console.error('\\n❌ Error:', error.message);
    await client.stop().catch(() => {});
    process.exit(1);
  }
}

main();

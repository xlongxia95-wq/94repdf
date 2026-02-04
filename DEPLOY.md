# 94RePdf 部署指南

## 目前狀態

| 項目 | 位置 | 狀態 |
|------|------|------|
| 前端 | GitHub Pages | ✅ 永久 |
| 後端 | Cloudflare Tunnel | ⚠️ 臨時 |

## 前端（已完成）

**URL**: https://xlongxia95-wq.github.io/94repdf/

GitHub Pages 已自動部署，推送到 `main` 分支的 `/docs` 目錄會自動更新。

## 後端部署選項

### 選項 1: Google Cloud Run（推薦）

需要 Google Cloud 帳號。

```bash
# 登入
gcloud auth login

# 建立專案
gcloud projects create 94repdf --name="94RePdf"
gcloud config set project 94repdf

# 部署
cd backend
gcloud run deploy 94repdf-api \
  --source . \
  --region asia-east1 \
  --allow-unauthenticated \
  --set-env-vars "GEMINI_API_KEY=xxx,PASSWORD_HASH=xxx"
```

### 選項 2: Render.com

1. 註冊 https://render.com
2. 連結 GitHub
3. 選擇 94repdf repo
4. 設定環境變數：
   - `GEMINI_API_KEY`
   - `PASSWORD_HASH`
5. 部署

### 選項 3: Fly.io

```bash
flyctl auth login
cd backend
flyctl launch --name 94repdf-api
flyctl secrets set GEMINI_API_KEY=xxx PASSWORD_HASH=xxx
flyctl deploy
```

### 選項 4: Hugging Face Spaces

1. 建立 Space (類型: Docker)
2. 上傳 backend 目錄
3. 設定 Secrets

## 臨時方案（目前使用）

```bash
# 啟動後端
cd backend
source venv/bin/activate
uvicorn main:app --host 127.0.0.1 --port 8080

# 建立隧道
cloudflared tunnel --url http://127.0.0.1:8080
```

## 環境變數

| 變數 | 說明 |
|------|------|
| `GEMINI_API_KEY` | Gemini API 金鑰 |
| `PASSWORD_HASH` | 密碼 SHA256 雜湊（預設: password） |
| `GCS_BUCKET` | Cloud Storage 儲存桶（選用） |

## 更新前端 API 位置

部署後端後，更新 `docs/js/app.js` 中的 API_BASE：

```javascript
const API_BASE = 'https://your-backend-url.com/api';
```

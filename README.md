# 94RePdf

> **就是讓 PDF 重生**

將 NotebookLM 等 AI 生成的圖片式 PDF 轉換為可編輯的 PPTX。

## ✨ 功能

- 📊 **轉 PPTX** - PDF 轉可編輯簡報（核心功能）
- ✏️ **快速編輯** - 線上直接修改文字
- 🖼️ **轉圖片** - PDF 轉 PNG/JPG
- 🔄 **旋轉** - 調整頁面方向
- 📐 **調尺寸** - 調整頁面大小
- 🔢 **加頁碼** - 自動添加頁碼

## 🛠️ 技術棧

- **前端**: HTML/CSS/JS (Firebase Hosting)
- **後端**: Python/FastAPI (Cloud Run)
- **AI**: Gemini 3 Flash API (OCR + Inpainting)
- **儲存**: Cloud Storage

## 🚀 快速開始

### 後端

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### 前端

直接開啟 `frontend/index.html` 或部署到 Firebase Hosting。

## 📁 專案結構

```
94RePdf/
├── frontend/           # 前端
│   ├── index.html
│   ├── css/
│   └── js/
├── backend/            # 後端
│   ├── main.py
│   ├── api/
│   ├── services/
│   └── utils/
└── README.md
```

## 🔧 環境變數

```
GEMINI_API_KEY=xxx
GCS_BUCKET=94repdf-temp
PASSWORD_HASH=xxx
```

## 📝 License

MIT

---

Built with ❤️ by 小摳

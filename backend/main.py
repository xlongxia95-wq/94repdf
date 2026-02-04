"""
94RePdf - 就是讓 PDF 重生
FastAPI 後端入口
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api import auth, upload, analyze, process, download

app = FastAPI(
    title="94RePdf API",
    description="PDF 轉 PPTX、文字編輯、格式轉換",
    version="1.0.0"
)

# CORS 設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 註冊路由
app.include_router(auth.router, prefix="/api/auth", tags=["認證"])
app.include_router(upload.router, prefix="/api", tags=["上傳"])
app.include_router(analyze.router, prefix="/api", tags=["分析"])
app.include_router(process.router, prefix="/api/process", tags=["處理"])
app.include_router(download.router, prefix="/api", tags=["下載"])


@app.get("/")
async def root():
    return {"message": "94RePdf API - 就是讓 PDF 重生"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)

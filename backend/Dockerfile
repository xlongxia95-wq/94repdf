FROM python:3.11-slim

WORKDIR /app

# 安裝系統依賴 (pdf2image 需要 poppler)
RUN apt-get update && apt-get install -y \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# 複製依賴檔案
COPY requirements.txt .

# 安裝 Python 依賴
RUN pip install --no-cache-dir -r requirements.txt

# 複製程式碼
COPY . .

# 暴露 port
EXPOSE 8080

# 啟動命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]

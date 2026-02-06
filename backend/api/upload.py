"""檔案上傳 API"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
import uuid
import os
import tempfile
import logging
from pypdf import PdfReader
from PIL import Image
import io

logger = logging.getLogger(__name__)
router = APIRouter()

# 暫存目錄
UPLOAD_DIR = tempfile.gettempdir() + "/94repdf_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 檔案暫存（實際應用應使用 Redis 或資料庫）
file_storage: dict = {}


class UploadResponse(BaseModel):
    success: bool
    file_id: str
    filename: str
    size: int
    pages: int


@router.post("/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    """上傳 PDF 檔案"""
    # 檢查檔案類型
    filename_lower = file.filename.lower()
    if not filename_lower.endswith(('.pdf', '.png', '.jpg', '.jpeg')):
        raise HTTPException(status_code=400, detail="只支援 PDF、PNG、JPG 格式")
    
    # 讀取檔案
    content = await file.read()
    file_size = len(content)
    
    # 檢查檔案是否為空
    if file_size == 0:
        raise HTTPException(status_code=400, detail="檔案是空的")
    
    # 檢查檔案大小 (50MB)
    if file_size > 50 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="檔案超過 50MB 限制")
    
    # 生成檔案 ID
    file_id = str(uuid.uuid4())
    
    # 分析頁數
    pages = 1
    if filename_lower.endswith('.pdf'):
        try:
            pdf = PdfReader(io.BytesIO(content))
            # 檢查是否加密
            if pdf.is_encrypted:
                raise HTTPException(status_code=400, detail="不支援密碼保護的 PDF，請先解除密碼")
            pages = len(pdf.pages)
            if pages == 0:
                raise HTTPException(status_code=400, detail="PDF 沒有頁面")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"PDF 分析錯誤: {e}")
            raise HTTPException(status_code=400, detail=f"無法讀取 PDF: {str(e)}")
    
    # 儲存檔案到暫存目錄
    ext = os.path.splitext(file.filename)[1]
    file_path = os.path.join(UPLOAD_DIR, f"{file_id}{ext}")
    with open(file_path, 'wb') as f:
        f.write(content)
    
    # 記錄檔案資訊
    file_storage[file_id] = {
        "path": file_path,
        "filename": file.filename,
        "size": file_size,
        "pages": pages,
        "content": content  # 暫存內容以便後續處理
    }
    
    return UploadResponse(
        success=True,
        file_id=file_id,
        filename=file.filename,
        size=file_size,
        pages=pages
    )


def get_file_content(file_id: str) -> bytes:
    """取得檔案內容"""
    if file_id not in file_storage:
        return None
    return file_storage[file_id].get("content")


def get_file_info(file_id: str) -> dict:
    """取得檔案資訊"""
    return file_storage.get(file_id)

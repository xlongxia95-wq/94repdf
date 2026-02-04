"""檔案上傳 API"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
import uuid

router = APIRouter()


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
    if not file.filename.lower().endswith(('.pdf', '.png', '.jpg', '.jpeg')):
        raise HTTPException(status_code=400, detail="只支援 PDF、PNG、JPG 格式")
    
    # 讀取檔案
    content = await file.read()
    file_size = len(content)
    
    # 檢查檔案大小 (50MB)
    if file_size > 50 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="檔案超過 50MB 限制")
    
    # 生成檔案 ID
    file_id = str(uuid.uuid4())
    
    # TODO: 儲存到 Cloud Storage
    # TODO: 分析 PDF 頁數
    pages = 1  # 暫時寫死
    
    return UploadResponse(
        success=True,
        file_id=file_id,
        filename=file.filename,
        size=file_size,
        pages=pages
    )

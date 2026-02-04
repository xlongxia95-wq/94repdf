"""檔案下載 API"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

router = APIRouter()


@router.get("/download/{file_id}")
async def download_file(file_id: str):
    """下載處理完成的檔案"""
    # TODO: 從 Cloud Storage 取得檔案
    # TODO: 產生簽名 URL 或直接串流
    
    raise HTTPException(
        status_code=404, 
        detail="檔案不存在或已過期"
    )

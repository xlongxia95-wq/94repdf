"""PDF 處理 API"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional, Dict
import uuid
import asyncio
import os
import tempfile

router = APIRouter()

# 任務狀態儲存（實際應用應使用 Redis 或資料庫）
task_status: Dict[str, dict] = {}


class ProcessPptxRequest(BaseModel):
    file_id: str
    output_ratio: str = "16:9"
    remove_watermark: bool = False
    pages: Optional[List[int]] = None


class ProcessImageRequest(BaseModel):
    file_id: str
    format: str = "png"
    quality: int = 90
    pages: Optional[List[int]] = None


class ProcessResponse(BaseModel):
    success: bool
    task_id: str
    status: str


class TaskStatus(BaseModel):
    success: bool
    task_id: str
    status: str
    progress: dict
    result_url: Optional[str] = None


async def process_pdf_to_pptx(task_id: str, file_id: str, output_ratio: str, remove_watermark: bool, pages: Optional[List[int]]):
    """背景任務：處理 PDF 轉 PPTX"""
    from services.pdf_service import PdfService
    from services.gemini_service import GeminiService
    from services.pptx_service import PptxService
    from PIL import Image
    import io
    
    try:
        task_status[task_id] = {
            "status": "processing",
            "progress": {"current_page": 0, "total_pages": 0, "current_step": "init", "percent": 0}
        }
        
        # TODO: 從 Cloud Storage 讀取檔案
        # 這裡先用模擬資料測試流程
        
        # 模擬處理
        total_pages = 5  # 模擬 5 頁
        task_status[task_id]["progress"]["total_pages"] = total_pages
        
        gemini = GeminiService()
        pptx = PptxService(ratio=output_ratio)
        
        for i in range(total_pages):
            page_num = i + 1
            task_status[task_id]["progress"]["current_page"] = page_num
            task_status[task_id]["progress"]["percent"] = int((i / total_pages) * 100)
            
            # Step 1: OCR
            task_status[task_id]["progress"]["current_step"] = "ocr"
            await asyncio.sleep(0.5)  # 模擬處理時間
            
            # Step 2: Inpainting
            task_status[task_id]["progress"]["current_step"] = "inpainting"
            await asyncio.sleep(0.5)
            
            # Step 3: 組合
            task_status[task_id]["progress"]["current_step"] = "pptx"
            await asyncio.sleep(0.3)
        
        task_status[task_id]["progress"]["percent"] = 100
        task_status[task_id]["status"] = "done"
        task_status[task_id]["result_url"] = f"/api/download/{task_id}"
        
    except Exception as e:
        task_status[task_id]["status"] = "failed"
        task_status[task_id]["error"] = str(e)


@router.post("/pptx", response_model=ProcessResponse)
async def process_to_pptx(request: ProcessPptxRequest, background_tasks: BackgroundTasks):
    """將 PDF 轉換為可編輯的 PPTX"""
    task_id = str(uuid.uuid4())
    
    # 加入背景任務
    background_tasks.add_task(
        process_pdf_to_pptx,
        task_id,
        request.file_id,
        request.output_ratio,
        request.remove_watermark,
        request.pages
    )
    
    task_status[task_id] = {
        "status": "pending",
        "progress": {"current_page": 0, "total_pages": 0, "current_step": "queued", "percent": 0}
    }
    
    return ProcessResponse(
        success=True,
        task_id=task_id,
        status="processing"
    )


@router.post("/image", response_model=ProcessResponse)
async def process_to_image(request: ProcessImageRequest, background_tasks: BackgroundTasks):
    """將 PDF 轉換為圖片"""
    task_id = str(uuid.uuid4())
    
    # TODO: 實作圖片轉換
    task_status[task_id] = {
        "status": "processing",
        "progress": {"current_page": 0, "total_pages": 0, "current_step": "converting", "percent": 0}
    }
    
    return ProcessResponse(
        success=True,
        task_id=task_id,
        status="processing"
    )


@router.get("/status/{task_id}", response_model=TaskStatus)
async def get_task_status(task_id: str):
    """查詢處理狀態"""
    if task_id not in task_status:
        raise HTTPException(status_code=404, detail="Task not found")
    
    status = task_status[task_id]
    
    return TaskStatus(
        success=True,
        task_id=task_id,
        status=status.get("status", "unknown"),
        progress=status.get("progress", {}),
        result_url=status.get("result_url")
    )

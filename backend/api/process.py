"""PDF 處理 API"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
import uuid

router = APIRouter()


class ProcessPptxRequest(BaseModel):
    file_id: str
    output_ratio: str = "16:9"
    remove_watermark: bool = False
    pages: Optional[List[int]] = None


class ProcessImageRequest(BaseModel):
    file_id: str
    format: str = "png"  # png, jpg, webp
    quality: int = 90
    pages: Optional[List[int]] = None


class ProcessResponse(BaseModel):
    success: bool
    task_id: str
    status: str


class TaskStatus(BaseModel):
    success: bool
    task_id: str
    status: str  # "pending", "processing", "done", "failed"
    progress: dict
    result_url: Optional[str] = None


@router.post("/pptx", response_model=ProcessResponse)
async def process_to_pptx(request: ProcessPptxRequest, background_tasks: BackgroundTasks):
    """將 PDF 轉換為可編輯的 PPTX"""
    task_id = str(uuid.uuid4())
    
    # TODO: 加入背景任務處理
    # background_tasks.add_task(convert_to_pptx, request, task_id)
    
    return ProcessResponse(
        success=True,
        task_id=task_id,
        status="processing"
    )


@router.post("/image", response_model=ProcessResponse)
async def process_to_image(request: ProcessImageRequest, background_tasks: BackgroundTasks):
    """將 PDF 轉換為圖片"""
    task_id = str(uuid.uuid4())
    
    # TODO: 加入背景任務處理
    
    return ProcessResponse(
        success=True,
        task_id=task_id,
        status="processing"
    )


@router.get("/status/{task_id}", response_model=TaskStatus)
async def get_task_status(task_id: str):
    """查詢處理狀態"""
    # TODO: 從資料庫/快取讀取狀態
    
    return TaskStatus(
        success=True,
        task_id=task_id,
        status="processing",
        progress={
            "current_page": 4,
            "total_pages": 10,
            "current_step": "ocr",
            "percent": 40
        }
    )

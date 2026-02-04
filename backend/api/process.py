"""PDF 處理 API"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional, Dict
import uuid
import asyncio
import os
import io

router = APIRouter()

# 任務狀態儲存（實際應用應使用 Redis 或資料庫）
task_status: Dict[str, dict] = {}
task_results: Dict[str, bytes] = {}


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
    from api.upload import get_file_content, get_file_info
    from services.pdf_service import PdfService
    from services.gemini_service import GeminiService
    from services.pptx_service import PptxService
    from PIL import Image
    
    try:
        task_status[task_id] = {
            "status": "processing",
            "progress": {"current_page": 0, "total_pages": 0, "current_step": "init", "percent": 0}
        }
        
        # 取得檔案
        file_info = get_file_info(file_id)
        if not file_info:
            raise Exception("檔案不存在")
        
        content = file_info.get("content")
        if not content:
            raise Exception("檔案內容為空")
        
        # PDF 轉圖片
        task_status[task_id]["progress"]["current_step"] = "converting"
        pdf_service = PdfService()
        images = pdf_service.pdf_to_images(content)
        
        total_pages = len(images)
        task_status[task_id]["progress"]["total_pages"] = total_pages
        
        # 篩選頁面
        if pages:
            images = [images[i-1] for i in pages if 0 < i <= len(images)]
            total_pages = len(images)
        
        # 初始化服務
        gemini = GeminiService()
        pptx = PptxService(ratio=output_ratio)
        
        for i, img in enumerate(images):
            page_num = i + 1
            task_status[task_id]["progress"]["current_page"] = page_num
            task_status[task_id]["progress"]["percent"] = int((i / total_pages) * 90)
            
            # 轉換圖片為 bytes
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='PNG')
            img_bytes = img_bytes.getvalue()
            
            # Step 1: OCR
            task_status[task_id]["progress"]["current_step"] = "ocr"
            ocr_result = await gemini.ocr_image(img_bytes, img.width, img.height)
            texts = ocr_result.get("texts", [])
            
            # Step 2: Inpainting（移除文字區域）
            task_status[task_id]["progress"]["current_step"] = "inpainting"
            if texts:
                bg_bytes = await gemini.inpaint_background(img_bytes, texts)
                bg_img = Image.open(io.BytesIO(bg_bytes))
            else:
                bg_img = img
            
            # Step 3: 加入 PPTX
            task_status[task_id]["progress"]["current_step"] = "pptx"
            pptx.add_slide_with_background(bg_img, texts)
        
        # 儲存結果
        task_status[task_id]["progress"]["percent"] = 95
        task_status[task_id]["progress"]["current_step"] = "saving"
        
        pptx_bytes = pptx.save()
        task_results[task_id] = pptx_bytes
        
        task_status[task_id]["progress"]["percent"] = 100
        task_status[task_id]["status"] = "done"
        task_status[task_id]["result_url"] = f"/api/download/{task_id}"
        
    except Exception as e:
        print(f"Process error: {e}")
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


def get_task_result(task_id: str) -> bytes:
    """取得任務結果"""
    return task_results.get(task_id)

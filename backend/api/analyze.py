"""PDF 分析 API"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter()


class OriginalSize(BaseModel):
    width_mm: float
    height_mm: float
    name: str


class EstimatedCost(BaseModel):
    ocr: float
    inpainting: float
    total: float
    currency: str = "USD"


class AnalysisResult(BaseModel):
    type: str  # "native_pdf", "image_pdf", "mixed"
    pages: int
    pages_with_text: int
    pages_need_ocr: int
    original_size: OriginalSize
    orientation: str  # "portrait", "landscape"
    is_notebooklm: bool
    has_watermark: bool
    estimated_cost: EstimatedCost


class AnalyzeResponse(BaseModel):
    success: bool
    file_id: str
    analysis: AnalysisResult


@router.get("/analyze/{file_id}", response_model=AnalyzeResponse)
async def analyze_pdf(file_id: str):
    """分析 PDF 類型和費用預估"""
    # TODO: 從 Cloud Storage 讀取檔案
    # TODO: 分析 PDF 類型
    
    # 暫時返回模擬資料
    return AnalyzeResponse(
        success=True,
        file_id=file_id,
        analysis=AnalysisResult(
            type="image_pdf",
            pages=10,
            pages_with_text=0,
            pages_need_ocr=10,
            original_size=OriginalSize(
                width_mm=257,
                height_mm=364,
                name="B4"
            ),
            orientation="portrait",
            is_notebooklm=True,
            has_watermark=True,
            estimated_cost=EstimatedCost(
                ocr=0.008,
                inpainting=0.16,
                total=0.168
            )
        )
    )

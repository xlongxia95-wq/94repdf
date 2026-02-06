"""PDF 分析 API"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import io
import logging

logger = logging.getLogger(__name__)
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


def detect_paper_size(width_mm: float, height_mm: float) -> str:
    """根據尺寸偵測紙張大小"""
    # 標準紙張尺寸 (mm)
    sizes = {
        "A4": (210, 297),
        "A3": (297, 420),
        "B4": (257, 364),
        "B5": (182, 257),
        "Letter": (216, 279),
        "Legal": (216, 356),
    }
    
    # 找最接近的尺寸
    min_diff = float('inf')
    best_match = "Custom"
    
    for name, (w, h) in sizes.items():
        # 考慮直向和橫向
        diff1 = abs(width_mm - w) + abs(height_mm - h)
        diff2 = abs(width_mm - h) + abs(height_mm - w)
        diff = min(diff1, diff2)
        
        if diff < min_diff and diff < 10:  # 允許 10mm 誤差
            min_diff = diff
            best_match = name
    
    return best_match


@router.get("/analyze/{file_id}", response_model=AnalyzeResponse)
async def analyze_pdf(file_id: str):
    """分析 PDF 類型和費用預估"""
    from api.upload import get_file_info
    from pypdf import PdfReader
    from PIL import Image
    
    # 取得檔案資訊
    file_info = get_file_info(file_id)
    if not file_info:
        raise HTTPException(status_code=404, detail="檔案不存在")
    
    content = file_info.get("content")
    filename = file_info.get("filename", "").lower()
    
    # 預設值
    pages = 1
    width_mm = 210
    height_mm = 297
    pdf_type = "image_pdf"
    pages_with_text = 0
    
    try:
        if filename.endswith('.pdf'):
            # 分析 PDF
            pdf = PdfReader(io.BytesIO(content))
            pages = len(pdf.pages)
            
            # 取得第一頁尺寸
            if pages > 0:
                page = pdf.pages[0]
                # PDF 單位是 points (1 point = 1/72 inch = 0.3528 mm)
                width_pt = float(page.mediabox.width)
                height_pt = float(page.mediabox.height)
                width_mm = round(width_pt * 0.3528, 1)
                height_mm = round(height_pt * 0.3528, 1)
                
                # 檢查是否有文字
                for p in pdf.pages:
                    text = p.extract_text()
                    if text and len(text.strip()) > 10:
                        pages_with_text += 1
            
            # 判斷 PDF 類型
            if pages_with_text == pages:
                pdf_type = "native_pdf"
            elif pages_with_text == 0:
                pdf_type = "image_pdf"
            else:
                pdf_type = "mixed"
                
        elif filename.endswith(('.png', '.jpg', '.jpeg')):
            # 分析圖片
            img = Image.open(io.BytesIO(content))
            # 假設 96 DPI
            width_mm = round(img.width / 96 * 25.4, 1)
            height_mm = round(img.height / 96 * 25.4, 1)
            pdf_type = "image_pdf"
            
    except Exception as e:
        logger.error(f"分析錯誤: {e}")
    
    # 判斷方向
    orientation = "portrait" if height_mm >= width_mm else "landscape"
    
    # 偵測紙張大小
    paper_name = detect_paper_size(width_mm, height_mm)
    
    # 計算需要 OCR 的頁數
    pages_need_ocr = pages - pages_with_text
    
    # 估算費用（Gemini 2.0 Flash）
    # 每頁約 $0.0004
    ocr_cost = pages_need_ocr * 0.0004
    
    return AnalyzeResponse(
        success=True,
        file_id=file_id,
        analysis=AnalysisResult(
            type=pdf_type,
            pages=pages,
            pages_with_text=pages_with_text,
            pages_need_ocr=pages_need_ocr,
            original_size=OriginalSize(
                width_mm=width_mm,
                height_mm=height_mm,
                name=paper_name
            ),
            orientation=orientation,
            is_notebooklm=pdf_type == "image_pdf",  # 簡單判斷
            has_watermark=False,  # TODO: 實際偵測
            estimated_cost=EstimatedCost(
                ocr=round(ocr_cost, 4),
                inpainting=0,
                total=round(ocr_cost, 4)
            )
        )
    )

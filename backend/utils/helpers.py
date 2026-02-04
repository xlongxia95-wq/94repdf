"""共用工具函數"""
import hashlib
from typing import Tuple

# 標準紙張尺寸 (mm)
PAPER_SIZES = {
    "A4": (210, 297),
    "A3": (297, 420),
    "A5": (148, 210),
    "B4": (257, 364),
    "B5": (176, 250),
    "Letter": (216, 279),
}


def detect_paper_size(width_mm: float, height_mm: float) -> str:
    """偵測紙張尺寸"""
    # 確保寬度 < 高度（直向）
    if width_mm > height_mm:
        width_mm, height_mm = height_mm, width_mm
    
    best_match = "Custom"
    min_diff = float('inf')
    
    for name, (w, h) in PAPER_SIZES.items():
        diff = abs(width_mm - w) + abs(height_mm - h)
        if diff < min_diff and diff < 10:  # 容許 10mm 誤差
            min_diff = diff
            best_match = name
    
    return best_match


def detect_orientation(width: float, height: float) -> str:
    """偵測頁面方向"""
    return "landscape" if width > height else "portrait"


def hash_password(password: str) -> str:
    """計算密碼 hash"""
    return hashlib.sha256(password.encode()).hexdigest()


def estimate_cost(pages: int, need_ocr: bool = True, need_inpainting: bool = True) -> dict:
    """
    估算處理費用
    
    Gemini 3 Flash 定價：
    - Input: $0.50 / 1M tokens
    - Output: $3.00 / 1M tokens
    """
    # 估算每頁 token 用量
    tokens_per_page_ocr = 2000  # OCR input
    tokens_per_page_output = 500  # OCR output
    tokens_per_page_inpaint = 5000  # Inpainting
    
    ocr_cost = 0
    inpaint_cost = 0
    
    if need_ocr:
        input_tokens = pages * tokens_per_page_ocr
        output_tokens = pages * tokens_per_page_output
        ocr_cost = (input_tokens * 0.50 + output_tokens * 3.00) / 1_000_000
    
    if need_inpainting:
        inpaint_tokens = pages * tokens_per_page_inpaint
        inpaint_cost = inpaint_tokens * 0.50 / 1_000_000
    
    return {
        "ocr": round(ocr_cost, 4),
        "inpainting": round(inpaint_cost, 4),
        "total": round(ocr_cost + inpaint_cost, 4),
        "currency": "USD"
    }

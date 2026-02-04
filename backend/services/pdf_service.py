"""PDF 處理服務"""
from typing import List, Tuple, Optional
from pypdf import PdfReader
from pdf2image import convert_from_bytes
from PIL import Image
import io


class PdfService:
    """PDF 處理服務類"""
    
    @staticmethod
    def get_page_count(pdf_bytes: bytes) -> int:
        """取得 PDF 頁數"""
        reader = PdfReader(io.BytesIO(pdf_bytes))
        return len(reader.pages)
    
    @staticmethod
    def has_text_layer(pdf_bytes: bytes, page_num: int = 0) -> bool:
        """檢查 PDF 頁面是否有文字層"""
        reader = PdfReader(io.BytesIO(pdf_bytes))
        if page_num >= len(reader.pages):
            return False
        
        page = reader.pages[page_num]
        text = page.extract_text()
        return bool(text and text.strip())
    
    @staticmethod
    def analyze_pdf_type(pdf_bytes: bytes) -> dict:
        """
        分析 PDF 類型
        
        Returns:
            {
                "type": "native_pdf" | "image_pdf" | "mixed",
                "pages": 10,
                "pages_with_text": 6,
                "pages_need_ocr": 4
            }
        """
        reader = PdfReader(io.BytesIO(pdf_bytes))
        total_pages = len(reader.pages)
        pages_with_text = 0
        
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text and text.strip():
                pages_with_text += 1
        
        pages_need_ocr = total_pages - pages_with_text
        
        if pages_with_text == total_pages:
            pdf_type = "native_pdf"
        elif pages_with_text == 0:
            pdf_type = "image_pdf"
        else:
            pdf_type = "mixed"
        
        return {
            "type": pdf_type,
            "pages": total_pages,
            "pages_with_text": pages_with_text,
            "pages_need_ocr": pages_need_ocr
        }
    
    @staticmethod
    def pdf_to_images(pdf_bytes: bytes, dpi: int = 150) -> List[Image.Image]:
        """將 PDF 轉換為圖片列表"""
        images = convert_from_bytes(pdf_bytes, dpi=dpi)
        return images
    
    @staticmethod
    def get_page_size(pdf_bytes: bytes, page_num: int = 0) -> Tuple[float, float]:
        """取得頁面尺寸 (mm)"""
        reader = PdfReader(io.BytesIO(pdf_bytes))
        if page_num >= len(reader.pages):
            return (0, 0)
        
        page = reader.pages[page_num]
        # PDF 單位是 point (1 point = 1/72 inch)
        width_pt = float(page.mediabox.width)
        height_pt = float(page.mediabox.height)
        
        # 轉換為 mm (1 inch = 25.4 mm)
        width_mm = width_pt / 72 * 25.4
        height_mm = height_pt / 72 * 25.4
        
        return (width_mm, height_mm)

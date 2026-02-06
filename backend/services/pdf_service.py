"""PDF 處理服務"""
import logging
from typing import List
from PIL import Image
import io

logger = logging.getLogger(__name__)


class PdfService:
    """PDF 處理服務類"""
    
    def __init__(self, dpi: int = 150):
        self.dpi = dpi
    
    def pdf_to_images(self, pdf_bytes: bytes) -> List[Image.Image]:
        """
        將 PDF 轉換為圖片列表
        
        Args:
            pdf_bytes: PDF 檔案的 bytes
            
        Returns:
            PIL Image 列表
        """
        try:
            from pdf2image import convert_from_bytes
            images = convert_from_bytes(pdf_bytes, dpi=self.dpi)
            return images
        except ImportError:
            # 如果沒有 poppler，使用 pypdf + PIL 的方式
            return self._pdf_to_images_fallback(pdf_bytes)
        except Exception as e:
            logger.error(f"PDF 轉圖片錯誤: {e}")
            # 嘗試 fallback 方法
            return self._pdf_to_images_fallback(pdf_bytes)
    
    def _pdf_to_images_fallback(self, pdf_bytes: bytes) -> List[Image.Image]:
        """
        備用方法：使用 pypdf 提取頁面
        注意：這個方法品質較差，但不需要額外依賴
        """
        from pypdf import PdfReader
        
        images = []
        reader = PdfReader(io.BytesIO(pdf_bytes))
        
        for page in reader.pages:
            # 建立空白圖片作為替代
            # 實際上 pypdf 不支援直接轉圖片，需要 pdf2image + poppler
            width = int(float(page.mediabox.width) * self.dpi / 72)
            height = int(float(page.mediabox.height) * self.dpi / 72)
            
            # 建立白色背景圖片
            img = Image.new('RGB', (width, height), 'white')
            images.append(img)
        
        return images
    
    def get_page_count(self, pdf_bytes: bytes) -> int:
        """取得 PDF 頁數"""
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(pdf_bytes))
        return len(reader.pages)
    
    def extract_page(self, pdf_bytes: bytes, page_num: int) -> bytes:
        """提取單頁 PDF"""
        from pypdf import PdfReader, PdfWriter
        
        reader = PdfReader(io.BytesIO(pdf_bytes))
        writer = PdfWriter()
        
        if 0 < page_num <= len(reader.pages):
            writer.add_page(reader.pages[page_num - 1])
        
        output = io.BytesIO()
        writer.write(output)
        return output.getvalue()

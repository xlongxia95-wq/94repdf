"""Gemini API 服務 - OCR 和 Inpainting"""
import os
from typing import List, Dict
import google.generativeai as genai

# 設定 API Key
genai.configure(api_key=os.getenv("GEMINI_API_KEY", ""))


class GeminiService:
    """Gemini API 服務類"""
    
    def __init__(self, model_name: str = "gemini-3-flash"):
        self.model = genai.GenerativeModel(model_name)
    
    async def ocr_image(self, image_bytes: bytes, width: int, height: int) -> Dict:
        """
        OCR 辨識圖片中的文字
        
        Returns:
            {
                "texts": [
                    {
                        "content": "文字內容",
                        "x": 100, "y": 50,
                        "width": 400, "height": 60,
                        "font_size": 36,
                        "font_weight": "bold",
                        "color": "#333333",
                        "confidence": 0.98
                    }
                ]
            }
        """
        prompt = f"""分析這張投影片圖片，請：

1. 辨識所有文字，輸出每個文字區塊的：
   - content: 文字內容
   - x, y: 左上角座標（像素）
   - width, height: 區塊尺寸（像素）
   - font_size: 字體大小（估計）
   - font_weight: "bold" 或 "normal"
   - color: 顏色（hex 格式）
   - confidence: 辨識信心度（0-1）

2. 輸出 JSON 格式，確保位置精確

圖片尺寸：{width} x {height} 像素
"""
        # TODO: 實作實際的 API 呼叫
        return {"texts": []}
    
    async def inpaint_background(self, image_bytes: bytes, text_regions: List[Dict]) -> bytes:
        """
        使用 Inpainting 移除文字區域，重建背景
        
        Args:
            image_bytes: 原始圖片
            text_regions: 需要移除的文字區域座標
            
        Returns:
            重建後的背景圖片 bytes
        """
        # TODO: 實作 Gemini Inpainting
        return image_bytes

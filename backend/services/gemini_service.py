"""Gemini API 服務 - OCR 和 Inpainting"""
import os
import json
import base64
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()

import google.generativeai as genai

# 設定 API Key
genai.configure(api_key=os.getenv("GEMINI_API_KEY", ""))


class GeminiService:
    """Gemini API 服務類"""
    
    def __init__(self, model_name: str = "gemini-2.0-flash"):
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
   - font_size: 字體大小（估計值）
   - font_weight: "bold" 或 "normal"
   - color: 顏色（hex 格式，如 #333333）
   - confidence: 辨識信心度（0-1）

2. 只輸出 JSON 格式，不要其他文字
3. 確保座標位置精確

圖片尺寸：{width} x {height} 像素

輸出格式：
{{"texts": [...]}}
"""
        
        # 將圖片轉為 base64
        image_data = base64.b64encode(image_bytes).decode('utf-8')
        
        # 建立圖片 part
        image_part = {
            "mime_type": "image/png",
            "data": image_data
        }
        
        try:
            response = self.model.generate_content([prompt, image_part])
            result_text = response.text.strip()
            
            # 解析 JSON（處理 markdown code block）
            if result_text.startswith("```"):
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]
            result_text = result_text.strip()
            
            return json.loads(result_text)
        except Exception as e:
            print(f"OCR Error: {e}")
            return {"texts": [], "error": str(e)}
    
    async def inpaint_background(self, image_bytes: bytes, text_regions: List[Dict]) -> bytes:
        """
        使用 Gemini 描述背景，然後用簡單方法填補
        （真正的 inpainting 需要用 Imagen 或其他圖像生成 API）
        
        這裡用簡化方案：分析背景顏色，用純色填補文字區域
        """
        from PIL import Image
        import io
        
        # 開啟圖片
        img = Image.open(io.BytesIO(image_bytes))
        
        # 對每個文字區域進行填補
        for region in text_regions:
            x = int(region.get('x', 0))
            y = int(region.get('y', 0))
            w = int(region.get('width', 0))
            h = int(region.get('height', 0))
            
            if w <= 0 or h <= 0:
                continue
            
            # 取樣周圍像素來估計背景色
            bg_color = self._sample_background_color(img, x, y, w, h)
            
            # 用背景色填補
            for px in range(max(0, x), min(img.width, x + w)):
                for py in range(max(0, y), min(img.height, y + h)):
                    img.putpixel((px, py), bg_color)
        
        # 轉回 bytes
        output = io.BytesIO()
        img.save(output, format='PNG')
        return output.getvalue()
    
    def _sample_background_color(self, img, x: int, y: int, w: int, h: int) -> tuple:
        """從區域周圍取樣背景顏色"""
        samples = []
        
        # 取樣區域上方
        if y > 5:
            for px in range(max(0, x), min(img.width, x + w), 10):
                samples.append(img.getpixel((px, y - 5)))
        
        # 取樣區域下方
        if y + h + 5 < img.height:
            for px in range(max(0, x), min(img.width, x + w), 10):
                samples.append(img.getpixel((px, y + h + 5)))
        
        # 取樣區域左側
        if x > 5:
            for py in range(max(0, y), min(img.height, y + h), 10):
                samples.append(img.getpixel((x - 5, py)))
        
        # 取樣區域右側
        if x + w + 5 < img.width:
            for py in range(max(0, y), min(img.height, y + h), 10):
                samples.append(img.getpixel((x + w + 5, py)))
        
        if not samples:
            return (255, 255, 255)  # 預設白色
        
        # 計算平均顏色
        if isinstance(samples[0], tuple):
            r = sum(s[0] for s in samples) // len(samples)
            g = sum(s[1] for s in samples) // len(samples)
            b = sum(s[2] for s in samples) // len(samples)
            return (r, g, b)
        else:
            return (255, 255, 255)
    
    async def analyze_slide(self, image_bytes: bytes) -> Dict:
        """
        分析投影片，判斷是否為 NotebookLM 生成、是否有浮水印等
        """
        prompt = """分析這張投影片圖片，請判斷：

1. is_notebooklm: 是否像是 NotebookLM/Nano Banana Pro 生成的（布局、風格判斷）
2. has_watermark: 是否有右下角的星星浮水印
3. background_type: 背景類型（"solid", "gradient", "image", "pattern"）
4. dominant_colors: 主要顏色（hex 格式，最多 3 個）
5. layout_type: 版面類型（"title", "content", "two_column", "image_heavy"）

只輸出 JSON 格式：
{"is_notebooklm": true/false, "has_watermark": true/false, "background_type": "...", "dominant_colors": [...], "layout_type": "..."}
"""
        
        image_data = base64.b64encode(image_bytes).decode('utf-8')
        image_part = {
            "mime_type": "image/png",
            "data": image_data
        }
        
        try:
            response = self.model.generate_content([prompt, image_part])
            result_text = response.text.strip()
            
            if result_text.startswith("```"):
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]
            result_text = result_text.strip()
            
            return json.loads(result_text)
        except Exception as e:
            print(f"Analyze Error: {e}")
            return {
                "is_notebooklm": False,
                "has_watermark": False,
                "background_type": "unknown",
                "dominant_colors": [],
                "layout_type": "unknown",
                "error": str(e)
            }


# 測試函數
async def test_gemini():
    """測試 Gemini API 連接"""
    service = GeminiService()
    model = genai.GenerativeModel("gemini-2.0-flash")
    response = model.generate_content("Say 'Hello, 94RePdf!' in one line.")
    return response.text


if __name__ == "__main__":
    import asyncio
    result = asyncio.run(test_gemini())
    print(f"Test result: {result}")

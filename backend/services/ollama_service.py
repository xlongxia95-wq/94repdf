"""Ollama 本地視覺模型服務 - OCR"""
import json
import base64
import httpx
import logging
from typing import Dict, List
from PIL import Image
import io

logger = logging.getLogger(__name__)


class OllamaService:
    """Ollama 本地視覺模型服務"""
    
    def __init__(
        self, 
        model_name: str = "qwen3-vl:8b",
        base_url: str = "http://localhost:11434"
    ):
        self.model = model_name
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=120.0)  # 本地模型可能較慢
    
    async def ocr_image(self, image_bytes: bytes, width: int, height: int) -> Dict:
        """
        使用本地視覺模型 OCR 辨識圖片中的文字
        
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
                        "confidence": 0.95
                    }
                ]
            }
        """
        prompt = f"""分析這張投影片圖片，辨識所有文字。

對每個文字區塊，輸出：
- content: 文字內容
- x, y: 左上角座標（像素，圖片尺寸 {width}x{height}）
- width, height: 區塊尺寸（像素）
- font_size: 字體大小估計
- font_weight: "bold" 或 "normal"
- color: 顏色 hex 格式

只輸出 JSON，格式：{{"texts": [...]}}

/no_think"""
        
        # Base64 編碼圖片
        image_b64 = base64.b64encode(image_bytes).decode('utf-8')
        
        try:
            response = await self.client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "images": [image_b64],
                    "stream": False,
                    "options": {
                        "temperature": 0.1,  # 低溫度，更精確
                        "num_predict": 4096
                    }
                }
            )
            response.raise_for_status()
            
            result = response.json()
            result_text = result.get("response", "").strip()
            
            # 解析 JSON（處理 markdown code block）
            if "```" in result_text:
                # 找到 JSON 部分
                parts = result_text.split("```")
                for part in parts:
                    part = part.strip()
                    if part.startswith("json"):
                        part = part[4:].strip()
                    if part.startswith("{"):
                        result_text = part
                        break
            
            # 找到 JSON 開始位置
            json_start = result_text.find("{")
            json_end = result_text.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                result_text = result_text[json_start:json_end]
            
            return json.loads(result_text)
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON Parse Error: {e}")
            logger.debug(f"Raw response: {result_text[:500]}")
            return {"texts": [], "error": f"JSON parse error: {str(e)}"}
        except Exception as e:
            logger.error(f"Ollama OCR Error: {e}")
            return {"texts": [], "error": str(e)}
    
    async def analyze_slide(self, image_bytes: bytes) -> Dict:
        """分析投影片特徵"""
        prompt = """分析這張投影片：

1. is_notebooklm: 是否像 NotebookLM 生成的
2. has_watermark: 是否有浮水印
3. background_type: 背景類型 (solid/gradient/image/pattern)
4. dominant_colors: 主要顏色 (hex 格式，最多3個)
5. layout_type: 版面類型 (title/content/two_column/image_heavy)

只輸出 JSON：{"is_notebooklm": bool, "has_watermark": bool, "background_type": "...", "dominant_colors": [...], "layout_type": "..."}

/no_think"""
        
        image_b64 = base64.b64encode(image_bytes).decode('utf-8')
        
        try:
            response = await self.client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "images": [image_b64],
                    "stream": False,
                    "options": {"temperature": 0.1}
                }
            )
            response.raise_for_status()
            
            result = response.json()
            result_text = result.get("response", "").strip()
            
            # 解析 JSON
            json_start = result_text.find("{")
            json_end = result_text.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                result_text = result_text[json_start:json_end]
            
            return json.loads(result_text)
            
        except Exception as e:
            logger.error(f"Analyze Error: {e}")
            return {
                "is_notebooklm": False,
                "has_watermark": False,
                "background_type": "unknown",
                "dominant_colors": [],
                "layout_type": "unknown",
                "error": str(e)
            }
    
    async def inpaint_background(self, image_bytes: bytes, text_regions: List[Dict]) -> bytes:
        """用背景色填補文字區域（同 GeminiService）"""
        img = Image.open(io.BytesIO(image_bytes))
        
        for region in text_regions:
            x = int(region.get('x', 0))
            y = int(region.get('y', 0))
            w = int(region.get('width', 0))
            h = int(region.get('height', 0))
            
            if w <= 0 or h <= 0:
                continue
            
            bg_color = self._sample_background_color(img, x, y, w, h)
            
            for px in range(max(0, x), min(img.width, x + w)):
                for py in range(max(0, y), min(img.height, y + h)):
                    img.putpixel((px, py), bg_color)
        
        output = io.BytesIO()
        img.save(output, format='PNG')
        return output.getvalue()
    
    def _sample_background_color(self, img, x: int, y: int, w: int, h: int) -> tuple:
        """從區域周圍取樣背景顏色"""
        samples = []
        
        if y > 5:
            for px in range(max(0, x), min(img.width, x + w), 10):
                samples.append(img.getpixel((px, y - 5)))
        if y + h + 5 < img.height:
            for px in range(max(0, x), min(img.width, x + w), 10):
                samples.append(img.getpixel((px, y + h + 5)))
        if x > 5:
            for py in range(max(0, y), min(img.height, y + h), 10):
                samples.append(img.getpixel((x - 5, py)))
        if x + w + 5 < img.width:
            for py in range(max(0, y), min(img.height, y + h), 10):
                samples.append(img.getpixel((x + w + 5, py)))
        
        if not samples:
            return (255, 255, 255)
        
        if isinstance(samples[0], tuple):
            r = sum(s[0] for s in samples) // len(samples)
            g = sum(s[1] for s in samples) // len(samples)
            b = sum(s[2] for s in samples) // len(samples)
            return (r, g, b)
        return (255, 255, 255)
    
    async def close(self):
        """關閉 HTTP 客戶端"""
        await self.client.aclose()


async def test_ollama():
    """測試 Ollama 連接"""
    service = OllamaService()
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:11434/api/tags")
            models = response.json().get("models", [])
            logger.info(f"Available models: {[m['name'] for m in models]}")
            return True
    except Exception as e:
        logger.error(f"Ollama test failed: {e}")
        return False


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_ollama())

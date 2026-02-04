"""端對端測試"""
import asyncio
import sys
sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv()


async def test_gemini_ocr():
    """測試 Gemini OCR"""
    from services.gemini_service import GeminiService
    from PIL import Image
    import io
    
    print("🧪 測試 Gemini OCR...")
    
    # 建立測試圖片（簡單的白底黑字）
    img = Image.new('RGB', (800, 600), color='white')
    from PIL import ImageDraw, ImageFont
    draw = ImageDraw.Draw(img)
    
    # 畫一些文字
    draw.text((100, 50), "94RePdf 測試", fill='black')
    draw.text((100, 150), "這是一個測試投影片", fill='gray')
    draw.text((100, 250), "Hello World!", fill='blue')
    
    # 轉成 bytes
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes = img_bytes.getvalue()
    
    # 測試 OCR
    service = GeminiService()
    result = await service.ocr_image(img_bytes, 800, 600)
    
    print(f"📝 OCR 結果: {result}")
    
    if result.get('texts'):
        print(f"✅ 辨識到 {len(result['texts'])} 個文字區塊")
        for text in result['texts'][:3]:
            print(f"   - {text.get('content', 'N/A')}")
    else:
        print("⚠️ 沒有辨識到文字（可能是圖片太簡單）")
    
    return result


async def test_pptx_generation():
    """測試 PPTX 生成"""
    from services.pptx_service import PptxService
    from PIL import Image
    
    print("\n🧪 測試 PPTX 生成...")
    
    # 建立測試背景圖
    bg = Image.new('RGB', (1920, 1080), color='#4F46E5')
    
    # 測試文字資料
    texts = [
        {"content": "94RePdf", "x": 100, "y": 100, "width": 400, "height": 80, "font_size": 48, "font_weight": "bold", "color": "#FFFFFF"},
        {"content": "就是讓 PDF 重生", "x": 100, "y": 200, "width": 500, "height": 40, "font_size": 24, "color": "#E5E7EB"},
    ]
    
    # 生成 PPTX
    pptx = PptxService(ratio="16:9")
    pptx.add_slide_with_background(bg, texts)
    pptx_bytes = pptx.save()
    
    # 儲存測試檔案
    with open('/tmp/test_94repdf.pptx', 'wb') as f:
        f.write(pptx_bytes)
    
    print(f"✅ PPTX 生成成功！檔案大小: {len(pptx_bytes)} bytes")
    print(f"📁 儲存至: /tmp/test_94repdf.pptx")
    
    return pptx_bytes


async def test_api():
    """測試 API 端點"""
    from fastapi.testclient import TestClient
    from main import app
    
    print("\n🧪 測試 API...")
    
    client = TestClient(app)
    
    # 測試首頁
    response = client.get("/")
    print(f"GET / : {response.status_code} - {response.json()}")
    
    # 測試健康檢查
    response = client.get("/health")
    print(f"GET /health : {response.status_code} - {response.json()}")
    
    # 測試分析 API
    response = client.get("/api/analyze/test-file-id")
    print(f"GET /api/analyze : {response.status_code}")
    
    # 測試處理 API
    response = client.post("/api/process/pptx", json={
        "file_id": "test-file-id",
        "output_ratio": "16:9",
        "remove_watermark": False
    })
    print(f"POST /api/process/pptx : {response.status_code} - {response.json()}")
    
    if response.status_code == 200:
        task_id = response.json()["task_id"]
        
        # 等待處理
        await asyncio.sleep(3)
        
        # 查詢狀態
        response = client.get(f"/api/process/status/{task_id}")
        print(f"GET /api/process/status : {response.status_code} - {response.json()}")
    
    print("✅ API 測試完成")


async def main():
    print("=" * 50)
    print("94RePdf 端對端測試")
    print("=" * 50)
    
    # 測試 Gemini OCR
    await test_gemini_ocr()
    
    # 測試 PPTX 生成
    await test_pptx_generation()
    
    # 測試 API
    await test_api()
    
    print("\n" + "=" * 50)
    print("✅ 所有測試完成！")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())

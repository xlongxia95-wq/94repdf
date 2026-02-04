"""PPTX 生成服務"""
from typing import List, Dict
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from PIL import Image
import io


class PptxService:
    """PPTX 生成服務類"""
    
    def __init__(self, ratio: str = "16:9"):
        """
        初始化簡報
        
        Args:
            ratio: 投影片比例 ("16:9" 或 "4:3")
        """
        self.prs = Presentation()
        
        # 設定投影片尺寸
        if ratio == "16:9":
            self.prs.slide_width = Inches(13.333)
            self.prs.slide_height = Inches(7.5)
        else:  # 4:3
            self.prs.slide_width = Inches(10)
            self.prs.slide_height = Inches(7.5)
    
    def add_slide_with_background(self, background_image: Image.Image, texts: List[Dict]) -> None:
        """
        新增一張投影片，包含背景圖和文字
        
        Args:
            background_image: 背景圖片
            texts: 文字資料列表 [{content, x, y, width, height, font_size, color, ...}]
        """
        # 使用空白版面
        blank_layout = self.prs.slide_layouts[6]
        slide = self.prs.slides.add_slide(blank_layout)
        
        # 儲存背景圖到 bytes
        img_bytes = io.BytesIO()
        background_image.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        # 添加背景圖（填滿整個投影片）
        slide.shapes.add_picture(
            img_bytes,
            Emu(0), Emu(0),
            self.prs.slide_width, self.prs.slide_height
        )
        
        # 計算縮放比例
        scale_x = self.prs.slide_width / Emu(background_image.width * 914400 / 96)
        scale_y = self.prs.slide_height / Emu(background_image.height * 914400 / 96)
        
        # 添加文字框
        for text_data in texts:
            self._add_text_box(slide, text_data, scale_x, scale_y)
    
    def _add_text_box(self, slide, text_data: Dict, scale_x: float, scale_y: float) -> None:
        """添加文字框到投影片"""
        # 計算位置（從像素轉換為 EMU）
        px_to_emu = 914400 / 96  # 96 DPI
        
        left = Emu(int(text_data['x'] * px_to_emu * scale_x))
        top = Emu(int(text_data['y'] * px_to_emu * scale_y))
        width = Emu(int(text_data['width'] * px_to_emu * scale_x))
        height = Emu(int(text_data['height'] * px_to_emu * scale_y))
        
        # 添加文字框
        textbox = slide.shapes.add_textbox(left, top, width, height)
        tf = textbox.text_frame
        tf.word_wrap = True
        
        p = tf.paragraphs[0]
        p.text = text_data['content']
        
        # 設定字體大小
        if 'font_size' in text_data:
            p.font.size = Pt(text_data['font_size'])
        
        # 設定粗體
        if text_data.get('font_weight') == 'bold':
            p.font.bold = True
        
        # 設定顏色
        if 'color' in text_data:
            hex_color = text_data['color'].lstrip('#')
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            p.font.color.rgb = RGBColor(r, g, b)
    
    def save(self) -> bytes:
        """儲存並返回 PPTX bytes"""
        output = io.BytesIO()
        self.prs.save(output)
        output.seek(0)
        return output.read()

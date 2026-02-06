# 94RePdf Code Review Report

**日期**: 2026-02-06
**審核者**: 小摳

---

## 📊 總體評估

| 項目 | 評分 | 說明 |
|------|------|------|
| 功能完整性 | ⭐⭐⭐ | 核心功能可用 |
| 代碼品質 | ⭐⭐ | 需要重構 |
| 安全性 | ⭐⭐⭐ | 基本安全措施有 |
| 效能 | ⭐⭐ | 有記憶體洩漏風險 |
| 可維護性 | ⭐⭐ | 結構清晰但需改進 |

---

## 🐛 發現的問題

### 🔴 嚴重問題

#### 1. 記憶體洩漏 - `process.py`
```python
# task_status 和 task_results 會無限增長
task_status: Dict[str, dict] = {}
task_results: Dict[str, bytes] = {}
```
**風險**: 長時間運行後記憶體爆炸
**建議**: 加入 TTL 自動清理機制

#### 2. 無日誌系統
```python
print(f"Process error: {e}")  # 散落各處的 print
```
**風險**: 生產環境難以追蹤問題
**建議**: 使用 Python logging 模組

---

### 🟡 中等問題

#### 3. 缺少輸入驗證
- 檔案大小限制只在後端，前端可繞過
- 沒有檔案類型的深度檢查（只看副檔名）

#### 4. 硬編碼配置
```python
model_name: str = "gemini-2.0-flash"  # 應該用環境變數
self.client = httpx.AsyncClient(timeout=120.0)  # 魔術數字
```

#### 5. 缺少重試機制
- Gemini API 失敗沒有重試
- Ollama 連線失敗沒有重試

#### 6. 未完成的功能
```python
@router.post("/image", response_model=ProcessResponse)
async def process_to_image(...):
    # TODO: 實作圖片轉換
```

---

### 🟢 輕微問題

#### 7. 代碼重複
- `gemini_service.py` 和 `ollama_service.py` 有相似的 OCR 邏輯
- 可以抽取共同介面

#### 8. 缺少類型提示
```python
def _sample_background_color(self, img, x: int, y: int, w: int, h: int) -> tuple:
    # img 沒有類型提示
```

#### 9. 前端魔術字串
```javascript
const API_BASE = window.location.hostname === 'localhost' || ...
```

---

## ✅ 做得好的地方

1. **API 結構清晰** - RESTful 設計
2. **錯誤處理** - 基本的 try-catch 覆蓋
3. **XSS 防護** - `escapeHtml()` 函數
4. **CORS 設定** - 正確配置
5. **密碼 Hash** - 使用 SHA256
6. **背景任務** - 使用 FastAPI BackgroundTasks

---

## 🔧 重構建議

### 優先級 1 (立即修復)
- [ ] 加入任務清理機制
- [ ] 改用 logging 模組

### 優先級 2 (本週完成)
- [ ] 抽取 OCR 服務介面
- [ ] 加入 API 重試機制
- [ ] 配置外部化

### 優先級 3 (後續迭代)
- [ ] 完成 `/image` 端點
- [ ] 加入單元測試
- [ ] 加入 API 文檔

---

## 📝 重構計畫

見下方實作...

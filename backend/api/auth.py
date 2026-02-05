"""密碼驗證 API"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import hashlib
import os

router = APIRouter()

# 從環境變數讀取密碼 hash
# 預設值為 "password" 的 SHA256（開發用）
DEFAULT_HASH = "5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8"
PASSWORD_HASH = os.getenv("PASSWORD_HASH", DEFAULT_HASH)


class VerifyRequest(BaseModel):
    password: str


class VerifyResponse(BaseModel):
    success: bool
    message: str


@router.post("/verify", response_model=VerifyResponse)
async def verify_password(request: VerifyRequest):
    """驗證密碼"""
    # 計算輸入密碼的 hash
    input_hash = hashlib.sha256(request.password.encode()).hexdigest()
    
    if input_hash == PASSWORD_HASH:
        return VerifyResponse(success=True, message="驗證成功")
    else:
        raise HTTPException(status_code=401, detail="密碼錯誤")

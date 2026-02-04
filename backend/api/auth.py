"""密碼驗證 API"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import hashlib
import os

router = APIRouter()

# 從環境變數讀取密碼 hash
PASSWORD_HASH = os.getenv("PASSWORD_HASH", "")


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

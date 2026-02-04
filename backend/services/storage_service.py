"""Cloud Storage 服務"""
import os
from typing import Optional
from google.cloud import storage

BUCKET_NAME = os.getenv("GCS_BUCKET", "94repdf-temp")


class StorageService:
    """Google Cloud Storage 服務類"""
    
    def __init__(self):
        self.client = storage.Client()
        self.bucket = self.client.bucket(BUCKET_NAME)
    
    def upload_file(self, file_id: str, content: bytes, content_type: str = "application/pdf") -> str:
        """
        上傳檔案到 Cloud Storage
        
        Returns:
            檔案的 GCS URI
        """
        blob = self.bucket.blob(f"uploads/{file_id}")
        blob.upload_from_string(content, content_type=content_type)
        return f"gs://{BUCKET_NAME}/uploads/{file_id}"
    
    def download_file(self, file_id: str) -> Optional[bytes]:
        """下載檔案"""
        blob = self.bucket.blob(f"uploads/{file_id}")
        if not blob.exists():
            return None
        return blob.download_as_bytes()
    
    def upload_result(self, file_id: str, content: bytes, content_type: str) -> str:
        """上傳處理結果"""
        blob = self.bucket.blob(f"results/{file_id}")
        blob.upload_from_string(content, content_type=content_type)
        return f"gs://{BUCKET_NAME}/results/{file_id}"
    
    def get_signed_url(self, file_id: str, expiration: int = 3600) -> str:
        """
        產生簽名 URL 供下載
        
        Args:
            file_id: 檔案 ID
            expiration: URL 有效期（秒）
        """
        blob = self.bucket.blob(f"results/{file_id}")
        url = blob.generate_signed_url(
            version="v4",
            expiration=expiration,
            method="GET"
        )
        return url
    
    def delete_file(self, file_id: str, folder: str = "uploads") -> bool:
        """刪除檔案"""
        blob = self.bucket.blob(f"{folder}/{file_id}")
        if blob.exists():
            blob.delete()
            return True
        return False

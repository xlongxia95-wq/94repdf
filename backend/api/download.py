"""下載 API"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

router = APIRouter()


@router.get("/download/{task_id}")
async def download_result(task_id: str):
    """下載處理結果"""
    from api.process import get_task_result, task_status
    
    # 檢查任務狀態
    if task_id not in task_status:
        raise HTTPException(status_code=404, detail="任務不存在")
    
    status = task_status[task_id]
    if status.get("status") != "done":
        raise HTTPException(status_code=400, detail="任務尚未完成")
    
    # 取得結果
    result = get_task_result(task_id)
    if not result:
        raise HTTPException(status_code=404, detail="結果不存在")
    
    # 返回 PPTX 檔案
    return Response(
        content=result,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers={
            "Content-Disposition": f"attachment; filename=94repdf_{task_id[:8]}.pptx"
        }
    )

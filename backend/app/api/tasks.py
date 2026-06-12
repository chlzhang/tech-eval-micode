"""
任务 API
"""

import os
import shutil
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File as FastAPIFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from ..core.database import get_db
from ..core.security import get_current_user
from ..core.config import settings
from ..models.user import User
from ..models.task import Task
from ..models.file import File
from ..schemas.task import TaskCreate, TaskResponse, TaskListResponse

router = APIRouter(prefix="/tasks", tags=["任务"])


@router.post("", response_model=TaskResponse)
async def create_task(
    request: TaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建评估任务"""
    task = Task(
        user_id=current_user.id,
        title=request.title,
        description=request.description,
        version=request.version,
        status="pending"
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    
    return _task_to_response(task)


@router.get("", response_model=TaskListResponse)
async def list_tasks(
    status: str = None,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取任务列表"""
    query = select(Task).where(Task.user_id == current_user.id)
    
    if status:
        query = query.where(Task.status == status)
    
    # 计算总数
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)
    
    # 分页查询
    query = query.order_by(Task.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    tasks = result.scalars().all()
    
    return TaskListResponse(
        total=total,
        items=[_task_to_response(t) for t in tasks]
    )


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取任务详情"""
    task = await _get_user_task(db, task_id, current_user.id)
    return _task_to_response(task)


@router.delete("/{task_id}")
async def delete_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除任务"""
    task = await _get_user_task(db, task_id, current_user.id)
    
    # 删除关联文件
    task_dir = Path(settings.UPLOAD_DIR) / str(task_id)
    if task_dir.exists():
        shutil.rmtree(task_dir)
    
    output_dir = Path(settings.OUTPUT_DIR) / str(task_id)
    if output_dir.exists():
        shutil.rmtree(output_dir)
    
    await db.delete(task)
    await db.commit()
    
    return {"message": "任务已删除"}


@router.post("/{task_id}/upload")
async def upload_file(
    task_id: int,
    file: UploadFile = FastAPIFile(...),
    file_type: str = "transcript",  # transcript, counterpart, benchmark
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """上传文件"""
    task = await _get_user_task(db, task_id, current_user.id)
    
    # 检查文件大小
    file_content = await file.read()
    if len(file_content) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="文件大小超过限制"
        )
    
    # 创建任务目录
    task_dir = Path(settings.UPLOAD_DIR) / str(task_id)
    task_dir.mkdir(parents=True, exist_ok=True)
    
    # 根据文件类型确定子目录
    type_dirs = {
        "transcript": "",
        "counterpart": "counterpart",
        "benchmark": "benchmark"
    }
    sub_dir = type_dirs.get(file_type, "")
    if sub_dir:
        (task_dir / sub_dir).mkdir(exist_ok=True)
    
    # 保存文件
    file_path = task_dir / sub_dir / file.filename
    with open(file_path, "wb") as f:
        f.write(file_content)
    
    # 记录文件信息
    db_file = File(
        task_id=task_id,
        filename=file.filename,
        file_path=str(file_path),
        file_size=len(file_content),
        file_type=file_type
    )
    db.add(db_file)
    await db.commit()
    
    return {"message": "文件上传成功", "file_id": db_file.id}


@router.post("/{task_id}/start")
async def start_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """启动任务"""
    task = await _get_user_task(db, task_id, current_user.id)
    
    if task.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"任务状态为 {task.status}，无法启动"
        )
    
    # 检查是否有转写文本
    transcript_dir = Path(settings.UPLOAD_DIR) / str(task_id)
    transcript_file = transcript_dir / "transcript.md"
    
    if not transcript_file.exists():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请先上传会议转写文本"
        )
    
    task.status = "running"
    task.started_at = datetime.utcnow()
    await db.commit()
    
    # TODO: 启动后台任务执行评估
    
    return {"message": "任务已启动"}


@router.get("/{task_id}/progress")
async def get_task_progress(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取任务进度"""
    task = await _get_user_task(db, task_id, current_user.id)
    
    return {
        "status": task.status,
        "progress": task.progress,
        "error_message": task.error_message
    }


async def _get_user_task(db: AsyncSession, task_id: int, user_id: int) -> Task:
    """获取用户的任务"""
    result = await db.execute(
        select(Task).where(Task.id == task_id, Task.user_id == user_id)
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    return task


def _task_to_response(task: Task) -> TaskResponse:
    """转换为响应格式"""
    return TaskResponse(
        id=task.id,
        title=task.title,
        description=task.description,
        status=task.status,
        version=task.version,
        progress=task.progress,
        error_message=task.error_message,
        created_at=task.created_at,
        started_at=task.started_at,
        completed_at=task.completed_at,
        file_count=len(task.files) if task.files else 0,
        has_report=len(task.reports) > 0 if task.reports else False
    )

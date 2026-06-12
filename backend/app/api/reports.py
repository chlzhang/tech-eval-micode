"""
报告 API
"""

import json
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse, HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..core.database import get_db
from ..core.security import get_current_user
from ..core.config import settings
from ..models.user import User
from ..models.task import Task
from ..models.report import Report
from ..schemas.report import ReportResponse, ReportDetailResponse

router = APIRouter(prefix="/reports", tags=["报告"])


@router.get("", response_model=list[ReportResponse])
async def list_reports(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取报告列表"""
    result = await db.execute(
        select(Report)
        .join(Task)
        .where(Task.user_id == current_user.id)
        .order_by(Report.created_at.desc())
    )
    reports = result.scalars().all()
    return reports


@router.get("/{report_id}", response_model=ReportDetailResponse)
async def get_report(
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取报告详情"""
    report = await _get_user_report(db, report_id, current_user.id)
    
    # 读取 HTML 内容
    html_content = None
    if report.html_path and Path(report.html_path).exists():
        html_content = Path(report.html_path).read_text(encoding="utf-8")
    
    # 读取图表数据
    chart_data = None
    if report.data_path and Path(report.data_path).exists():
        chart_data = json.loads(Path(report.data_path).read_text(encoding="utf-8"))
    
    return ReportDetailResponse(
        id=report.id,
        task_id=report.task_id,
        title=report.title,
        tech_topic=report.tech_topic,
        version=report.version,
        quality_score=report.quality_score,
        created_at=report.created_at,
        html_content=html_content,
        chart_data=chart_data
    )


@router.get("/{report_id}/html")
async def get_report_html(
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取 HTML 报告"""
    report = await _get_user_report(db, report_id, current_user.id)
    
    if not report.html_path or not Path(report.html_path).exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="报告文件不存在"
        )
    
    html_content = Path(report.html_path).read_text(encoding="utf-8")
    return HTMLResponse(content=html_content)


@router.get("/{report_id}/docx")
async def download_report_docx(
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """下载 Word 报告"""
    report = await _get_user_report(db, report_id, current_user.id)
    
    if not report.docx_path or not Path(report.docx_path).exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Word 报告文件不存在"
        )
    
    filename = f"{report.title or '技术评估报告'}.docx"
    return FileResponse(
        path=report.docx_path,
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )


@router.get("/{report_id}/data")
async def get_report_data(
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取图表数据"""
    report = await _get_user_report(db, report_id, current_user.id)
    
    if not report.data_path or not Path(report.data_path).exists():
        return {}
    
    return json.loads(Path(report.data_path).read_text(encoding="utf-8"))


@router.delete("/{report_id}")
async def delete_report(
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除报告"""
    report = await _get_user_report(db, report_id, current_user.id)
    
    # 删除文件
    for path in [report.html_path, report.docx_path, report.data_path]:
        if path and Path(path).exists():
            Path(path).unlink()
    
    await db.delete(report)
    await db.commit()
    
    return {"message": "报告已删除"}


async def _get_user_report(db: AsyncSession, report_id: int, user_id: int) -> Report:
    """获取用户的报告"""
    result = await db.execute(
        select(Report)
        .join(Task)
        .where(Report.id == report_id, Task.user_id == user_id)
    )
    report = result.scalar_one_or_none()
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="报告不存在"
        )
    
    return report

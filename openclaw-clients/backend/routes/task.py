from fastapi import APIRouter
import logging
from typing import Optional
from services.task_service import task_service
from shared import success_response, error_response, TaskRequest

router = APIRouter(prefix="/api/v1/task", tags=["task"])

@router.post("/create")
async def task_create(request: TaskRequest):
    try:
        result = await task_service.create_task(
            title=request.title, description=request.description,
            assignee=request.assignee, due_date=request.due_date, priority=request.priority
        )
        return success_response(result)
    except Exception as e:
        return error_response(str(e))

@router.get("/list")
async def task_list(status: Optional[str] = None, assignee: Optional[str] = None):
    try:
        result = await task_service.list_tasks(status=status, assignee=assignee)
        return success_response(result)
    except Exception as e:
        return error_response(str(e))

@router.put("/complete")
async def task_complete(task_id: str):
    try:
        result = await task_service.complete_task(task_id)
        return success_response(result)
    except Exception as e:
        return error_response(str(e))

@router.get("/stats/completion")
async def task_stats_completion():
    try:
        result = await task_service.get_completion_stats()
        return success_response(result)
    except Exception as e:
        return error_response(str(e))

@router.get("/stats/ranking")
async def task_stats_ranking():
    try:
        result = await task_service.get_ranking()
        return success_response(result)
    except Exception as e:
        return error_response(str(e))
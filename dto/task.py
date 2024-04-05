from __future__ import annotations

import datetime
from typing import Optional

from pydantic import BaseModel

import model


class TaskStatusUpdateDto(BaseModel):
    uuid: str
    task_uuid: str
    status: model.TaskStatus
    detail: Optional[str] = None
    updated_at: datetime.datetime
    updated_by: Optional[str] = None

    @staticmethod
    def from_model(m: model.TaskStatusUpdate) -> TaskStatusUpdateDto:
        print(m.updated_at)
        return TaskStatusUpdateDto(
            uuid=m.uuid,
            task_uuid=m.task_uuid,
            status=m.status,
            detail=m.detail,
            updated_at=m.updated_at,
            updated_by=m.updated_by,
        )


class TaskInDto(BaseModel):
    description: str
    subtasks: list[TaskInDto]


class TaskWithStatusDto(BaseModel):
    uuid: str
    description: str
    runbook_uuid: str
    depends_on: Optional[TaskDto] = None
    last_status: Optional[TaskStatusUpdateDto] = None

    @staticmethod
    def from_model(m: model.Task, status: model.TaskStatusUpdate) -> TaskWithStatusDto:
        return TaskWithStatusDto(
            uuid=m.uuid,
            description=m.description,
            runbook_uuid=m.runbook_uuid,
            depends_on=m.dependency and TaskDto.from_model(m.dependency, max_subtask_depth=0),
            last_status=status and TaskStatusUpdateDto.from_model(status),
        )


class TaskDto(BaseModel):
    uuid: Optional[str] = None
    description: str
    subtasks: list[TaskDto]
    runbook_uuid: str
    depends_on: Optional[TaskDto] = None
    parent: Optional[TaskDto] = None

    @staticmethod
    def from_model(m: model.Task, max_subtask_depth: Optional[int] = None) -> TaskDto:
        if max_subtask_depth is not None:
            subtasks = map(
                lambda task: TaskDto.from_model(task, max_subtask_depth - 1), m.subtasks
            ) if max_subtask_depth > 0 else []
        else:
            subtasks = map(TaskDto.from_model, m.subtasks)
        return TaskDto(
            uuid=m.uuid,
            description=m.description,
            subtasks=subtasks,
            runbook_uuid=m.runbook_uuid,
            depends_on=m.dependency and TaskDto.from_model(m.dependency, 0),
            parent=m.parent and TaskDto.from_model(m.parent, 0),
        )


class TaskCreateRequest(BaseModel):
    runbook_uuid: str
    description: str
    depends_on: Optional[str] = None
    parent: Optional[str] = None


class TaskCreateResponse(BaseModel):
    created: TaskDto


class TaskGetRequest(BaseModel):
    uuid: str
    max_subtasks_depth: Optional[int] = None
    calculate_progress: bool = False


class TaskGetResponse(BaseModel):
    task: TaskDto


class TaskStructureImportRequest(BaseModel):
    runbook_uuid: str
    tasks: list[TaskInDto]


class TaskStructureImportResponse(BaseModel):
    tasks: list[TaskDto]


class TaskListRequest(BaseModel):
    runbook_uuid: str
    flat: bool = False


class TaskListResponse(BaseModel):
    tasks: list[TaskDto]


class TaskGetStatusUpdatesRequest(BaseModel):
    task_uuid: str
    limit: int = 10


class TaskGetStatusUpdatesResponse(BaseModel):
    updates: list[TaskStatusUpdateDto]


class TaskUpdateStatusRequest(BaseModel):
    task_uuid: str
    status: model.TaskStatus
    detail: str
    updated_by: Optional[str] = None


class TaskUpdateStatusResponse(BaseModel):
    update: TaskStatusUpdateDto


class TaskListWithStatusRequest(BaseModel):
    runbook_uuid: Optional[str] = None
    parent_task_uuid: Optional[str] = None


class TaskListWithStatusResponse(BaseModel):
    tasks: list[TaskWithStatusDto]

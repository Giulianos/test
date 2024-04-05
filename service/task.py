import datetime
import uuid
from http import HTTPStatus

from fastapi import HTTPException
from sqlalchemy import Engine, select
from sqlalchemy.exc import DatabaseError
from sqlalchemy.orm import Session
from typing import Optional

import dto
import model


class TaskService:

    def __init__(self, db: Engine) -> None:
        self.db = db

    def get(self, req: dto.TaskGetRequest) -> dto.TaskGetResponse:
        with Session(self.db) as session:
            task: Optional[model.Task] = session.query(model.Task).get(req.uuid)
            if task is None:
                raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='task not found')
            return dto.TaskGetResponse(
                task=dto.TaskDto.from_model(task, max_subtask_depth=req.max_subtasks_depth),
            )

    def create(self, req: dto.TaskCreateRequest) -> dto.TaskCreateResponse:
        with Session(self.db) as session:
            session.begin()
            try:
                runbook: Optional[model.Project] = session.query(model.Runbook).get(req.runbook_uuid)
                if runbook is None:
                    raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='runbook not found')

                parent: Optional[model.Task] = None
                if req.parent:
                    retrieved_parent = session.query(model.Task).get(req.parent)
                    if retrieved_parent is None:
                        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='parent task not found')
                    parent = retrieved_parent

                # TODO: if depends_on has a dependant task, make it dependant on the new one we are creating
                depends_on: Optional[model.Task] = None
                if req.depends_on:
                    retrieved_depends_on = session.query(model.Task).get(req.depends_on)
                    if retrieved_depends_on is None:
                        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='depends_on task not found')
                    depends_on = retrieved_depends_on

                task = model.Task(
                    uuid=str(uuid.uuid4()),
                    description=req.description,
                    parent=parent,
                    dependency=depends_on,
                    runbook=runbook,
                )
                session.add(task)
            except DatabaseError:
                session.rollback()
                raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR)
            else:
                session.commit()
                return dto.TaskCreateResponse(
                    created=dto.TaskDto.from_model(task)
                )

    def list(self, req: dto.TaskListRequest) -> dto.TaskListResponse:
        with Session(self.db) as session:
            stmt = select(model.Task).where(model.Task.runbook_uuid == req.runbook_uuid)
            if not req.flat:
                stmt = stmt.where(model.Task.parent_task_uuid == None)
            tasks = session.scalars(stmt)
            return dto.TaskListResponse(
                tasks=map(
                    lambda task: dto.TaskDto.from_model(task, 0),
                    tasks
                )
            )

    def list_with_status(self, req: dto.TaskListWithStatusRequest) -> dto.TaskListWithStatusResponse:
        with Session(self.db) as session:
            stmt = select(model.Task)
            if req.parent_task_uuid is not None:
                stmt = stmt.where(model.Task.parent_task_uuid == req.parent_task_uuid)
            elif req.runbook_uuid is not None:
                stmt = stmt.where(model.Task.runbook_uuid == req.runbook_uuid).\
                    where(model.Task.parent_task_uuid == None)
            else:
                raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail='at least one of runbook_uuid or parent_task_uuid must be privided')

            tasks = session.scalars(stmt)
            tasks_dto: list[dto.TaskWithStatusDto] = []
            for task in tasks:
                last_status_update: Optional[model.TaskStatusUpdate] = None
                if task.last_status_uuid:
                    last_status_update = session.query(model.TaskStatusUpdate).get(task.last_status_uuid)
                tasks_dto.append(dto.TaskWithStatusDto.from_model(task, last_status_update))
            return dto.TaskListWithStatusResponse(
                tasks=tasks_dto
            )


    @staticmethod
    def persist_task(
            session: Session,
            runbook: model.Runbook,
            task: dto.TaskInDto,
            parent: Optional[model.Task],
            depends_on: Optional[model.Task]
    ) -> model.Task:
        task_model = model.Task(
            uuid=str(uuid.uuid4()),
            description=task.description,
            parent=parent,
            dependency=depends_on,
            runbook_uuid=runbook.uuid
        )
        if task.subtasks:
            previous_subtask = None
            for subtask in task.subtasks:
                previous_subtask = TaskService.persist_task(
                    session=session,
                    runbook=runbook,
                    task=subtask,
                    parent=task_model,
                    depends_on=previous_subtask
                )

        session.add(task_model)
        return task_model

    def structure_import(self, req: dto.TaskStructureImportRequest) -> dto.TaskStructureImportResponse:
        with Session(self.db) as session:
            session.begin()
            try:
                runbook: Optional[model.Runbook] = session.query(model.Runbook).get(req.runbook_uuid)
                if runbook is None:
                    raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='runbook not found')

                tasks: list[model.Task] = []
                previous_task: Optional[model.Task] = None
                for task in req.tasks:
                    previous_task = TaskService.persist_task(
                        session=session,
                        runbook=runbook,
                        task=task,
                        parent=None,
                        depends_on=previous_task
                    )
                    tasks.append(previous_task)
            except DatabaseError:
                session.rollback()
                raise
            else:
                session.commit()
                return dto.TaskStructureImportResponse(
                    tasks=map(dto.TaskDto.from_model, tasks)
                )

    def get_status_updates(self, req: dto.TaskGetStatusUpdatesRequest) -> dto.TaskGetStatusUpdatesResponse:
        with Session(self.db) as session:
            stmt = select(model.TaskStatusUpdate). \
                where(model.TaskStatusUpdate.task_uuid == req.task_uuid). \
                order_by(model.TaskStatusUpdate.updated_at.desc()). \
                limit(req.limit)

            updates = session.scalars(stmt)
            return dto.TaskGetStatusUpdatesResponse(
                updates=map(dto.TaskStatusUpdateDto.from_model, updates)
            )

    def update_status(self, req: dto.TaskUpdateStatusRequest) -> dto.TaskUpdateStatusResponse:
        with Session(self.db) as session:
            try:
                task: model.Task = session.query(model.Task).get(req.task_uuid)
                if task is None:
                    raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='task not found')

                update: model.TaskStatusUpdate = model.TaskStatusUpdate(
                    uuid=str(uuid.uuid4()),
                    task_uuid=req.task_uuid,
                    status=req.status,
                    detail=req.detail,
                    updated_by=req.updated_by,
                    updated_at=datetime.datetime.utcnow(),
                )
                task.last_status_uuid = update.uuid
                session.add(update)
                TaskService.update_parent_status(session, task)
            except DatabaseError:
                session.rollback()
                raise
            else:
                session.commit()
                return dto.TaskUpdateStatusResponse(
                    update=dto.TaskStatusUpdateDto.from_model(update),
                )

    @staticmethod
    def update_parent_status(session: Session, task: model.Task):
        parent: model[model.Task] = task.parent
        if parent is None:
            return
        status_count: dict[model.TaskStatus, int] = {
            model.TaskStatus.NOT_STARTED: 0,
            model.TaskStatus.IN_PROGRESS: 0,
            model.TaskStatus.COMPLETED: 0,
            model.TaskStatus.ERROR: 0,
        }
        total = 0
        for sibling in parent.subtasks:
            total += 1
            if not sibling.last_status_uuid:
                status_count[model.TaskStatus.NOT_STARTED] += 1
            else:
                status: model.TaskStatusUpdate = session.query(model.TaskStatusUpdate).get(sibling.last_status_uuid)
                status_count[status.status] += 1

        new_parent_status: Optional[model.TaskStatus] = None
        if status_count[model.TaskStatus.ERROR] != 0:
            new_parent_status = model.TaskStatus.ERROR
            new_detail = f'There are {status_count[model.TaskStatus.ERROR]} subtasks with errors'
        elif status_count[model.TaskStatus.COMPLETED] == total:
            new_parent_status = model.TaskStatus.COMPLETED
            new_detail = f'{total}/{total} subtasks completed'
        elif status_count[model.TaskStatus.NOT_STARTED] == total:
            new_parent_status = model.TaskStatus.NOT_STARTED
            new_detail = f'There are {total} not started subtasks'
        else:
            new_parent_status = model.TaskStatus.IN_PROGRESS
            new_detail = f'{status_count[model.TaskStatus.COMPLETED]} completed, '
            new_detail += f'{status_count[model.TaskStatus.IN_PROGRESS]} in progress,  '
            new_detail += f'{status_count[model.TaskStatus.NOT_STARTED]} not started'

        last_parent_status_update: model.TaskStatusUpdate = session.query(
            model.TaskStatusUpdate
        ).get(task.parent.last_status_uuid)
        if last_parent_status_update is None and new_parent_status == model.TaskStatus.NOT_STARTED:
            return

        parent_status_update = model.TaskStatusUpdate(
            uuid=str(uuid.uuid4()),
            task_uuid=parent.uuid,
            status=new_parent_status,
            detail=new_detail,
            updated_by='Subtask change',
            updated_at=datetime.datetime.utcnow(),
        )
        parent.last_status_uuid = parent_status_update.uuid
        session.add(parent_status_update)
        TaskService.update_parent_status(session, parent)

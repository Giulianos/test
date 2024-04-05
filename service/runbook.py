import uuid
from http import HTTPStatus

from fastapi import HTTPException
from sqlalchemy import Engine, select
from sqlalchemy.exc import DatabaseError
from sqlalchemy.orm import Session
from typing import Optional

import dto
import model


class RunbookService:

    def __init__(self, db: Engine) -> None:
        self.db = db

    def create(self, req: dto.RunbookCreateRequest) -> dto.RunbookCreateResponse:
        with Session(self.db) as session:
            session.begin()
            try:
                project: Optional[model.Project] = session.query(model.Project).get(req.project_uuid)
                if project is None:
                    raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='project not found')
                runbook = model.Runbook(
                    uuid=str(uuid.uuid4()),
                    name=req.name,
                    source=req.source,
                    target=req.target,
                    project=project,
                )
                session.add(runbook)
            except DatabaseError:
                session.rollback()
                raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR)
            else:
                session.commit()
                return dto.RunbookCreateResponse(
                    created=dto.RunbookDto.from_model(runbook)
                )

    def list(self, req: dto.RunbookListRequest) -> dto.RunbookListResponse:
        with Session(self.db) as session:
            runbooks = session.scalars(
                select(model.Runbook).where(model.Runbook.project_uuid == req.project_uuid)
            )

            return dto.RunbookListResponse(
                runbooks=map(dto.RunbookDto.from_model, runbooks)
            )

    def get(self, req: dto.RunbookGetRequest) -> dto.RunbookGetResponse:
        with Session(self.db) as session:
            runbook: Optional[model.Runbook] = session.query(model.Runbook).get(req.uuid)
            if runbook is None:
                raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='runbook not found')
            return dto.RunbookGetResponse(
                runbook=dto.RunbookDto.from_model(runbook),
            )

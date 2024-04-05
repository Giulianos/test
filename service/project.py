import uuid
from http import HTTPStatus

from fastapi import HTTPException
from sqlalchemy import Engine, select
from sqlalchemy.orm import Session
from sqlalchemy.exc import DatabaseError

import dto
import model


class ProjectService:

    def __init__(self, db: Engine) -> None:
        self.db = db

    def get(self, req: dto.ProjectGetRequest) -> dto.ProjectGetResponse:
        with Session(self.db) as session:
            project: model.Project = session.query(model.Project).get(req.uuid)
            if project is None:
                raise HTTPException(status_code=HTTPStatus.NOT_FOUND)
            return dto.ProjectGetResponse(
                project=dto.ProjectDto.from_model(project)
            )

    def create(self, req: dto.ProjectCreateRequest) -> dto.ProjectCreateResponse:
        with Session(self.db) as session:
            session.begin()
            try:
                project = model.Project(
                    uuid=str(uuid.uuid4()),
                    name=req.name,
                )
                session.add(project)
            except DatabaseError:
                session.rollback()
                raise
            else:
                session.commit()
                return dto.ProjectCreateResponse(
                    created=dto.ProjectDto.from_model(project)
                )

    def list(self, req: dto.ProjectListRequest) -> dto.ProjectListResponse:
        with Session(self.db) as session:
            projects = session.scalars(select(model.Project))
            return dto.ProjectListResponse(
                projects=list(map(dto.ProjectDto.from_model, projects))
            )

from __future__ import annotations
from pydantic import BaseModel

import model


class ProjectDto(BaseModel):
    uuid: str
    name: str

    @staticmethod
    def from_model(m: model.Project) -> ProjectDto:
        return ProjectDto(
            uuid=m.uuid,
            name=m.name,
        )


class ProjectGetRequest(BaseModel):
    uuid: str


class ProjectGetResponse(BaseModel):
    project: ProjectDto


class ProjectCreateRequest(BaseModel):
    name: str


class ProjectCreateResponse(BaseModel):
    created: ProjectDto


class ProjectListRequest(BaseModel):
    pass


class ProjectListResponse(BaseModel):
    projects: list[ProjectDto]

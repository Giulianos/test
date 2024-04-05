from __future__ import annotations
from pydantic import BaseModel

import model


class RunbookDto(BaseModel):
    uuid: str
    project_uuid: str
    name: str
    source: str
    target: str

    @staticmethod
    def from_model(m: model.Runbook) -> RunbookDto:
        return RunbookDto(
            uuid=m.uuid,
            project_uuid=m.project_uuid,
            name=m.name,
            source=m.source,
            target=m.target,
        )


class RunbookCreateRequest(BaseModel):
    project_uuid: str
    name: str
    source: str
    target: str


class RunbookCreateResponse(BaseModel):
    created: RunbookDto


class RunbookListRequest(BaseModel):
    project_uuid: str


class RunbookListResponse(BaseModel):
    runbooks: list[RunbookDto]


class RunbookGetRequest(BaseModel):
    uuid: str


class RunbookGetResponse(BaseModel):
    runbook: RunbookDto

import time

from fastapi import FastAPI, APIRouter
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine

import dto
import service
import model

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)
api = FastAPI()

db_engine = create_engine("sqlite:///waverunner.db", echo=True)
model.Base.metadata.create_all(db_engine)

project_service = service.ProjectService(db=db_engine)
runbook_service = service.RunbookService(db=db_engine)
task_service = service.TaskService(db=db_engine)

app.mount("/api", api)
app.mount("/", StaticFiles(directory="frontend_dist", html=True), name="frontend")


@api.post('/project/get')
async def project_get(request: dto.ProjectGetRequest) -> dto.ProjectGetResponse:
    return project_service.get(request)


@api.post('/project/create')
async def project_create(request: dto.ProjectCreateRequest) -> dto.ProjectCreateResponse:
    return project_service.create(request)


@api.post('/project/list')
async def project_list(request: dto.ProjectListRequest) -> dto.ProjectListResponse:
    return project_service.list(request)


@api.post('/runbook/create')
async def runbook_create(request: dto.RunbookCreateRequest) -> dto.RunbookCreateResponse:
    return runbook_service.create(request)


@api.post('/runbook/list')
async def runbook_list(request: dto.RunbookListRequest) -> dto.RunbookListResponse:
    return runbook_service.list(request)


@api.post('/runbook/get')
async def runbook_get(request: dto.RunbookGetRequest) -> dto.RunbookGetResponse:
    return runbook_service.get(request)


@api.post('/task/create')
async def task_create(request: dto.TaskCreateRequest) -> dto.TaskCreateResponse:
    return task_service.create(request)


@api.post('/task/get')
async def task_get(request: dto.TaskGetRequest) -> dto.TaskGetResponse:
    return task_service.get(request)


@api.post('/task/list')
async def task_list(request: dto.TaskListRequest) -> dto.TaskListResponse:
    return task_service.list(request)


@api.post('/task/list-with-status')
async def task_list_with_status(request: dto.TaskListWithStatusRequest) -> dto.TaskListWithStatusResponse:
    return task_service.list_with_status(request)


@api.post('/task/get-status-updates')
async def task_get_status_updates(request: dto.TaskGetStatusUpdatesRequest) -> dto.TaskGetStatusUpdatesResponse:
    return task_service.get_status_updates(request)


@api.post('/task/update-status')
async def task_update_status(request: dto.TaskUpdateStatusRequest) -> dto.TaskUpdateStatusResponse:
    return task_service.update_status(request)


@api.post('/task/structure-import')
async def task_structure_import(request: dto.TaskStructureImportRequest) -> dto.TaskStructureImportResponse:
    return task_service.structure_import(request)

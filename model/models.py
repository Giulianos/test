import datetime
from enum import Enum

from sqlalchemy import ForeignKey, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from typing import List


class Base(DeclarativeBase):
    pass


class Project(Base):
    __tablename__ = "projects"

    uuid: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str]

    runbooks: Mapped[List["Runbook"]] = relationship(
        back_populates='project', cascade='all, delete-orphan'
    )


class Runbook(Base):
    __tablename__ = "runbooks"

    uuid: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str]
    source: Mapped[str]
    target: Mapped[str]
    project_uuid: Mapped[str] = mapped_column(ForeignKey("projects.uuid"))

    project: Mapped["Project"] = relationship(back_populates='runbooks')
    tasks: Mapped[List["Task"]] = relationship(back_populates='runbook')


class Task(Base):
    __tablename__ = "tasks"

    uuid: Mapped[str] = mapped_column(primary_key=True)
    description: Mapped[str]

    runbook_uuid: Mapped[str] = mapped_column(ForeignKey("runbooks.uuid"))
    parent_task_uuid: Mapped[str] = mapped_column(ForeignKey("tasks.uuid"))
    depends_on_task_uuid: Mapped[str] = mapped_column(ForeignKey("tasks.uuid"))
    last_status_uuid: Mapped[str]

    runbook: Mapped["Runbook"] = relationship(back_populates='tasks')
    parent: Mapped["Task"] = relationship(remote_side=uuid, backref='subtasks', foreign_keys=[parent_task_uuid])
    dependency: Mapped["Task"] = relationship(remote_side=uuid, backref='dependants', foreign_keys=[depends_on_task_uuid])
    status_updates: Mapped["TaskStatusUpdate"] = relationship(remote_side=uuid, back_populates='task')


class TaskStatus(str, Enum):
    NOT_STARTED = 'NOT_STARTED'
    IN_PROGRESS = 'IN_PROGRESS'
    COMPLETED = 'COMPLETED'
    ERROR = 'ERROR'


class TaskStatusUpdate(Base):
    __tablename__ = "task_status"

    uuid: Mapped[str] = mapped_column(primary_key=True)
    task_uuid: Mapped[str] = mapped_column(ForeignKey("tasks.uuid"))
    status: Mapped[TaskStatus] = mapped_column(nullable=False)
    detail: Mapped[str]
    updated_at: Mapped[datetime.datetime] = mapped_column(nullable=False, server_default=func.now())
    updated_by: Mapped[str]

    task: Mapped["Task"] = relationship(back_populates='status_updates')

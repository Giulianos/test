CREATE TABLE IF NOT EXISTS projects (
    uuid TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS runbooks (
    uuid TEXT PRIMARY KEY,
    name TEXT,
    source TEXT,
    target TEXT,
    project_uuid TEXT,

    FOREIGN KEY(project_uuid) REFERENCES projects(uuid)
);

CREATE TABLE IF NOT EXISTS tasks (
    uuid TEXT PRIMARY KEY,
    description TEXT NOT NULL,

    runbook_uuid TEXT,
    parent_task_uuid TEXT,
    depends_on_task_uuid TEXT,
    last_status_uuid TEXT,

    FOREIGN KEY (runbook_uuid) REFERENCES  runbooks(uuid),
    FOREIGN KEY (parent_task_uuid) REFERENCES tasks(uuid),
    FOREIGN KEY (depends_on_task_uuid) REFERENCES tasks(uuid),
    FOREIGN KEY (last_status_uuid) REFERENCES task_status(uuid)
);

CREATE TABLE IF NOT EXISTS task_status (
    uuid TEXT PRIMARY KEY,
    task_uuid TEXT,
    status TEXT NOT NULL,
    detail TEXT NOT NULL,
    updated_at DATETIME,
    updated_by TEXT,

    FOREIGN KEY (task_uuid) REFERENCES tasks(uuid),
    UNIQUE (task_uuid, updated_at)
);

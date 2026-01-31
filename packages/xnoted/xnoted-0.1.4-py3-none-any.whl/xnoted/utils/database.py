import sqlite3
from typing import Any, Dict, List, Optional

DB_NAME = "database.db"

CREATE_TASK_TABLE = """
CREATE TABLE IF NOT EXISTS task(
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    title TEXT,
    content TEXT,
    status INTEGER DEFAULT 0,
    createdAt TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES project(id)
)
"""

INSERT_TASK_DATA = (
    "INSERT INTO task(id, project_id, title, content, status) VALUES(?, ?, ?, ?, ?)"
)

UPDATE_TASK_DATA = "UPDATE task SET title = ?, content = ?, status = ? WHERE id = ?"

QUERY_TASKS_BY_PROJECT = """
SELECT id, title, content, status, createdAt 
FROM task 
WHERE project_id = ? 
ORDER BY createdAt
"""

QUERY_ONE_TASKS_BY_ID = """
SELECT id, title, content, status, createdAt 
FROM task 
WHERE id = ? 
"""

CREATE_PROJECT_TABLE = """
CREATE TABLE IF NOT EXISTS project(
    id TEXT PRIMARY KEY,
    title TEXT,
    description TEXT,
    type TEXT,
    createdAt TEXT DEFAULT CURRENT_TIMESTAMP
)
"""

INSERT_PROJECT_DATA = (
    "INSERT INTO project(id, title, description, type) VALUES(?, ?, ?, ?)"
)

UPDATE_PROJECT_DATA = (
    "UPDATE project SET title = ?, description = ?, type = ? WHERE id = ?"
)

QUERY_ALL_PROJECT_DATA = """
SELECT id, title, description, type, createdAt 
FROM project 
ORDER BY createdAt
"""

QUERY_ONE_PROJECT_DATA = """
SELECT id, title, description, type, createdAt 
FROM project 
WHERE id = ?
"""

DELETE_PROJECT_DATA = "DELETE FROM project WHERE id = ?"

DELETE_PROJECT_TASKS = "DELETE FROM task WHERE project_id = ?"

DELETE_TASK = "DELETE FROM task WHERE id = ?"


class Database:
    def __init__(self):
        self.path = DB_NAME
        self.current_project_id: Optional[str] = None
        self.project_name: str = "Project"
        self.project_type: str = ""
        self.con = sqlite3.connect(DB_NAME)
        self.cur = self.con.cursor()
        self.cur.execute(CREATE_TASK_TABLE)
        self.cur.execute(CREATE_PROJECT_TABLE)
        self.con.commit()

        # Ensure a default project exists
        self._ensure_default_project()

        # Set current project to the first project
        projects = self.load_projects()
        if projects:
            self.current_project_id = projects[0]["id"]
            self.project_type = projects[0]["type"]

    def _ensure_default_project(self):
        """Create a default project if no projects exist"""
        try:
            self.cur.execute("SELECT COUNT(*) FROM project")
            count = self.cur.fetchone()[0]

            if count == 0:
                import uuid

                default_project = {
                    "id": str(uuid.uuid4()),
                    "title": "Default",
                    "description": "Default project",
                    "type": "general",
                }
                self.cur.execute(
                    INSERT_PROJECT_DATA,
                    (
                        default_project["id"],
                        default_project["title"],
                        default_project["description"],
                        default_project["type"],
                    ),
                )
                self.con.commit()
        except Exception as e:
            print(f"Error creating default project: {e}")

    def set_current_project(self, project_id: str):
        """Set the current project context"""
        self.current_project_id = project_id
        project = self.get_project(project_id)
        self.project_name = project['title']
        self.project_type = project['type']

    def save(self, data: Dict[str, Any]):
        """Save a task to the current project"""
        if not self.current_project_id:
            raise ValueError("No project selected. Call set_current_project() first.")

        try:
            self.cur.execute(
                INSERT_TASK_DATA,
                (
                    data["id"],
                    self.current_project_id,
                    data["title"],
                    data["content"],
                    0,
                ),
            )
            self.con.commit()
        except Exception as e:
            print(f"Error saving data: {e}")
            raise

    def save_project(self, data: Dict[str, Any]):
        """Create a new project"""
        try:
            self.cur.execute(
                INSERT_PROJECT_DATA,
                (data["id"], data["title"], data["description"], data["type"]),
            )
            self.con.commit()
        except Exception as e:
            print(f"Error saving project: {e}")
            raise

    def update_task(self, task_id: str, data: Dict[str, Any]):
        """Update an existing task"""
        try:
            self.cur.execute(
                UPDATE_TASK_DATA,
                (data["title"], data["content"], data.get("status", 0), task_id),
            )
            self.con.commit()
        except Exception as e:
            print(f"Error updating task: {e}")
            raise

    def update_project(self, project_id: str, data: Dict[str, Any]):
        """Update an existing project"""
        try:
            self.cur.execute(
                UPDATE_PROJECT_DATA,
                (data["title"], data["description"], data["type"], project_id),
            )
            self.con.commit()
        except Exception as e:
            print(f"Error updating project: {e}")
            raise

    def delete_project(self, project_id: str):
        """Delete a project and all its tasks"""
        try:
            self.cur.execute(DELETE_PROJECT_TASKS, (project_id,))
            self.cur.execute(DELETE_PROJECT_DATA, (project_id,))
            self.con.commit()
        except Exception as e:
            print(f"Error deleting project: {e}")
            raise

    def delete_task(self, task_id: str):
        """Delete a task"""
        try:
            self.cur.execute(DELETE_TASK, (task_id,))
            self.con.commit()
        except Exception as e:
            print(f"Error deleting task: {e}")
            raise

    def load(self, project_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Load all tasks for a specific project"""
        pid = project_id or self.current_project_id
        if not pid:
            raise ValueError(
                "No project specified. Provide project_id or call set_current_project() first."
            )

        try:
            res = self.cur.execute(QUERY_TASKS_BY_PROJECT, (pid,))
            rows = res.fetchall()
            print(rows, "----------")
            return [
                {
                    "id": row[0],
                    "title": row[1],
                    "content": row[2],
                    "status": row[3],
                    "createdAt": row[4],
                }
                for row in rows
            ]
        except Exception as e:
            print(f"Error loading data: {e}")
            return []

    def get_task(self, task_id: Optional[str] = None) -> List[Dict[str, Any]]:
        if not task_id:
            raise ValueError("No task id specified. Provide task_id.")

        try:
            res = self.cur.execute(QUERY_ONE_TASKS_BY_ID, (task_id,))
            row = res.fetchone()
            return {
                "id": row[0],
                "title": row[1],
                "content": row[2],
                "status": row[3],
                "createdAt": row[4],
            }
        except Exception as e:
            print(f"Error loading data: {e}")
            return {}

    def load_projects(self) -> List[Dict[str, Any]]:
        """Load all projects"""
        try:
            res = self.cur.execute(QUERY_ALL_PROJECT_DATA)
            rows = res.fetchall()
            return [
                {
                    "id": row[0],
                    "title": row[1],
                    "description": row[2],
                    "type": row[3],
                    "createdAt": row[4],
                }
                for row in rows
            ]
        except Exception as e:
            print(f"Error loading projects: {e}")
            return []

    def get_first_project(self) -> Dict[str, Any]:
        """Get the first project"""
        try:
            res = self.cur.execute(QUERY_ALL_PROJECT_DATA)
            row = res.fetchone()
            return {
                "id": row[0],
                "title": row[1],
                "description": row[2],
                "type": row[3],
                "createdAt": row[4],
            }
        except Exception as e:
            print(f"Error loading project: {e}")
            return {}

    def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific project by ID"""
        try:
            self.cur.execute(QUERY_ONE_PROJECT_DATA, (project_id,))
            row = self.cur.fetchone()
            if row:
                return {
                    "id": row[0],
                    "title": row[1],
                    "description": row[2],
                    "type": row[3],
                    "createdAt": row[4],
                }
            return None
        except Exception as e:
            print(f"Error loading project: {e}")
            return None

    def append(self, data: Dict[str, Any]):
        """Alias for save()"""
        self.save(data)

    def update(self, data: List[Dict[str, Any]]):
        """Batch update/insert tasks for the current project"""
        if not self.current_project_id:
            raise ValueError("No project selected. Call set_current_project() first.")

        try:
            values = [
                (d["id"], self.current_project_id, d["title"], d["content"], 0)
                for d in data
            ]
            self.cur.executemany(INSERT_TASK_DATA, values)
            self.con.commit()
        except Exception as e:
            print(f"Error updating data: {e}")
            raise

    def is_storage_exist(self) -> bool:
        """Check if storage is accessible"""
        try:
            self.cur.execute("SELECT 1 FROM task LIMIT 1")
            return True
        except Exception:
            return False

    def is_empty(self) -> bool:
        """Check if the database is empty (exactly 1 project and no tasks).

        Returns:
            True if there's exactly 1 project and 0 tasks, False otherwise
        """
        try:
            self.cur.execute("SELECT COUNT(*) FROM project")
            project_count = self.cur.fetchone()[0]

            self.cur.execute("SELECT COUNT(*) FROM task")
            task_count = self.cur.fetchone()[0]

            return project_count == 1 and task_count == 0
        except Exception:
            return True

    def get_last_id(self, project_id: Optional[str] = None) -> str:
        """Get the last task ID for a project"""
        tasks = self.load(project_id)
        if tasks:
            return tasks[-1]["id"]
        return "0"

    def __del__(self):
        if hasattr(self, "con"):
            self.con.close()

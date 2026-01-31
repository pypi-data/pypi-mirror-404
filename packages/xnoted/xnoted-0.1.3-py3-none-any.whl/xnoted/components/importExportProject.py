import json
from pathlib import Path
from datetime import datetime
from textual.containers import Container
from textual.widgets import RadioSet, RadioButton, Input
from textual.app import ComposeResult
from textual.binding import Binding
from xnoted.utils.database import Database
from xnoted.utils.constants import (
    EXPORT_PROJECT_ID,
    IMPORT_PROJECT_ID,
    EXPORT_PROJECT_RADIO_ID,
)

class ProjectTypeContainer(RadioSet):
    def __init__(self):
        super().__init__(id=EXPORT_PROJECT_RADIO_ID)
        self.border_title = "Import or Export project"

    def compose(self):
        yield RadioButton("Import", id=IMPORT_PROJECT_ID, value=True)
        yield RadioButton("Export", id=EXPORT_PROJECT_ID)


class ImportExportProject(Container):
    def __init__(self, database: Database):
        super().__init__()
        self.database = database

    BINDINGS = [
        Binding("ctrl+s", "import_export", "Export or Import", show=False),
    ]

    def compose(self) -> ComposeResult:
        yield ProjectTypeContainer()
        yield Input(placeholder="File path (e.g., export.json)", id="file_path_input")

    def action_import_export(
        self,
    ) -> None:
        """Handle execute button press"""
        radio_set = self.query_one(ProjectTypeContainer)
        selected = radio_set.pressed_button

        if selected and selected.id == EXPORT_PROJECT_ID:
            self.handle_export()
        elif selected and selected.id == IMPORT_PROJECT_ID:
            self.handle_import()

    def handle_export(self) -> None:
        """Export current project and its tasks to JSON"""
        try:
            file_path_input = self.query_one("#file_path_input", Input)
            file_path = file_path_input.value.strip()

            if not file_path:
                file_path = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

            if not file_path.endswith(".json"):
                file_path += ".json"

            # Get current project
            if not self.database.current_project_id:
                self._update_status("No project selected", "error")
                return

            project = self.database.get_project(self.database.current_project_id)
            if not project:
                self._update_status("Project not found", "error")
                return

            # Get all tasks for the project
            tasks = self.database.load(self.database.current_project_id)

            # Create export data structure
            export_data = {
                "version": "1.0",
                "exported_at": datetime.now().isoformat(),
                "project": project,
                "tasks": tasks,
                "task_count": len(tasks),
            }

            # Write to file
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

            self._update_status(f"Successfully exported to {file_path}", "success")
            self.log(f"Exported project '{project['title']}' with {len(tasks)} tasks")

        except Exception as e:
            self._update_status(f"Export failed: {str(e)}", "error")
            self.log(f"Export error: {e}")

    def handle_import(self) -> None:
        """Import project and tasks from JSON"""
        try:
            file_path_input = self.query_one("#file_path_input", Input)
            file_path = file_path_input.value.strip()

            if not file_path:
                self._update_status("Please enter a file path", "error")
                return

            if not Path(file_path).exists():
                self._update_status(f"File not found: {file_path}", "error")
                return

            # Read JSON file
            with open(file_path, "r", encoding="utf-8") as f:
                import_data = json.load(f)

            # Validate data structure
            if "project" not in import_data or "tasks" not in import_data:
                self._update_status("Invalid JSON format", "error")
                return

            project_data = import_data["project"]
            tasks_data = import_data["tasks"]

            # Generate new IDs to avoid conflicts
            import uuid

            new_project_id = str(uuid.uuid4())

            # Create new project
            new_project = {
                "id": new_project_id,
                "title": f"{project_data['title']} (Imported)",
                "description": project_data.get("description", ""),
                "type": project_data.get("type", "general"),
            }

            self.database.save_project(new_project)

            # Import tasks with new IDs
            id_mapping = {}  # Map old IDs to new IDs
            imported_count = 0

            for task in tasks_data:
                old_task_id = task["id"]
                new_task_id = str(uuid.uuid4())
                id_mapping[old_task_id] = new_task_id

                new_task = {
                    "id": new_task_id,
                    "title": task.get("title", ""),
                    "content": task.get("content", ""),
                    "status": task.get("status", 0),
                }

                # Temporarily set current project to the new one
                original_project = self.database.current_project_id
                self.database.set_current_project(new_project_id)

                self.database.save(new_task)
                imported_count += 1

                # Restore original project
                if original_project:
                    self.database.set_current_project(original_project)

            self._update_status(
                f"Successfully imported project '{new_project['title']}' with {imported_count} tasks",
                "success",
            )
            self.log(f"Imported {imported_count} tasks into project {new_project_id}")

        except json.JSONDecodeError as e:
            self._update_status(f"Invalid JSON file: {str(e)}", "error")
            self.log(f"JSON decode error: {e}")
        except Exception as e:
            self._update_status(f"Import failed: {str(e)}", "error")
            self.log(f"Import error: {e}")

    def _update_status(self, message: str, status_type: str = "info") -> None:
        """Update status message with styling"""
        project_type_container = self.query_one(f"#{EXPORT_PROJECT_RADIO_ID}")

        if status_type == "success":
            project_type_container.border_title = project_type_container.border_title + f" | ✓ {message}"
        elif status_type == "error":
            project_type_container.border_title = project_type_container.border_title + f" | ✗ {message}"
        else:
            project_type_container.border_title = project_type_container.border_title + f" | {message}"

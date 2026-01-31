from textual.screen import ModalScreen
from collections.abc import Callable
from textual.widgets import Label, ListView, ListItem
from xnoted.utils.database import Database
from textual.binding import Binding
from xnoted.utils.helpers import slugify
from xnoted.screens.createProject import CreateProjectModal
from xnoted.screens.confirm import ConfirmModal
from xnoted.utils.constants import PROJECTS_ID, TASK_HEADER_ID, TASKS_ID


class Projects(ListView):
    def __init__(self, database: Database, close_app: Callable[[], None]):
        super().__init__(id=PROJECTS_ID)
        self.has_task_result = True
        self.database = database
        self.close_app = close_app

    BORDER_TITLE = "Projects"
    BINDINGS = [
        Binding("k", "cursor_up", "Cursor up", show=False),
        Binding("j", "cursor_down", "Cursor down", show=False),
        Binding("e", "edit_project", "Cursor down", show=False),
        Binding("d", "delete_project", "Cursor down", show=False),
    ]

    def on_mount(self):
        self.load_projects()

    def load_projects(self) -> None:
        self.clear()
        projects = self.database.load_projects()

        if projects:
            for project in projects:
                title = project.get("title")
                project_id = project.get("id")
                list_item = ListItem(Label(f"{title}"))
                list_item.project_id = project_id
                list_item.project_name = slugify(title)
                self.append(list_item)
        else:
            self.append(ListItem(Label("No projects yet")))

    def on_list_view_selected(self, event: ListView.Highlighted) -> None:
        project_id = event.item.project_id
        self.database.set_current_project(project_id)
        tasks_widget = self.app.query_one(f"#{TASKS_ID}")
        tasks_widget.refresh_tasks()
        task_header_label_widget: Label = self.app.query_one(f"#{TASK_HEADER_ID}")
        task_header_label_widget.update(self.database.project_name)
        self.close_app()

    def action_edit_project(self):
        child: ListItem = self.highlighted_child

        if child and hasattr(child, "project_id"):
            project_id = child.project_id
            project = self.database.get_project(project_id)
            self.app.push_screen(
                CreateProjectModal(
                    database=self.database,
                    title=project["title"],
                    description=project["description"],
                    editing=True,
                    project_id=project_id,
                    project_type=project["type"],
                )
            )

    def action_delete_project(self):
        child: ListItem = self.highlighted_child

        if child and hasattr(child, "project_id"):
            project_id = child.project_id

            def on_confirm():
                self.database.delete_project(project_id)
                first_project = self.database.get_first_project()
                self.database.set_current_project(first_project["id"])
                self.load_projects()
                tasks_widget = self.app.query_one("#tasks")
                tasks_widget.refresh_tasks()

            self.app.push_screen(ConfirmModal(on_confirm=on_confirm))


class SelectProjectModal(ModalScreen):
    def __init__(self, database: Database):
        self.database = database
        super().__init__()

    BINDINGS = [
        ("escape", "close", "Close modal"),
    ]

    def compose(self):
        yield Projects(database=self.database, close_app=self.action_close)

    def action_close(self):
        self.app.pop_screen()

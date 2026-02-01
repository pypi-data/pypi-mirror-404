from textual.screen import ModalScreen
from collections.abc import Callable
from textual.widgets import Label, ListView, ListItem
from xnoted.utils.database import Database
from textual.binding import Binding
from xnoted.utils.helpers import slugify
from xnoted.utils.constants import PROJECTS_ID


class SelectProject(ListView):
    def __init__(
        self,
        database: Database,
        close_app: Callable[[], None],
        on_select: Callable[[ListView.Highlighted], None],
        close_on_select: bool,
        border_title: str,
    ):
        super().__init__(id=PROJECTS_ID)
        self.has_task_result = True
        self.database = database
        self.close_app = close_app
        self.on_select = on_select
        self.close_on_select = close_on_select
        self.border_title = border_title

    BINDINGS = [
        Binding("k", "cursor_up", "Cursor up", show=False),
        Binding("j", "cursor_down", "Cursor down", show=False),
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
        self.on_select(event)
        if self.close_on_select:
            self.close_app()


class SelectProjectModal(ModalScreen):
    def __init__(
        self,
        database: Database,
        on_select: Callable[[ListView.Highlighted], None],
        _border_title="Select project",
    ):
        super().__init__()
        self.database = database
        self.on_select = on_select
        self._border_title = _border_title

    BINDINGS = [
        ("escape", "close", "Close modal"),
    ]

    def compose(self):
        yield SelectProject(
            database=self.database,
            close_app=self.action_close,
            close_on_select=True,
            on_select=self.on_select,
            border_title=self._border_title,
        )

    def action_close(self):
        self.app.pop_screen()

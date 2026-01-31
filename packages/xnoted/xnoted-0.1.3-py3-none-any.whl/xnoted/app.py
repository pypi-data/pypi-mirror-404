from textual.app import App
from xnoted.screens.createTask import CreateTaskModal
from xnoted.screens.projects import SelectProjectModal
from xnoted.screens.createProject import CreateProjectModal
from xnoted.screens.importExportProject import ImportExportProjectModal
from xnoted.components.content import ContentWrapper
from xnoted.components.footer import Footer
from xnoted.components.body import Body
from xnoted.utils.database import Database


class XNotedApp(App):
    def __init__(self):
        super().__init__()
        self.database = Database()

    CSS_PATH = "styles/main.tcss"
    BINDINGS = [
        ("ctrl+n", "create_new_task", "Create new task"),
        ("ctrl+l", "select_project", "Select project"),
        ("ctrl+o", "import_export_project", "Import or Export project"),
        ("ctrl+b", "create_new_project", "Create project"),
        ("ctrl+d", "scroll_body_down", "Scroll body down"),
        ("ctrl+u", "scroll_body_up", "Scroll body up"),
        ("ctrl+r", "show_readme", "Show readme"),
    ]

    def compose(self):
        yield ContentWrapper(database=self.database)
        yield Footer(database=self.database)

    def action_create_new_task(self):
        self.app.push_screen(CreateTaskModal(database=self.database))

    def action_create_new_project(self):
        self.app.push_screen(CreateProjectModal(database=self.database))

    def action_import_export_project(self):
        self.app.push_screen(ImportExportProjectModal(database=self.database))

    def action_select_project(self):
        self.app.push_screen(SelectProjectModal(database=self.database))

    def action_scroll_body_down(self):
        body_widget: Body = self.app.query_one(Body)
        body_widget.scroll_down()

    def action_show_readme(self):
        body_widget: Body = self.app.query_one(Body)
        body_widget.welcome()

    def action_scroll_body_up(self):
        body_widget = self.app.query_one(Body)
        body_widget.scroll_up()

from textual.widgets import Static, Label
from xnoted.utils.database import Database
from xnoted.utils.constants import TASK_HEADER_ID


class TaskHeader(Static):
    BORDER_TITLE = "Project"

    def __init__(self, database: Database):
        super().__init__()
        self.database = database

    def compose(self):
        yield Label(self.database.project_name, id=TASK_HEADER_ID)

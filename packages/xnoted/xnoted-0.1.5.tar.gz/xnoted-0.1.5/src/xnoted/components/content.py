from textual.widgets import Static
from xnoted.components.body import Body
from xnoted.components.taskContainer import TaskContainer
from textual.containers import Vertical
from xnoted.utils.database import Database

from xnoted.components.taskHeader import TaskHeader


class Content(Static):
    def __init__(self, database: Database):
        super().__init__()
        self.database = database

    def compose(self):
        yield Vertical(
            TaskHeader(database=self.database),
            TaskContainer(database=self.database),
        )
        yield Body(database=self.database)

    def on_mount(self) -> None:
        # Show welcome screen
        if self.database.is_empty():
            body_widget: Body = self.app.query_one(Body)
            body_widget.welcome()

class ContentWrapper(Static):
    def __init__(self, database: Database):
        super().__init__()
        self.database = database

    def compose(self):
        yield Content(database=self.database)

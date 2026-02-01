from textual.containers import Vertical
from textual.screen import ModalScreen
from xnoted.components.sidebar import Form
from xnoted.utils.database import Database


class CreateTaskModal(ModalScreen):
    def __init__(
        self, database: Database, title="", content="", editing=False, task_id=""
    ):
        super().__init__(id="createTaskModal")
        self.title = title
        self.content = content
        self.editing = editing
        self.task_id = task_id
        self.database = database

    TITLE = "Modal Title"
    SUB_TITLE = "Modal Title"
    BINDINGS = [
        ("escape", "close", "Close modal"),
    ]

    def compose(self):
        yield Vertical(
            Form(
                database=self.database,
                title=self.title,
                content=self.content,
                editing=self.editing,
                task_id=self.task_id,
            ),
            id="modal-content",
        )

    def action_close(self):
        self.app.pop_screen()

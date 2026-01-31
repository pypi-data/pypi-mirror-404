from textual.widgets import Static, Label
from textual.reactive import reactive
from xnoted.utils.database import Database

class FooterLabel(Static):    
    is_searching = reactive(False)
    
    def __init__(self, database: Database):
        super().__init__()
        self.database = database
    
    def compose(self):
        yield Label(
            "Move down: j | Move up: k | Edit task: e | Delete task: d | "
            "Previous status: ← | Next status: → | Body down: Ctrl+d | "
            "Body up: Ctrl+u | Search: /",
            id="help-text"
        )
    

from textual import on
from textual.app import ComposeResult
from textual.widgets import Select, Static

LINES = """I must not fear.
Fear is the mind-killer.
Fear is the little-death that brings total obliteration.
I will face my fear.
I will permit it to pass over me and through me.""".splitlines()


class Projects(Static):
    def __init__(self):
        super().__init__()

    def compose(self) -> ComposeResult:
        yield Select((line, line) for line in LINES)

    @on(Select.Changed)
    def select_changed(self, event: Select.Changed) -> None:
        self.title = str(event.value)

import uuid
from textual.containers import Container
from textual.widgets import Input, TextArea, RadioSet, RadioButton, Label
from textual.app import ComposeResult
from xnoted.utils.database import Database
from xnoted.components.tasks import Tasks
from xnoted.utils.constants import (
    PROJECT_TITLE_ID,
    PROJECT_DESCRIPTION_ID,
    TASKS_ID,
    TASK_HEADER_ID,
    PROJECT_TASK_TYPE_ID,
    PROJECT_TYPE_ID,
    PROJECT_OTHER_TYPE_ID,
)


class InputContainer(Input):
    BORDER_TITLE = "Project Title"

    def __init__(self):
        super().__init__(id=PROJECT_TITLE_ID)


class ContentContainer(TextArea):
    BORDER_TITLE = "Content"

    def __init__(self):
        super().__init__(
            id=PROJECT_DESCRIPTION_ID,
        )


class ProjectTypeContainer(RadioSet):
    BORDER_TITLE = "Type"

    def __init__(self):
        super().__init__(id=PROJECT_TYPE_ID)

    def compose(self):
        yield RadioButton("Task", id=PROJECT_TASK_TYPE_ID)
        yield RadioButton("Other", id=PROJECT_OTHER_TYPE_ID)


class CreateProjectForm(Container):
    def __init__(
        self,
        database: Database,
        title="",
        description="",
        project_id="",
        project_type=PROJECT_TASK_TYPE_ID,
        editing=False,
    ):
        super().__init__()
        self.database = database
        self.title = title
        self.description = description
        self.project_type = project_type
        self.editing = title
        self.project_id = project_id

    BINDINGS = [
        ("ctrl+s", "submit", "Save project form"),
    ]

    def on_mount(self):
        input_widget = self.query_one(f"#{PROJECT_TITLE_ID}")
        # project_type_widget = self.query_one(f"#{PROJECT_TYPE_ID}")
        project_descripton_widget = self.query_one(f"#{PROJECT_DESCRIPTION_ID}")
        input_widget.value = self.title
        # project_type_widget.value = self.project_type
        project_descripton_widget.text = self.description

        match self.project_type:
            case "task":
                radio_button_widget: RadioButton = self.query_one(
                    f"#{PROJECT_TASK_TYPE_ID}"
                )
                radio_button_widget.value = True
                return
            case _:
                radio_button_widget: RadioButton = self.query_one(
                    f"#{PROJECT_OTHER_TYPE_ID}"
                )
                radio_button_widget.value = True
                return

    def compose(self) -> ComposeResult:
        yield InputContainer()
        yield ContentContainer()
        yield ProjectTypeContainer()

    def handle_save_new(self) -> None:
        title = self.query_one(f"#{PROJECT_TITLE_ID}").value
        description = self.query_one(f"#{PROJECT_DESCRIPTION_ID}").text
        project_type: RadioSet = self.query_one(f"#{PROJECT_TYPE_ID}")

        # Only title is required
        if title:
            data = {
                "id": str(uuid.uuid4()),
                "title": title,
                "description": description,
                "type": project_type.pressed_button.id
                if project_type.pressed_button
                else PROJECT_TASK_TYPE_ID,
            }
            self.database.save_project(data)

    def handle_edit(self) -> None:
        updated_title = self.query_one(f"#{PROJECT_TITLE_ID}").value
        updated_description = self.query_one(f"#{PROJECT_DESCRIPTION_ID}").text
        project_type: RadioSet = self.query_one(f"#{PROJECT_TYPE_ID}")

        data = {
            "title": updated_title,
            "description": updated_description,
            "type": project_type.pressed_button.id
            if project_type.pressed_button
            else PROJECT_TASK_TYPE_ID,
        }

        self.database.update_project(self.project_id, data)
        tasks_widget: Tasks = self.app.query_one(f"#{TASKS_ID}")

        task_header_label_widget: Label = self.app.query_one(f"#{TASK_HEADER_ID}")
        task_header_label_widget.update("self.database.project_name")

        # Refresh only if task type is selected
        if self.database.project_type == project_type.pressed_button.id:
            tasks_widget.refresh_tasks()
            task_header_label_widget: Label = self.app.query_one(f"#{TASK_HEADER_ID}")
            task_header_label_widget.update(self.database.project_name)

    def action_submit(self) -> None:
        if self.editing:
            self.handle_edit()
        else:
            self.handle_save_new()

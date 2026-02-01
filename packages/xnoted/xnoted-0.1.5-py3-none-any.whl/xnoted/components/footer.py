from textual.widgets import Static
from xnoted.utils.database import Database
from textual.reactive import reactive
from xnoted.components.footerLabel import FooterLabel
from xnoted.components.footerSearch import FooterSearch
from xnoted.utils.constants import FOOTER_ID


class Footer(Static):
    is_searching = reactive(False, recompose=True)

    def __init__(self, database: Database):
        super().__init__(id=FOOTER_ID)
        self.database = database

    def compose(self):
        if not self.is_searching:
            yield FooterLabel(database=self.database)
        else:
            yield FooterSearch(database=self.database, toggle_search = self.toggle_search)
        
    def toggle_search(self):
        """Toggle between help text and search input"""
        self.is_searching = not self.is_searching

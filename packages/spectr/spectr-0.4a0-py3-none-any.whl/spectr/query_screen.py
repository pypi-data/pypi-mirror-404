from textual.app import ComposeResult
from textual.containers import Grid
from textual.screen import ModalScreen
from textual.widgets import Input, Label


class QueryScreen(ModalScreen[str]):
    BINDINGS = []

    CSS_PATH = "query_screen.tcss"

    def __init__(
        self,
        user_query: str,
        name: str | None = None,
        id: str | None = None,  # noqa: A002
        classes: str | None = None,
    ) -> None:
        super().__init__(name, id, classes)
        self._user_query = user_query

    def compose(self) -> ComposeResult:
        with Grid(id="query-layout"):
            yield Label("SELECT * FROM buffer_metadata WHERE", classes="query-text")
            yield Input(
                self._user_query,
                placeholder="compression_time = 1 AND compression_frq = 2",
                validate_on=("submitted",),
                validators=[],
                id="query-input",
            )
            yield Label("ORDER BY process DESC", classes="query-text")

    def on_input_submitted(self, event):
        self.dismiss(event.value)

    def action_clear(self):
        input_item = self.query_one(Input)
        input_item.value = ""

    def key_escape(self):
        input_item = self.query_one(Input)
        self.dismiss(input_item.value)

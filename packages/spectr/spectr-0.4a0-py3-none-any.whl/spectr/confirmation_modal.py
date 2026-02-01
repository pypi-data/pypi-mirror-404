from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Center, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Label


class ConfirmationModal(ModalScreen[bool]):
    CSS_PATH = "confirmation_modal.tcss"
    BINDINGS = [
        Binding("y", "yes", "Yes", show=True),
        Binding("n", "no", "No", show=True),
    ]

    def __init__(self, header: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._header = header

    def compose(self) -> ComposeResult:
        with Vertical(id="confirmation-modal-layout"):
            with Center():
                yield Label(self._header, id="confirmation-label")
            with Center():  # noqa
                with Horizontal(id="confirmation-buttons"):
                    yield Button("Yes", variant="success", id="yes")
                    yield Button("No", variant="error", id="no")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        match event.button.id:
            case "yes":
                self.dismiss(True)
            case "no":
                self.dismiss(False)

    def action_yes(self):
        self.dismiss(True)

    def action_no(self):
        self.dismiss(False)

from enum import Enum

from qass.tools.analyzer.buffer_metadata_cache import BufferMetadata
from textual.app import ComposeResult
from textual.containers import Grid, VerticalScroll
from textual.events import Resize
from textual.reactive import reactive
from textual.widgets import Static

from spectr.types import BufferMetadataProperty


class FileStats(VerticalScroll):
    """Widget to display statistics about the selected file."""

    buffer_metadata: reactive[BufferMetadata | None] = reactive(None)

    MEDIUM_COLUMN_WIDTH_SWITCH = 80
    LARGE_COLUMN_WIDTH_SWITCH = 150

    def __init__(self, attributes: list[BufferMetadataProperty], *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.attributes = attributes

    def on_mount(self):
        self.border_title = "Metadata"

    def compose(self) -> ComposeResult:
        with Grid(id="metadata-grid", classes="wide"):
            for prop in self.attributes:
                yield Static(f"{prop}", id=f"label-{prop}")
                yield Static("-", id=f"value-{prop}")

    def watch_buffer_metadata(self, _, new_metadata: BufferMetadata | None):
        """Update the displayed statistics."""
        for prop in self.attributes:
            widget = self.query_one(f"#value-{prop}", Static)
            if new_metadata is None:
                widget.update("-")
                continue
            value = getattr(new_metadata, prop)
            if isinstance(value, Enum):
                value = value.name
            if value is None:
                value = "-"
            widget.update(str(value))

    def on_resize(self, event: Resize) -> None:
        grid = self.query_one("#metadata-grid", Grid)
        if event.size.width < self.MEDIUM_COLUMN_WIDTH_SWITCH:
            grid.remove_class("wide")
            grid.remove_class("medium")
            grid.add_class("narrow")
        elif event.size.width < self.LARGE_COLUMN_WIDTH_SWITCH:
            grid.remove_class("wide")
            grid.add_class("medium")
            grid.remove_class("narrow")
        else:
            grid.add_class("wide")
            grid.remove_class("narrow")
            grid.remove_class("medium")

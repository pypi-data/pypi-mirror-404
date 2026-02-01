import shutil
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from qass.tools.analyzer.buffer_metadata_cache import (
    BufferMetadata,
    BufferMetadataCache,
)
from sqlalchemy import select, text
from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.driver import Driver
from textual.reactive import reactive
from textual.types import CSSPathType
from textual.widgets import DataTable, Footer, Header, Static
from textual.worker import NoActiveWorker, Worker, WorkerState, get_current_worker

from spectr.config import Config
from spectr.copy_screen import CopyConflictResolution, CopyTargetScreen, CopyTask
from spectr.types import DownsamplingAlgorithm

from .confirmation_modal import ConfirmationModal
from .downsample import largest_triangle_three_buckets, maximum_bucket
from .file_preview import FilePreview
from .file_stats import FileStats
from .file_table import FileTable
from .query_screen import QueryScreen


def get_downsample_func(downsampling: DownsamplingAlgorithm) -> Callable:
    match downsampling:
        case "lttb":
            return largest_triangle_three_buckets
        case "max_bucket":
            return maximum_bucket
    raise LookupError(f"Invalid downsampling method: {downsampling}")


@dataclass
class Progress:
    current: int
    total: int

    @property
    def percentage(self) -> float:
        return (self.current / self.total) * 100 if self.total > 0 else 0


class ProgressIndicator(Static):
    progress: reactive[Progress | None] = reactive(None)

    def watch_progress(self, _, new_progress: Progress | None) -> None:
        if new_progress is None:
            self.update("")
            self.remove_class("visible")
            return
        self.add_class("visible")
        self.update(f"Copying: {round(new_progress.percentage, 2)}%")


class Spectr(App):
    CSS_PATH = "app.tcss"

    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
        Binding("/", "open_query", "Filter", show=True),
        Binding("c", "copy_selection", "Copy Selection", show=True),
        Binding("x", "cancel_copy", "Cancel Copy", show=True),
        Binding("e", "expand_widget", "Expand", show=True),
    ]

    user_filter = reactive("")
    copy_worker: reactive[Worker | None] = reactive(None)

    def __init__(
        self,
        cache: BufferMetadataCache,
        config: Config,
        driver_class: type[Driver] | None = None,
        css_path: CSSPathType | None = None,
        watch_css: bool = False,
        ansi_color: bool = False,
    ):
        super().__init__(driver_class, css_path, watch_css, ansi_color)
        self.cache = cache
        self.config = config
        self.theme = "catppuccin-mocha"

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            yield FileTable(id="file-table", classes="panel")
            with Vertical(id="right-panel"):
                yield FileStats(
                    attributes=self.config.stats.attributes, id="stats", classes="panel"
                )
                yield FilePreview(
                    buffer_cls=self.cache.Buffer_cls,
                    marker=self.config.plot.marker,
                    displayed_datapoints=self.config.plot.displayed_datapoints,
                    downsample_func=get_downsample_func(self.config.plot.downsampling),
                    id="file-preview",
                    classes="panel",
                )

        with Horizontal(id="footer-container"):
            with Horizontal(id="footer-inner", classes="full-width"):
                yield Footer()
            yield ProgressIndicator("100%", id="label")

    def watch_user_filter(self, old, new) -> None:
        """Callback function for the reactive `user_filter` property"""
        if old == new:
            return
        self.load_files()

    def watch_copy_worker(self, *_) -> None:
        self.refresh_bindings()

    def check_action(self, action: str, _: tuple) -> bool:  # type: ignore
        match action:
            case "copy_selection":
                return self.copy_worker is None
            case "cancel_copy":
                return self.copy_worker is not None
            case "expand_widget":
                preview = self.query_one(FilePreview)
                table = self.query_one(FileTable)
                stats = self.query_one(FileStats)
                widgets = (preview, table, stats)
                return any(w.has_focus_within for w in widgets)
        return True

    def action_quit(self):
        if self.copy_worker is not None:

            def callback(q: bool):
                if q:
                    self.app.exit(0)

            self.push_screen(
                ConfirmationModal(
                    "Copy operation still running, do you really want to quit?"
                ),
                callback,
            )  # type: ignore
            return
        self.app.exit(0)

    def action_open_query(self) -> None:
        """Open the query modal screen to update the user filter"""

        def callback(user_filter: str) -> None:
            self.user_filter = user_filter

        self.push_screen(QueryScreen(self.user_filter, classes="modal-screen"), callback)  # type: ignore

    def action_copy_selection(self) -> None:
        bms = self.get_filtered_metadata()
        files = [Path(bm.filepath) for bm in bms]

        def callback(response: CopyTask):
            target_folder, resolution_strategy = response
            if (
                target_folder is None
                or resolution_strategy is None
                or resolution_strategy == CopyConflictResolution.ABORT
            ):
                if resolution_strategy == CopyConflictResolution.ABORT:
                    self.notify("Aborted Copy Operation")
                return
            self.copy_worker = self.copy_files(files, target_folder, resolution_strategy)
            # TODO: display indicator somewhere and somehow

        self.push_screen(CopyTargetScreen(files=files), callback)  # type: ignore

    def action_cancel_copy(self):
        if self.copy_worker is None:
            self.refresh_bindings()  # TODO: this should not be necessary
            return
        self.copy_worker.cancel()

    def action_expand_widget(self):
        preview = self.query_one(FilePreview)
        table = self.query_one(FileTable)
        stats = self.query_one(FileStats)
        widgets = (preview, table, stats)
        # Check if one is maximized already (revert in this case)
        if any(w.has_class("maximized") for w in widgets):
            for w in widgets:
                w.remove_class("maximized")
                w.remove_class("hidden")
            return

        in_focus = list(filter(lambda w: w.has_focus_within, widgets))
        if len(in_focus) != 1:
            self.notify("Nothing in focus", severity="error")
            return
        (in_focus_widget,) = in_focus
        in_focus_widget.add_class("maximized")
        for w in widgets:
            if w == in_focus_widget:
                continue
            w.add_class("hidden")

    @work(name="copy_files", exclusive=True, thread=True)
    def copy_files(
        self,
        files: list[Path],
        target_path: Path,
        resolution_strategy: CopyConflictResolution,
    ):
        if not target_path.exists():
            raise LookupError("Target folder does not exist")
        try:
            for i, file in enumerate(files):
                worker = get_current_worker()

                target_file = target_path / file.name
                if target_file.exists():
                    match resolution_strategy:
                        case CopyConflictResolution.SKIP:
                            continue
                        case CopyConflictResolution.OVERWRITE:
                            if target_file == file:
                                self.notify(
                                    "Trying to replace a file with itself, aborting",
                                    severity="error",
                                )
                                raise Exception
                            target_file.unlink()
                shutil.copyfile(file, target_file)
                if worker.is_cancelled:
                    return (i + 1, target_path)
                self.call_from_thread(
                    self._update_progress, Progress(current=i + 1, total=len(files))
                )
        except NoActiveWorker:
            return (i, target_path)
        except Exception:
            return (i, target_path)
        return (len(files), target_path)

    def _update_progress(self, progress: Progress | None):
        progress_indicator = self.query_one(ProgressIndicator)
        progress_indicator.progress = progress

    def on_mount(self) -> None:
        table = self.query_one(FileTable)
        table.add_columns(*self.config.table.columns)
        table.cursor_type = "row"
        table.zebra_stripes = True
        self.load_files()

    def get_metadata_query(self):
        query = "SELECT * FROM buffer_metadata"
        if self.user_filter == "":
            pass
        else:
            query = f"{query} WHERE {self.user_filter}"
        return (
            f"{query} ORDER BY {self.config.table.sort.attribute} "
            f"{self.config.table.sort.order}"
        )

    def get_filtered_metadata(self) -> list[BufferMetadata]:
        query = self.get_metadata_query()
        try:
            bms: list[BufferMetadata] = self.cache.get_matching_metadata(
                select(BufferMetadata).from_statement(text(query))  # type: ignore
            )
        except Exception as e:
            self.notify(f"Invalid Query {e}", severity="error")
            return []
        return bms

    def on_data_table_row_highlighted(self, event: FileTable.RowHighlighted):
        table = self.query_one(FileTable)
        table.border_title = f"{event.cursor_row + 1}/{table.row_count}"

    @work
    async def load_files(self) -> None:
        table = self.query_one(FileTable)
        table.loading = True
        table.clear()
        bms = self.get_filtered_metadata()
        self.notify(f"Found {len(bms)} results")
        for bm in bms:
            table.add_row(
                # TODO: I do not like this very much...
                *(getattr(bm, col) for col in self.config.table.columns),
                key=str(bm.id),
            )
        table.loading = False

    async def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        bm = self.cache.get_matching_metadata(
            select(BufferMetadata).filter(BufferMetadata.id == event.row_key.value)
        )
        if len(bm) != 1:
            self.notify(
                "Query returned more than one matching metadata for table entry\n",
                severity="error",
            )
            return
        (bm,) = bm
        self.selected_file = bm
        stats = self.query_one(FileStats)
        stats.buffer_metadata = bm
        plot = self.query_one(FilePreview)
        plot.loading = True
        plot.preview_file(Path(bm.filepath))

    def handle_copy_worker_state_change(self, event: Worker.StateChanged) -> None:
        match event.state:
            case WorkerState.SUCCESS:
                if not isinstance(event.worker.result, tuple):
                    msg = "Finished copying with malformed result"
                    severity = "warning"
                else:
                    n_files, target_path = event.worker.result
                    msg = f"Finished copying {n_files} files to\n{target_path}"
                    severity = "information"
            case WorkerState.ERROR:
                msg = f"Copy failed: {event.worker.error}"
                severity = "error"
            case WorkerState.CANCELLED:
                progress = self.query_one(ProgressIndicator).progress
                if progress is None:
                    msg = "Aborted copy operation"
                else:
                    msg = f"Aborted copying after {progress.current} files"
                severity = "information"
            case _:
                return
        self._update_progress(None)
        self.copy_worker = None
        self.notify(msg, severity=severity)

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        match event.worker.name:
            case "copy_files":
                return self.handle_copy_worker_state_change(event)

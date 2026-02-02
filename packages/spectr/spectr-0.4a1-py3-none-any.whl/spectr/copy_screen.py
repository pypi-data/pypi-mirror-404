from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import TypeAlias

from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Center, Horizontal, Vertical
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.widget import Widget
from textual.widgets import Button, DirectoryTree, Footer, Header, Label, Static

from spectr.file_table import FileTable


class CopyConflictResolution(Enum):
    OVERWRITE = 0
    SKIP = 1
    ABORT = 2


CopyTask: TypeAlias = tuple[Path | None, None] | tuple[Path, CopyConflictResolution]


@dataclass
class CopyPreview:
    files_to_copy: list[Path]
    total_size: int
    target_folder: Path
    existing_files_in_target: int
    existing_folders_in_target: int
    conflicts: list[Path]

    @property
    def has_conflicts(self) -> bool:
        return len(self.conflicts) > 0

    @property
    def target_is_empty(self) -> bool:
        return self.existing_files_in_target == 0 and self.existing_folders_in_target == 0


class FilteredDirectoryTree(DirectoryTree):
    BINDINGS = [
        Binding("j", "cursor_down", "Scroll Down", show=False),
        Binding("k", "cursor_up", "Scroll Up", show=False),
        Binding("J", "page_down", "Page Down", show=False),
        Binding("K", "page_up", "Page Up", show=False),
        Binding("G", "scroll_end", "Scroll Bottom", show=False),
        Binding("g", "scroll_home", "Scroll Top", show=False),
    ]

    def filter_paths(self, paths: Iterable[Path]) -> Iterable[Path]:
        return filter(lambda p: p.is_dir() and not p.name.startswith("."), paths)


class CopySummary(Widget):
    preview: reactive[CopyPreview | None] = reactive(None)

    def compose(self) -> ComposeResult:
        with Vertical(classes="panel", id="summary-container"):
            yield Static("No folder selected", id="target-folder")
            yield Static("", id="file-count")
            yield Static("", id="target-status")
            yield Static("", id="conflicts")
        yield FileTable(show_header=False, id="copy-file-table", classes="panel")

    def watch_preview(self, _, new_preview: CopyPreview) -> None:
        target_folder = self.query_one("#target-folder", Static)
        file_count = self.query_one("#file-count", Static)
        target_status = self.query_one("#target-status", Static)
        conflicts = self.query_one("#conflicts", Static)
        if new_preview is None:
            target_folder.update("No folder selected")
            file_count.update("")
            target_status.update("")
            conflicts.update("")
            return

        target_folder.update(f"Target: [b]{new_preview.target_folder}[/b]")
        file_count.update(
            f"Files to copy: [b]{len(new_preview.files_to_copy)}[/b] "
            f"({round(new_preview.total_size / 1024**2, 3)} MB)"
        )
        if new_preview.target_is_empty:
            target_status.update("[dim]Target folder: Empty[/dim]")
        else:
            target_status.update(
                "Target folder: [yellow]"
                f"{new_preview.existing_files_in_target} files | "
                f"{new_preview.existing_folders_in_target} folders[/yellow]"
            )
        if new_preview.has_conflicts:
            conflicts.update(
                f"[b $warning]Conflicts: {len(new_preview.conflicts)}[/b $warning]"
            )
        else:
            conflicts.update("")

        self.update_table()

    def on_mount(self):
        table = self.query_one(FileTable)
        table.add_columns("file")
        table.border_title = "Conflicting Files"
        table.border_subtitle = "Foo"

    @work(exclusive=True)
    async def update_table(self):
        table = self.query_one(FileTable)
        table.clear()
        if self.preview is None:
            return
        rows = ((p.name,) for p in self.preview.conflicts)
        table.add_rows(rows)


class CopyConflictResolutionScreen(ModalScreen[CopyConflictResolution]):
    CSS_PATH = "conflict_resolution_screen.tcss"

    def __init__(self, conflicts: list[Path], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.conflicts = conflicts

    BINDINGS = [
        Binding("s", "skip", "Skip", show=True),
        Binding("o", "overwrite", "Overwrite", show=True),
        Binding("a", "abort", "Abort", show=True),
    ]

    def compose(self) -> ComposeResult:
        with Vertical():
            with Center():
                yield Label(
                    f"Found {len(self.conflicts)} conflicting files", id="conflict-label"
                )
            with Center():  # noqa
                with Horizontal(id="conflict-buttons"):
                    yield Button("Skip", id="skip", variant="primary")
                    yield Button("Overwrite", id="overwrite", variant="warning")
                    yield Button("Abort", id="abort", variant="default")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        match event.button.id:
            case "skip":
                self.dismiss(CopyConflictResolution.SKIP)
            case "overwrite":
                self.dismiss(CopyConflictResolution.OVERWRITE)
            case "abort":
                self.dismiss(CopyConflictResolution.ABORT)
            case _:
                self.dismiss(CopyConflictResolution.ABORT)

    def action_skip(self):
        self.dismiss(CopyConflictResolution.SKIP)

    def action_overwrite(self):
        self.dismiss(CopyConflictResolution.OVERWRITE)

    def action_abort(self):
        self.dismiss(CopyConflictResolution.ABORT)


class CopyTargetScreen(ModalScreen[CopyTask]):
    CSS_PATH = "copy_screen.tcss"

    BINDINGS = [
        # TODO: only display once target folder is selected
        Binding("c", "copy", "Copy", show=True),
    ]

    target_folder: reactive[Path | None] = reactive(None)

    def __init__(
        self,
        files: list[Path],
        name: str | None = None,
        id: str | None = None,  # noqa: A002
        classes: str | None = None,
    ) -> None:
        super().__init__(name, id, classes)
        self.files = list(files)
        self.filenames = {f.name for f in self.files}
        self._cum_file_size = sum(f.stat().st_size for f in self.files)
        self._target_folder = None

    def compose(self) -> ComposeResult:
        yield Header()
        yield Horizontal(
            FilteredDirectoryTree("/", id="directory-tree", classes="panel"),
            CopySummary(),
            id="horizontal",
        )
        yield Footer()

    async def on_mount(self):
        self.query_one(FilteredDirectoryTree).border_title = "Target Folder"

    async def watch_target_folder(self, old: Path | None, new: Path | None) -> None:
        if old == new:
            return
        copy_summary = self.query_one(CopySummary)
        if new is None:
            copy_summary.preview = None
            return
        target_folder_files = list(filter(lambda entry: entry.is_file(), new.glob("*")))
        target_folder_filenames = {f.name for f in target_folder_files}
        file_conflicts = [
            new / f for f in self.filenames.intersection(target_folder_filenames)
        ]
        preview = CopyPreview(
            files_to_copy=self.files,
            total_size=self._cum_file_size,
            target_folder=new,
            existing_files_in_target=len(target_folder_files),
            existing_folders_in_target=len([f for f in new.glob("*") if f.is_dir()]),
            conflicts=file_conflicts,
        )
        copy_summary.preview = preview

    def key_escape(self):
        self.dismiss((None, None))

    def on_directory_tree_directory_selected(
        self, selection: DirectoryTree.DirectorySelected
    ):
        assert selection.path.is_dir()
        self.target_folder = selection.path
        # TODO: check amount of space left
        # TODO: check if there are files already there

    def action_quit(self):
        exit(0)

    def action_copy(self):
        summary = self.query_one(CopySummary)
        if summary.preview is None:
            self.notify(
                "Please select a folder", title="Invalid Selection", severity="error"
            )
            return
        if summary.preview.has_conflicts:
            # TODO: open modal

            def callback(resolution: CopyConflictResolution):
                assert summary.preview is not None
                self.dismiss((summary.preview.target_folder, resolution))

            self.app.push_screen(
                CopyConflictResolutionScreen(summary.preview.conflicts), callback
            )  # type: ignore
            return
        self.dismiss((summary.preview.target_folder, CopyConflictResolution.SKIP))

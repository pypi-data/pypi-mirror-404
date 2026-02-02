import logging
from collections.abc import Callable
from pathlib import Path

import numpy as np
import numpy.typing as npt
from textual import work
from textual.worker import Worker, WorkerState
from textual_plotext import PlotextPlot

from .downsample import largest_triangle_three_buckets

logger = logging.getLogger(__name__)


class FilePreview(PlotextPlot):
    """Widget to display file preview using plotext."""

    can_focus = True

    def __init__(
        self,
        buffer_cls,
        *,
        marker: str = "braille",
        displayed_datapoints: int = 10_000,
        downsample_func: Callable = largest_triangle_three_buckets,
        name: str | None = None,
        id: str | None = None,  # noqa: A002
        classes: str | None = None,
        disabled: bool = False,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes, disabled=disabled)
        self._buffer_cls = buffer_cls
        self._marker = marker
        self._displayed_datapoints = displayed_datapoints
        self._downsample_func = downsample_func
        self._title = "Plotext Plot"
        self._preview_file = None

    def on_mount(self):
        self.border_title = "Preview"

    @work(name="preview", exclusive=True, thread=True)
    def preview_file(self, file_path: Path):
        """Update the preview visualization."""
        self._preview_file = file_path
        logger.debug(f"Previewing {file_path}")
        try:
            with self._buffer_cls(self._preview_file) as b:
                y = b.get_data() * b.ref_energy
                if not isinstance(y, np.ndarray):
                    raise ValueError("Invalid return while loading file")

                if y.ndim == 2:
                    y = y.sum(axis=1)
                compression = int(len(y) / self._displayed_datapoints)
                if compression > 1:
                    x, y = self._downsample_func(y, compression_factor=compression)
                else:
                    x = np.arange(len(y))

                x = x * b.spec_duration / 1e6
                title = file_path.name
                self.replot(x, y, title)
        except Exception as e:
            self._preview_file = None
            self.notify(
                f"Error while loading file preview data for {file_path}\n{e}",
                severity="error",
            )
            self.replot(np.array([]), np.array([]), "")

    def replot(self, x: npt.NDArray, y: npt.NDArray, title: str):
        self.plt.clear_figure()
        self.plt.xlabel("Time [ms]")
        self.plt.ylabel("Amplitude")
        if self._preview_file is None or y is None or x is None:
            logger.info("Preview file, preview data or x-data is None, unable to preview")
            self.refresh(layout=True)
            return
        self.plt.plot(
            x.tolist(),
            y.tolist(),
            xside="lower",
            yside="left",
            marker=self._marker,
        )
        self.plt.title(title)
        self.refresh(layout=True)

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        if event.worker.name != "preview":
            return
        match event.state:
            case WorkerState.PENDING:
                pass
            case WorkerState.SUCCESS | WorkerState.ERROR | WorkerState.CANCELLED:
                self.loading = False

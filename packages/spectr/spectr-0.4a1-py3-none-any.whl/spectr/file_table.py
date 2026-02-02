from textual.binding import Binding
from textual.widgets import DataTable


class FileTable(DataTable):
    BINDINGS = [
        Binding("j", "cursor_down", "Scroll Down", show=False),
        Binding("k", "cursor_up", "Scroll Up", show=False),
        Binding("J", "page_down", "Scroll Down", show=False),
        Binding("K", "page_up", "Scroll Up", show=False),
        Binding("$", "scroll_end", "Scroll last column", show=False),
        Binding("0", "scroll_home", "Scroll first column", show=False),
        Binding("h", "cursor_left", "Scroll Left", show=False),
        Binding("l", "cursor_right", "Scroll Right", show=False),
        Binding("G", "scroll_bottom", "Scroll Bottom", show=False),
        # TODO: implement the possibility to use `gg` as in vim
        Binding("g", "scroll_top", "Scroll Top", show=False),
    ]

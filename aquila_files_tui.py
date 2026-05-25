import asyncio
import os
import subprocess
from pathlib import Path
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Static, Button, Label, ListView, ListItem
from textual.binding import Binding
from textual import on, work

BG_MAIN    = "#0b0f19"
BG_CARD    = "#111625"
BG_GLASS   = "#181E2E"
BG_HOVER   = "#1d243a"
COLOR_BLUE = "#8DB4FF"
COLOR_BLUE2= "#A7BDF5"
COLOR_TEXT = "#E6ECFF"
COLOR_MUTED= "#AAB6D6"
COLOR_GREEN= "#4ade80"
COLOR_RED  = "#f87171"
COLOR_ROSE = "#D9B8CC"

DIR_ICON = "📁"
FILE_ICON= "📄"
EXEC_ICON= "⚡"
IMG_ICON = "🖼"
MUSIC_ICON="🎵"
CODE_ICON = "💻"
ARCH_ICON = "📦"

EXT_MAP = {
    ".py": CODE_ICON, ".js": CODE_ICON, ".ts": CODE_ICON, ".html": CODE_ICON,
    ".css": CODE_ICON, ".c": CODE_ICON, ".cpp": CODE_ICON, ".h": CODE_ICON,
    ".java": CODE_ICON, ".rs": CODE_ICON, ".go": CODE_ICON,
    ".jpg": IMG_ICON, ".jpeg": IMG_ICON, ".png": IMG_ICON, ".gif": IMG_ICON,
    ".webp": IMG_ICON, ".svg": IMG_ICON,
    ".mp3": MUSIC_ICON, ".wav": MUSIC_ICON, ".flac": MUSIC_ICON, ".ogg": MUSIC_ICON,
    ".zip": ARCH_ICON, ".tar": ARCH_ICON, ".gz": ARCH_ICON, ".rar": ARCH_ICON,
    ".7z": ARCH_ICON, ".bz2": ARCH_ICON,
}

CSS = f"""
Screen {{ background: {BG_MAIN}; align: center middle; }}
#frame {{ width: 86; height: 28; border: round {COLOR_BLUE}; background: {BG_CARD}; layout: vertical; padding: 1; }}
#header {{ height: 3; layout: horizontal; align: left middle; margin-bottom: 1; }}
#path-label {{ width: 1fr; color: {COLOR_BLUE2}; text-style: bold; background: {BG_GLASS}; padding: 0 1; }}
#nav-back {{ height: 3; width: 8; background: {BG_GLASS}; color: {COLOR_BLUE}; border: none; text-style: bold; }}
#nav-up {{ height: 3; width: 8; background: {BG_GLASS}; color: {COLOR_BLUE}; border: none; text-style: bold; }}
#file-list {{ height: 1fr; background: transparent; border: none; }}
FileItem {{ height: 2; background: {BG_GLASS}; border: round {BG_GLASS}; margin-bottom: 1; padding: 0 1; layout: horizontal; align: left middle; }}
FileItem:hover {{ background: {BG_HOVER}; border: round {COLOR_BLUE}; }}
.file-icon {{ width: 4; color: {COLOR_BLUE}; }}
.file-name {{ width: 1fr; color: {COLOR_TEXT}; text-style: bold; }}
.file-size {{ width: 10; color: {COLOR_MUTED}; text-align: right; }}
.file-mtime {{ width: 14; color: {COLOR_MUTED}; text-align: right; }}
#exit-btn {{ width: 100%; height: 3; background: {BG_GLASS}; color: {COLOR_RED}; border: none; text-style: bold; dock: bottom; }}
#exit-btn:hover {{ background: {COLOR_RED}; color: {BG_MAIN}; }}
"""

class FileItem(Static):
    def __init__(self, path: Path, icon: str, display_name: str, size_str: str, mtime_str: str, is_dir: bool):
        super().__init__()
        self.path = path
        self.is_dir = is_dir
        self.display_name = display_name
        self.size_str = size_str
        self.mtime_str = mtime_str
        self.icon = icon

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Label(self.icon, classes="file-icon")
            yield Label(self.display_name, classes="file-name")
            yield Label(self.size_str, classes="file-size")
            yield Label(self.mtime_str, classes="file-mtime")

class AquilaFilesTUI(App):
    CSS = CSS
    BINDINGS = [Binding("q", "quit", "Sair"), Binding("escape", "go_up", "Voltar")]

    def __init__(self, start_dir: str | None = None, **kw):
        super().__init__(**kw)
        self._current = Path(start_dir or os.path.expanduser("~"))
        self._history: list[Path] = []

    def compose(self) -> ComposeResult:
        with Container(id="frame"):
            with Horizontal(id="header"):
                yield Button("←", id="nav-back", classes="ctrl-btn")
                yield Button("↑", id="nav-up", classes="ctrl-btn")
                yield Label(str(self._current), id="path-label")
            yield ListView(id="file-list")
            yield Button("SAIR", id="exit-btn")

    def on_mount(self):
        self._load_dir()

    @work(exclusive=True)
    async def _load_dir(self, path: Path | None = None):
        if path:
            if self._current != path:
                self._history.append(self._current)
            self._current = path
        loop = asyncio.get_event_loop()
        entries = await loop.run_in_executor(None, self._list_dir, self._current)
        self.query_one("#path-label", Label).update(str(self._current))
        flist = self.query_one("#file-list", ListView)
        await flist.clear()
        for entry in entries:
            await flist.append(FileItem(*entry))

    @staticmethod
    def _list_dir(path: Path):
        try:
            items = sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        except PermissionError:
            items = []
        result = []
        for p in items:
            try:
                st = p.stat()
                is_dir = p.is_dir()
                icon = DIR_ICON if is_dir else (EXEC_ICON if st.st_mode & 0o111 else EXT_MAP.get(p.suffix.lower(), FILE_ICON))
                name = p.name + "/" if is_dir else p.name
                if st.st_size < 1024:
                    sz = f"{st.st_size} B"
                elif st.st_size < 1024**2:
                    sz = f"{st.st_size/1024:.0f}K"
                else:
                    sz = f"{st.st_size/1024**2:.1f}M"
                mtime = st.st_mtime
                import datetime
                mtime_str = datetime.datetime.fromtimestamp(mtime).strftime("%d/%m %H:%M")
                result.append((p, icon, name[:28], sz, mtime_str, is_dir))
            except OSError:
                pass
        return result

    async def on_list_view_selected(self, event: ListView.Selected):
        item = event.item
        if isinstance(item, FileItem):
            if item.is_dir:
                await self._load_dir(item.path)
            else:
                subprocess.Popen(["xdg-open", str(item.path)], start_new_session=True,
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    @on(Button.Pressed)
    async def _on_btn(self, event: Button.Pressed):
        bid = event.button.id or ""
        if bid == "exit-btn":
            self.exit()
        elif bid == "nav-up":
            parent = self._current.parent
            if parent != self._current:
                self._history.append(self._current)
                await self._load_dir(parent)
        elif bid == "nav-back":
            if self._history:
                await self._load_dir(self._history.pop())

    def action_go_up(self):
        parent = self._current.parent
        if parent != self._current:
            self._history.append(self._current)
            self._load_dir(parent)

class FilesWindow:
    title = "Arquivos"
    window_id = "files"
    @staticmethod
    def create():
        return AquilaFilesTUI()

if __name__ == "__main__":
    AquilaFilesTUI().run()

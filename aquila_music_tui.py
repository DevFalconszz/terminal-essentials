import asyncio
import subprocess
import os
import signal
from pathlib import Path
from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, Horizontal
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
COLOR_LAVA = "#B8B7D9"

MUSIC_EXTS = {".mp3", ".wav", ".flac", ".ogg", ".m4a", ".wma", ".aac", ".opus"}

CSS = f"""
Screen {{ background: {BG_MAIN}; align: center middle; }}
#frame {{ width: 74; height: 26; border: round {COLOR_BLUE}; background: {BG_CARD}; layout: horizontal; }}
#sidebar {{ width: 22; height: 100%; padding: 1; layout: vertical; border-right: round {BG_GLASS}; }}
#logo {{ height: 1; content-align: center middle; color: {COLOR_BLUE}; text-style: bold; margin-bottom: 1; }}
#now-playing {{ height: 4; border: round {BG_GLASS}; background: {BG_GLASS}; content-align: center middle; color: {COLOR_BLUE2}; margin-bottom: 1; padding: 0 1; }}
.ctrl-btn {{ width: 100%; height: 3; margin-bottom: 1; background: {BG_GLASS}; color: {COLOR_BLUE}; border: none; text-style: bold; }}
.ctrl-btn:hover {{ background: {COLOR_BLUE}; color: {BG_MAIN}; }}
#spacer {{ height: 1fr; }}
#exit-btn {{ width: 100%; height: 3; background: {BG_GLASS}; color: {COLOR_RED}; border: none; text-style: bold; }}
#exit-btn:hover {{ background: {COLOR_RED}; color: {BG_MAIN}; }}
#right-panel {{ width: 1fr; height: 100%; padding: 1; layout: vertical; }}
#panel-title {{ height: 1; color: {COLOR_MUTED}; text-style: bold; margin-bottom: 1; }}
#music-list {{ height: 1fr; background: transparent; border: none; }}
MusicItem {{ height: 3; background: {BG_GLASS}; border: round {BG_GLASS}; margin-bottom: 1; padding: 0 1; layout: horizontal; align: left middle; }}
MusicItem:hover {{ background: {BG_HOVER}; border: round {COLOR_BLUE}; }}
.music-name {{ width: 1fr; color: {COLOR_TEXT}; text-style: bold; }}
.music-dir {{ width: 14; color: {COLOR_MUTED}; text-align: right; }}
"""

AUDIO_DIR = Path.home() / "Music"

class MusicItem(Static):
    def __init__(self, path: Path, name: str, parent: str, idx: int):
        super().__init__()
        self.file_path = path
        self.music_name = name
        self.music_parent = parent
        self.idx = idx

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Label(self.music_name[:32], classes="music-name")
            yield Label(self.music_parent[:12], classes="music-dir")


class AquilaMusicTUI(App):
    CSS = CSS
    BINDINGS = [Binding("q", "quit", "Sair"), Binding("space", "toggle", "Play/Stop")]

    def __init__(self, **kw):
        super().__init__(**kw)
        self._proc: subprocess.Popen | None = None
        self._tracks: list[Path] = []
        self._current_idx = -1
        self._has_player = False

    def compose(self) -> ComposeResult:
        with Container(id="frame"):
            with Vertical(id="sidebar"):
                yield Label("🎵 MÚSICA", id="logo")
                yield Label("Parado\n🎶", id="now-playing")
                yield Button("▶ PLAY", id="btn-play", classes="ctrl-btn")
                yield Button("⏹ STOP", id="btn-stop", classes="ctrl-btn")
                yield Button("PRÓXIMA", id="btn-next", classes="ctrl-btn")
                yield Button("ESCANEAR", id="btn-scan", classes="ctrl-btn")
                yield Static(id="spacer")
                yield Button("SAIR", id="exit-btn")
            with Vertical(id="right-panel"):
                yield Label("BIBLIOTECA MUSICAL", id="panel-title")
                yield ListView(id="music-list")

    def on_mount(self):
        self._has_player = bool(subprocess.run("which mpv", shell=True, capture_output=True).stdout.strip())
        self._scan_music()

    @work(exclusive=True)
    async def _scan_music(self, select_idx: int = -1):
        loop = asyncio.get_event_loop()
        tracks = await loop.run_in_executor(None, self._find_tracks)
        self._tracks = tracks
        mlist = self.query_one("#music-list", ListView)
        await mlist.clear()
        for i, path in enumerate(tracks):
            name = path.stem[:28]
            parent = path.parent.name[:10]
            await mlist.append(MusicItem(path, name, parent, i))
        if not tracks:
            self.query_one("#now-playing", Label).update("Sem músicas em\n~/Music")
        if select_idx >= 0 and mlist.children:
            mlist.index = min(select_idx, len(mlist.children) - 1)

    @staticmethod
    def _find_tracks():
        if not AUDIO_DIR.is_dir():
            return []
        result = []
        for f in sorted(AUDIO_DIR.rglob("*")):
            if f.suffix.lower() in MUSIC_EXTS:
                result.append(f)
        return result[:200]

    def _stop_playback(self):
        if self._proc:
            try:
                os.killpg(self._proc.pid, signal.SIGKILL)
            except Exception:
                pass
            try:
                self._proc.wait(0.5)
            except Exception:
                pass
            self._proc = None

    def _play_file(self, path: Path):
        self._stop_playback()
        if not self._has_player:
            self.query_one("#now-playing", Label).update("⚠ mpv não instalado")
            return
        self._proc = subprocess.Popen(
            ["mpv", "--no-video", "--really-quiet", str(path)],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        name = path.stem[:30]
        self.query_one("#now-playing", Label).update(f"▶ Tocando:\n{name}")

    @on(Button.Pressed)
    async def _on_btn(self, event: Button.Pressed):
        bid = event.button.id or ""
        if bid == "exit-btn":
            self._stop_playback()
            self.exit()
        elif bid == "btn-play":
            mlist = self.query_one("#music-list", ListView)
            if mlist.children:
                idx = mlist.index if mlist.index is not None else 0
                if idx < len(self._tracks):
                    self._current_idx = idx
                    self._play_file(self._tracks[idx])
        elif bid == "btn-stop":
            self._stop_playback()
            self.query_one("#now-playing", Label).update("Parado\n🎶")
        elif bid == "btn-next":
            if self._tracks:
                self._current_idx = (self._current_idx + 1) % len(self._tracks)
                self._play_file(self._tracks[self._current_idx])
        elif bid == "btn-scan":
            await self._scan_music()

    async def on_list_view_selected(self, event: ListView.Selected):
        item = event.item
        if isinstance(item, MusicItem):
            if item.idx < len(self._tracks):
                self._current_idx = item.idx
                self._play_file(self._tracks[item.idx])

    def action_toggle(self):
        if self._proc:
            self._stop_playback()
            self.query_one("#now-playing", Label).update("Parado\n🎶")
        else:
            mlist = self.query_one("#music-list", ListView)
            if mlist.children:
                idx = mlist.index if mlist.index is not None else 0
                if idx < len(self._tracks):
                    self._current_idx = idx
                    self._play_file(self._tracks[idx])

class MusicWindow:
    title = "Player de Música"
    window_id = "music"
    @staticmethod
    def create():
        return AquilaMusicTUI()

if __name__ == "__main__":
    AquilaMusicTUI().run()

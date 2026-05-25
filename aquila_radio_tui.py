import asyncio
import subprocess
import os
import signal
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

STATIONS = [
    ("Cultura FM", "https://culturafm.jmvstream.com/live"),
    ("Jazz24", "https://live.wostreaming.net/direct/ppm-jazz24aac-ibc4"),
    ("BBC Radio 1", "https://a.files.bbci.co.uk/media/live/manifesto/audio/simulcast/dash/nonuk/dash_low/aks/bbc_radio_one.mpd"),
    ("NTS Radio", "https://stream-relay-geo.ntslive.net/stream"),
    ("Lofi Girl", "https://play.streamafrica.net/lofiradio"),
    ("SomaFM Groove", "https://ice.somafm.com/groovesalad"),
    ("SomaFM Digital", "https://ice.somafm.com/digitalis"),
    ("Ambient", "https://ice.somafm.com/dronezone"),
    ("Rock Classics", "https://stream.zeno.fm/0r0xa792kwzuv"),
    ("MPB Brasil", "https://stream.zeno.fm/v4u8cyqsq0usv"),
]

CSS = f"""
Screen {{ background: {BG_MAIN}; align: center middle; }}
#frame {{ width: 72; height: 26; border: round {COLOR_BLUE}; background: {BG_CARD}; layout: horizontal; }}
#sidebar {{ width: 20; height: 100%; padding: 1; layout: vertical; border-right: round {BG_GLASS}; }}
#logo {{ height: 1; content-align: center middle; color: {COLOR_BLUE}; text-style: bold; margin-bottom: 1; }}
#now-playing {{ height: 4; border: round {BG_GLASS}; background: {BG_GLASS}; content-align: center middle; color: {COLOR_BLUE2}; margin-bottom: 1; padding: 0 1; }}
.ctrl-btn {{ width: 100%; height: 3; margin-bottom: 1; background: {BG_GLASS}; color: {COLOR_BLUE}; border: none; text-style: bold; }}
.ctrl-btn:hover {{ background: {COLOR_BLUE}; color: {BG_MAIN}; }}
.ctrl-btn.active {{ background: {COLOR_GREEN}; color: {BG_MAIN}; }}
#spacer {{ height: 1fr; }}
#exit-btn {{ width: 100%; height: 3; background: {BG_GLASS}; color: {COLOR_RED}; border: none; text-style: bold; }}
#exit-btn:hover {{ background: {COLOR_RED}; color: {BG_MAIN}; }}
#right-panel {{ width: 1fr; height: 100%; padding: 1; layout: vertical; }}
#panel-title {{ height: 1; color: {COLOR_MUTED}; text-style: bold; margin-bottom: 1; }}
#station-list {{ height: 1fr; background: transparent; border: none; }}
StationItem {{ height: 3; background: {BG_GLASS}; border: round {BG_GLASS}; margin-bottom: 1; padding: 0 1; layout: horizontal; align: left middle; }}
StationItem:hover {{ background: {BG_HOVER}; border: round {COLOR_BLUE}; }}
.station-name {{ width: 1fr; color: {COLOR_TEXT}; text-style: bold; }}
.station-play {{ width: 10; color: {COLOR_MUTED}; text-align: right; }}
"""

class StationItem(Static):
    def __init__(self, idx: int, name: str, url: str):
        super().__init__()
        self.idx = idx
        self.station_name = name
        self.url = url

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Label(self.station_name, classes="station-name")
            yield Label("▶", classes="station-play")

class AquilaRadioTUI(App):
    CSS = CSS
    BINDINGS = [Binding("q", "quit", "Sair"), Binding("space", "toggle", "Play/Stop")]

    def __init__(self, **kw):
        super().__init__(**kw)
        self._proc: subprocess.Popen | None = None
        self._current_station = ""

    def compose(self) -> ComposeResult:
        with Container(id="frame"):
            with Vertical(id="sidebar"):
                yield Label("📻 RÁDIO", id="logo")
                yield Label("Parado\n", id="now-playing")
                yield Button("▶ PLAY", id="btn-play", classes="ctrl-btn")
                yield Button("⏹ STOP", id="btn-stop", classes="ctrl-btn")
                yield Static(id="spacer")
                yield Button("SAIR", id="exit-btn")
            with Vertical(id="right-panel"):
                yield Label("ESTAÇÕES", id="panel-title")
                yield ListView(id="station-list")

    def on_mount(self):
        slist = self.query_one("#station-list", ListView)
        for i, (name, url) in enumerate(STATIONS):
            slist.append(StationItem(i, name, url))

    def _check_player(self):
        return bool(subprocess.run("which mpv", shell=True, capture_output=True).stdout.strip())

    @on(Button.Pressed)
    async def _on_btn(self, event: Button.Pressed):
        bid = event.button.id or ""
        if bid == "exit-btn":
            self._stop()
            self.exit()
        elif bid == "btn-play":
            if self._proc:
                self._resume()
            elif self._current_station:
                await self._play_url(self._current_station)
        elif bid == "btn-stop":
            self._stop()

    async def on_list_view_selected(self, event: ListView.Selected):
        item = event.item
        if isinstance(item, StationItem):
            self._current_station = item.url
            await self._play_url(item.url)
            self.query_one("#now-playing", Label).update(f"▶ Tocando:\n{item.station_name}")

    async def _play_url(self, url: str):
        self._stop()
        player = "mpv"
        if not self._check_player():
            self.query_one("#now-playing", Label).update("⚠ mpv não instalado\napt install mpv")
            return
        loop = asyncio.get_event_loop()
        self._proc = await loop.run_in_executor(None, lambda: subprocess.Popen(
            ["mpv", "--no-video", "--really-quiet", url],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            start_new_session=True,
        ))

    def _stop(self):
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

    def _resume(self):
        pass

    @staticmethod
    def _check_cmd(cmd: str) -> bool:
        return bool(subprocess.run(f"which {cmd}", shell=True, capture_output=True).stdout.strip())

class RadioWindow:
    title = "Rádio Online"
    window_id = "radio"
    @staticmethod
    def create():
        return AquilaRadioTUI()

if __name__ == "__main__":
    AquilaRadioTUI().run()

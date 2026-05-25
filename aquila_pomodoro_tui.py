import asyncio
import time
from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Static, Button, Label
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

CSS = f"""
Screen {{ background: {BG_MAIN}; align: center middle; }}
#frame {{ width: 50; height: 24; border: round {COLOR_BLUE}; background: {BG_CARD}; layout: vertical; padding: 1; align: center middle; }}
#logo {{ height: 1; content-align: center middle; color: {COLOR_BLUE}; text-style: bold; margin-bottom: 1; }}
#phase {{ height: 2; content-align: center middle; color: {COLOR_GREEN}; text-style: bold; }}
#timer {{ height: 6; content-align: center middle; color: {COLOR_BLUE}; text-style: bold; }}
#info {{ height: 2; content-align: center middle; color: {COLOR_MUTED}; }}
.ctrl-row {{ height: 4; layout: horizontal; align: center middle; margin-bottom: 1; }}
.ctrl-btn {{ height: 3; min-width: 12; margin: 0 1; background: {BG_GLASS}; color: {COLOR_BLUE}; border: none; text-style: bold; }}
.ctrl-btn:hover {{ background: {COLOR_BLUE}; color: {BG_MAIN}; }}
.ctrl-btn.start {{ background: {COLOR_GREEN}; color: {BG_MAIN}; }}
.ctrl-btn.stop {{ background: {COLOR_RED}; color: {BG_MAIN}; }}
#config {{ height: auto; layout: vertical; }}
.config-row {{ height: 2; layout: horizontal; align: center middle; }}
.config-label {{ width: 16; color: {COLOR_MUTED}; text-align: right; }}
.config-val {{ width: 8; color: {COLOR_BLUE2}; text-style: bold; text-align: left; }}
#exit-btn {{ width: 100%; height: 3; background: {BG_GLASS}; color: {COLOR_RED}; border: none; text-style: bold; dock: bottom; }}
#exit-btn:hover {{ background: {COLOR_RED}; color: {BG_MAIN}; }}
"""

class AquilaPomodoroTUI(App):
    CSS = CSS
    BINDINGS = [Binding("q", "quit", "Sair"), Binding("space", "toggle", "Iniciar/Pausar")]

    WORK_MIN = 25
    BREAK_MIN = 5
    LONG_BREAK_MIN = 15
    POMOS_BEFORE_LONG = 4

    def __init__(self, **kw):
        super().__init__(**kw)
        self._running = False
        self._seconds = self.WORK_MIN * 60
        self._phase = "work"  # work | break
        self._pomo_count = 0
        self._timer_task: asyncio.Task | None = None

    def compose(self) -> ComposeResult:
        with Container(id="frame"):
            yield Label("🍅 POMODORO", id="logo")
            yield Label("Foco", id="phase")
            yield Label("25:00", id="timer")
            yield Label("0/4 pomodoros", id="info")
            with Horizontal(classes="ctrl-row"):
                yield Button("▶ INICIAR", id="btn-start", classes="ctrl-btn start")
                yield Button("⏹ RESET", id="btn-reset", classes="ctrl-btn")
            with Vertical(id="config"):
                with Horizontal(classes="config-row"):
                    yield Label("Tempo foco:", classes="config-label")
                    yield Label("25 min", classes="config-val")
                with Horizontal(classes="config-row"):
                    yield Label("Pausa curta:", classes="config-label")
                    yield Label("5 min", classes="config-val")
                with Horizontal(classes="config-row"):
                    yield Label("Pausa longa:", classes="config-label")
                    yield Label("15 min", classes="config-val")
            yield Button("SAIR", id="exit-btn")

    def _update_display(self):
        mins = self._seconds // 60
        secs = self._seconds % 60
        self.query_one("#timer", Label).update(f"{mins:02d}:{secs:02d}")
        phase_label = self.query_one("#phase", Label)
        if self._phase == "work":
            phase_label.update("🍅 Foco — Concentre-se!")
            phase_label.styles.color = COLOR_GREEN
        else:
            phase_label.update("☕ Pausa — Descanse!")
            phase_label.styles.color = COLOR_BLUE
        self.query_one("#info", Label).update(f"{self._pomo_count}/{self.POMOS_BEFORE_LONG} pomodoros")

    def _switch_phase(self):
        if self._phase == "work":
            self._pomo_count += 1
            if self._pomo_count % self.POMOS_BEFORE_LONG == 0:
                self._phase = "long_break"
                self._seconds = self.LONG_BREAK_MIN * 60
            else:
                self._phase = "break"
                self._seconds = self.BREAK_MIN * 60
        else:
            self._phase = "work"
            self._seconds = self.WORK_MIN * 60
        self._update_display()

    @work(exclusive=True)
    async def _timer_loop(self):
        while self._running:
            await asyncio.sleep(1)
            if not self._running:
                break
            self._seconds -= 1
            self._update_display()
            if self._seconds <= 0:
                self._running = False
                self._switch_phase()
                self._running = True

    @on(Button.Pressed)
    async def _on_btn(self, event: Button.Pressed):
        bid = event.button.id or ""
        if bid == "exit-btn":
            self._running = False
            self.exit()
        elif bid == "btn-start":
            if self._running:
                self._running = False
                self.query_one("#btn-start", Button).label = "▶ INICIAR"
            else:
                self._running = True
                self.query_one("#btn-start", Button).label = "⏸ PAUSAR"
                self._timer_loop()
        elif bid == "btn-reset":
            self._running = False
            self._seconds = self.WORK_MIN * 60
            self._phase = "work"
            self._pomo_count = 0
            self._update_display()
            self.query_one("#btn-start", Button).label = "▶ INICIAR"

    def action_toggle(self):
        btn = self.query_one("#btn-start", Button)
        btn.press()

class PomodoroWindow:
    title = "Pomodoro Timer"
    window_id = "pomodoro"
    @staticmethod
    def create():
        return AquilaPomodoroTUI()

if __name__ == "__main__":
    AquilaPomodoroTUI().run()

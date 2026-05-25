"""widgets/taskbar.py – Barra de tarefas do Aquila Desktop."""

import time
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Static, Button, Label
from textual import work
import asyncio


class TaskBar(Static):
    """Barra de tarefas: botões de janelas abertas + relógio em tempo real."""

    DEFAULT_CSS = """
    TaskBar {
        dock: bottom;
        height: 3;
        background: #0f1728;
        border-top: solid #263452;
        layout: horizontal;
        padding: 0 1;
        align: left middle;
    }

    #taskbar-windows {
        width: 1fr;
        height: 3;
        layout: horizontal;
        align: left middle;
    }

    .task-btn {
        height: 3;
        min-width: 22;
        background: #141c30;
        color: #BFD1FF;
        border: round #263452;
        margin-right: 1;
        text-style: bold;
    }

    .task-btn:hover {
        background: #1c2945;
        border: round #8DB4FF;
        color: #E6ECFF;
    }

    .task-btn.-active {
        background: #8DB4FF;
        border: round #E6ECFF;
        color: #0b0f19;
    }

    #taskbar-right {
        width: auto;
        height: 3;
        layout: horizontal;
        align: right middle;
    }

    #taskbar-icons {
        color: #8DB4FF;
        margin-right: 1;
    }

    #clock {
        color: #E6ECFF;
        text-style: bold;
        min-width: 8;
        content-align: right middle;
    }
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._window_buttons: dict = {}

    def compose(self) -> ComposeResult:
        yield Horizontal(id="taskbar-windows")
        with Horizontal(id="taskbar-right"):
            yield Label("󰤨  🔋", id="taskbar-icons")
            yield Label(time.strftime("%H:%M:%S"), id="clock")

    def on_mount(self) -> None:
        self._tick()

    @work(exclusive=True)
    async def _tick(self) -> None:
        """Atualiza o relógio a cada segundo."""
        while True:
            await asyncio.sleep(1)
            try:
                self.query_one("#clock", Label).update(time.strftime("%H:%M:%S"))
            except Exception:
                break

    def add_window_button(self, win) -> None:
        """Adiciona botão de janela à barra de tarefas."""
        wid = win.window_id
        if wid in self._window_buttons:
            self.set_active(wid)
            return
        icon = getattr(win, "icon", "▪")
        btn = Button(f"{icon} {win.title}", id=f"task-{wid}", classes="task-btn")
        self._window_buttons[wid] = btn
        self.query_one("#taskbar-windows").mount(btn)
        self.set_active(wid)

    def remove_window_button(self, window_id: str) -> None:
        """Remove botão de janela da barra de tarefas."""
        btn = self._window_buttons.pop(window_id, None)
        if btn:
            btn.remove()

    def set_active(self, window_id: str) -> None:
        """Marca a janela ativa na barra de tarefas."""
        for wid, button in self._window_buttons.items():
            if wid == window_id:
                button.add_class("-active")
            else:
                button.remove_class("-active")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id or ""
        if btn_id.startswith("task-"):
            win_id = btn_id[5:]
            try:
                self.app.activate_window(win_id)
            except Exception:
                pass

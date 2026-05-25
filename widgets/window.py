"""widgets/window.py – Janela arrastável base do Aquila Desktop."""

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Static, Button, Label
from textual import events


class Window(Static):
    """Janela genérica com barra de título, fechar, minimizar e arrastar.

    Subclasses devem:
    - Definir ``title`` (str)
    - Definir ``window_id`` (str, apenas [a-z0-9_-])
    - Sobrescrever ``build_content()`` que retorna widgets do corpo.
    """

    title: str = "Janela"
    window_id: str = "window"

    DEFAULT_CSS = """
    Window {
        layer: windows;
        background: #111625;
        border: round #8DB4FF;
        width: 80;
        height: 26;
        margin: 1 2;
    }

    Window.minimized {
        height: 3;
    }

    Window:focus-within {
        border: round #8DB4FF;
    }

    .win-titlebar {
        height: 3;
        background: #0b0f19;
        border-bottom: solid #181E2E;
        layout: horizontal;
        align: left middle;
        padding: 0 1;
    }

    .win-icon {
        width: 3;
        color: #8DB4FF;
    }

    .win-title {
        width: 1fr;
        color: #E6ECFF;
        text-style: bold;
    }

    .win-btn {
        width: 3;
        height: 1;
        border: none;
        text-style: bold;
        margin-left: 1;
    }

    .win-minimize {
        background: #B8B7D9;
        color: #0b0f19;
    }

    .win-minimize:hover {
        background: #A7BDF5;
    }

    .win-close {
        background: #f87171;
        color: #0b0f19;
    }

    .win-close:hover {
        background: #ff5555;
    }

    .win-body {
        width: 100%;
        height: 1fr;
    }
    """

    def compose(self) -> ComposeResult:
        self.id = self.window_id
        with Horizontal(classes="win-titlebar"):
            yield Label("▪", classes="win-icon")
            yield Label(self.title, classes="win-title")
            yield Button("─", classes="win-btn win-minimize", id=f"{self.window_id}-min")
            yield Button("✕", classes="win-btn win-close", id=f"{self.window_id}-close")
        with Container(classes="win-body"):
            yield from self.build_content()

    def build_content(self) -> ComposeResult:
        """Sobrescreva para fornecer o conteúdo da janela."""
        yield Static("Sem conteúdo.")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id or ""
        if btn_id.endswith("-close"):
            # Notifica o desktop para remover da taskbar
            self.app.on_window_closed(self.window_id)
            await self.remove()
        elif btn_id.endswith("-min"):
            if self.has_class("minimized"):
                self.remove_class("minimized")
            else:
                self.add_class("minimized")

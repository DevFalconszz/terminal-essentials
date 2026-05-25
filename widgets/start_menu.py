from textual.app import ComposeResult
from textual.containers import Vertical, ScrollableContainer
from textual.widgets import Static, Button, Label

APPS = [
    ("🌐  Wi‑Fi", "start-wifi"),
    ("🔵  Bluetooth", "start-bluetooth"),
    ("📊  Processos", "start-process"),
    ("💻  Monitor Sistema", "start-sysmon"),
    ("📁  Arquivos", "start-files"),
    ("📻  Rádio Online", "start-radio"),
    ("📝  Notas", "start-notes"),
    ("🌤  Clima", "start-weather"),
    ("🔧  Comandos", "start-commands"),
    ("🍅  Pomodoro", "start-pomodoro"),
    ("🐳  Docker", "start-docker"),
    ("🎵  Música", "start-music"),
]

class StartMenu(Static):
    DEFAULT_CSS = """
    StartMenu {
        dock: bottom;
        layer: overlay;
        offset: 0 -100%;
        width: 42;
        height: 100%;
        max-height: 30;
        background: #111625;
        border: round #8DB4FF;
        padding: 1 1;
        display: none;
    }
    StartMenu.visible {
        display: block;
        offset-y: -3;
    }
    #menu-header {
        height: 2;
        border-bottom: solid #181E2E;
        margin-bottom: 1;
    }
    #menu-title {
        color: #8DB4FF;
        text-style: bold;
    }
    #menu-theme {
        color: #AAB6D6;
        text-style: italic;
    }
    .menu-section-title {
        color: #AAB6D6;
        text-style: bold;
        margin-top: 1;
        margin-bottom: 0;
    }
    .menu-btn {
        width: 100%;
        height: 2;
        background: #181E2E;
        color: #A7BDF5;
        border: none;
        text-style: bold;
        margin-bottom: 1;
        transition: background 120ms, color 120ms;
    }
    .menu-btn:hover {
        background: #8DB4FF;
        color: #0b0f19;
    }
    #menu-divider {
        border-bottom: solid #181E2E;
        height: 1;
        margin: 1 0;
    }
    #menu-exit-btn {
        width: 100%;
        height: 3;
        background: #181E2E;
        color: #D9B8CC;
        border: none;
        text-style: bold;
        transition: background 120ms, color 120ms;
    }
    #menu-exit-btn:hover {
        background: #f87171;
        color: #0b0f19;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="menu-header"):
            yield Label("⚡ Terminal-Essentials", id="menu-title")
            yield Label("Tema: Áquila Azure Night", id="menu-theme")
        yield Label("APLICAÇÕES", classes="menu-section-title")
        with ScrollableContainer():
            for label, btn_id in APPS:
                yield Button(label, id=btn_id, classes="menu-btn")
        yield Static(id="menu-divider")
        yield Button("⏻  Sair do Desktop", id="menu-exit-btn")

    def toggle(self) -> None:
        if self.has_class("visible"):
            self.remove_class("visible")
        else:
            self.add_class("visible")

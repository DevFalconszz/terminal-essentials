import asyncio
import json
import subprocess
import os
from pathlib import Path
from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Static, Button, Label, ListView, Input
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

DATA_FILE = Path.home() / ".local" / "share" / "terminal-essentials" / "commands.json"

DEFAULT_COMMANDS = [
    {"cmd": "ip a", "desc": "Mostrar interfaces de rede", "cat": "Rede"},
    {"cmd": "ping -c 4 google.com", "desc": "Testar conectividade", "cat": "Rede"},
    {"cmd": "ss -tlnp", "desc": "Portas TCP escutando", "cat": "Rede"},
    {"cmd": "df -h", "desc": "Espaço em disco", "cat": "Sistema"},
    {"cmd": "free -h", "desc": "Uso de memória", "cat": "Sistema"},
    {"cmd": "ps auxf", "desc": "Árvore de processos", "cat": "Sistema"},
    {"cmd": "journalctl -p 3 -xb", "desc": "Erros do sistema", "cat": "Sistema"},
    {"cmd": "du -sh * | sort -h", "desc": "Tamanho das pastas", "cat": "Disco"},
    {"cmd": "ncdu", "desc": "Analisador de disco (TUI)", "cat": "Disco"},
    {"cmd": "lsof -i", "desc": "Conexões de rede abertas", "cat": "Rede"},
    {"cmd": "htop", "desc": "Monitor de processos (TUI)", "cat": "Sistema"},
    {"cmd": "dmesg -T | tail -20", "desc": "Últimas mensagens do kernel", "cat": "Sistema"},
    {"cmd": "who", "desc": "Usuários logados", "cat": "Sistema"},
    {"cmd": "uptime", "desc": "Tempo de atividade", "cat": "Sistema"},
    {"cmd": "uname -a", "desc": "Info do kernel", "cat": "Sistema"},
]

CSS = f"""
Screen {{ background: {BG_MAIN}; align: center middle; }}
#frame {{ width: 82; height: 28; border: round {COLOR_BLUE}; background: {BG_CARD}; layout: horizontal; }}
#sidebar {{ width: 24; height: 100%; padding: 1; layout: vertical; border-right: round {BG_GLASS}; }}
#logo {{ height: 1; content-align: center middle; color: {COLOR_BLUE}; text-style: bold; margin-bottom: 1; }}
#status-card {{ height: 2; border: round {BG_GLASS}; background: {BG_GLASS}; content-align: center middle; color: {COLOR_MUTED}; margin-bottom: 1; }}
.ctrl-btn {{ width: 100%; height: 3; margin-bottom: 1; background: {BG_GLASS}; color: {COLOR_BLUE}; border: none; text-style: bold; }}
.ctrl-btn:hover {{ background: {COLOR_BLUE}; color: {BG_MAIN}; }}
#spacer {{ height: 1fr; }}
#exit-btn {{ width: 100%; height: 3; background: {BG_GLASS}; color: {COLOR_RED}; border: none; text-style: bold; }}
#exit-btn:hover {{ background: {COLOR_RED}; color: {BG_MAIN}; }}
#right-panel {{ width: 1fr; height: 100%; padding: 1; layout: vertical; }}
#panel-title {{ height: 1; color: {COLOR_MUTED}; text-style: bold; margin-bottom: 1; }}
#search-input {{ height: 3; background: {BG_GLASS}; color: {COLOR_TEXT}; border: round {COLOR_BLUE}; margin-bottom: 1; }}
#cmd-list {{ height: 1fr; background: transparent; border: none; }}
#cmd-preview {{ height: 4; background: {BG_GLASS}; color: {COLOR_GREEN}; border: round {BG_HOVER}; padding: 1; margin-top: 1; }}
CmdItem {{ height: 3; background: {BG_GLASS}; border: round {BG_GLASS}; margin-bottom: 1; padding: 0 1; layout: horizontal; align: left middle; }}
CmdItem:hover {{ background: {BG_HOVER}; border: round {COLOR_BLUE}; }}
.cmd-desc {{ width: 1fr; color: {COLOR_TEXT}; text-style: bold; }}
.cmd-cat {{ width: 10; color: {COLOR_MUTED}; text-align: center; }}
.btn-copy {{ height: 1; min-width: 8; padding: 0 1; border: none; background: {COLOR_BLUE}; color: {BG_MAIN}; text-style: bold; }}
.btn-copy:hover {{ background: {COLOR_BLUE2}; }}
"""

class CmdItem(Static):
    def __init__(self, cmd: str, desc: str, cat: str, idx: int):
        super().__init__()
        self.cmd = cmd
        self.cmd_desc = desc
        self.cmd_cat = cat
        self.idx = idx

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Label(self.cmd_desc, classes="cmd-desc")
            yield Label(self.cmd_cat, classes="cmd-cat")
            yield Button("USAR", id=f"use-{self.idx}", classes="btn-copy")

class AquilaCommandsTUI(App):
    CSS = CSS
    BINDINGS = [Binding("q", "quit", "Sair"), Binding("/", "focus_search", "Buscar")]

    def __init__(self, **kw):
        super().__init__(**kw)
        self._commands = self._load_commands()
        self._filtered = list(self._commands)

    def compose(self) -> ComposeResult:
        with Container(id="frame"):
            with Vertical(id="sidebar"):
                yield Label("💻 COMANDOS", id="logo")
                yield Label(f"{len(self._commands)} comandos", id="status-card")
                yield Button("ADICIONAR", id="btn-add", classes="ctrl-btn")
                yield Button("EXECUTAR", id="btn-run", classes="ctrl-btn")
                yield Static(id="spacer")
                yield Button("SAIR", id="exit-btn")
            with Vertical(id="right-panel"):
                yield Label("COMANDOS FAVORITOS", id="panel-title")
                yield Input(placeholder="Filtrar…", id="search-input")
                yield ListView(id="cmd-list")
                yield Static("Clique em um comando", id="cmd-preview")

    def on_mount(self):
        self._render()

    def _render(self):
        nlist = self.query_one("#cmd-list", ListView)
        nlist.clear()
        for i, cmd in enumerate(self._filtered):
            nlist.append(CmdItem(cmd["cmd"], cmd["desc"], cmd["cat"], i))
        self.query_one("#status-card", Label).update(f"📋 {len(self._filtered)}/{len(self._commands)} comandos")

    @staticmethod
    def _load_commands():
        if DATA_FILE.is_file():
            try:
                return json.loads(DATA_FILE.read_text())
            except Exception:
                pass
        DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        DATA_FILE.write_text(json.dumps(DEFAULT_COMMANDS, indent=2))
        return list(DEFAULT_COMMANDS)

    @on(Button.Pressed)
    async def _on_btn(self, event: Button.Pressed):
        bid = event.button.id or ""
        if bid == "exit-btn":
            self.exit()
        elif bid == "btn-add":
            inp = self.query_one("#search-input", Input)
            if inp.value.strip():
                self._commands.append({"cmd": inp.value.strip(), "desc": inp.value.strip()[:40], "cat": "Custom"})
                DATA_FILE.write_text(json.dumps(self._commands, indent=2))
                self._filtered = list(self._commands)
                inp.value = ""
                self._render()
        elif bid == "btn-run":
            nlist = self.query_one("#cmd-list", ListView)
            if nlist.children:
                selected = nlist.children[nlist.index]
                if isinstance(selected, CmdItem):
                    cmd = selected.cmd
                    subprocess.Popen(cmd, shell=True, start_new_session=True,
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elif bid.startswith("use-"):
            idx = int(bid[4:])
            cmd = self._filtered[idx]
            preview = self.query_one("#cmd-preview", Static)
            preview.update(f"$ {cmd['cmd']}\n\nPressione EXECUTAR ou copie manualmente")
            self.query_one("#search-input", Input).value = cmd["cmd"]

    def on_input_changed(self, event: Input.Changed):
        if event.input.id == "search-input":
            q = event.value.lower()
            if q:
                self._filtered = [c for c in self._commands
                                  if q in c["cmd"].lower() or q in c["desc"].lower() or q in c["cat"].lower()]
            else:
                self._filtered = list(self._commands)
            self._render()

    async def on_list_view_selected(self, event: ListView.Selected):
        item = event.item
        if isinstance(item, CmdItem):
            preview = self.query_one("#cmd-preview", Static)
            preview.update(f"$ {item.cmd}")

    def action_focus_search(self):
        self.query_one("#search-input", Input).focus()

class CommandsWindow:
    title = "Comandos Rápidos"
    window_id = "commands"
    @staticmethod
    def create():
        return AquilaCommandsTUI()

if __name__ == "__main__":
    AquilaCommandsTUI().run()

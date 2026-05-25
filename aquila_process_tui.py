import asyncio
import signal
import os
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
COLOR_TEXT = "#E6ECFF"
COLOR_MUTED= "#AAB6D6"
COLOR_GREEN= "#4ade80"
COLOR_RED  = "#f87171"

CSS = f"""
Screen {{ background: {BG_MAIN}; align: center middle; }}
#frame {{ width: 90; height: 28; border: round {COLOR_BLUE}; background: {BG_CARD}; layout: horizontal; }}
#sidebar {{ width: 22; height: 100%; padding: 1; layout: vertical; border-right: round {BG_GLASS}; }}
#logo {{ height: 1; content-align: center middle; color: {COLOR_BLUE}; text-style: bold; margin-bottom: 1; }}
#status-card {{ height: 2; border: round {BG_GLASS}; background: {BG_GLASS}; content-align: center middle; color: {COLOR_MUTED}; margin-bottom: 1; }}
.ctrl-btn {{ width: 100%; height: 3; margin-bottom: 1; background: {BG_GLASS}; color: {COLOR_BLUE}; border: none; text-style: bold; }}
.ctrl-btn:hover {{ background: {COLOR_BLUE}; color: {BG_MAIN}; }}
#spacer {{ height: 1fr; }}
#exit-btn {{ width: 100%; height: 3; background: {BG_GLASS}; color: {COLOR_RED}; border: none; text-style: bold; }}
#exit-btn:hover {{ background: {COLOR_RED}; color: {BG_MAIN}; }}
#right-panel {{ width: 1fr; height: 100%; padding: 1; layout: vertical; }}
#panel-title {{ height: 1; color: {COLOR_MUTED}; text-style: bold; margin-bottom: 1; }}
#proc-list {{ height: 1fr; background: transparent; border: none; }}
ProcItem {{ height: 3; background: {BG_GLASS}; border: round {BG_GLASS}; margin-bottom: 1; padding: 0 1; layout: horizontal; align: left middle; }}
ProcItem:hover {{ background: {BG_HOVER}; border: round {COLOR_BLUE}; }}
.proc-pid {{ width: 8; color: {COLOR_MUTED}; }}
.proc-name {{ width: 1fr; color: {COLOR_TEXT}; text-style: bold; }}
.proc-cpu {{ width: 8; color: {COLOR_BLUE}; text-align: right; }}
.proc-mem {{ width: 8; color: {COLOR_GREEN}; text-align: right; }}
.btn-kill {{ height: 1; min-width: 8; padding: 0 1; border: none; background: {COLOR_RED}; color: {BG_MAIN}; text-style: bold; }}
.btn-kill:hover {{ background: {COLOR_TEXT}; }}
"""

class ProcItem(Static):
    def __init__(self, pid: int, name: str, cpu: float, mem: float):
        super().__init__()
        self.pid = pid
        self.pname = name
        self.cpu = cpu
        self.mem = mem

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Label(str(self.pid), classes="proc-pid")
            yield Label(self.pname[:20], classes="proc-name")
            yield Label(f"{self.cpu:.1f}%", classes="proc-cpu")
            yield Label(f"{self.mem:.1f}%", classes="proc-mem")
            yield Button("KILL", id=f"kill-{self.pid}", classes="btn-kill")

class AquilaProcessTUI(App):
    CSS = CSS
    BINDINGS = [Binding("q", "quit", "Sair"), Binding("r", "refresh", "Recarregar")]

    def __init__(self, **kw):
        super().__init__(**kw)
        self._procs: list = []

    def compose(self) -> ComposeResult:
        with Container(id="frame"):
            with Vertical(id="sidebar"):
                yield Label("⚡ PROCESSOS", id="logo")
                yield Label("Carregando…", id="status-card")
                yield Button("RECARREGAR", id="btn-refresh", classes="ctrl-btn")
                yield Button("MATAR TODOS", id="btn-killall", classes="ctrl-btn")
                yield Static(id="spacer")
                yield Button("SAIR", id="exit-btn")
            with Vertical(id="right-panel"):
                yield Label("PID  NOME                 CPU    MEM", id="panel-title")
                yield ListView(id="proc-list")

    def on_mount(self):
        self._refresh()

    @work(exclusive=True)
    async def _refresh(self):
        loop = asyncio.get_event_loop()
        self._procs = await loop.run_in_executor(None, self._get_procs)
        plist = self.query_one("#proc-list", ListView)
        await plist.clear()
        status = self.query_one("#status-card", Label)
        status.update(f"📊 {len(self._procs)} processos")
        for pid, name, cpu, mem in self._procs:
            await plist.append(ProcItem(pid, name, cpu, mem))

    @staticmethod
    def _get_procs():
        import psutil
        procs = []
        for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                pinfo = p.info
                if pinfo['pid'] is None:
                    continue
                procs.append((pinfo['pid'], pinfo['name'] or '?',
                              pinfo['cpu_percent'] or 0.0, pinfo['memory_percent'] or 0.0))
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        procs.sort(key=lambda x: x[2], reverse=True)
        return procs[:100]

    @on(Button.Pressed)
    async def _on_btn(self, event: Button.Pressed):
        bid = event.button.id or ""
        if bid == "exit-btn":
            self.exit()
        elif bid in ("btn-refresh",):
            await self._refresh()
        elif bid == "btn-killall":
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._kill_all)
            await self._refresh()
        elif bid.startswith("kill-"):
            pid = int(bid[5:])
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: self._kill_proc(pid))
            await self._refresh()

    @staticmethod
    def _kill_proc(pid: int):
        import psutil
        try:
            p = psutil.Process(pid)
            p.terminate()
        except Exception:
            pass

    @staticmethod
    def _kill_all():
        import psutil
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                p = proc.info
                if p['pid'] and p['pid'] > 1 and p['pid'] != os.getpid():
                    psutil.Process(p['pid']).terminate()
            except Exception:
                pass

class ProcessWindow:
    title = "Gerenciador de Processos"
    window_id = "process"
    @staticmethod
    def create():
        return AquilaProcessTUI()

if __name__ == "__main__":
    AquilaProcessTUI().run()

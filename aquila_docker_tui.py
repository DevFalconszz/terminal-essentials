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
COLOR_LAVA = "#B8B7D9"

CSS = f"""
Screen {{ background: {BG_MAIN}; align: center middle; }}
#frame {{ width: 86; height: 28; border: round {COLOR_BLUE}; background: {BG_CARD}; layout: horizontal; }}
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
#container-list {{ height: 1fr; background: transparent; border: none; }}
#log-view {{ height: 6; background: {BG_GLASS}; color: {COLOR_GREEN}; border: round {BG_HOVER}; padding: 1; margin-top: 1; }}
DockerItem {{ height: 3; background: {BG_GLASS}; border: round {BG_GLASS}; margin-bottom: 1; padding: 0 1; layout: horizontal; align: left middle; }}
DockerItem:hover {{ background: {BG_HOVER}; border: round {COLOR_BLUE}; }}
.docker-name {{ width: 1fr; color: {COLOR_TEXT}; text-style: bold; }}
.docker-status {{ width: 14; color: {COLOR_MUTED}; text-align: center; }}
.docker-ports {{ width: 16; color: {COLOR_LAVA}; text-align: right; }}
.btn-docker {{ height: 1; min-width: 8; padding: 0 1; border: none; margin-left: 1; text-style: bold; }}
.btn-start {{ background: {COLOR_GREEN}; color: {BG_MAIN}; }}
.btn-stop {{ background: {COLOR_RED}; color: {BG_MAIN}; }}
.btn-restart {{ background: {COLOR_BLUE}; color: {BG_MAIN}; }}
.btn-docker:hover {{ opacity: 0.8; }}
"""

class DockerItem(Static):
    def __init__(self, cid: str, name: str, status: str, ports: str, idx: int):
        super().__init__()
        self.cid = cid
        self.dkr_name = name
        self.dkr_status = status
        self.dkr_ports = ports
        self.idx = idx

    def compose(self) -> ComposeResult:
        is_running = "Up" in self.dkr_status
        with Horizontal():
            yield Label(self.dkr_name[:24], classes="docker-name")
            yield Label(self.dkr_status[:12], classes="docker-status")
            yield Label(self.dkr_ports[:14], classes="docker-ports")
            if is_running:
                yield Button("STOP", id=f"stop-{self.idx}", classes="btn-docker btn-stop")
                yield Button("RESTART", id=f"restart-{self.idx}", classes="btn-docker btn-restart")
            else:
                yield Button("START", id=f"start-{self.idx}", classes="btn-docker btn-start")

class AquilaDockerTUI(App):
    CSS = CSS
    BINDINGS = [Binding("q", "quit", "Sair"), Binding("r", "refresh", "Recarregar")]

    def __init__(self, **kw):
        super().__init__(**kw)
        self._containers: list = []
        self._has_docker = False

    def compose(self) -> ComposeResult:
        with Container(id="frame"):
            with Vertical(id="sidebar"):
                yield Label("🐳 DOCKER", id="logo")
                yield Label("Verificando…", id="status-card")
                yield Button("RECARREGAR", id="btn-refresh", classes="ctrl-btn")
                yield Button("LOGS", id="btn-logs", classes="ctrl-btn")
                yield Static(id="spacer")
                yield Button("SAIR", id="exit-btn")
            with Vertical(id="right-panel"):
                yield Label("CONTAINERS", id="panel-title")
                yield ListView(id="container-list")
                yield Static("Logs aparecem aqui", id="log-view")

    def on_mount(self):
        self._has_docker = bool(subprocess.run("which docker", shell=True, capture_output=True).stdout.strip())
        self._refresh()

    @work(exclusive=True)
    async def _refresh(self):
        if not self._has_docker:
            self.query_one("#status-card", Label).update("⚠ Docker não encontrado")
            self.query_one("#log-view", Static).update("Instale o Docker:\n  sudo apt install docker.io")
            return
        self.query_one("#status-card", Label).update("🔄 Carregando…")
        loop = asyncio.get_event_loop()
        containers = await loop.run_in_executor(None, self._get_containers)
        self._containers = containers
        clist = self.query_one("#container-list", ListView)
        await clist.clear()
        self.query_one("#status-card", Label).update(f"📦 {len(containers)} containers")
        for i, (cid, name, status, ports) in enumerate(containers):
            await clist.append(DockerItem(cid, name, status, ports, i))

    @staticmethod
    def _get_containers():
        try:
            out = subprocess.run(
                "docker ps -a --format '{{.ID}}|{{.Names}}|{{.Status}}|{{.Ports}}'",
                shell=True, capture_output=True, text=True, timeout=5
            ).stdout.strip()
            result = []
            for line in out.splitlines():
                parts = line.split("|", 3)
                if len(parts) >= 3:
                    result.append((parts[0][:12], parts[1], parts[2], parts[3] if len(parts) > 3 else ""))
            return result
        except Exception:
            return []

    @on(Button.Pressed)
    async def _on_btn(self, event: Button.Pressed):
        bid = event.button.id or ""
        if bid == "exit-btn":
            self.exit()
        elif bid == "btn-refresh":
            await self._refresh()
        elif bid == "btn-logs":
            clist = self.query_one("#container-list", ListView)
            if clist.children:
                selected = clist.children[clist.index]
                if isinstance(selected, DockerItem):
                    log_view = self.query_one("#log-view", Static)
                    log_view.update("🔄 Carregando logs…")
                    loop = asyncio.get_event_loop()
                    logs = await loop.run_in_executor(None, lambda: subprocess.run(
                        f"docker logs --tail 15 {selected.cid}", shell=True, capture_output=True, text=True, timeout=5
                    ).stdout.strip())
                    log_view.update(logs or "(sem logs)")
        elif bid.startswith("start-"):
            idx = int(bid[6:])
            subprocess.run(f"docker start {self._containers[idx][0]}", shell=True, timeout=10,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            await self._refresh()
        elif bid.startswith("stop-"):
            idx = int(bid[5:])
            subprocess.run(f"docker stop {self._containers[idx][0]}", shell=True, timeout=10,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            await self._refresh()
        elif bid.startswith("restart-"):
            idx = int(bid[8:])
            subprocess.run(f"docker restart {self._containers[idx][0]}", shell=True, timeout=15,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            await self._refresh()

class DockerWindow:
    title = "Docker Manager"
    window_id = "docker"
    @staticmethod
    def create():
        return AquilaDockerTUI()

if __name__ == "__main__":
    AquilaDockerTUI().run()

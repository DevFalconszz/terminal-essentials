import asyncio
import os
import subprocess
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Static, Button, Label, ListView
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
#frame {{ width: 72; height: 28; border: round {COLOR_BLUE}; background: {BG_CARD}; layout: vertical; padding: 1; }}
#logo {{ height: 1; content-align: center middle; color: {COLOR_BLUE}; text-style: bold; margin-bottom: 1; }}
#status-card {{ height: 2; border: round {BG_GLASS}; background: {BG_GLASS}; content-align: center middle; color: {COLOR_MUTED}; margin-bottom: 1; }}
.bar-row {{ height: 3; layout: horizontal; align: left middle; margin-bottom: 1; }}
.bar-label {{ width: 16; color: {COLOR_BLUE2}; text-style: bold; }}
.bar-bg {{ width: 1fr; height: 2; background: {BG_GLASS}; border: none; margin: 0 1; }}
.bar-fill {{ height: 2; background: {COLOR_GREEN}; }}
.bar-fill.warn {{ background: {COLOR_LAVA}; }}
.bar-fill.crit {{ background: {COLOR_RED}; }}
.bar-pct {{ width: 8; color: {COLOR_MUTED}; text-align: right; }}
.info-grid {{ height: auto; layout: vertical; margin-bottom: 1; }}
.info-row {{ height: 2; layout: horizontal; align: left middle; }}
.info-label {{ width: 20; color: {COLOR_MUTED}; }}
.info-value {{ color: {COLOR_TEXT}; text-style: bold; }}
#exit-btn {{ width: 100%; height: 3; background: {BG_GLASS}; color: {COLOR_RED}; border: none; text-style: bold; dock: bottom; }}
#exit-btn:hover {{ background: {COLOR_RED}; color: {BG_MAIN}; }}
"""

def _run(cmd: str) -> str:
    try:
        return subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout.strip()
    except Exception:
        return ""

class AquilaSysmonTUI(App):
    CSS = CSS
    BINDINGS = [Binding("q", "quit", "Sair"), Binding("r", "refresh", "Recarregar")]

    def compose(self) -> ComposeResult:
        with Container(id="frame"):
            yield Label("⚡ MONITOR DO SISTEMA", id="logo")
            yield Label("veritas-TI", id="status-card")
            yield Static(id="info-grid")
            yield Label("CPU", classes="bar-label", id="cpu-label")
            yield Static(id="cpu-bar", classes="bar-bg")
            yield Label("", id="cpu-pct", classes="bar-pct")
            yield Label("MEMÓRIA", classes="bar-label", id="mem-label")
            yield Static(id="mem-bar", classes="bar-bg")
            yield Label("", id="mem-pct", classes="bar-pct")
            yield Label("DISCO", classes="bar-label", id="disk-label")
            yield Static(id="disk-bar", classes="bar-bg")
            yield Label("", id="disk-pct", classes="bar-pct")
            yield Button("SAIR", id="exit-btn")

    def on_mount(self):
        self._refresh()

    @work(exclusive=True)
    async def _refresh(self):
        while True:
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(None, self._gather_data)
            self._update_ui(data)
            await asyncio.sleep(3)

    def _update_ui(self, data: dict):
        self.query_one("#status-card", Label).update(f"🖥 {data['hostname']}  Uptime: {data['uptime']}")
        self._set_bar("cpu", data["cpu_pct"])
        self._set_bar("mem", data["mem_pct"])
        self._set_bar("disk", data["disk_pct"])

        info = self.query_one("#info-grid", Static)
        info.update(
            f"  CPU Load: 1m={data['load1']:.1f}  5m={data['load5']:.1f}  15m={data['load15']:.1f}\n"
            f"  RAM: {data['mem_used']:.1f}G / {data['mem_total']:.1f}G\n"
            f"  DISK: {data['disk_used']:.1f}G / {data['disk_total']:.1f}G\n"
            f"  Processos: {data['procs']}  |  Users: {data['users']}"
        )

    def _set_bar(self, prefix: str, pct: float):
        bar = self.query_one(f"#{prefix}-bar", Static)
        label = self.query_one(f"#{prefix}-pct", Label)
        w = max(1, int((self.size.width - 40) * pct / 100))
        color = "crit" if pct > 90 else ("warn" if pct > 70 else "")
        bar.styles.background = BG_GLASS
        bar.update(" " * w)
        bar.styles.width = w
        bar.set_class(color, bool(color))
        if color == "crit":
            bar.styles.background = COLOR_RED
        elif color == "warn":
            bar.styles.background = COLOR_LAVA
        else:
            bar.styles.background = COLOR_GREEN
        label.update(f"{pct:.1f}%")

    @staticmethod
    def _gather_data():
        import psutil
        cpu = psutil.cpu_percent(interval=0.5)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        load1, load5, load15 = os.getloadavg()
        uptime_sec = float(_run("cat /proc/uptime").split()[0]) if _run("cat /proc/uptime") else 0
        days = int(uptime_sec // 86400)
        hours = int((uptime_sec % 86400) // 3600)
        mins = int((uptime_sec % 3600) // 60)
        uptime_str = f"{days}d {hours:02d}h {mins:02d}m"
        hostname = os.uname().nodename
        procs = len(psutil.pids())
        users = len(psutil.users())
        return {
            "hostname": hostname, "uptime": uptime_str,
            "cpu_pct": cpu, "load1": load1, "load5": load5, "load15": load15,
            "mem_pct": mem.percent, "mem_used": mem.used / 1e9, "mem_total": mem.total / 1e9,
            "disk_pct": disk.percent, "disk_used": disk.used / 1e9, "disk_total": disk.total / 1e9,
            "procs": procs, "users": users,
        }

    @on(Button.Pressed)
    def _on_btn(self, event: Button.Pressed):
        if event.button.id == "exit-btn":
            self.exit()

class SysmonWindow:
    title = "Monitor do Sistema"
    window_id = "sysmon"
    @staticmethod
    def create():
        return AquilaSysmonTUI()

if __name__ == "__main__":
    AquilaSysmonTUI().run()

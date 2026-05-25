#!/usr/bin/env python3
"""aquila_wifi_tui.py
A Textual TUI for Wi‑Fi management that mirrors the Azure Night design of the Bluetooth TUI.
Implements status, power toggle, scan, connect, and disconnect using `nmcli`.
"""

import asyncio
import subprocess
from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Static, Button, ListView, Label
from textual.binding import Binding
from textual import on, work

# ─── Azure Night palette (same as Bluetooth TUI) ────────────────────────────────
BG_MAIN       = "#0b0f19"
BG_CARD       = "#111625"
BG_GLASS      = "#181E2E"
BG_HOVER      = "#1d243a"
COLOR_BLUE    = "#8DB4FF"
COLOR_BLUE2   = "#A7BDF5"
COLOR_LAVA    = "#B8B7D9"
COLOR_ROSE    = "#D9B8CC"
COLOR_TEXT    = "#E6ECFF"
COLOR_MUTED   = "#AAB6D6"
COLOR_GREEN   = "#4ade80"
COLOR_RED     = "#f87171"
COLOR_CONN_BG = "#0f2030"

ICON_DEFAULT = "📶"

CSS = f"""
Screen {{
    background: {BG_MAIN};
    align: center middle;
}}

#frame {{
    width: 80;
    height: 24;
    border: round {COLOR_BLUE};
    background: {BG_CARD};
    layout: horizontal;
}}

#sidebar {{
    width: 24;
    height: 100%;
    padding: 1 1;
    layout: vertical;
    border-right: round {BG_GLASS};
}}

#logo {{
    height: 1;
    content-align: center middle;
    color: {COLOR_BLUE};
    text-style: bold;
    margin-bottom: 1;
}}

#status-card {{
    height: 3;
    border: round {COLOR_LAVA};
    background: {BG_GLASS};
    content-align: center middle;
    color: {COLOR_BLUE2};
    margin-bottom: 2;
    padding: 0 1;
}}

#status-card.online {{
    border: round {COLOR_GREEN};
    color: {COLOR_GREEN};
}}

.ctrl-btn {{
    width: 100%;
    height: 3;
    margin-bottom: 1;
    background: {BG_GLASS};
    color: {COLOR_BLUE2};
    border: none;
    text-style: bold;
    transition: background 120ms, color 120ms;
}}

.ctrl-btn:hover {{
    background: {COLOR_BLUE};
    color: {BG_MAIN};
}}

#spacer {{
    height: 1fr;
}}

#exit-btn {{
    width: 100%;
    height: 3;
    background: {BG_GLASS};
    color: {COLOR_ROSE};
    border: none;
    text-style: bold;
    transition: background 120ms, color 120ms;
}}

#exit-btn:hover {{
    background: {COLOR_RED};
    color: {BG_MAIN};
}}

#right-panel {{
    width: 1fr;
    height: 100%;
    padding: 1 1;
    layout: vertical;
}}

#panel-title {{
    height: 1;
    color: {COLOR_MUTED};
    text-style: bold;
    margin-bottom: 1;
    content-align: left middle;
}}

#network-list {{
    height: 1fr;
    background: transparent;
    border: none;
}}

NetworkItem {{
    height: 3;
    background: {BG_GLASS};
    border: round {BG_GLASS};
    margin-bottom: 1;
    padding: 0 1;
    layout: horizontal;
    align: left middle;
    transition: background 120ms, border 120ms;
}}

NetworkItem:hover {{
    background: {BG_HOVER};
    border: round {COLOR_BLUE};
}}

NetworkItem.connected {{
    background: {COLOR_CONN_BG};
    border: round {COLOR_GREEN};
}}

.dev-icon {{
    width: 4;
    content-align: center middle;
    color: {COLOR_BLUE};
}}

.dev-info {{
    width: 1fr;
    layout: vertical;
    align-vertical: middle;
}}

.dev-name {{
    text-style: bold;
    color: {COLOR_TEXT};
}}

.dev-sub {{
    color: {COLOR_MUTED};
}}

.dev-sub.connected {{
    color: {COLOR_GREEN};
}}

.btn-connect {{
    height: 1;
    min-width: 12;
    padding: 0 2;
    border: none;
    background: {COLOR_BLUE};
    color: {BG_MAIN};
    text-style: bold;
    transition: background 120ms;
}}

.btn-connect:hover {{
    background: {COLOR_BLUE2};
}}

.btn-disconnect {{
    height: 1;
    min-width: 12;
    padding: 0 2;
    border: none;
    background: {COLOR_ROSE};
    color: {BG_MAIN};
    text-style: bold;
    transition: background 120ms;
}}

.btn-disconnect:hover {{
    background: {COLOR_RED};
}}
"""

class NetworkItem(Static):
    """Widget representing a Wi‑Fi network."""
    def __init__(self, ssid: str, signal: str, security: str, connected: bool = False):
        super().__init__()
        self.ssid = ssid
        self.signal = signal
        self.security = security
        self.connected = connected
        if connected:
            self.add_class("connected")

    def compose(self) -> ComposeResult:
        import re
        safe = re.sub(r'[^A-Za-z0-9_-]', '_', self.ssid)
        sub_class = "dev-sub connected" if self.connected else "dev-sub"
        with Horizontal():
            yield Label(ICON_DEFAULT, classes="dev-icon")
            with Vertical(classes="dev-info"):
                yield Label(self.ssid, classes="dev-name")
                yield Label(f"{self.signal}% {self.security}", classes=sub_class, id=f"sub-{safe}")
            if self.connected:
                yield Button("Desconectar", id=f"disc-{safe}", classes="btn-disconnect")
            else:
                yield Button("Conectar", id=f"conn-{safe}", classes="btn-connect")

class AquilaWifiTUI(App):
    CSS = CSS
    BINDINGS = [Binding("q", "quit", "Sair")]

    def __init__(self, **kw):
        super().__init__(**kw)
        self._networks: dict = {}
        self._connected_ssid: str | None = None

    # ── Layout ──────────────────────────────────────────────────────
    def compose(self) -> ComposeResult:
        with Container(id="frame"):
            with Vertical(id="sidebar"):
                yield Label("⚡ AQUILA WIFI", id="logo")
                yield Label("Inicializando…", id="status-card")
                yield Button("POWER", id="btn-power", classes="ctrl-btn")
                yield Button("SCAN", id="btn-scan", classes="ctrl-btn")
                yield Static(id="spacer")
                yield Button("SAIR", id="exit-btn")
            with Vertical(id="right-panel"):
                yield Label("REDES DISPONÍVEIS", id="panel-title")
                yield ListView(id="network-list")

    # ── Lifecycle ────────────────────────────────────────────────
    def on_mount(self) -> None:
        self._refresh_loop()

    @work(exclusive=True)
    async def _refresh_loop(self) -> None:
        while True:
            await self._refresh()
            await asyncio.sleep(5)

    # ── Helper functions ────────────────────────────────────────
    @staticmethod
    def _run_cmd(cmd: str) -> str:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout.strip()

    def _get_status(self):
        powered = self._run_cmd("nmcli radio wifi") == "enabled"
        ssid = ""
        if powered:
            out = self._run_cmd("nmcli -t -f ACTIVE,SSID dev wifi | grep '^yes'")
            if out:
                ssid = out.split(":")[1]
        return powered, ssid

    def _scan_networks(self):
        self._run_cmd("nmcli dev wifi list --rescan yes > /dev/null 2>&1")
        out = self._run_cmd("nmcli -t -f SSID,SIGNAL,SECURITY dev wifi list")
        networks = []
        seen = set()
        for line in out.splitlines():
            parts = line.split(":")
            if len(parts) < 3:
                continue
            ssid, signal, sec = parts[0], parts[1], parts[2]
            if ssid and ssid not in seen:
                networks.append((ssid, signal, sec))
                seen.add(ssid)
        return networks

    # ── UI refresh ────────────────────────────────────────────────
    async def _refresh(self):
        powered, cur_ssid = self._get_status()
        status_lbl = self.query_one("#status-card", Label)
        if powered:
            status_lbl.update("󰂯  WiFi ATIVADO ●")
            status_lbl.add_class("online")
        else:
            status_lbl.update("󰂲  WiFi DESATIVADO ○")
            status_lbl.remove_class("online")
        list_view = self.query_one("#network-list", ListView)
        networks = self._scan_networks()
        cur_set = {n[0] for n in networks}
        for item in list(list_view.children):
            if isinstance(item, NetworkItem) and item.ssid not in cur_set:
                await item.remove()
        for ssid, signal, sec in networks:
            connected = ssid == cur_ssid
            if ssid not in self._networks:
                item = NetworkItem(ssid, signal, sec, connected)
                await list_view.append(item)
                self._networks[ssid] = item
            else:
                item = self._networks[ssid]
                if item.connected != connected:
                    item.connected = connected
                    if connected:
                        item.add_class("connected")
                    else:
                        item.remove_class("connected")
        self._connected_ssid = cur_ssid

    # ── Button actions ──────────────────────────────────────────────
    @on(Button.Pressed)
    async def _on_button(self, event: Button.Pressed) -> None:
        bid = event.button.id
        if not bid:
            return
        self.query_one("#status-card", Label).update("Aguarde…")
        loop = asyncio.get_event_loop()
        if bid == "exit-btn":
            self.exit()
            return
        if bid == "btn-power":
            cmd = "nmcli radio wifi toggle"
            await loop.run_in_executor(None, lambda: subprocess.run(cmd, shell=True))
        elif bid == "btn-scan":
            await loop.run_in_executor(None, lambda: subprocess.run("nmcli dev wifi list --rescan yes", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
        elif bid.startswith("conn-"):
            ssid = bid[5:].replace("-", " ")
            cmd = f"nmcli dev wifi connect '{ssid}'"
            await loop.run_in_executor(None, lambda: subprocess.run(cmd, shell=True))
        elif bid.startswith("disc-"):
            await loop.run_in_executor(None, lambda: subprocess.run("nmcli networking off && nmcli networking on", shell=True))
        self._refresh_loop()

class WifiWindow:
    """Wrapper que expõe AquilaWifiTUI como sub‑app do desktop."""
    title = "Wi‑Fi Manager"
    window_id = "wifi"

    @staticmethod
    def create() -> "AquilaWifiTUI":
        return AquilaWifiTUI()


if __name__ == "__main__":
    AquilaWifiTUI().run()


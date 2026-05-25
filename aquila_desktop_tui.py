#!/usr/bin/env python3
"""aquila_desktop_tui.py
Terminal-Essentials Desktop – simulação de ambiente desktop no terminal.
Tema: Áquila Azure Night.
"""

import json
import asyncio
import subprocess
import re
import os
import signal
from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual import events
from textual.widgets import Static, Button, Label, ListView
from textual.binding import Binding
from textual import on

from widgets.start_menu import StartMenu
from widgets.taskbar import TaskBar
from aquila_bluetooth_tui import DeviceItem, ICON_MAP, ICON_DEFAULT as BT_ICON_DEFAULT
from aquila_wifi_tui import NetworkItem

# ─── Palette ──────────────────────────────────────────────────────────────────
BG_MAIN    = "#0b0f19"
BG_CARD    = "#111625"
BG_GLASS   = "#181E2E"
COLOR_BLUE = "#8DB4FF"
COLOR_TEXT = "#E6ECFF"
COLOR_MUTED = "#AAB6D6"
COLOR_GREEN = "#4ade80"
COLOR_RED   = "#f87171"

STATE_FILE = Path(__file__).parent / ".desktop_state.json"


def run_shell(cmd: str, timeout: float = 4.0) -> str:
    proc = None
    try:
        proc = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            start_new_session=True,
        )
        stdout, _stderr = proc.communicate(timeout=timeout)
        return stdout.strip()
    except subprocess.TimeoutExpired:
        if proc is not None:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except Exception:
                pass
            try:
                proc.communicate(timeout=0.5)
            except Exception:
                pass
        return ""
    except Exception:
        return ""


def run_shell_quiet(cmd: str, timeout: float = 8.0) -> None:
    proc = None
    try:
        proc = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        if proc is not None:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except Exception:
                pass
            try:
                proc.wait(timeout=0.5)
            except Exception:
                pass
    except Exception:
        pass

CSS = f"""
Screen {{
    background: {BG_MAIN};
    layers: base windows window-active overlay;
}}

/* ── Área do desktop ─────────────────────────────────────── */
#desktop {{
    width: 100%;
    height: 1fr;
    background: {BG_MAIN};
    layer: base;
    layout: vertical;
    align: left top;
    padding: 0;
}}

#desktop-icons {{
    position: absolute;
    offset: 2 2;
    width: auto;
    height: auto;
    layout: vertical;
}}

.desktop-row {{
    width: auto;
    height: auto;
    layout: horizontal;
}}

.desktop-icon {{
    width: 9;
    height: 3;
    margin: 0 1 1 0;
    background: transparent;
    color: {COLOR_TEXT};
    border: none;
    text-style: bold;
    content-align: center middle;
}}

.desktop-icon:hover {{
    background: {BG_GLASS};
    color: {COLOR_BLUE};
    border: none;
}}

/* ── Barra de status superior (topbar) ──────────────────── */
#topbar {{
    dock: top;
    height: 2;
    background: {BG_GLASS};
    layout: horizontal;
    align: left middle;
    padding: 0 2;
    color: {COLOR_MUTED};
}}

#topbar-title {{
    width: auto;
    color: {COLOR_BLUE};
    text-style: bold;
    margin-right: 2;
}}

#topbar-theme {{
    width: auto;
    color: {COLOR_BLUE};
    text-style: bold;
    background: {BG_CARD};
    padding: 0 1;
    border: none;
}}

#topbar-host {{
    width: 1fr;
    content-align: right middle;
    color: {COLOR_MUTED};
    text-style: italic;
}}

/* ── Watermark / wallpaper text ─────────────────────────── */
#wallpaper {{
    width: 100%;
    height: 1fr;
    content-align: center middle;
    color: {BG_GLASS};
    text-style: bold;
}}

/* ── Botão Iniciar ──────────────────────────────────────── */
#start-button {{
    dock: bottom;
    width: 16;
    height: 3;
    background: {COLOR_BLUE};
    color: {BG_MAIN};
    border: none;
    text-style: bold;
}}

#start-button:hover {{
    background: #A7BDF5;
}}

/* ── Painéis internos (sidebar dos sub-apps) ────────────── */
.bt-sidebar {{
    width: 24;
    height: 100%;
    padding: 1 1;
    layout: vertical;
    border-right: round {BG_GLASS};
}}

.bt-panel {{
    width: 1fr;
    height: 100%;
    padding: 1 1;
    layout: vertical;
}}

.window-titlebar {{
    height: 3;
    background: #0d1424;
    border-bottom: solid {BG_GLASS};
    layout: horizontal;
    align: left middle;
    padding: 0 1;
}}

.window-icon {{
    width: 4;
    color: {COLOR_BLUE};
    text-style: bold;
}}

.window-title {{
    width: 1fr;
    color: {COLOR_TEXT};
    text-style: bold;
}}

.window-btn {{
    width: 4;
    height: 1;
    margin-left: 1;
    background: {BG_GLASS};
    color: {COLOR_TEXT};
    border: none;
    text-style: bold;
}}

.window-btn:hover {{
    background: {COLOR_BLUE};
    color: {BG_MAIN};
}}

.window-close:hover {{
    background: {COLOR_RED};
    color: {BG_MAIN};
}}

.resize-handle {{
    dock: bottom;
    height: 2;
    content-align: right middle;
    color: {COLOR_MUTED};
    background: {BG_CARD};
    padding-right: 1;
}}

DeviceItem, NetworkItem {{
    height: 3;
    background: {BG_GLASS};
    border: round {BG_GLASS};
    margin-bottom: 1;
    padding: 0 1;
    layout: horizontal;
    align: left middle;
}}

DeviceItem:hover, NetworkItem:hover {{
    background: #1d243a;
    border: round {COLOR_BLUE};
}}

DeviceItem.connected, NetworkItem.connected {{
    background: #0f2030;
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
}}

.btn-disconnect {{
    height: 1;
    min-width: 12;
    padding: 0 2;
    border: none;
    background: #D9B8CC;
    color: {BG_MAIN};
    text-style: bold;
}}

#bt-logo, #wf-logo {{
    height: 1;
    content-align: center middle;
    color: {COLOR_BLUE};
    text-style: bold;
    margin-bottom: 1;
}}

#bt-status, #wf-status {{
    height: 3;
    border: round #B8B7D9;
    background: {BG_GLASS};
    content-align: center middle;
    color: #A7BDF5;
    margin-bottom: 2;
    padding: 0 1;
}}

#bt-panel-title, #wf-panel-title {{
    height: 1;
    color: {COLOR_MUTED};
    text-style: bold;
    margin-bottom: 1;
}}

.ctrl-btn {{
    width: 100%;
    height: 3;
    margin-bottom: 1;
    background: {BG_GLASS};
    color: #A7BDF5;
    border: none;
    text-style: bold;
    transition: background 120ms, color 120ms;
}}

.ctrl-btn:hover {{
    background: {COLOR_BLUE};
    color: {BG_MAIN};
}}

.ctrl-btn-close {{
    width: 100%;
    height: 3;
    background: {BG_GLASS};
    color: #D9B8CC;
    border: none;
    text-style: bold;
    transition: background 120ms, color 120ms;
}}

.sidebar-spacer {{
    height: 1fr;
}}

.ctrl-btn-close:hover {{
    background: {COLOR_RED};
    color: {BG_MAIN};
}}
"""

# ─── Window Manager ───────────────────────────────────────────────────────────
class ManagedWindow(Static):
    """Janela simples: move pela barra de título e redimensiona pelo canto."""

    title = "Aplicação"
    icon = "□"
    window_id = "window"
    app_key = "window"
    default_offset = (4, 2)
    min_width = 52
    min_height = 16
    default_width = 82
    default_height = 28

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._drag_mode: str | None = None
        self._drag_start = (0, 0)
        self._start_offset = self.default_offset
        self._start_size = (self.default_width, self.default_height)

    def on_mount(self) -> None:
        self.offset = self.default_offset
        self.styles.width = self.default_width
        self.styles.height = self.default_height

    def snapshot(self) -> dict[str, int]:
        width = int(getattr(self.size, "width", self.default_width) or self.default_width)
        height = int(getattr(self.size, "height", self.default_height) or self.default_height)
        return {"x": self.offset.x, "y": self.offset.y, "w": width, "h": height}

    def restore(self, state: dict[str, int]) -> None:
        self.offset = (int(state.get("x", self.default_offset[0])), int(state.get("y", self.default_offset[1])))
        self.styles.width = max(self.min_width, int(state.get("w", self.default_width)))
        self.styles.height = max(self.min_height, int(state.get("h", self.default_height)))
        self.constrain_to_desktop()

    def _desktop_bounds(self) -> tuple[int, int]:
        try:
            desktop = self.app.query_one("#desktop")
            return max(1, desktop.size.width), max(1, desktop.size.height)
        except Exception:
            return 120, 40

    def _clamp_offset(self, x: int, y: int, width: int | None = None, height: int | None = None) -> tuple[int, int]:
        desktop_w, desktop_h = self._desktop_bounds()
        width = width or self.size.width
        height = height or self.size.height
        max_x = max(0, desktop_w - min(width, desktop_w))
        max_y = max(0, desktop_h - min(height, desktop_h))
        return max(0, min(x, max_x)), max(0, min(y, max_y))

    def constrain_to_desktop(self) -> None:
        desktop_w, desktop_h = self._desktop_bounds()
        width = max(self.min_width, min(int(self.size.width or self.default_width), desktop_w))
        height = max(self.min_height, min(int(self.size.height or self.default_height), desktop_h))
        self.styles.width = width
        self.styles.height = height
        self.offset = self._clamp_offset(self.offset.x, self.offset.y, width, height)

    def _begin_drag(self, mode: str, event: events.MouseEvent) -> None:
        self._drag_mode = mode
        self._drag_start = (event.screen_x, event.screen_y)
        self._start_offset = (self.offset.x, self.offset.y)
        self._start_size = (max(1, self.size.width), max(1, self.size.height))
        self.capture_mouse()

    async def on_mouse_down(self, event: events.MouseDown) -> None:
        if not self.has_class("open"):
            return
        self.app.activate_window(self.window_id)
        local_x = event.screen_x - self.region.x
        local_y = event.screen_y - self.region.y
        width = max(1, self.size.width)
        height = max(1, self.size.height)
        if self._is_resize_zone(local_x, local_y, width, height):
            self._begin_drag("resize", event)
        elif 0 <= local_y <= 2 and local_x < width - 10:
            self._begin_drag("move", event)
        else:
            self._drag_mode = None
            return
        event.stop()

    async def on_mouse_move(self, event: events.MouseMove) -> None:
        if not self._drag_mode:
            return
        dx = event.screen_x - self._drag_start[0]
        dy = event.screen_y - self._drag_start[1]
        if self._drag_mode == "move":
            x, y = self._clamp_offset(self._start_offset[0] + dx, self._start_offset[1] + dy)
            self.offset = (x, y)
        elif self._drag_mode == "resize":
            desktop_w, desktop_h = self._desktop_bounds()
            max_w = max(self.min_width, desktop_w - self.offset.x)
            max_h = max(self.min_height, desktop_h - self.offset.y)
            self.styles.width = max(self.min_width, min(self._start_size[0] + dx, max_w))
            self.styles.height = max(self.min_height, min(self._start_size[1] + dy, max_h))
        event.stop()

    async def on_mouse_up(self, event: events.MouseUp) -> None:
        if self._drag_mode:
            self._drag_mode = None
            self.release_mouse()
            try:
                self.app._save_state()
            except Exception:
                pass
            event.stop()

    def _is_resize_zone(self, local_x: int, local_y: int, width: int, height: int) -> bool:
        return local_y >= height - 4 and local_x >= width - 12


class ResizeHandle(Static):
    """Canto de redimensionamento que inicia o drag diretamente."""

    async def on_mouse_down(self, event: events.MouseDown) -> None:
        parent = self.parent
        if isinstance(parent, ManagedWindow) and parent.has_class("open"):
            parent.app.activate_window(parent.window_id)
            parent._begin_drag("resize", event)
            event.stop()


# ─── Janela Bluetooth ──────────────────────────────────────────────────────────
class BluetoothPanel(ManagedWindow):
    """Painel de Bluetooth integrado ao desktop."""

    title = "Bluetooth Manager"
    icon = "󰂯"
    window_id = "bluetooth-panel"
    app_key = "bluetooth"
    default_offset = (24, 3)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._devices: dict[str, dict] = {}
        self._refresh_task: asyncio.Task | None = None

    def on_mount(self) -> None:
        super().on_mount()

    def _consume_refresh_error(self, task: asyncio.Task) -> None:
        if task.cancelled():
            return
        try:
            task.exception()
        except Exception:
            pass

    def refresh_now(self) -> None:
        if self._refresh_task and not self._refresh_task.done():
            return
        self._refresh_task = asyncio.create_task(self._refresh())
        self._refresh_task.add_done_callback(self._consume_refresh_error)

    def cancel_refresh(self) -> None:
        if self._refresh_task and not self._refresh_task.done():
            self._refresh_task.cancel()

    @staticmethod
    def _get_bt_info():
        show = run_shell("bluetoothctl show", timeout=3)
        powered = "Powered: yes" in show
        host_name = "Adaptador"
        for line in show.splitlines():
            if "Name: " in line:
                host_name = line.split("Name: ", 1)[1].strip()
                break

        dev_raw = run_shell("bluetoothctl devices", timeout=3)
        devices = {}
        for line in dev_raw.splitlines():
            parts = line.split(" ", 2)
            if len(parts) < 3:
                continue
            mac, name = parts[1], parts[2]
            if mac in devices:
                continue
            info = run_shell(f"bluetoothctl info {mac}", timeout=3)
            connected = "Connected: yes" in info
            icon_key = "default"
            for info_line in info.splitlines():
                if "Icon: " in info_line:
                    icon_key = info_line.split("Icon: ", 1)[1].strip()
                    break
            devices[mac] = {
                "mac": mac,
                "name": name,
                "connected": connected,
                "icon": ICON_MAP.get(icon_key, BT_ICON_DEFAULT),
            }
        return powered, host_name, list(devices.values())

    async def _refresh(self) -> None:
        powered, host_name, devices = self._get_bt_info()
        status = self.query_one("#bt-status", Label)
        if powered:
            status.update(f"󰂯  {host_name}  ●")
            status.add_class("online")
        else:
            status.update(f"󰂲  {host_name}  ○")
            status.remove_class("online")

        device_list = self.query_one("#bt-device-list", ListView)
        await device_list.clear()
        self._devices = {}
        for dev in devices:
            await device_list.append(DeviceItem(dev["mac"], dev["name"], dev["connected"], dev["icon"]))
            self._devices[dev["mac"]] = dev

    async def handle_button(self, bid: str) -> None:
        self.query_one("#bt-status", Label).update("Aguarde...")
        if bid == "bt-btn-power":
            cmd = "bluetoothctl show | grep -q 'Powered: yes' && bluetoothctl power off || bluetoothctl power on"
            run_shell_quiet(cmd, timeout=6)
        elif bid == "bt-btn-scan":
            self.query_one("#bt-status", Label).update("Ligando BT…")
            run_shell_quiet("bluetoothctl power off >/dev/null 2>&1", timeout=4)
            await asyncio.sleep(1)
            run_shell_quiet("bluetoothctl power on >/dev/null 2>&1", timeout=4)
            self.query_one("#bt-status", Label).update("Escaneando… (12s)")
            run_shell_quiet("timeout 12 bluetoothctl scan on", timeout=14)
        elif bid.startswith("conn-"):
            mac = bid[5:].replace("-", ":")
            run_shell_quiet(f"bluetoothctl connect {mac}", timeout=8)
        elif bid.startswith("disc-"):
            mac = bid[5:].replace("-", ":")
            run_shell_quiet(f"bluetoothctl disconnect {mac}", timeout=8)
        await self._refresh()

    DEFAULT_CSS = f"""
    BluetoothPanel {{
        position: absolute;
        layer: windows;
        layout: vertical;
        width: 82;
        height: 28;
        border: round {COLOR_BLUE};
        background: {BG_CARD};
        display: none;
    }}
    BluetoothPanel.open {{
        display: block;
    }}
    """

    def compose(self) -> ComposeResult:
        with Horizontal(classes="window-titlebar"):
            yield Label(self.icon, classes="window-icon")
            yield Label(self.title, classes="window-title")
            yield Button("×", id=f"{self.window_id}-close", classes="window-btn window-close")
        with Horizontal():
            with Vertical(id="bt-sidebar", classes="bt-sidebar"):
                yield Label("⚡ BLUETOOTH", id="bt-logo")
                yield Label("Inicializando…", id="bt-status")
                yield Button("POWER",  id="bt-btn-power",  classes="ctrl-btn")
                yield Button("SCAN",   id="bt-btn-scan",   classes="ctrl-btn")
                yield Static(classes="sidebar-spacer")
                yield Button("FECHAR", id="bt-close-btn", classes="ctrl-btn-close")
            with Vertical(id="bt-panel", classes="bt-panel"):
                yield Label("DISPOSITIVOS PAREADOS", id="bt-panel-title")
                yield ListView(id="bt-device-list")
        yield ResizeHandle("◢", classes="resize-handle")


# ─── Janela Wi-Fi ──────────────────────────────────────────────────────────────
class WifiPanel(ManagedWindow):
    """Painel de Wi‑Fi integrado ao desktop."""

    title = "Wi‑Fi Manager"
    icon = "📶"
    window_id = "wifi-panel"
    app_key = "wifi"
    default_offset = (30, 5)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._networks: dict[str, NetworkItem] = {}
        self._network_ids: dict[str, str] = {}
        self._connected_ssid: str | None = None
        self._refresh_task: asyncio.Task | None = None

    def on_mount(self) -> None:
        super().on_mount()

    def _consume_refresh_error(self, task: asyncio.Task) -> None:
        if task.cancelled():
            return
        try:
            task.exception()
        except Exception:
            pass

    def refresh_now(self) -> None:
        if self._refresh_task and not self._refresh_task.done():
            return
        self._refresh_task = asyncio.create_task(self._refresh())
        self._refresh_task.add_done_callback(self._consume_refresh_error)

    def cancel_refresh(self) -> None:
        if self._refresh_task and not self._refresh_task.done():
            self._refresh_task.cancel()

    @staticmethod
    def _run_cmd(cmd: str) -> str:
        return run_shell(cmd, timeout=5)

    def _get_status(self) -> tuple[bool, str]:
        powered = self._run_cmd("nmcli radio wifi") == "enabled"
        ssid = ""
        if powered:
            out = self._run_cmd("nmcli -t -f ACTIVE,SSID dev wifi | grep '^yes'")
            if out:
                ssid = out.split(":", 1)[1]
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

    @staticmethod
    def _safe_ssid(ssid: str) -> str:
        return re.sub(r"[^A-Za-z0-9_-]", "_", ssid)

    async def _refresh(self) -> None:
        powered, cur_ssid = self._get_status()
        networks = self._scan_networks()
        status = self.query_one("#wf-status", Label)
        if powered:
            status.update("󰤨  WiFi ATIVADO ●")
            status.add_class("online")
        else:
            status.update("󰤭  WiFi DESATIVADO ○")
            status.remove_class("online")

        list_view = self.query_one("#wf-network-list", ListView)
        await list_view.clear()
        self._networks = {}
        self._network_ids = {}
        for ssid, signal, sec in networks:
            connected = ssid == cur_ssid
            item = NetworkItem(ssid, signal, sec, connected)
            await list_view.append(item)
            self._networks[ssid] = item
            self._network_ids[self._safe_ssid(ssid)] = ssid
        self._connected_ssid = cur_ssid

    async def handle_button(self, bid: str) -> None:
        self.query_one("#wf-status", Label).update("Aguarde...")
        if bid == "wf-btn-power":
            run_shell_quiet("nmcli radio wifi toggle", timeout=8)
        elif bid == "wf-btn-scan":
            run_shell_quiet("nmcli dev wifi list --rescan yes", timeout=10)
        elif bid.startswith("conn-"):
            key = bid[5:]
            ssid = self._network_ids.get(key)
            if ssid:
                run_shell_quiet(f"nmcli dev wifi connect '{ssid}'", timeout=15)
        elif bid.startswith("disc-"):
            run_shell_quiet("nmcli networking off && nmcli networking on", timeout=10)
        await self._refresh()

    DEFAULT_CSS = f"""
    WifiPanel {{
        position: absolute;
        layer: windows;
        layout: vertical;
        width: 82;
        height: 28;
        border: round {COLOR_BLUE};
        background: {BG_CARD};
        display: none;
    }}
    WifiPanel.open {{
        display: block;
    }}
    """

    def compose(self) -> ComposeResult:
        with Horizontal(classes="window-titlebar"):
            yield Label(self.icon, classes="window-icon")
            yield Label(self.title, classes="window-title")
            yield Button("×", id=f"{self.window_id}-close", classes="window-btn window-close")
        with Horizontal():
            with Vertical(id="wf-sidebar", classes="bt-sidebar"):
                yield Label("⚡ WI‑FI", id="wf-logo")
                yield Label("Inicializando…", id="wf-status")
                yield Button("POWER",  id="wf-btn-power",  classes="ctrl-btn")
                yield Button("SCAN",   id="wf-btn-scan",   classes="ctrl-btn")
                yield Static(classes="sidebar-spacer")
                yield Button("FECHAR", id="wf-close-btn", classes="ctrl-btn-close")
            with Vertical(id="wf-panel", classes="bt-panel"):
                yield Label("REDES DISPONÍVEIS", id="wf-panel-title")
                yield ListView(id="wf-network-list")
        yield ResizeHandle("◢", classes="resize-handle")


# ─── Desktop App ───────────────────────────────────────────────────────────────
class DesktopApp(App[None]):
    """Terminal-Essentials Desktop – tema Áquila Azure Night."""

    CSS = CSS

    BINDINGS = [
        Binding("ctrl+b",      "open_bluetooth",    "Bluetooth", show=True),
        Binding("ctrl+w",      "open_wifi",         "Wi‑Fi", show=True),
        Binding("ctrl+q",      "quit_app",          "Sair", show=True),
    ]

    def compose(self) -> ComposeResult:
        # Topbar
        with Static(id="topbar"):
            yield Label("⚡ Terminal-Essentials", id="topbar-title")
            yield Label(" Áquila Azure Night ", id="topbar-theme")
            yield Label(os.uname().nodename, id="topbar-host")

        # Área principal do desktop
        with Container(id="desktop"):
            yield Label(
                "Terminal-Essentials\n\nCtrl+B → Bluetooth   Ctrl+W → Wi‑Fi   Ctrl+Q → Sair",
                id="wallpaper"
            )
            with Vertical(id="desktop-icons"):
                with Horizontal(classes="desktop-row"):
                    yield Button("󰤨 Wi‑Fi", id="desktop-wifi", classes="desktop-icon")
                    yield Button("󰂯  BT", id="desktop-bluetooth", classes="desktop-icon")
                    yield Button("📊 Proc", id="desktop-process", classes="desktop-icon")
                    yield Button("💻  Sys", id="desktop-sysmon", classes="desktop-icon")
                with Horizontal(classes="desktop-row"):
                    yield Button("📁 Arqs", id="desktop-files", classes="desktop-icon")
                    yield Button("📻 Rádio", id="desktop-radio", classes="desktop-icon")
                    yield Button("📝 Notas", id="desktop-notes", classes="desktop-icon")
                    yield Button("🌤 Clima", id="desktop-weather", classes="desktop-icon")
                with Horizontal(classes="desktop-row"):
                    yield Button("🔧  Cmd", id="desktop-commands", classes="desktop-icon")
                    yield Button("🍅 Pomo", id="desktop-pomodoro", classes="desktop-icon")
                    yield Button("🐳 Dock", id="desktop-docker", classes="desktop-icon")
                    yield Button("🎵 Musi", id="desktop-music", classes="desktop-icon")
            yield BluetoothPanel(id="bluetooth-panel")
            yield WifiPanel(id="wifi-panel")

        # Start menu (docked bottom)
        yield StartMenu(id="start-menu")

        # Botão Iniciar
        yield Button("⚡ Iniciar", id="start-button")

        # Taskbar
        yield TaskBar(id="taskbar")

    # ── Lifecycle ──────────────────────────────────────────────────────────────
    def on_mount(self) -> None:
        self._open_panels: set[str] = set()
        self._load_state()

    def on_resize(self, event: events.Resize) -> None:
        for panel in self.query(ManagedWindow):
            panel.constrain_to_desktop()

    # ── State persistence ──────────────────────────────────────────────────────
    def _save_state(self) -> None:
        open_panels = sorted(getattr(self, "_open_panels", set()))
        geometry = {}
        for panel_cls in (BluetoothPanel, WifiPanel):
            try:
                panel = self.query_one(panel_cls)
                geometry[panel.app_key] = panel.snapshot()
            except Exception:
                pass
        try:
            STATE_FILE.write_text(json.dumps({"open": open_panels, "geometry": geometry}))
        except Exception:
            pass

    def _load_state(self) -> None:
        if not STATE_FILE.is_file():
            return
        try:
            data = json.loads(STATE_FILE.read_text())
            geometry = data.get("geometry", {})
            for panel_cls in (BluetoothPanel, WifiPanel):
                panel = self.query_one(panel_cls)
                panel_state = geometry.get(panel.app_key)
                if isinstance(panel_state, dict):
                    panel.restore(panel_state)
            for name in data.get("open", []):
                if name == "bluetooth":
                    self.action_open_bluetooth()
                elif name == "wifi":
                    self.action_open_wifi()
        except Exception:
            pass

    # ── Actions ────────────────────────────────────────────────────────────────
    def action_toggle_start_menu(self) -> None:
        self.query_one(StartMenu).toggle()

    def activate_window(self, window_id: str) -> None:
        try:
            panel = self.query_one(f"#{window_id}", ManagedWindow)
            for other in self.query(ManagedWindow):
                other.styles.layer = "windows"
            panel.add_class("open")
            panel.styles.layer = "window-active"
            panel.focus()
            self.query_one(TaskBar).set_active(window_id)
        except Exception:
            pass

    def _close_panel(self, panel_cls: type[ManagedWindow], app_key: str, window_id: str) -> None:
        try:
            panel = self.query_one(panel_cls)
            if hasattr(panel, "cancel_refresh"):
                panel.cancel_refresh()
            panel.remove_class("open")
            self._open_panels.discard(app_key)
            self.query_one(TaskBar).remove_window_button(window_id)
            self._save_state()
        except Exception:
            pass

    def action_open_bluetooth(self) -> None:
        panel = self.query_one(BluetoothPanel)
        panel.constrain_to_desktop()
        panel.add_class("open")
        panel.refresh_now()
        self._open_panels.add("bluetooth")
        taskbar = self.query_one(TaskBar)
        taskbar.add_window_button(panel)
        # Close start menu if open
        self.query_one(StartMenu).remove_class("visible")
        self.activate_window("bluetooth-panel")
        self._save_state()

    def action_open_wifi(self) -> None:
        panel = self.query_one(WifiPanel)
        panel.constrain_to_desktop()
        panel.add_class("open")
        panel.refresh_now()
        self._open_panels.add("wifi")
        taskbar = self.query_one(TaskBar)
        taskbar.add_window_button(panel)
        self.query_one(StartMenu).remove_class("visible")
        self.activate_window("wifi-panel")
        self._save_state()

    def action_quit_app(self) -> None:
        self._save_state()
        for panel in self.query(ManagedWindow):
            if hasattr(panel, "cancel_refresh"):
                panel.cancel_refresh()
        self.workers.cancel_all()
        self.exit()

    def on_window_closed(self, window_id: str) -> None:
        try:
            self.query_one(TaskBar).remove_window_button(window_id)
        except Exception:
            pass

    # ── App launcher ──────────────────────────────────────────────────────────
    @staticmethod
    def _launch_app(filename: str) -> None:
        import shutil
        terminal = shutil.which("kitty") or shutil.which("xterm") or "x-terminal-emulator"
        script = Path(__file__).parent / filename
        subprocess.Popen(
            [terminal, "python3", str(script)],
            start_new_session=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    # ── Button routing ─────────────────────────────────────────────────────────
    @on(Button.Pressed)
    async def _on_btn(self, event: Button.Pressed) -> None:
        bid = event.button.id or ""

        if bid == "start-button":
            self.action_toggle_start_menu()
        elif bid in ("start-bluetooth", "desktop-bluetooth"):
            self.action_open_bluetooth()
        elif bid in ("start-wifi", "desktop-wifi"):
            self.action_open_wifi()
        elif bid in ("start-process", "desktop-process"):
            self._launch_app("aquila_process_tui.py")
        elif bid in ("start-sysmon", "desktop-sysmon"):
            self._launch_app("aquila_sysmon_tui.py")
        elif bid in ("start-files", "desktop-files"):
            self._launch_app("aquila_files_tui.py")
        elif bid in ("start-radio", "desktop-radio"):
            self._launch_app("aquila_radio_tui.py")
        elif bid in ("start-notes", "desktop-notes"):
            self._launch_app("aquila_notes_tui.py")
        elif bid in ("start-weather", "desktop-weather"):
            self._launch_app("aquila_weather_tui.py")
        elif bid in ("start-commands", "desktop-commands"):
            self._launch_app("aquila_commands_tui.py")
        elif bid in ("start-pomodoro", "desktop-pomodoro"):
            self._launch_app("aquila_pomodoro_tui.py")
        elif bid in ("start-docker", "desktop-docker"):
            self._launch_app("aquila_docker_tui.py")
        elif bid in ("start-music", "desktop-music"):
            self._launch_app("aquila_music_tui.py")
        elif bid == "menu-exit-btn":
            self.action_quit_app()
        elif bid in ("bt-close-btn", "bluetooth-panel-close"):
            self._close_panel(BluetoothPanel, "bluetooth", "bluetooth-panel")
        elif bid in ("wf-close-btn", "wifi-panel-close"):
            self._close_panel(WifiPanel, "wifi", "wifi-panel")
        elif bid in ("bt-btn-power", "bt-btn-scan") or bid.startswith(("conn-", "disc-")):
            wifi = self.query_one(WifiPanel)
            if bid.startswith(("conn-", "disc-")) and bid[5:] in getattr(wifi, "_network_ids", {}):
                await wifi.handle_button(bid)
            else:
                await self.query_one(BluetoothPanel).handle_button(bid)
        elif bid in ("wf-btn-power", "wf-btn-scan"):
            await self.query_one(WifiPanel).handle_button(bid)

    async def on_unmount(self) -> None:
        # Estado já foi salvo em action_quit_app ou ao fechar painéis.
        # Não chamar _save_state aqui pois a screen stack já foi desmontada.
        pass


if __name__ == "__main__":
    DesktopApp().run()

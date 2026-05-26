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
from rich.text import Text as RichText

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
from aquila_process_tui import ProcItem
from aquila_files_tui import FileItem, DIR_ICON, FILE_ICON
from aquila_radio_tui import StationItem, STATIONS
from aquila_notes_tui import NoteItem, NOTES_DIR
from aquila_commands_tui import CmdItem, DEFAULT_COMMANDS
from aquila_docker_tui import DockerItem
from aquila_music_tui import MusicItem, MUSIC_EXTS, AUDIO_DIR

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
    align: center middle;
    padding: 0;
}}

#desktop-icons {{
    position: absolute;
    width: 100%;
    height: 100%;
    layout: vertical;
    align: center middle;
}}

.desktop-row {{
    width: auto;
    height: auto;
    layout: horizontal;
    align: center middle;
}}

.desktop-icon {{
    width: 10;
    height: 3;
    margin: 1 1;
    background: transparent;
    color: {COLOR_TEXT};
    border: none;
    text-style: bold;
    content-align: center middle;
    padding: 0 0;
    transition: background 150ms, color 150ms;
}}

.desktop-icon:hover {{
    background: {BG_GLASS};
    color: {COLOR_BLUE};
    border: none;
}}

/* ── Barra de status superior (topbar) ──────────────────── */
#topbar {{
    dock: top;
    width: 100%;
    height: 1;
    background: {BG_GLASS};
    layout: horizontal;
    padding: 0 1;
}}

#topbar-left {{
    width: 1fr;
}}

#topbar-right {{
    width: auto;
    color: #AAB6D6;
    text-style: italic;
}}

/* ── Watermark / wallpaper text ─────────────────────────── */
#wallpaper {{
    width: 100%;
    height: 1fr;
    content-align: center middle;
    color: #0f1a30;
    text-style: bold;
    padding: 0;
    margin: 0;
}}

/* ── Botão Iniciar ──────────────────────────────────────── */
#start-button {{
    dock: bottom;
    width: 16;
    height: 2;
    background: {COLOR_BLUE};
    color: {BG_MAIN};
    border: none;
    text-style: bold;
    content-align: center middle;
    padding: 0 1;
    transition: background 150ms;
}}

#start-button:hover {{
    background: #A7BDF5;
}}

/* ── Painéis internos (sidebar dos sub-apps) ────────────── */
.bt-sidebar {{
    width: 20;
    height: 100%;
    padding: 0 1;
    layout: vertical;
    border-right: round {BG_GLASS};
}}

.bt-panel {{
    width: 1fr;
    height: 100%;
    padding: 0 1;
    layout: vertical;
}}

.window-titlebar {{
    height: 2;
    background: #0d1424;
    border-bottom: solid #1d2a44;
    layout: horizontal;
    align: left middle;
    padding: 0 1;
}}

.window-icon {{
    width: 3;
    color: {COLOR_BLUE};
    text-style: bold;
}}

.window-title {{
    width: 1fr;
    color: {COLOR_TEXT};
    text-style: bold;
}}

.window-btn {{
    width: 3;
    height: 1;
    margin-left: 1;
    background: {BG_GLASS};
    color: {COLOR_TEXT};
    border: none;
    text-style: bold;
    content-align: center middle;
    transition: background 120ms;
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
    height: 1;
    content-align: right middle;
    color: {COLOR_BLUE};
    background: {BG_CARD};
    padding-right: 1;
    border-top: solid #1d2a44;
}}

DeviceItem, NetworkItem {{
    height: 2;
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
    padding: 0 1;
    border: none;
    background: {COLOR_BLUE};
    color: {BG_MAIN};
    text-style: bold;
    content-align: center middle;
}}

.btn-disconnect {{
    height: 1;
    min-width: 12;
    padding: 0 1;
    border: none;
    background: {COLOR_RED};
    color: {BG_MAIN};
    text-style: bold;
    content-align: center middle;
}}

#bt-logo, #wf-logo {{
    height: 1;
    content-align: center middle;
    color: {COLOR_BLUE};
    text-style: bold;
    margin-bottom: 0;
}}

#bt-status, #wf-status {{
    height: 2;
    border: round #B8B7D9;
    background: {BG_GLASS};
    content-align: center middle;
    color: #A7BDF5;
    margin-bottom: 1;
    padding: 0 1;
}}

#bt-panel-title, #wf-panel-title {{
    height: 1;
    color: {COLOR_MUTED};
    text-style: bold;
    margin-bottom: 0;
}}

.ctrl-btn {{
    width: 100%;
    height: 2;
    margin-bottom: 0;
    background: {BG_GLASS};
    color: #A7BDF5;
    border: none;
    text-style: bold;
    content-align: center middle;
    transition: background 120ms, color 120ms;
}}

.ctrl-btn:hover {{
    background: {COLOR_BLUE};
    color: {BG_MAIN};
}}

.ctrl-btn-close {{
    width: 100%;
    height: 2;
    background: {BG_GLASS};
    color: #D9B8CC;
    border: none;
    text-style: bold;
    content-align: center middle;
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
    default_offset = (2, 1)
    min_width = 44
    min_height = 12
    default_width = 64
    default_height = 18

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
        width: 64;
        height: 18;
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
        self._start_auto_refresh()

    def _start_auto_refresh(self) -> None:
        if self._refresh_task and not self._refresh_task.done():
            return
        self._refresh_task = asyncio.create_task(self._auto_refresh_loop())

    def _consume_refresh_error(self, task: asyncio.Task) -> None:
        if task.cancelled():
            return
        try:
            task.exception()
        except Exception:
            pass

    def refresh_now(self) -> None:
        self._start_auto_refresh()

    def cancel_refresh(self) -> None:
        if self._refresh_task and not self._refresh_task.done():
            self._refresh_task.cancel()

    async def _auto_refresh_loop(self) -> None:
        while True:
            try:
                await self._refresh()
            except Exception:
                pass
            await asyncio.sleep(5)

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
            text = "󰤨  WiFi ATIVADO"
            if cur_ssid:
                text += f"  •  {cur_ssid}"
            status.update(text)
            status.add_class("online")
        else:
            status.update("󰤭  WiFi DESATIVADO")
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
        width: 64;
        height: 18;
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


# ─── Janela Processos ──────────────────────────────────────────────────────────
class ProcessPanel(ManagedWindow):
    title = "Gerenciador de Processos"
    icon = "📊"
    window_id = "process-panel"
    app_key = "process"
    default_offset = (10, 3)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._refresh_task: asyncio.Task | None = None

    def on_mount(self) -> None:
        super().on_mount()

    def _consume_refresh_error(self, task: asyncio.Task) -> None:
        if task.cancelled(): return
        try: task.exception()
        except: pass

    def refresh_now(self) -> None:
        if self._refresh_task and not self._refresh_task.done(): return
        self._refresh_task = asyncio.create_task(self._refresh())
        self._refresh_task.add_done_callback(self._consume_refresh_error)

    def cancel_refresh(self) -> None:
        if self._refresh_task and not self._refresh_task.done():
            self._refresh_task.cancel()

    @staticmethod
    def _get_processes():
        import pwd
        procs = []
        try:
            for p in os.listdir("/proc"):
                if not p.isdigit(): continue
                try:
                    with open(f"/proc/{p}/status") as f:
                        lines = f.readlines()
                    name = ""
                    for line in lines:
                        if line.startswith("Name:"):
                            name = line.split(":", 1)[1].strip()
                            break
                    with open(f"/proc/{p}/stat") as f:
                        parts = f.read().split()
                    state = parts[2] if len(parts) > 2 else "?"
                    try:
                        with open(f"/proc/{p}/cmdline") as f:
                            cmdline = f.read().replace("\0", " ").strip()
                    except:
                        cmdline = name
                    procs.append({"pid": int(p), "name": name, "state": state, "cmdline": cmdline or name})
                except:
                    pass
        except:
            pass
        return sorted(procs, key=lambda x: x["pid"])

    async def _refresh(self) -> None:
        procs = self._get_processes()
        status = self.query_one("#pr-status", Label)
        status.update(f"📊 {len(procs)} processos")
        lst = self.query_one("#pr-list", ListView)
        await lst.clear()
        for p in procs[:200]:
            await lst.append(ProcItem(p["pid"], p["cmdline"][:40], 0.0, 0.0))

    async def handle_button(self, bid: str) -> None:
        if bid == "pr-btn-refresh":
            await self._refresh()
        elif bid.startswith("kill-"):
            try:
                pid = int(bid[5:])
                os.kill(pid, signal.SIGKILL)
            except:
                pass
            await self._refresh()

    DEFAULT_CSS = f"""
    ProcessPanel {{ position: absolute; layer: windows; layout: vertical; width: 64; height: 18; border: round {COLOR_BLUE}; background: {BG_CARD}; display: none; }}
    ProcessPanel.open {{ display: block; }}
    """

    def compose(self) -> ComposeResult:
        with Horizontal(classes="window-titlebar"):
            yield Label(self.icon, classes="window-icon")
            yield Label(self.title, classes="window-title")
            yield Button("×", id="process-panel-close", classes="window-btn window-close")
        with Horizontal():
            with Vertical(classes="bt-sidebar"):
                yield Label("📊 PROCESSOS", id="pr-logo")
                yield Label("Carregando…", id="pr-status")
                yield Button("RECARREGAR", id="pr-btn-refresh", classes="ctrl-btn")
                yield Static(classes="sidebar-spacer")
                yield Button("FECHAR", id="pr-close-btn", classes="ctrl-btn-close")
            with Vertical(classes="bt-panel"):
                yield Label("PROCESSOS ATIVOS", id="pr-panel-title")
                yield ListView(id="pr-list")
        yield ResizeHandle("◢", classes="resize-handle")


# ─── Janela SysMon ─────────────────────────────────────────────────────────────
class SysMonPanel(ManagedWindow):
    title = "Monitor do Sistema"
    icon = "💻"
    window_id = "sysmon-panel"
    app_key = "sysmon"
    default_offset = (16, 4)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._refresh_task: asyncio.Task | None = None

    def on_mount(self) -> None:
        super().on_mount()

    def _consume_refresh_error(self, task: asyncio.Task) -> None:
        if task.cancelled(): return
        try: task.exception()
        except: pass

    def refresh_now(self) -> None:
        if self._refresh_task and not self._refresh_task.done(): return
        self._refresh_task = asyncio.create_task(self._refresh())
        self._refresh_task.add_done_callback(self._consume_refresh_error)

    def cancel_refresh(self) -> None:
        if self._refresh_task and not self._refresh_task.done():
            self._refresh_task.cancel()

    def _get_stats(self):
        stats = {"cpu": 0, "mem_pct": 0, "mem_used": 0, "mem_total": 0, "disk_pct": 0, "disk_used": 0, "disk_total": 0, "host": os.uname().nodename, "uptime": 0}
        try:
            with open("/proc/stat") as f:
                parts = f.readline().split()
                if len(parts) > 4:
                    total = sum(int(x) for x in parts[1:4])
                    idle = int(parts[4])
                    stats["cpu"] = round((total - idle) / total * 100, 1) if total > 0 else 0
        except: pass
        try:
            with open("/proc/meminfo") as f:
                lines = f.readlines()
            total = int(lines[0].split()[1]) if len(lines) > 0 else 0
            avail = int(lines[2].split()[1]) if len(lines) > 2 else 0
            stats["mem_total"] = total // 1024
            stats["mem_used"] = (total - avail) // 1024
            stats["mem_pct"] = round((total - avail) / total * 100, 1) if total > 0 else 0
        except: pass
        try:
            import shutil
            usage = shutil.disk_usage("/")
            stats["disk_total"] = usage.total // (1024**3)
            stats["disk_used"] = usage.used // (1024**3)
            stats["disk_pct"] = round(usage.used / usage.total * 100, 1)
        except: pass
        try:
            with open("/proc/uptime") as f:
                stats["uptime"] = int(float(f.read().split()[0]) / 60)
        except: pass
        return stats

    async def _refresh(self) -> None:
        s = self._get_stats()
        self.query_one("#sm-host", Label).update(f"💻 {s['host']}")
        self.query_one("#sm-cpu", Label).update(f"CPU: {s['cpu']}%")
        self.query_one("#sm-mem", Label).update(f"RAM: {s['mem_used']}/{s['mem_total']}MB ({s['mem_pct']}%)")
        self.query_one("#sm-disk", Label).update(f"DISK: {s['disk_used']}/{s['disk_total']}GB ({s['disk_pct']}%)")
        self.query_one("#sm-uptime", Label).update(f"Uptime: {s['uptime']}min")

    async def handle_button(self, bid: str) -> None:
        if bid == "sm-btn-refresh":
            await self._refresh()

    DEFAULT_CSS = f"""
    SysMonPanel {{ position: absolute; layer: windows; layout: vertical; width: 56; height: 16; border: round {COLOR_BLUE}; background: {BG_CARD}; display: none; }}
    SysMonPanel.open {{ display: block; }}
    """

    def compose(self) -> ComposeResult:
        with Horizontal(classes="window-titlebar"):
            yield Label(self.icon, classes="window-icon")
            yield Label(self.title, classes="window-title")
            yield Button("×", id="sysmon-panel-close", classes="window-btn window-close")
        with Vertical():
            yield Label("💻 ...", id="sm-host")
            yield Label("CPU: ...", id="sm-cpu")
            yield Label("RAM: ...", id="sm-mem")
            yield Label("DISK: ...", id="sm-disk")
            yield Label("Uptime: ...", id="sm-uptime")
            yield Static(classes="sidebar-spacer")
            with Horizontal():
                yield Button("ATUALIZAR", id="sm-btn-refresh")
                yield Static()
                yield Button("FECHAR", id="sm-close-btn")
        yield ResizeHandle("◢", classes="resize-handle")


# ─── Janela Arquivos ───────────────────────────────────────────────────────────
class FilesPanel(ManagedWindow):
    title = "Gerenciador de Arquivos"
    icon = "📁"
    window_id = "files-panel"
    app_key = "files"
    default_offset = (8, 2)
    _current_path: str = "/"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._refresh_task: asyncio.Task | None = None

    def on_mount(self) -> None:
        super().on_mount()

    def _consume_refresh_error(self, task: asyncio.Task) -> None:
        if task.cancelled(): return
        try: task.exception()
        except: pass

    def refresh_now(self) -> None:
        if self._refresh_task and not self._refresh_task.done(): return
        self._refresh_task = asyncio.create_task(self._refresh())
        self._refresh_task.add_done_callback(self._consume_refresh_error)

    def cancel_refresh(self) -> None:
        if self._refresh_task and not self._refresh_task.done():
            self._refresh_task.cancel()

    @staticmethod
    def _list_dir(path: str):
        entries = []
        try:
            for e in sorted(os.listdir(path)):
                full = os.path.join(path, e)
                is_dir = os.path.isdir(full)
                try:
                    size = os.path.getsize(full)
                    mtime = os.path.getmtime(full)
                except:
                    size, mtime = 0, 0
                entries.append({"name": e, "is_dir": is_dir, "size": size, "mtime": mtime})
        except:
            pass
        return entries

    async def _refresh(self) -> None:
        self.query_one("#fl-path", Label).update(f"📁 {self._current_path}")
        entries = self._list_dir(self._current_path)
        lst = self.query_one("#fl-list", ListView)
        await lst.clear()
        for e in entries:
            icon = DIR_ICON if e["is_dir"] else FILE_ICON
            await lst.append(FileItem(os.path.join(self._current_path, e["name"]), icon, e["name"], str(e["size"]), "", e["is_dir"]))

    async def handle_button(self, bid: str) -> None:
        if bid == "fl-btn-back":
            self._current_path = os.path.dirname(self._current_path.rstrip("/")) or "/"
            await self._refresh()
        elif bid == "fl-btn-up":
            parent = os.path.dirname(self._current_path.rstrip("/")) or "/"
            if parent != self._current_path:
                self._current_path = parent
                await self._refresh()

    DEFAULT_CSS = f"""
    FilesPanel {{ position: absolute; layer: windows; layout: vertical; width: 66; height: 18; border: round {COLOR_BLUE}; background: {BG_CARD}; display: none; }}
    FilesPanel.open {{ display: block; }}
    """

    def compose(self) -> ComposeResult:
        with Horizontal(classes="window-titlebar"):
            yield Label(self.icon, classes="window-icon")
            yield Label(self.title, classes="window-title")
            yield Button("×", id="files-panel-close", classes="window-btn window-close")
        with Vertical():
            with Horizontal():
                yield Button("←", id="fl-btn-back")
                yield Button("↑", id="fl-btn-up")
                yield Label("📁 /", id="fl-path")
            yield Label("ARQUIVOS", id="fl-panel-title")
            yield ListView(id="fl-list")
            yield Button("FECHAR", id="fl-close-btn")
        yield ResizeHandle("◢", classes="resize-handle")


# ─── Janela Rádio ──────────────────────────────────────────────────────────────
class RadioPanel(ManagedWindow):
    title = "Rádio Online"
    icon = "📻"
    window_id = "radio-panel"
    app_key = "radio"
    default_offset = (12, 3)

    def compose(self) -> ComposeResult:
        with Horizontal(classes="window-titlebar"):
            yield Label(self.icon, classes="window-icon")
            yield Label(self.title, classes="window-title")
            yield Button("×", id="radio-panel-close", classes="window-btn window-close")
        with Horizontal():
            with Vertical(classes="bt-sidebar"):
                yield Label("📻 RÁDIO", id="rd-logo")
                yield Label("Parado", id="rd-now")
                yield Button("▶ PLAY", id="rd-btn-play", classes="ctrl-btn")
                yield Button("⏹ STOP", id="rd-btn-stop", classes="ctrl-btn")
                yield Static(classes="sidebar-spacer")
                yield Button("FECHAR", id="rd-close-btn", classes="ctrl-btn-close")
            with Vertical(classes="bt-panel"):
                yield Label("ESTAÇÕES", id="rd-panel-title")
                yield ListView(id="rd-list")
        yield ResizeHandle("◢", classes="resize-handle")

    DEFAULT_CSS = f"""
    RadioPanel {{ position: absolute; layer: windows; layout: vertical; width: 56; height: 16; border: round {COLOR_BLUE}; background: {BG_CARD}; display: none; }}
    RadioPanel.open {{ display: block; }}
    """

    def on_mount(self) -> None:
        super().on_mount()
        self._load_stations()

    async def _load_stations(self):
        lst = self.query_one("#rd-list", ListView)
        await lst.clear()
        for i, (name, url) in enumerate(STATIONS):
            await lst.append(StationItem(i, name, url))

    async def handle_button(self, bid: str) -> None:
        if bid == "rd-btn-play":
            self.query_one("#rd-now", Label).update("▶ Tocando…")
        elif bid == "rd-btn-stop":
            self.query_one("#rd-now", Label).update("⏹ Parado")


# ─── Janela Notas ──────────────────────────────────────────────────────────────
class NotesPanel(ManagedWindow):
    title = "Notas"
    icon = "📝"
    window_id = "notes-panel"
    app_key = "notes"
    default_offset = (14, 3)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._refresh_task: asyncio.Task | None = None

    def on_mount(self) -> None:
        super().on_mount()

    def _consume_refresh_error(self, task: asyncio.Task) -> None:
        if task.cancelled(): return
        try: task.exception()
        except: pass

    def refresh_now(self) -> None:
        if self._refresh_task and not self._refresh_task.done(): return
        self._refresh_task = asyncio.create_task(self._refresh())
        self._refresh_task.add_done_callback(self._consume_refresh_error)

    def cancel_refresh(self) -> None:
        if self._refresh_task and not self._refresh_task.done():
            self._refresh_task.cancel()

    def _get_notes(self):
        notes = []
        try:
            NOTES_DIR.mkdir(parents=True, exist_ok=True)
            for f in sorted(NOTES_DIR.iterdir()):
                if f.suffix == ".txt":
                    notes.append(NoteItem(str(f), f.stem, ""))
        except:
            pass
        return notes

    async def _refresh(self) -> None:
        notes = self._get_notes()
        self.query_one("#nt-status", Label).update(f"📝 {len(notes)} notas")
        lst = self.query_one("#nt-list", ListView)
        await lst.clear()
        for n in notes:
            await lst.append(n)

    async def handle_button(self, bid: str) -> None:
        if bid == "nt-btn-new":
            inp = self.query_one("#nt-input")
            inp.focus()

    DEFAULT_CSS = f"""
    NotesPanel {{ position: absolute; layer: windows; layout: vertical; width: 56; height: 16; border: round {COLOR_BLUE}; background: {BG_CARD}; display: none; }}
    NotesPanel.open {{ display: block; }}
    """

    def compose(self) -> ComposeResult:
        with Horizontal(classes="window-titlebar"):
            yield Label(self.icon, classes="window-icon")
            yield Label(self.title, classes="window-title")
            yield Button("×", id="notes-panel-close", classes="window-btn window-close")
        with Horizontal():
            with Vertical(classes="bt-sidebar"):
                yield Label("📝 NOTAS", id="nt-logo")
                yield Label("0 notas", id="nt-status")
                yield Button("NOVA", id="nt-btn-new", classes="ctrl-btn")
                yield Static(classes="sidebar-spacer")
                yield Button("FECHAR", id="nt-close-btn", classes="ctrl-btn-close")
            with Vertical(classes="bt-panel"):
                yield Label("MINHAS NOTAS", id="nt-panel-title")
                yield ListView(id="nt-list")
        yield ResizeHandle("◢", classes="resize-handle")


# ─── Janela Clima ───────────────────────────────────────────────────────────────
class WeatherPanel(ManagedWindow):
    title = "Clima"
    icon = "🌤"
    window_id = "weather-panel"
    app_key = "weather"
    default_offset = (18, 4)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._refresh_task: asyncio.Task | None = None

    def on_mount(self) -> None:
        super().on_mount()

    def _consume_refresh_error(self, task: asyncio.Task) -> None:
        if task.cancelled(): return
        try: task.exception()
        except: pass

    def refresh_now(self) -> None:
        if self._refresh_task and not self._refresh_task.done(): return
        self._refresh_task = asyncio.create_task(self._refresh())
        self._refresh_task.add_done_callback(self._consume_refresh_error)

    def cancel_refresh(self) -> None:
        if self._refresh_task and not self._refresh_task.done():
            self._refresh_task.cancel()

    async def _refresh(self) -> None:
        import urllib.request, json
        status = self.query_one("#we-status", Label)
        try:
            req = urllib.request.urlopen("https://wttr.in/?format=%C|%t|%h|%w", timeout=5)
            data = req.read().decode().strip()
            parts = data.split("|")
            cond, temp, hum, wind = (parts + [""]*4)[:4]
            self.query_one("#we-cond", Label).update(f"🌤 {cond}")
            self.query_one("#we-temp", Label).update(f"🌡 {temp}")
            self.query_one("#we-hum", Label).update(f"💧 {hum}")
            self.query_one("#we-wind", Label).update(f"🌬 {wind}")
            status.update("🌤 Online")
        except:
            status.update("⚠ Sem internet")

    async def handle_button(self, bid: str) -> None:
        if bid == "we-btn-refresh":
            await self._refresh()

    DEFAULT_CSS = f"""
    WeatherPanel {{ position: absolute; layer: windows; layout: vertical; width: 52; height: 14; border: round {COLOR_BLUE}; background: {BG_CARD}; display: none; }}
    WeatherPanel.open {{ display: block; }}
    """

    def compose(self) -> ComposeResult:
        with Horizontal(classes="window-titlebar"):
            yield Label(self.icon, classes="window-icon")
            yield Label(self.title, classes="window-title")
            yield Button("×", id="weather-panel-close", classes="window-btn window-close")
        with Vertical():
            yield Label("🌤 Carregando…", id="we-status")
            yield Label("", id="we-cond")
            yield Label("", id="we-temp")
            yield Label("", id="we-hum")
            yield Label("", id="we-wind")
            yield Static(classes="sidebar-spacer")
            with Horizontal():
                yield Button("ATUALIZAR", id="we-btn-refresh", classes="ctrl-btn")
                yield Static()
                yield Button("FECHAR", id="we-close-btn", classes="ctrl-btn-close")
        yield ResizeHandle("◢", classes="resize-handle")


# ─── Janela Comandos ────────────────────────────────────────────────────────────
class CommandsPanel(ManagedWindow):
    title = "Comandos"
    icon = "🔧"
    window_id = "commands-panel"
    app_key = "commands"
    default_offset = (10, 2)

    def compose(self) -> ComposeResult:
        with Horizontal(classes="window-titlebar"):
            yield Label(self.icon, classes="window-icon")
            yield Label(self.title, classes="window-title")
            yield Button("×", id="commands-panel-close", classes="window-btn window-close")
        with Horizontal():
            with Vertical(classes="bt-sidebar"):
                yield Label("🔧 COMANDOS", id="cm-logo")
                yield Label(f"{len(DEFAULT_COMMANDS)} comandos", id="cm-status")
                yield Static(classes="sidebar-spacer")
                yield Button("FECHAR", id="cm-close-btn", classes="ctrl-btn-close")
            with Vertical(classes="bt-panel"):
                yield Label("COMANDOS", id="cm-panel-title")
                yield ListView(id="cm-list")
        yield ResizeHandle("◢", classes="resize-handle")

    DEFAULT_CSS = f"""
    CommandsPanel {{ position: absolute; layer: windows; layout: vertical; width: 60; height: 16; border: round {COLOR_BLUE}; background: {BG_CARD}; display: none; }}
    CommandsPanel.open {{ display: block; }}
    """

    def on_mount(self) -> None:
        super().on_mount()
        self._load_commands()

    async def _load_commands(self):
        lst = self.query_one("#cm-list", ListView)
        await lst.clear()
        for i, cmd in enumerate(DEFAULT_COMMANDS):
            await lst.append(CmdItem(cmd["cmd"], cmd["desc"], cmd["cat"], i))


# ─── Janela Pomodoro ────────────────────────────────────────────────────────────
class PomodoroPanel(ManagedWindow):
    title = "Pomodoro"
    icon = "🍅"
    window_id = "pomodoro-panel"
    app_key = "pomodoro"
    default_offset = (20, 5)
    WORK_MIN = 25
    BREAK_MIN = 5

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._running = False
        self._remaining = self.WORK_MIN * 60
        self._phase = "Foco"
        self._timer_task: asyncio.Task | None = None

    def _format_time(self, secs: int) -> str:
        return f"{secs // 60:02d}:{secs % 60:02d}"

    def _update_display(self):
        self.query_one("#pd-timer", Label).update(self._format_time(self._remaining))
        self.query_one("#pd-phase", Label).update(self._phase)

    async def _tick(self):
        while self._running and self._remaining > 0:
            await asyncio.sleep(1)
            self._remaining -= 1
            self._update_display()
        if self._remaining <= 0:
            self._running = False
            self._phase = "Pausa" if self._phase == "Foco" else "Foco"
            self._remaining = (self.BREAK_MIN if self._phase == "Pausa" else self.WORK_MIN) * 60
            self._update_display()

    async def handle_button(self, bid: str) -> None:
        if bid == "pd-btn-start":
            if not self._running:
                self._running = True
                self._timer_task = asyncio.create_task(self._tick())
        elif bid == "pd-btn-reset":
            self._running = False
            if self._timer_task and not self._timer_task.done():
                self._timer_task.cancel()
            self._remaining = self.WORK_MIN * 60
            self._phase = "Foco"
            self._update_display()

    DEFAULT_CSS = f"""
    PomodoroPanel {{ position: absolute; layer: windows; layout: vertical; width: 44; height: 12; border: round {COLOR_BLUE}; background: {BG_CARD}; display: none; }}
    PomodoroPanel.open {{ display: block; }}
    """

    def compose(self) -> ComposeResult:
        with Horizontal(classes="window-titlebar"):
            yield Label(self.icon, classes="window-icon")
            yield Label(self.title, classes="window-title")
            yield Button("×", id="pomodoro-panel-close", classes="window-btn window-close")
        with Vertical():
            yield Label("🍅 POMODORO", id="pd-logo")
            yield Label("Foco", id="pd-phase")
            yield Label("25:00", id="pd-timer")
            yield Static(classes="sidebar-spacer")
            with Horizontal():
                yield Button("▶ INICIAR", id="pd-btn-start", classes="ctrl-btn")
                yield Static()
                yield Button("⏹ RESET", id="pd-btn-reset", classes="ctrl-btn")
            yield Button("FECHAR", id="pd-close-btn", classes="ctrl-btn-close")
        yield ResizeHandle("◢", classes="resize-handle")


# ─── Janela Docker ──────────────────────────────────────────────────────────────
class DockerPanel(ManagedWindow):
    title = "Docker"
    icon = "🐳"
    window_id = "docker-panel"
    app_key = "docker"
    default_offset = (22, 5)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._refresh_task: asyncio.Task | None = None

    def on_mount(self) -> None:
        super().on_mount()

    def _consume_refresh_error(self, task: asyncio.Task) -> None:
        if task.cancelled(): return
        try: task.exception()
        except: pass

    def refresh_now(self) -> None:
        if self._refresh_task and not self._refresh_task.done(): return
        self._refresh_task = asyncio.create_task(self._refresh())
        self._refresh_task.add_done_callback(self._consume_refresh_error)

    def cancel_refresh(self) -> None:
        if self._refresh_task and not self._refresh_task.done():
            self._refresh_task.cancel()

    def _get_containers(self):
        containers = []
        try:
            out = run_shell("docker ps -a --format '{{.ID}}|{{.Names}}|{{.Status}}|{{.Ports}}'", timeout=5)
            for line in out.splitlines():
                parts = line.split("|", 3)
                if len(parts) >= 3:
                    cid, name, status = parts[0], parts[1], parts[2]
                    ports = parts[3] if len(parts) > 3 else ""
                    containers.append(DockerItem(cid, name, status, ports, len(containers)))
        except:
            pass
        return containers

    async def _refresh(self) -> None:
        containers = self._get_containers()
        self.query_one("#dk-status", Label).update(f"🐳 {len(containers)} containers")
        lst = self.query_one("#dk-list", ListView)
        await lst.clear()
        for c in containers:
            await lst.append(c)

    async def handle_button(self, bid: str) -> None:
        if bid == "dk-btn-refresh":
            await self._refresh()

    DEFAULT_CSS = f"""
    DockerPanel {{ position: absolute; layer: windows; layout: vertical; width: 64; height: 18; border: round {COLOR_BLUE}; background: {BG_CARD}; display: none; }}
    DockerPanel.open {{ display: block; }}
    """

    def compose(self) -> ComposeResult:
        with Horizontal(classes="window-titlebar"):
            yield Label(self.icon, classes="window-icon")
            yield Label(self.title, classes="window-title")
            yield Button("×", id="docker-panel-close", classes="window-btn window-close")
        with Horizontal():
            with Vertical(classes="bt-sidebar"):
                yield Label("🐳 DOCKER", id="dk-logo")
                yield Label("Verificando…", id="dk-status")
                yield Button("RECARREGAR", id="dk-btn-refresh", classes="ctrl-btn")
                yield Static(classes="sidebar-spacer")
                yield Button("FECHAR", id="dk-close-btn", classes="ctrl-btn-close")
            with Vertical(classes="bt-panel"):
                yield Label("CONTAINERS", id="dk-panel-title")
                yield ListView(id="dk-list")
        yield ResizeHandle("◢", classes="resize-handle")


# ─── Janela Música ──────────────────────────────────────────────────────────────
class MusicPanel(ManagedWindow):
    title = "Música"
    icon = "🎵"
    window_id = "music-panel"
    app_key = "music"
    default_offset = (26, 6)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._refresh_task: asyncio.Task | None = None

    def on_mount(self) -> None:
        super().on_mount()

    def _consume_refresh_error(self, task: asyncio.Task) -> None:
        if task.cancelled(): return
        try: task.exception()
        except: pass

    def refresh_now(self) -> None:
        if self._refresh_task and not self._refresh_task.done(): return
        self._refresh_task = asyncio.create_task(self._refresh())
        self._refresh_task.add_done_callback(self._consume_refresh_error)

    def cancel_refresh(self) -> None:
        if self._refresh_task and not self._refresh_task.done():
            self._refresh_task.cancel()

    def _get_music_files(self):
        files = []
        try:
            if AUDIO_DIR.exists():
                for f in sorted(AUDIO_DIR.iterdir()):
                    if f.suffix.lower() in MUSIC_EXTS:
                        files.append(MusicItem(str(f), f.stem, str(f.parent.name), len(files)))
        except:
            pass
        return files

    async def _refresh(self) -> None:
        files = self._get_music_files()
        self.query_one("#ms-status", Label).update(f"🎵 {len(files)} músicas")
        lst = self.query_one("#ms-list", ListView)
        await lst.clear()
        for m in files:
            await lst.append(m)

    async def handle_button(self, bid: str) -> None:
        if bid == "ms-btn-play":
            self.query_one("#ms-now", Label).update("▶ Tocando…")
        elif bid == "ms-btn-stop":
            self.query_one("#ms-now", Label).update("⏹ Parado")
        elif bid == "ms-btn-scan":
            await self._refresh()

    DEFAULT_CSS = f"""
    MusicPanel {{ position: absolute; layer: windows; layout: vertical; width: 56; height: 16; border: round {COLOR_BLUE}; background: {BG_CARD}; display: none; }}
    MusicPanel.open {{ display: block; }}
    """

    def compose(self) -> ComposeResult:
        with Horizontal(classes="window-titlebar"):
            yield Label(self.icon, classes="window-icon")
            yield Label(self.title, classes="window-title")
            yield Button("×", id="music-panel-close", classes="window-btn window-close")
        with Horizontal():
            with Vertical(classes="bt-sidebar"):
                yield Label("🎵 MÚSICA", id="ms-logo")
                yield Label("Parado", id="ms-now")
                yield Button("▶ PLAY", id="ms-btn-play", classes="ctrl-btn")
                yield Button("⏹ STOP", id="ms-btn-stop", classes="ctrl-btn")
                yield Button("ESCANEAR", id="ms-btn-scan", classes="ctrl-btn")
                yield Static(classes="sidebar-spacer")
                yield Button("FECHAR", id="ms-close-btn", classes="ctrl-btn-close")
            with Vertical(classes="bt-panel"):
                yield Label("BIBLIOTECA MUSICAL", id="ms-panel-title")
                yield ListView(id="ms-list")
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
        left_text = RichText.assemble(
            ("⚡ Terminal-Essentials  ", "bold #8DB4FF"),
            ("Áquila Azure Night", "bold #8DB4FF on #111625"),
        )
        with Horizontal(id="topbar"):
            yield Static(left_text, id="topbar-left")
            yield Static("pythrian", id="topbar-right")

        # Área principal do desktop
        with Container(id="desktop"):
            yield Label(
                "╔══════════════════════════════════════╗\n"
                "║      ⚡ Terminal-Essentials          ║\n"
                "║    Áquila Azure Night Desktop       ║\n"
                "╠══════════════════════════════════════╣\n"
                "║  Ctrl+B → Bluetooth                 ║\n"
                "║  Ctrl+W → Wi‑Fi                     ║\n"
                "║  Ctrl+Q → Sair                      ║\n"
                "╚══════════════════════════════════════╝",
                id="wallpaper"
            )
            with Vertical(id="desktop-icons"):
                with Horizontal(classes="desktop-row"):
                    yield Button("󰤨\nWi‑Fi", id="desktop-wifi", classes="desktop-icon")
                    yield Button("󰂯\nBluetooth", id="desktop-bluetooth", classes="desktop-icon")
                    yield Button("📊\nProcessos", id="desktop-process", classes="desktop-icon")
                    yield Button("💻\nSysMon", id="desktop-sysmon", classes="desktop-icon")
                with Horizontal(classes="desktop-row"):
                    yield Button("📁\nArquivos", id="desktop-files", classes="desktop-icon")
                    yield Button("📻\nRádio", id="desktop-radio", classes="desktop-icon")
                    yield Button("📝\nNotas", id="desktop-notes", classes="desktop-icon")
                    yield Button("🌤\nClima", id="desktop-weather", classes="desktop-icon")
                with Horizontal(classes="desktop-row"):
                    yield Button("🔧\nComandos", id="desktop-commands", classes="desktop-icon")
                    yield Button("🍅\nPomodoro", id="desktop-pomodoro", classes="desktop-icon")
                    yield Button("🐳\nDocker", id="desktop-docker", classes="desktop-icon")
                    yield Button("🎵\nMúsica", id="desktop-music", classes="desktop-icon")
            yield BluetoothPanel(id="bluetooth-panel")
            yield WifiPanel(id="wifi-panel")
            yield ProcessPanel(id="process-panel")
            yield SysMonPanel(id="sysmon-panel")
            yield FilesPanel(id="files-panel")
            yield RadioPanel(id="radio-panel")
            yield NotesPanel(id="notes-panel")
            yield WeatherPanel(id="weather-panel")
            yield CommandsPanel(id="commands-panel")
            yield PomodoroPanel(id="pomodoro-panel")
            yield DockerPanel(id="docker-panel")
            yield MusicPanel(id="music-panel")

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
    PANEL_CLASSES = [
        BluetoothPanel, WifiPanel, ProcessPanel, SysMonPanel, FilesPanel,
        RadioPanel, NotesPanel, WeatherPanel, CommandsPanel, PomodoroPanel,
        DockerPanel, MusicPanel,
    ]

    def _save_state(self) -> None:
        open_panels = sorted(getattr(self, "_open_panels", set()))
        geometry = {}
        for panel_cls in self.PANEL_CLASSES:
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
            for panel_cls in self.PANEL_CLASSES:
                try:
                    panel = self.query_one(panel_cls)
                    panel_state = geometry.get(panel.app_key)
                    if isinstance(panel_state, dict):
                        panel.restore(panel_state)
                except Exception:
                    pass
            for name in data.get("open", []):
                action_map = {
                    "bluetooth": self.action_open_bluetooth,
                    "wifi": self.action_open_wifi,
                    "process": self.action_open_process,
                    "sysmon": self.action_open_sysmon,
                    "files": self.action_open_files,
                    "radio": self.action_open_radio,
                    "notes": self.action_open_notes,
                    "weather": self.action_open_weather,
                    "commands": self.action_open_commands,
                    "pomodoro": self.action_open_pomodoro,
                    "docker": self.action_open_docker,
                    "music": self.action_open_music,
                }
                action = action_map.get(name)
                if action:
                    action()
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

    def _open_panel(self, panel_cls, app_key) -> None:
        try:
            panel = self.query_one(panel_cls)
            import random
            try:
                d = self.query_one("#desktop")
                dw, dh = d.size.width, d.size.height
            except:
                dw, dh = 80, 24
            pw = max(44, getattr(panel, "default_width", 64))
            ph = max(12, getattr(panel, "default_height", 18))
            max_x = max(1, dw - pw - 2)
            max_y = max(1, dh - ph - 2)
            panel.offset = (random.randint(1, max_x), random.randint(1, max_y))
            panel.constrain_to_desktop()
            panel.add_class("open")
            if hasattr(panel, "refresh_now"):
                panel.refresh_now()
            self._open_panels.add(app_key)
            taskbar = self.query_one(TaskBar)
            taskbar.add_window_button(panel)
            self.query_one(StartMenu).remove_class("visible")
            self.activate_window(panel.window_id)
            self._save_state()
        except Exception:
            pass

    def action_open_bluetooth(self) -> None: self._open_panel(BluetoothPanel, "bluetooth")
    def action_open_wifi(self) -> None: self._open_panel(WifiPanel, "wifi")
    def action_open_process(self) -> None: self._open_panel(ProcessPanel, "process")
    def action_open_sysmon(self) -> None: self._open_panel(SysMonPanel, "sysmon")
    def action_open_files(self) -> None: self._open_panel(FilesPanel, "files")
    def action_open_radio(self) -> None: self._open_panel(RadioPanel, "radio")
    def action_open_notes(self) -> None: self._open_panel(NotesPanel, "notes")
    def action_open_weather(self) -> None: self._open_panel(WeatherPanel, "weather")
    def action_open_commands(self) -> None: self._open_panel(CommandsPanel, "commands")
    def action_open_pomodoro(self) -> None: self._open_panel(PomodoroPanel, "pomodoro")
    def action_open_docker(self) -> None: self._open_panel(DockerPanel, "docker")
    def action_open_music(self) -> None: self._open_panel(MusicPanel, "music")

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

    # ── Panel button routing helper ────────────────────────────────────────────
    PANEL_CLOSE_MAP = {
        "bt-close-btn": (BluetoothPanel, "bluetooth", "bluetooth-panel"),
        "wf-close-btn": (WifiPanel, "wifi", "wifi-panel"),
        "pr-close-btn": (ProcessPanel, "process", "process-panel"),
        "sm-close-btn": (SysMonPanel, "sysmon", "sysmon-panel"),
        "fl-close-btn": (FilesPanel, "files", "files-panel"),
        "rd-close-btn": (RadioPanel, "radio", "radio-panel"),
        "nt-close-btn": (NotesPanel, "notes", "notes-panel"),
        "we-close-btn": (WeatherPanel, "weather", "weather-panel"),
        "cm-close-btn": (CommandsPanel, "commands", "commands-panel"),
        "pd-close-btn": (PomodoroPanel, "pomodoro", "pomodoro-panel"),
        "dk-close-btn": (DockerPanel, "docker", "docker-panel"),
        "ms-close-btn": (MusicPanel, "music", "music-panel"),
        "bluetooth-panel-close": (BluetoothPanel, "bluetooth", "bluetooth-panel"),
        "wifi-panel-close": (WifiPanel, "wifi", "wifi-panel"),
        "process-panel-close": (ProcessPanel, "process", "process-panel"),
        "sysmon-panel-close": (SysMonPanel, "sysmon", "sysmon-panel"),
        "files-panel-close": (FilesPanel, "files", "files-panel"),
        "radio-panel-close": (RadioPanel, "radio", "radio-panel"),
        "notes-panel-close": (NotesPanel, "notes", "notes-panel"),
        "weather-panel-close": (WeatherPanel, "weather", "weather-panel"),
        "commands-panel-close": (CommandsPanel, "commands", "commands-panel"),
        "pomodoro-panel-close": (PomodoroPanel, "pomodoro", "pomodoro-panel"),
        "docker-panel-close": (DockerPanel, "docker", "docker-panel"),
        "music-panel-close": (MusicPanel, "music", "music-panel"),
    }

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
            self.action_open_process()
        elif bid in ("start-sysmon", "desktop-sysmon"):
            self.action_open_sysmon()
        elif bid in ("start-files", "desktop-files"):
            self.action_open_files()
        elif bid in ("start-radio", "desktop-radio"):
            self.action_open_radio()
        elif bid in ("start-notes", "desktop-notes"):
            self.action_open_notes()
        elif bid in ("start-weather", "desktop-weather"):
            self.action_open_weather()
        elif bid in ("start-commands", "desktop-commands"):
            self.action_open_commands()
        elif bid in ("start-pomodoro", "desktop-pomodoro"):
            self.action_open_pomodoro()
        elif bid in ("start-docker", "desktop-docker"):
            self.action_open_docker()
        elif bid in ("start-music", "desktop-music"):
            self.action_open_music()
        elif bid == "menu-exit-btn":
            self.action_quit_app()
        elif bid in self.PANEL_CLOSE_MAP:
            cls, key, wid = self.PANEL_CLOSE_MAP[bid]
            self._close_panel(cls, key, wid)
        elif bid.startswith(("conn-", "disc-", "bt-btn-power", "bt-btn-scan")):
            wifi = self.query_one(WifiPanel)
            if bid.startswith(("conn-", "disc-")) and bid[5:] in getattr(wifi, "_network_ids", {}):
                await wifi.handle_button(bid)
            else:
                await self.query_one(BluetoothPanel).handle_button(bid)
        elif bid in ("wf-btn-power", "wf-btn-scan"):
            await self.query_one(WifiPanel).handle_button(bid)
        elif bid in ("bt-btn-power", "bt-btn-scan"):
            await self.query_one(BluetoothPanel).handle_button(bid)
        elif bid == "pr-btn-refresh":
            await self.query_one(ProcessPanel).handle_button(bid)
        elif bid.startswith("kill-"):
            await self.query_one(ProcessPanel).handle_button(bid)
        elif bid == "sm-btn-refresh":
            await self.query_one(SysMonPanel).handle_button(bid)
        elif bid in ("fl-btn-back", "fl-btn-up"):
            await self.query_one(FilesPanel).handle_button(bid)
        elif bid in ("rd-btn-play", "rd-btn-stop"):
            await self.query_one(RadioPanel).handle_button(bid)
        elif bid in ("nt-btn-new",):
            await self.query_one(NotesPanel).handle_button(bid)
        elif bid == "we-btn-refresh":
            await self.query_one(WeatherPanel).handle_button(bid)
        elif bid in ("pd-btn-start", "pd-btn-reset"):
            await self.query_one(PomodoroPanel).handle_button(bid)
        elif bid == "dk-btn-refresh":
            await self.query_one(DockerPanel).handle_button(bid)
        elif bid in ("ms-btn-play", "ms-btn-stop", "ms-btn-scan"):
            await self.query_one(MusicPanel).handle_button(bid)

    async def on_unmount(self) -> None:
        # Estado já foi salvo em action_quit_app ou ao fechar painéis.
        # Não chamar _save_state aqui pois a screen stack já foi desmontada.
        pass


if __name__ == "__main__":
    DesktopApp().run()

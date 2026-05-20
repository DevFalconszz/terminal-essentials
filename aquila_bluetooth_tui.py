from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Static, Button, ListView, Label
from textual.binding import Binding
from textual import on, work
import subprocess
import asyncio

# ─── AQUILA SOFT AZURE NIGHT ───────────────────────────────────────────────────
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

# ─── Icon mapping via bluetoothctl icon property ────────────────────────────────
ICON_MAP = {
    "phone":           "📱",
    "audio-card":      "🎧",
    "audio-headset":   "🎧",
    "headset":         "🎧",
    "input-keyboard":  "⌨️ ",
    "keyboard":        "⌨️ ",
    "input-mouse":     "🖱️ ",
    "mouse":           "🖱️ ",
    "input-gaming":    "🎮",
    "computer":        "💻",
}
ICON_DEFAULT = "📶"

CSS = f"""
Screen {{
    background: {BG_MAIN};
    align: center middle;
}}

/* ── Outer frame ─────────────────────────────────────────── */
#frame {{
    width: 80;
    height: 24;
    border: round {COLOR_BLUE};
    background: {BG_CARD};
    layout: horizontal;
}}

/* ── Left sidebar ─────────────────────────────────────────── */
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

/* ── Right panel ─────────────────────────────────────────── */
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

#device-list {{
    height: 1fr;
    background: transparent;
    border: none;
}}

/* ── Device cards ─────────────────────────────────────────── */
DeviceItem {{
    height: 3;
    background: {BG_GLASS};
    border: round {BG_GLASS};
    margin-bottom: 1;
    padding: 0 1;
    layout: horizontal;
    align: left middle;
    transition: background 120ms, border 120ms;
}}

DeviceItem:hover {{
    background: {BG_HOVER};
    border: round {COLOR_BLUE};
}}

DeviceItem.connected {{
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


class DeviceItem(Static):
    def __init__(self, mac: str, name: str, connected: bool, icon: str = ICON_DEFAULT):
        super().__init__()
        self.mac = mac
        self.device_name = name
        self.connected = connected
        self.icon = icon
        if connected:
            self.add_class("connected")

    def compose(self) -> ComposeResult:
        safe = self.mac.replace(":", "-")
        status_label = "● Conectado" if self.connected else "○ Desconectado"
        sub_class = "dev-sub connected" if self.connected else "dev-sub"
        with Horizontal():
            yield Label(self.icon, classes="dev-icon")
            with Vertical(classes="dev-info"):
                yield Label(self.device_name, classes="dev-name")
                yield Label(status_label, classes=sub_class, id=f"sub-{safe}")
            if self.connected:
                yield Button("Desconectar", id=f"disc-{safe}", classes="btn-disconnect")
            else:
                yield Button("Conectar", id=f"conn-{safe}", classes="btn-connect")


class AquilaBluetoothTUI(App):
    CSS = CSS

    BINDINGS = [Binding("q", "quit", "Sair")]

    def __init__(self, **kw):
        super().__init__(**kw)
        self._devices: dict = {}

    # ── Compose ────────────────────────────────────────────────────────────────
    def compose(self) -> ComposeResult:
        with Container(id="frame"):
            with Vertical(id="sidebar"):
                yield Label("⚡ AQUILA BT", id="logo")
                yield Label("Inicializando…", id="status-card")
                yield Button("POWER", id="btn-power", classes="ctrl-btn")
                yield Button("SCAN",  id="btn-scan",  classes="ctrl-btn")
                yield Static(id="spacer")
                yield Button("SAIR",  id="exit-btn")
            with Vertical(id="right-panel"):
                yield Label("DISPOSITIVOS PAREADOS", id="panel-title")
                yield ListView(id="device-list")

    # ── Lifecycle ──────────────────────────────────────────────────────────────
    def on_mount(self) -> None:
        self._refresh_loop()

    @work(exclusive=True)
    async def _refresh_loop(self):
        while True:
            await self._refresh()
            await asyncio.sleep(4)

    # ── Data refresh ───────────────────────────────────────────────────────────
    async def _refresh(self):
        loop = asyncio.get_event_loop()
        powered, host_name, devices = await loop.run_in_executor(None, self._get_bt_info)

        card = self.query_one("#status-card", Label)
        if powered:
            card.update(f"󰂯  {host_name}  ●")
            card.add_class("online")
        else:
            card.update(f"󰂲  {host_name}  ○")
            card.remove_class("online")

        device_list = self.query_one("#device-list", ListView)
        current_macs = {d["mac"] for d in devices}

        # Remove devices no longer seen
        for mac in list(self._devices.keys()):
            if mac not in current_macs:
                for item in device_list.query(DeviceItem):
                    if item.mac == mac:
                        await item.remove()
                        break
                del self._devices[mac]

        # Add / update
        for dev in devices:
            mac = dev["mac"]
            if mac not in self._devices:
                item = DeviceItem(mac, dev["name"], dev["connected"], dev["icon"])
                await device_list.append(item)
                self._devices[mac] = dev
            elif self._devices[mac]["connected"] != dev["connected"]:
                for item in device_list.query(DeviceItem):
                    if item.mac == mac:
                        safe = mac.replace(":", "-")
                        # Update connected state
                        item.connected = dev["connected"]
                        if dev["connected"]:
                            item.add_class("connected")
                        else:
                            item.remove_class("connected")
                        # Update sub-label
                        sub = item.query_one(f"#sub-{safe}", Label)
                        if dev["connected"]:
                            sub.update("● Conectado")
                            sub.add_class("connected")
                        else:
                            sub.update("○ Desconectado")
                            sub.remove_class("connected")
                        # Update button
                        btn = item.query_one(Button)
                        if dev["connected"]:
                            btn.label = "Desconectar"
                            btn.id = f"disc-{safe}"
                            btn.remove_class("btn-connect")
                            btn.add_class("btn-disconnect")
                        else:
                            btn.label = "Conectar"
                            btn.id = f"conn-{safe}"
                            btn.remove_class("btn-disconnect")
                            btn.add_class("btn-connect")
                        break
                self._devices[mac] = dev

    # ── Bluetooth queries (blocking, run in executor) ──────────────────────────
    @staticmethod
    def _get_bt_info():
        show = subprocess.run(
            "bluetoothctl show", shell=True, capture_output=True, text=True
        ).stdout
        powered = "Powered: yes" in show
        host_name = "Adaptador"
        for line in show.splitlines():
            if "Name: " in line:
                host_name = line.split("Name: ", 1)[1].strip()
                break

        dev_raw = subprocess.run(
            "bluetoothctl devices", shell=True, capture_output=True, text=True
        ).stdout
        devices = {}
        for line in dev_raw.splitlines():
            parts = line.split(" ", 2)
            if len(parts) < 3:
                continue
            mac, name = parts[1], parts[2]
            if mac in devices:
                continue
            info = subprocess.run(
                f"bluetoothctl info {mac}", shell=True, capture_output=True, text=True
            ).stdout
            connected = "Connected: yes" in info
            icon_key = "default"
            for il in info.splitlines():
                if "Icon: " in il:
                    icon_key = il.split("Icon: ", 1)[1].strip()
                    break
            devices[mac] = {
                "mac": mac,
                "name": name,
                "connected": connected,
                "icon": ICON_MAP.get(icon_key, ICON_DEFAULT),
            }
        return powered, host_name, list(devices.values())

    @on(Button.Pressed)
    async def _on_button(self, event: Button.Pressed) -> None:
        bid = event.button.id
        if not bid:
            return

        if bid == "exit-btn":
            self.exit()
            return

        self.query_one("#status-card", Label).update("Aguarde…")
        loop = asyncio.get_event_loop()

        if bid == "btn-power":
            cmd = (
                "bluetoothctl show | grep -q 'Powered: yes' "
                "&& bluetoothctl power off "
                "|| bluetoothctl power on"
            )
            await loop.run_in_executor(
                None, lambda: subprocess.run(f"{cmd} >/dev/null 2>&1", shell=True)
            )
        elif bid == "btn-scan":
            scan = (
                "bluetoothctl scan on >/dev/null 2>&1 & "
                "sleep 5; "
                "bluetoothctl scan off >/dev/null 2>&1"
            )
            await loop.run_in_executor(
                None, lambda: subprocess.run(scan, shell=True)
            )
        elif bid.startswith("conn-"):
            mac = bid[5:].replace("-", ":")
            await loop.run_in_executor(
                None,
                lambda: subprocess.run(f"bluetoothctl connect {mac} >/dev/null 2>&1", shell=True),
            )
        elif bid.startswith("disc-"):
            mac = bid[5:].replace("-", ":")
            await loop.run_in_executor(
                None,
                lambda: subprocess.run(f"bluetoothctl disconnect {mac} >/dev/null 2>&1", shell=True),
            )

        # Atualiza os dados imediatamente após a ação reiniciando o loop exclusivo
        self._refresh_loop()


if __name__ == "__main__":
    AquilaBluetoothTUI().run()

import asyncio
import os
import subprocess
import datetime
from pathlib import Path
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Static, Button, Label, ListView, ListItem, Input
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

NOTES_DIR = Path.home() / ".local" / "share" / "terminal-essentials" / "notes"

CSS = f"""
Screen {{ background: {BG_MAIN}; align: center middle; }}
#frame {{ width: 78; height: 26; border: round {COLOR_BLUE}; background: {BG_CARD}; layout: horizontal; }}
#sidebar {{ width: 24; height: 100%; padding: 1; layout: vertical; border-right: round {BG_GLASS}; }}
#logo {{ height: 1; content-align: center middle; color: {COLOR_BLUE}; text-style: bold; margin-bottom: 1; }}
#status-card {{ height: 2; border: round {BG_GLASS}; background: {BG_GLASS}; content-align: center middle; color: {COLOR_MUTED}; margin-bottom: 1; }}
.ctrl-btn {{ width: 100%; height: 3; margin-bottom: 1; background: {BG_GLASS}; color: {COLOR_BLUE}; border: none; text-style: bold; }}
.ctrl-btn:hover {{ background: {COLOR_BLUE}; color: {BG_MAIN}; }}
#spacer {{ height: 1fr; }}
#exit-btn {{ width: 100%; height: 3; background: {BG_GLASS}; color: {COLOR_RED}; border: none; text-style: bold; }}
#exit-btn:hover {{ background: {COLOR_RED}; color: {BG_MAIN}; }}
#right-panel {{ width: 1fr; height: 100%; padding: 1; layout: vertical; }}
#panel-title {{ height: 1; color: {COLOR_MUTED}; text-style: bold; margin-bottom: 1; content-align: left middle; }}
#note-list {{ height: 1fr; background: transparent; border: none; }}
#note-input {{ height: 3; background: {BG_GLASS}; color: {COLOR_TEXT}; border: round {COLOR_BLUE}; margin-top: 1; }}
#note-preview {{ height: 1fr; background: {BG_GLASS}; color: {COLOR_TEXT}; border: round {BG_HOVER}; padding: 1; }}
NoteItem {{ height: 3; background: {BG_GLASS}; border: round {BG_GLASS}; margin-bottom: 1; padding: 0 1; layout: horizontal; align: left middle; }}
NoteItem:hover {{ background: {BG_HOVER}; border: round {COLOR_BLUE}; }}
.note-title {{ width: 1fr; color: {COLOR_TEXT}; text-style: bold; }}
.note-date {{ width: 14; color: {COLOR_MUTED}; text-align: right; }}
.btn-delete-note {{ height: 1; min-width: 6; padding: 0 1; border: none; background: {COLOR_RED}; color: {BG_MAIN}; text-style: bold; }}
.btn-delete-note:hover {{ background: {COLOR_ROSE}; }}
"""

class NoteItem(Static):
    def __init__(self, path: Path, title: str, mtime: str):
        super().__init__()
        self.note_path = path
        self.note_title = title
        self.note_mtime = mtime

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Label(self.note_title, classes="note-title")
            yield Label(self.note_mtime, classes="note-date")
            yield Button("DEL", id=f"delnote-{self.note_path.stem}", classes="btn-delete-note")

class AquilaNotesTUI(App):
    CSS = CSS
    BINDINGS = [Binding("q", "quit", "Sair"), Binding("n", "new_note", "Nova")]

    def __init__(self, **kw):
        super().__init__(**kw)
        NOTES_DIR.mkdir(parents=True, exist_ok=True)

    def compose(self) -> ComposeResult:
        with Container(id="frame"):
            with Vertical(id="sidebar"):
                yield Label("📝 NOTAS", id="logo")
                yield Label("0 notas", id="status-card")
                yield Button("NOVA", id="btn-new", classes="ctrl-btn")
                yield Button("EDITAR", id="btn-edit", classes="ctrl-btn")
                yield Static(id="spacer")
                yield Button("SAIR", id="exit-btn")
            with Vertical(id="right-panel"):
                yield Label("MINHAS NOTAS", id="panel-title")
                yield ListView(id="note-list")
                yield Input(placeholder="Nome da nova nota…", id="note-input")

    def on_mount(self):
        self._list_notes()

    @work(exclusive=True)
    async def _list_notes(self, select_title: str | None = None):
        loop = asyncio.get_event_loop()
        notes = await loop.run_in_executor(None, self._scan_notes)
        nlist = self.query_one("#note-list", ListView)
        await nlist.clear()
        self.query_one("#status-card", Label).update(f"📄 {len(notes)} notas")
        for path, title, mtime in notes:
            await nlist.append(NoteItem(path, title, mtime))
        if select_title:
            for child in nlist.children:
                if isinstance(child, NoteItem) and child.note_title == select_title:
                    nlist.index = nlist.children.index(child)
                    break

    @staticmethod
    def _scan_notes():
        if not NOTES_DIR.is_dir():
            return []
        result = []
        for f in sorted(NOTES_DIR.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
            if f.suffix == ".txt":
                title = f.stem.replace("_", " ").replace("-", " — ")
                mtime = datetime.datetime.fromtimestamp(f.stat().st_mtime).strftime("%d/%m %H:%M")
                result.append((f, title, mtime))
        return result

    @on(Button.Pressed)
    async def _on_btn(self, event: Button.Pressed):
        bid = event.button.id or ""
        if bid == "exit-btn":
            self.exit()
        elif bid == "btn-new":
            inp = self.query_one("#note-input", Input)
            name = inp.value.strip()
            if not name:
                name = f"nota_{datetime.datetime.now().strftime('%d%m_%H%M')}"
            safe_name = name.replace(" ", "_")[:30]
            fpath = NOTES_DIR / f"{safe_name}.txt"
            if not fpath.exists():
                fpath.write_text("", encoding="utf-8")
            inp.value = ""
            await self._list_notes(safe_name)
        elif bid == "btn-edit":
            nlist = self.query_one("#note-list", ListView)
            if nlist.children:
                selected = nlist.children[nlist.index]
                if isinstance(selected, NoteItem):
                    subprocess.Popen(["xdg-open", str(selected.note_path)],
                                     start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    self.exit()
        elif bid.startswith("delnote-"):
            name = bid[8:]
            fpath = NOTES_DIR / f"{name}.txt"
            if fpath.exists():
                fpath.unlink()
            await self._list_notes()

    async def on_list_view_selected(self, event: ListView.Selected):
        item = event.item
        if isinstance(item, NoteItem):
            try:
                content = item.note_path.read_text(encoding="utf-8") or "(vazio)"
            except Exception:
                content = "(erro ao ler)"
            preview = self.query_one("#note-preview", Static)
            if not preview:
                preview = Static(content, id="note-preview")
                self.query_one("#right-panel", Vertical).mount(preview)
            else:
                preview.update(content[:500])

class NotesWindow:
    title = "Notas Rápidas"
    window_id = "notes"
    @staticmethod
    def create():
        return AquilaNotesTUI()

if __name__ == "__main__":
    AquilaNotesTUI().run()

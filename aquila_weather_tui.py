import asyncio
import json
import urllib.request
import datetime
from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Static, Button, Label
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
#frame {{ width: 60; height: 26; border: round {COLOR_BLUE}; background: {BG_CARD}; layout: vertical; padding: 1; }}
#logo {{ height: 1; content-align: center middle; color: {COLOR_BLUE}; text-style: bold; margin-bottom: 1; }}
#status-card {{ height: 2; border: round {BG_GLASS}; background: {BG_GLASS}; content-align: center middle; color: {COLOR_MUTED}; margin-bottom: 1; }}
#city-label {{ height: 2; color: {COLOR_TEXT}; text-style: bold; content-align: center middle; }}
#temp-label {{ height: 4; color: {COLOR_BLUE}; text-style: bold; content-align: center middle; }}
#cond-label {{ height: 2; color: {COLOR_BLUE2}; content-align: center middle; }}
.detail-row {{ height: 2; layout: horizontal; align: center middle; margin-bottom: 0; }}
.detail-label {{ width: 20; color: {COLOR_MUTED}; text-align: right; }}
.detail-value {{ width: 15; color: {COLOR_TEXT}; text-style: bold; text-align: left; }}
#forecast {{ height: auto; layout: vertical; margin-top: 1; }}
.forecast-row {{ height: 2; layout: horizontal; align: center middle; }}
.forecast-day {{ width: 10; color: {COLOR_LAVA}; text-style: bold; }}
.forecast-temp {{ width: 10; color: {COLOR_BLUE}; }}
.forecast-cond {{ width: 20; color: {COLOR_MUTED}; }}
#exit-btn {{ width: 100%; height: 3; background: {BG_GLASS}; color: {COLOR_RED}; border: none; text-style: bold; dock: bottom; }}
#exit-btn:hover {{ background: {COLOR_RED}; color: {BG_MAIN}; }}
"""

class AquilaWeatherTUI(App):
    CSS = CSS
    BINDINGS = [Binding("q", "quit", "Sair"), Binding("r", "refresh", "Recarregar")]

    def compose(self) -> ComposeResult:
        with Container(id="frame"):
            yield Label("🌤 CLIMA", id="logo")
            yield Label("Carregando…", id="status-card")
            yield Label("", id="city-label")
            yield Label("", id="temp-label")
            yield Label("", id="cond-label")
            yield Static(id="detail-grid")
            yield Label("PREVISÃO", id="status-card")
            yield Static(id="forecast")
            yield Button("SAIR", id="exit-btn")

    def on_mount(self):
        self._refresh()

    @work(exclusive=True)
    async def _refresh(self):
        self.query_one("#status-card", Label).update("⏳ Obtendo dados…")
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(None, self._fetch_weather)
        if data:
            self._update_ui(data)
        else:
            self.query_one("#status-card", Label).update("⚠ Falha ao obter clima")
            self.query_one("#city-label", Label).update("Verifique sua conexão")

    def _update_ui(self, data: dict):
        self.query_one("#status-card", Label).update(f"📍 {data['city']}  |  {data['country']}")
        self.query_one("#city-label", Label).update(data["city"])
        self.query_one("#temp-label", Label).update(f"{data['temp']}°C   {data['emoji']}")
        self.query_one("#cond-label", Label).update(data["condition"])

        detail = self.query_one("#detail-grid", Static)
        detail.update(
            f"  Umidade:       {data['humidity']}%\n"
            f"  Vento:         {data['wind']} km/h\n"
            f"  Sensação:      {data['feels_like']}°C\n"
            f"  Pressão:       {data['pressure']} hPa\n"
            f"  Visibilidade:  {data['visibility']} km"
        )

        fc = self.query_one("#forecast", Static)
        lines = []
        for day in data['forecast']:
            lines.append(f"  {day['day']:8s}  {day['temp']:>8s}  {day['cond']}")
        fc.update("\n".join(lines) if lines else "  Sem previsão")

    @staticmethod
    def _fetch_weather():
        try:
            url = "https://wttr.in/?format=j1"
            with urllib.request.urlopen(url, timeout=8) as resp:
                raw = json.loads(resp.read().decode())
            cc = raw["current_condition"][0]
            weather = raw["weather"]
            city = raw["nearest_area"][0]["areaName"][0]["value"]
            country = raw["nearest_area"][0]["country"][0]["value"]
            emoji_map = {
                "Clear": "☀️", "Sunny": "☀️", "Partly cloudy": "⛅", "Cloudy": "☁️",
                "Overcast": "☁️", "Mist": "🌫", "Fog": "🌫", "Light rain": "🌦",
                "Moderate rain": "🌧", "Heavy rain": "🌧", "Light snow": "🌨",
                "Snow": "❄️", "Thunderstorm": "⛈", "Drizzle": "🌦",
            }
            cond = cc["weatherDesc"][0]["value"]
            emoji = emoji_map.get(cond, "🌡")
            forecast = []
            for w in weather[:5]:
                dt = datetime.datetime.strptime(w["date"], "%Y-%m-%d")
                day_name = dt.strftime("%a")
                forecast.append({
                    "day": day_name,
                    "temp": f"{w['avgtempC']}°C",
                    "cond": w["hourly"][0]["weatherDesc"][0]["value"],
                })
            return {
                "city": city, "country": country, "emoji": emoji,
                "temp": cc["temp_C"], "feels_like": cc["FeelsLikeC"],
                "condition": cond, "humidity": cc["humidity"],
                "wind": cc["windspeedKmph"], "pressure": cc["pressure"],
                "visibility": cc["visibility"], "forecast": forecast,
            }
        except Exception:
            return None

    @on(Button.Pressed)
    def _on_btn(self, event: Button.Pressed):
        if event.button.id == "exit-btn":
            self.exit()

class WeatherWindow:
    title = "Clima"
    window_id = "weather"
    @staticmethod
    def create():
        return AquilaWeatherTUI()

if __name__ == "__main__":
    AquilaWeatherTUI().run()

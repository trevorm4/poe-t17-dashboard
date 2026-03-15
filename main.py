#!/usr/bin/env python3
"""
Path of Exile Fragment Farming Calculator — TUI
Controls: Tab = switch panel | Arrow keys = navigate | E = edit | Enter = map breakdown | C = config | R = refresh prices | Q = quit
"""

import json
import os
import requests
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import DataTable, Static, Input, Button
from textual.binding import Binding

CONFIG = {
    "Frags per map": 2.5,
    "Div price": 272.0,
    "Map cost": 25.0,
    "Carry price": 60.0,
    "Carrys per map": 1.5,
}

CONFIG_FILE = os.path.expanduser("~/.poe_frag_calc.json")


def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                saved = json.load(f)
                for key in saved:
                    if key in CONFIG:
                        CONFIG[key] = saved[key]
        except (json.JSONDecodeError, IOError):
            pass


def save_config():
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(CONFIG, f)
    except IOError:
        pass


load_config()

MAPS = [
    {
        "name": "Sanctuary",
        "frag_count": 3,
        "frag_avg_val": 120.8333333,
        "unique_name": "The Dark Seer",
        "unique_type": "weapon",
        "time_per_map": 1.25,
        "gem_name": "Scornful Herald Support",
    },
    {
        "name": "Fortress",
        "frag_count": 2,
        "frag_avg_val": 121.25,
        "unique_name": "Yoke of Suffering",
        "unique_type": "accessory",
        "time_per_map": 0.70,
        "gem_name": "Overloaded Intensity Support",
    },
    {
        "name": "Ziggurat",
        "frag_count": 2,
        "frag_avg_val": 208.75,
        "unique_name": "Wraithlord",
        "unique_type": "armour",
        "time_per_map": 1.60,
        "gem_name": "Minion Pact Support",
    },
    {
        "name": "Citadel",
        "frag_count": 2,
        "frag_avg_val": 123.75,
        "unique_name": "Manastorm",
        "unique_type": "armour",
        "time_per_map": 1.40,
        "gem_name": "Cast on Ward Break Support",
    },
    {
        "name": "Abomination",
        "frag_count": 2,
        "frag_avg_val": 122.5,
        "unique_name": "Malachai's Mark",
        "unique_type": "armour",
        "time_per_map": 0.80,
        "gem_name": "Unholy Trinity Support",
    },
]

MAP_FRAG_POOLS = {
    "Sanctuary": ["Reverent", "Lonely", "Traumatic"],
    "Fortress": ["Decaying", "Synthesising"],
    "Ziggurat": ["Blazing", "Devouring"],
    "Citadel": ["Cosmic", "Synthesising"],
    "Abomination": ["Reality", "Awakening"],
}

FRAGS = {
    "Cosmic": 90.0,
    "Decaying": 88.0,
    "Lonely": 19.0,
    "Traumatic": 36.0,
    "Reality": 95.0,
    "Reverent": 90.0,
    "Devouring": 148.0,
    "Blazing": 19.0,
    "Awakening": 3.0,
    "Synthesising": 9.0,
}

POE_NINJA_LEAGUE = "Mirage"


UNIQUE_PRICES = {}
GEM_PRICES = {}


def fetch_prices():
    """Fetch prices from poe.ninja exchange API."""
    try:
        div_url = "https://poe.ninja/poe1/api/economy/exchange/current/details?league=Mirage&type=Currency&id=divine-orb"
        div_r = requests.get(div_url, timeout=10)
        div_data = div_r.json()
        div_price = 272.0
        for pair in div_data.get("pairs", []):
            if pair.get("id") == "chaos":
                div_price = pair.get("rate", 272.0)
                break

        frag_url_base = "https://poe.ninja/poe1/api/economy/exchange/current/details?league=Mirage&type=Fragment&id="
        fragment_ids = [
            "cosmic-fragment",
            "decaying-fragment",
            "lonely-fragment",
            "traumatic-fragment",
            "reality-fragment",
            "reverent-fragment",
            "devouring-fragment",
            "blazing-fragment",
            "awakening-fragment",
            "synthesising-fragment",
        ]

        frag_prices = {}
        name_to_key = {
            "Cosmic Fragment": "Cosmic",
            "Decaying Fragment": "Decaying",
            "Lonely Fragment": "Lonely",
            "Traumatic Fragment": "Traumatic",
            "Reality Fragment": "Reality",
            "Reverent Fragment": "Reverent",
            "Devouring Fragment": "Devouring",
            "Blazing Fragment": "Blazing",
            "Awakening Fragment": "Awakening",
            "Synthesising Fragment": "Synthesising",
        }

        for frag_id in fragment_ids:
            url = frag_url_base + frag_id
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                data = r.json()
                name = data.get("item", {}).get("name", "")
                for pair in data.get("pairs", []):
                    if pair.get("id") == "chaos":
                        key = name_to_key.get(name)
                        if key:
                            frag_prices[key] = pair.get("rate", 0)
                        break

        unique_armour_url = "https://poe.ninja/poe1/api/economy/stash/current/item/overview?league=Mirage&type=UniqueArmour"
        unique_accessory_url = "https://poe.ninja/poe1/api/economy/stash/current/item/overview?league=Mirage&type=UniqueAccessory"
        unique_weapon_url = "https://poe.ninja/poe1/api/economy/stash/current/item/overview?league=Mirage&type=UniqueWeapon"

        unique_prices = {}
        for url in [unique_armour_url, unique_accessory_url, unique_weapon_url]:
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                data = r.json()
                for item in data.get("lines", []):
                    name = item.get("name", "")
                    chaos = item.get("chaosValue", 0)
                    if chaos:
                        unique_prices[name] = chaos

        gem_url = "https://poe.ninja/poe1/api/economy/stash/current/item/overview?league=Mirage&type=SkillGem"
        gem_prices = {}
        r = requests.get(gem_url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            for item in data.get("lines", []):
                name = item.get("name", "")
                chaos = item.get("chaosValue", 0)
                if chaos:
                    gem_prices[name] = chaos

        return frag_prices, div_price, unique_prices, gem_prices

    except Exception:
        return None, None, None, None


def compute_map(m):
    div_price = CONFIG["Div price"]
    map_cost = CONFIG["Map cost"]
    carry_p = CONFIG["Carry price"]
    cpp_map = CONFIG["Carrys per map"]
    fav = m["frag_avg_val"]

    unique_name = m.get("unique_name", "")
    unique_price = UNIQUE_PRICES.get(unique_name, 0) * 0.05

    gem_name = m.get("gem_name", "")
    gem_price = GEM_PRICES.get(gem_name, 0) * 0.05

    total_c = fav + unique_price + gem_price - map_cost
    time_hr = m["time_per_map"] / 60.0
    div_hr = (total_c / div_price) / time_hr if time_hr else 0.0
    carry_rev = cpp_map * carry_p / div_price
    carry_time_hr = (m["time_per_map"] + 20 / 60) / 60.0
    div_hr_c = (
        (total_c / div_price + carry_rev) / carry_time_hr if carry_time_hr else 0.0
    )

    return {
        "total": total_c,
        "div_hr": div_hr,
        "div_hr_carry": div_hr_c,
        "unique_price": unique_price,
        "gem_price": gem_price,
    }


def recompute_frag_avgs():
    """Recompute frag_avg_val for each map based on fragment pools.
    Each map has on average 2.5 fragments, randomly sampled with replacement
    from the available fragment types.
    """
    for m in MAPS:
        map_name = m["name"]
        pool = MAP_FRAG_POOLS.get(map_name, [])
        if pool:
            frag_sum = sum(FRAGS.get(frag, 0) for frag in pool)
            m["frag_avg_val"] = 2.5 * frag_sum / len(pool)


class MapTable(DataTable):
    BINDINGS = [Binding("enter", "show_breakdown", "Show Breakdown")]

    def __init__(self):
        super().__init__(cursor_type="row", show_cursor=True)

    def action_show_breakdown(self):
        if self.cursor_row is not None:
            row = self.cursor_row
            m = MAPS[row]
            map_name = m["name"]
            frags = MAP_FRAG_POOLS.get(map_name, [])
            unique_name = m.get("unique_name", "")
            unique_price = UNIQUE_PRICES.get(unique_name, 0)
            gem_name = m.get("gem_name", "")
            gem_price = GEM_PRICES.get(gem_name, 0)
            self.app.push_screen(
                MapBreakdownModal(
                    map_name, frags, unique_name, unique_price, gem_name, gem_price
                )
            )


class ConfigPanel(Vertical):
    def compose(self) -> ComposeResult:
        yield Static("⚙  Config", classes="panel-title")
        for key in CONFIG:
            safe_key = key.replace(" ", "_")
            yield Static(f"{key:<16} {CONFIG[key]:>6.2f}", id=f"cfg-{safe_key}")

    def update_values(self):
        for key in CONFIG:
            safe_key = key.replace(" ", "_")
            self.query_one(f"#cfg-{safe_key}", Static).update(
                f"{key:<16} {CONFIG[key]:>6.2f}"
            )


class FragPanel(Vertical):
    def compose(self) -> ComposeResult:
        yield Static("⚗  Fragment Prices", classes="panel-title")
        for key in FRAGS:
            val = FRAGS[key]
            div = val / CONFIG["Div price"] if CONFIG["Div price"] else 0
            yield Static(f"{key:<12} {val:>6.0f}c  {div:>5.3f} div", id=f"frag-{key}")

    def update_values(self):
        for key in FRAGS:
            val = FRAGS[key]
            div = val / CONFIG["Div price"] if CONFIG["Div price"] else 0
            self.query_one(f"#frag-{key}", Static).update(
                f"{key:<12} {val:>6.0f}c  {div:>5.3f} div"
            )


class MapBreakdownModal(ModalScreen):
    def __init__(
        self,
        map_name: str,
        frags: list,
        unique_name: str,
        unique_price: float,
        gem_name: str,
        gem_price: float,
    ):
        super().__init__()
        self.map_name = map_name
        self.frags = frags
        self.unique_name = unique_name
        self.unique_price = unique_price
        self.gem_name = gem_name
        self.gem_price = gem_price

    def compose(self) -> ComposeResult:
        yield Container(
            Static(f"⚔  {self.map_name} Breakdown", classes="panel-title"),
            Static("─" * 40),
            Static("Fragments (2.5 avg per map):"),
            *[Static(f"  • {frag}: {FRAGS.get(frag, 0):.0f}c") for frag in self.frags],
            Static(""),
            Static("Unique Drop:"),
            Static(f"  • {self.unique_name}: {self.unique_price:.0f}c (5% drop)"),
            Static(f"  Expected: {self.unique_price * 0.05:.2f}c per map"),
            Static(""),
            Static("Skill Gem:"),
            Static(f"  • {self.gem_name}: {self.gem_price:.0f}c"),
            Static("─" * 40),
            Button("Close", id="close"),
            id="modal-container",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "close":
            self.app.pop_screen()


class ConfigModal(ModalScreen):
    def compose(self) -> ComposeResult:
        yield Container(
            Static("⚙  Configuration", classes="panel-title"),
            Static("─" * 40),
            Static("Carry price:"),
            Input(value=str(CONFIG["Carry price"]), id="carry-price"),
            Static("Carrys per map:"),
            Input(value=str(CONFIG["Carrys per map"]), id="carry-per-map"),
            Static("Frags per map:"),
            Input(value=str(CONFIG["Frags per map"]), id="frags-per-map"),
            Static("Map cost:"),
            Input(value=str(CONFIG["Map cost"]), id="map-cost"),
            Static("─" * 40),
            Button("Save", id="save", variant="primary"),
            Button("Cancel", id="cancel"),
            id="modal-container",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save":
            try:
                CONFIG["Carry price"] = float(
                    self.query_one("#carry-price", Input).value
                )
                CONFIG["Carrys per map"] = float(
                    self.query_one("#carry-per-map", Input).value
                )
                CONFIG["Frags per map"] = float(
                    self.query_one("#frags-per-map", Input).value
                )
                CONFIG["Map cost"] = float(self.query_one("#map-cost", Input).value)
                save_config()
                recompute_frag_avgs()
                app = self.app
                self.app.pop_screen()
                app.update_map_table()  # type: ignore[attr-defined]
                app.query_one(ConfigPanel).update_values()
            except ValueError:
                pass
        elif event.button.id == "cancel":
            self.app.pop_screen()


class POE(App):
    CSS = """
    Screen { background: $surface; }

    #title {
        dock: top; height: 2;
        content-align: center middle;
        text-style: bold; color: $accent;
    }

    #subtitle {
        dock: top; height: 1;
        content-align: center middle;
        color: $text-muted;
    }

    #main { height: 1fr; }

    MapTable {
        height: 1fr; margin: 1 1;
        border: solid $border;
    }

    .panel {
        width: 35; height: 16;
        border: solid $border;
        margin: 1; padding: 1;
    }

    .panel-title {
        text-style: bold; color: $accent;
        margin-bottom: 1;
    }

    #status {
        dock: bottom; height: 1;
        content-align: left middle;
        background: $accent; color: $text;
        text-style: bold;
    }

    #message {
        dock: bottom; height: 1;
        content-align: left middle;
        color: $success; text-style: bold;
    }

    #note {
        dock: bottom; height: 1;
        content-align: left middle;
        color: $text-muted;
    }

    MapBreakdownModal {
        align: center middle;
    }

    #modal-container {
        width: 50; height: auto;
        border: thick $accent;
        background: $surface;
        padding: 1 2;
    }

    #modal-container > .panel-title {
        margin-bottom: 1;
    }

    #modal-close {
        margin-top: 1;
        align: center middle;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh_prices", "Refresh"),
        Binding("c", "open_config", "Config"),
        Binding("tab", "focus_next", "Next Panel"),
        Binding("e", "edit_value", "Edit"),
    ]

    def __init__(self):
        super().__init__()
        self.focus_stack = ["map", "config", "frags"]
        self.focus_index = 0
        self.message = ""

    def action_open_config(self):
        self.push_screen(ConfigModal())

    def compose(self) -> ComposeResult:
        avg = sum(FRAGS.values()) / len(FRAGS) if FRAGS else 0
        yield Static("◈ PATH OF EXILE · Fragment Farming Calculator ◈", id="title")
        yield Static(
            f"Pool avg: {avg:.1f}c  |  Div: {CONFIG['Div price']:.0f}c  |  Map cost: {CONFIG['Map cost']:.0f}c",
            id="subtitle",
        )

        with Container(id="main"):
            yield MapTable()

        with Horizontal():
            yield ConfigPanel()
            yield FragPanel()

        yield Static(
            "←→↑↓ Navigate  [E] Edit  [R] Refresh prices  [Tab] Switch  [Q] Quit",
            id="status",
        )
        yield Static("", id="message")
        yield Static("Prices from poe.ninja (Mirage league)", id="note")

    def on_mount(self) -> None:
        table = self.query_one(MapTable)
        table.add_columns(
            "Map",
            "Frag Avg",
            "Unique",
            "Min/map",
            "Gem Avg",
            "Total",
            "Div/hr",
            "Div/hr with carries",
        )
        self.update_map_table()
        self.action_refresh_prices()

    def action_refresh_prices(self):
        self.query_one("#message", Static).update("Fetching prices from poe.ninja...")

        frag_prices, div_price, unique_prices, gem_prices = fetch_prices()

        if frag_prices and div_price and unique_prices and gem_prices:
            global UNIQUE_PRICES, GEM_PRICES
            UNIQUE_PRICES = unique_prices
            GEM_PRICES = gem_prices

            for key, price in frag_prices.items():
                if key in FRAGS:
                    FRAGS[key] = price

            CONFIG["Div price"] = div_price

            recompute_frag_avgs()
            self.update_map_table()
            self.query_one(ConfigPanel).update_values()
            self.query_one(FragPanel).update_values()

            avg = sum(FRAGS.values()) / len(FRAGS) if FRAGS else 0
            self.query_one("#subtitle", Static).update(
                f"Pool avg: {avg:.1f}c  |  Div: {CONFIG['Div price']:.0f}c  |  Map cost: {CONFIG['Map cost']:.0f}c"
            )
            self.query_one("#message", Static).update(
                f"✓ Prices updated! (Div: {div_price:.0f}c)"
            )
        else:
            self.query_one("#message", Static).update("✗ Failed to fetch prices")

    def update_map_table(self):
        table = self.query_one(MapTable)
        table.clear()

        max_dc = max((compute_map(m)["div_hr_carry"] for m in MAPS), default=1)

        for m in MAPS:
            c = compute_map(m)
            unique_name = m.get("unique_name", "")
            unique_price = c.get("unique_price", 0)
            unique_str = f"{unique_price:.0f}c" if unique_price > 0 else "-"

            row = [
                m["name"],
                f"{m['frag_avg_val']:.2f}c",
                unique_str,
                f"{m['time_per_map']:.2f} min",
                f"{c['gem_price']:.1f}c",
                f"{c['total']:.1f}c",
                f"{c['div_hr']:.2f}",
                f"{c['div_hr_carry']:.2f}",
            ]
            table.add_row(*row)

    def action_focus_next(self):
        self.focus_index = (self.focus_index + 1) % len(self.focus_stack)
        focus = self.focus_stack[self.focus_index]

        if focus == "map":
            self.query_one(MapTable).focus()
        elif focus == "config":
            self.query_one(ConfigPanel).focus()
        elif focus == "frags":
            self.query_one(FragPanel).focus()

    def action_edit_value(self):
        focus = self.focus_stack[self.focus_index]

        if focus == "map":
            table = self.query_one(MapTable)
            if table.cursor_row is not None:
                row = table.cursor_row
                col = table.cursor_column

                field_map = {
                    1: "frag_avg_val",
                    3: "time_per_map",
                }
                if col in field_map:
                    field = field_map[col]
                    current = MAPS[row][field]
                    self.push_input(current, field, row)
        elif focus == "config":
            self.notify("Config editing - coming soon", severity="warning")
        elif focus == "frags":
            self.notify("Fragment price editing - coming soon", severity="warning")

    def push_input(self, current, field, row):
        def handle_submit(value):
            try:
                new_val = float(value) if "." in value else int(value)
                MAPS[row][field] = new_val
                self.update_map_table()
                self.query_one("#message", Static).update(
                    f"✓ Updated {field} → {value}"
                )
            except ValueError:
                self.query_one("#message", Static).update("✗ Invalid number")

        input_widget = Input(str(current), id="edit-input")
        input_widget.submit_on_enter = True  # type: ignore[attr-defined]
        input_widget.on_submit = lambda e: handle_submit(e.value)  # type: ignore[attr-defined]

        self.mount(input_widget)
        input_widget.focus()


if __name__ == "__main__":
    app = POE()
    app.run()

# PoE Fragment Farming Calculator

A terminal-based calculator for Path of Exile fragment farming profitability.

## Features

- Live price fetching from poe.ninja (Mirage league)
- Supports 5 map types: Sanctuary, Fortress, Ziggurat, Citadel, Abomination
- Calculates profitability including:
  - Fragment drops (2.5 avg per map)
  - Unique item drops (5% drop rate)
  - Skill gem drops (5% drop rate)
  - Carry earnings
- Configurable settings (persist across sessions)
- Interactive TUI with map breakdown modals

## Controls

| Key | Action |
|-----|--------|
| Tab | Switch panel |
| ↑↓ | Navigate table |
| Enter | Map breakdown |
| E | Edit value |
| C | Open config |
| R | Refresh prices |
| Q | Quit |

## Setup

```bash
# Install dependencies and run
uv run main.py
```

## Configuration

Press `C` to open the config modal and adjust:
- Carry price
- Carrys per map
- Frags per map
- Map cost

Settings are saved to `~/.poe_frag_calc.json`.

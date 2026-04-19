# InTIMEsication

**The most contagious time tracker in the wild.**

A lightweight desktop time tracking widget built with Python and Tkinter. Stays on top of all windows, tracks your sessions, and saves history locally.

## Features

- Start / pause / stop timer with a single button
- **Pomodoro mode** — 25-minute focus intervals with 5-minute breaks, break notifications with Start / Snooze / Skip actions
- Session history with auto-refresh
- Light and dark theme
- Adjustable opacity
- Always-on-top widget with drag support
- Single instance enforcement

## Requirements

- Python 3.10+
- Pillow (`pip install pillow`)

## Run from source

```bash
python tracker.py
```

## Build executable

```bash
pip install pyinstaller
pyinstaller InTIMEsication.spec
```

## Download

Grab the latest release from the [Releases](https://github.com/StaffiloCode/InTIMEsication/releases) page.

## License

All rights reserved. Purely coded, naturally spread by [Staffilocode](https://github.com/StaffiloCode).

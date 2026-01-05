
# K-Bot — Kamihime Auto-battler

A simple GUI bot that automates quests and raids for Kamihime Project R. This README explains how to set up and run the program on Windows (PowerShell), aimed at users without a programming background.

IMPORTANT: This tool controls your mouse and keyboard. Only run it when you can safely let the program take over input. Use the STOP button or press F7 to stop the bot immediately.

---

## Download

Get the latest Windows build from GitHub Releases:

👉 [Download K-Bot for Windows](https://github.com/Aprilandi/kamihime-auto-battler/releases/latest)

- Note: Currently optimized for 1920x1080 with 100% display scaling and game setting NO ZOOM (Zoom in nor Zoom out).
- If your resolution differs, add matching images under `images/<your-resolution>/` and rebuild using the provided PyInstaller command (or `main.spec`).

## How to build your own (if you want to modify images)

1. **Install dependencies**
   ```powershell
   pip install -r requirements.txt

2. **Build the script**
   ```powershell
   pyinstaller main.spec

---

## Quick overview (non-technical)
- Double-click `main.py` (or run a single command in PowerShell) to open the small K-Bot window.
- Click one of the mode buttons to start: `Raid Rot`, `Epic Rush`, or `Retry Farm`.
- While a bot mode is running the other mode buttons will be disabled (so only one runs at a time).
- Watch the log box for messages that describe what the bot is doing.
- The loop counters (Farm / Epic / Raid) are shown near the top and update while the bot runs.
- To stop the bot: press the big `STOP (F7)` button or press F7 on your keyboard.
- To reset progress counters: press `RESET`.

---

## What you need (prerequisites)
- Windows machine
- Python 3.8+ installed and available in your PATH (type `python --version` in PowerShell to check)
- The `images/` folder in this project must remain in the repository — it contains the screenshot templates the bot uses to find buttons. Do not remove it if you expect the bot to work.

Important: resolution and image templates
- This bot is designed to work with a 1920x1080 display resolution and Windows display scaling set to 100% (no zoom). The image templates in `images/` were captured at 1920x1080 — if your game runs at a different resolution or scaling the template matching will likely fail.
- If you run the game at a different resolution, retake the screenshots from your screen so they match exactly. To keep the repository tidy, move the old screenshots into a subfolder `images/old/` and save the new PNGs in `images/` using the same filenames. The bot expects the filenames in `images/` to match the keys in `config.IMAGES`.
- Quick way to replace screenshots: open the `images/` folder, create a new `old/` folder, move the existing PNG files into `images/old/`, then capture new PNGs from your running game and save them into `images/` with the same names.

If you're unsure about Python, follow the step-by-step instructions below.

---

## Easy step-by-step install (PowerShell)
Open PowerShell and run these commands from the project folder (where `main.py` is located). Copy/paste each line and press Enter.

1) Create a virtual environment (keeps dependencies local):

```powershell
python -m venv .venv
```

2) Activate it (PowerShell):

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, temporarily allow scripts for this session:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

3) Upgrade pip and install required packages:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

4) Run the app:

```powershell
python main.py
```

The GUI should open. If you see errors during install, copy the error text and paste it into an issue or message so we can help.

---

## Quick usage guide (what each UI item does)
- `Raid Rot` — cycles through selected raid elements and difficulties, hosting or joining where configured.
- `Epic Rush` — plays epic quest/story nodes (the bot will skip story when possible and run combat).
- `Retry Farm` — runs the retry farm loop (retries the quest when the retry prompt appears).
- `RESCUE` (checkbox) — when checked, the bot will attempt in-game rescue flows; when unchecked, the bot will give up and return to the quest list on death.
- Loop counters (Farm / Epic / Raid) — show how many iterations have run.
- `STOP (F7)` — stop any running sequence (hotkey F7 works too).
- `RESET` — set progress (counters) back to zero.

---

## Safety & troubleshooting
- The bot clicks the screen. Make sure the game is visible and not obscured by other windows.
- If the bot appears to do nothing, confirm:
	- The game window is visible and at the expected resolution.
	- The `images/` folder is present and intact (PNG files).
	- The virtual environment is activated and dependencies installed.
- If image detection fails often, try increasing your screen brightness or run the game at a stable resolution / scaling (100%).
- If PowerShell shows permission errors when activating the venv, run the `Set-ExecutionPolicy` line above to allow the script for your session.

---

## Want to tweak behavior?
- If you want counters shown in a different place or the bot to count different events, we can adjust it.
- If detection is flaky we can relax the confidence thresholds or add extra sleeps.

---

Thank you — be careful when running automation, and keep an eye on the log box so you can stop the bot if something unexpected happens.

# kamihime-auto-battler


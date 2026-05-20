
# K-Bot — Kamihime Auto-battler

A simple GUI bot that automates quests and raids for Kamihime Project R. This bot currently only optimized for screen resolution 1920x1080 with 100% display scaling and browser setting NO ZOOM (Zoom in nor Zoom out). If you have different screen resolution this README explains how to set up, modify, and run the program on Windows (PowerShell), aimed at users without a programming background.

IMPORTANT: This tool controls your mouse. Only run it when you can safely let the program take over input. Use the STOP button or press F7 (may need multiple times) to stop the bot immediately.

---

## Download

Get the latest Windows build from GitHub Releases:

👉 [Download K-Bot for Windows](https://github.com/Aprilandi/kamihime-auto-battler/releases/latest)

- Note: Currently optimized for 1920x1080 with 100% display scaling and browser setting NO ZOOM (Zoom in nor Zoom out).
- If your resolution differs, add matching images under `images/<your-resolution>/` and rebuild, follow the steps after `Quick overview (non-technical)`.

---

## Quick overview (non-technical)
- Button `Raid Host` is used for starting raid quests, starting point for this is at `Raid Quests` under `Fire Element` on the `First Page` always even if you did not check any `Fire Raid Quests` always open the `Fire Element First Page`.
- Button `Farm Raid` is used for auto joining selected raids, starting point for this is at `Raid Boss Available!`.
- Button `Quest Rush` is used for starting `Main Quest`, starting point this is when the `Magic Jewel` on screen.
- Button `Epic Quest Rush` is used for starting the `Epic Quest`, starting point for this is the same with `Quest Rush` but for `Epic Quest`.
- Button `Retry Farm` is used for starting the same quest over and over again until you stop the bot, starting point for this is when the `Retry` button available (after you completed the quest or on the summary of the battle page).
- Button `Episode Rush` is used for auto completing all of the unread harem episode, starting point for this is in `Episode` where the `Exclamation Mark` exists (turn on filter `Episode Unread` for much faster automation).
- To stop the bot: press the big `STOP (F7)` button or press F7 on your keyboard.
- To reset progress counters: press `RESET`.

---
## This step is for when you modify the code or you have different resolution and added your own images

### What you need (prerequisites)

- Windows machine
- Python 3.8+ installed and available in your PATH (type `python --version` in PowerShell to check)
- The `images/` folder in this project must remain in the repository — it contains the screenshot templates the bot uses to find buttons. Do not remove it if you expect the bot to work.

**Important: resolution and image templates**

- This bot is designed to work with a **1920x1080** display resolution and Windows display scaling set to **100%** (no zoom). The image templates in `images/` were captured at 1920x1080 — if your game runs at a different resolution or scaling the template matching will likely fail.
- If you run the game at a different resolution, add a new folder named from your resolution under folder `images/`.
- Retake all screenshots from `images/1920x1080` from your screen with the exact same name and filetype (`.PNG`), and save it under your resolution folder.
- After you are done retaking all images from `images/1920x1080` into your own resolution folder `images/<your resolution>`, rebuild the code.

If you're unsure about Python, follow the step-by-step instructions below.



### How to build your own (if you want to modify or add images)

1. **Install dependencies**
   ```powershell
   pip install -r requirements.txt
   ```

2. **Build the script**
   ```powershell
   pyinstaller main.spec
   ```

3. **Locate the exe file and run it**
   ```powershell
   .\kamihime-auto-battler\dist
   ```

The GUI should open. If you see errors during install, copy the error text and paste it into an issue or message so we can help.

---

## Safety & troubleshooting

- The bot clicks the screen. Make sure the game is visible and not obscured by other windows.
- If the bot appears to do nothing, confirm:
  - **Ensure** the game window is visible and at the expected resolution.
  - **Check** the `images/` folder is present and intact (PNG files).
  - **Activate** the virtual environment and install dependencies.
- If image detection fails often, try increasing your screen brightness or run the game at a stable resolution / scaling (**100%**).
- If PowerShell shows permission errors when activating the venv, run the `Set-ExecutionPolicy` line above to allow the script for your session.

---

## Want to tweak behavior?

- If you want counters shown in a different place or the bot to count different events, we can adjust it.
- If detection is flaky we can relax the confidence thresholds or add extra sleeps.

---

Thank you — be careful when running automation, and keep an eye on the log box so you can stop the bot if something unexpected happens.

# kamihime-auto-battler


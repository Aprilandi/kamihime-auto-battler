import pyautogui
import time
import os
from .core import state, CONFIDENCE, SLEEP, log_msg


def find_and_click(image, timeout=SLEEP, confidence=CONFIDENCE, max_attempts=1, log_widget=None):
    """Try locateOnScreen and click the center. Returns True if clicked.

    Will attempt up to max_attempts times (useful for transient UIs). Sleeps `timeout` after click.
    """
    if not image:
        return False

    # friendly name for logs
    try:
        name = os.path.basename(image)
    except Exception:
        name = str(image)

    log_msg(f"Searching for {name}", log_widget)

    attempts = 0
    while attempts < max_attempts and state.get("running", False):
        try:
            btn = pyautogui.locateOnScreen(image, confidence=confidence)
            if btn:
                log_msg(f"Found {name}, clicking", log_widget)
                try:
                    time.sleep(0.5)
                    pyautogui.click(pyautogui.center(btn))
                except Exception:
                    # fallback: click top-left of the located box
                    pyautogui.click(btn.left + 5, btn.top + 5)
                log_msg(f"Clicked {name}", log_widget)
                return True
            time.sleep(timeout)
        except Exception as e:
            log_msg(f"Error locating {name}: {e}", log_widget)
        attempts += 1
        time.sleep(0.12)
    log_msg(f"Did not find {name} after {attempts} attempts", log_widget)
    return False


def _clear_ok_multiple(IMAGES, log_widget=None, max_clicks=6):
    """Click OK repeatedly (up to max_clicks) while it appears on screen.

    Returns the number of OK clicks performed.
    """
    clicks = 0
    while clicks < max_clicks and state.get("running", False):
        ok = IMAGES.get("ok")
        if ok and pyautogui.locateOnScreen(ok, confidence=CONFIDENCE):
            find_and_click(ok, timeout=0.3, confidence=CONFIDENCE, max_attempts=3, log_widget=log_widget)
            clicks += 1
            time.sleep(0.3)
            continue
        break
    return clicks


def wait_for_image(image, confidence=CONFIDENCE, timeout=10):
    """Wait until an image appears on screen or timeout expires."""
    start = time.time()
    while time.time() - start < timeout and state.get("running", False):
        if pyautogui.locateOnScreen(image, confidence=confidence):
            return True
        time.sleep(0.25)  # avoid busy loop
    return False


def ongoing_raids(IMAGES, log_widget=None, timeout=1.0, attempts=1):
    """Check for ongoing raids dialog and click resume if found.

    Returns True if an ongoing raid was detected and resumed.
    """
    log_msg("Checking for ongoing or completed raids...", log_widget)
    tried = 0
    while tried < attempts and state.get("running", False):
        start_time = time.time()
        while time.time() - start_time < timeout and state.get("running", False):
            if IMAGES.get("ongoing") and pyautogui.locateOnScreen(IMAGES["ongoing"], confidence=CONFIDENCE):
                log_msg("Ongoing raid detected, cancelling", log_widget)
                find_and_click(IMAGES["cancel"], timeout=0.5, max_attempts=3, log_widget=log_widget)
                time.sleep(SLEEP)
                return False
            elif IMAGES.get("batch") and pyautogui.locateOnScreen(IMAGES["batch"], confidence=CONFIDENCE):
                log_msg("Batch raid detected, completing", log_widget)
                find_and_click(IMAGES["batch"], timeout=0.5, max_attempts=3, log_widget=log_widget)
                time.sleep(SLEEP)
                return True
            time.sleep(0.3)
        tried += 1
    return True


def try_page_down(IMAGES):
    down = None
    try:
        if IMAGES.get("down"):
            down = pyautogui.locateOnScreen(IMAGES["down"], confidence=0.88)
    except Exception as e:
        log_msg(f"Error locating down button: {e}")

    if not down:
        return False

    # Safely check for down_max within an expanded region around the down button.
    try:
        left = max(0, down.left - 20)
        top = max(0, down.top - 20)
        width = down.width + 40
        height = down.height + 40
        region = (left, top, width, height)

        # If down_max exists within the region, we are at the end
        if IMAGES.get("down_max"):
            try:
                if pyautogui.locateOnScreen(IMAGES["down_max"], region=region, confidence=0.9):
                    return False
            except ValueError:
                # needle too large for region; fallback to full-screen search
                if pyautogui.locateOnScreen(IMAGES["down_max"], confidence=0.9):
                    return False
    except Exception as e:
        # be defensive: if anything goes wrong, log and continue with a safe full-screen check
        log_msg(f"Error checking down_max: {e}")
        if IMAGES.get("down_max") and pyautogui.locateOnScreen(IMAGES["down_max"], confidence=0.9):
            return False

    # Click the down button (use center) and wait briefly
    try:
        pyautogui.click(pyautogui.center(down))
    except Exception:
        # fallback click the raw box
        pyautogui.click(down.left + 5, down.top + 5)
    time.sleep(1.2)
    return True

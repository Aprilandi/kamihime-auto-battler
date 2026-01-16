import time
import pyautogui
import os
from config import CONFIDENCE, IMAGES, SLEEP, CONNECTING, resource_path
from PIL import Image
import pytesseract
import re

# Path relative to your project
pytesseract.pytesseract.tesseract_cmd = resource_path(
    os.path.join("tesseract", "tesseract.exe")
)


# Shared state and common constants
state = {"running": False, "raid_settings": {}, "completed_raids": {}}
CONFIDENCE = 0.8
SLEEP = 1.0


def log_msg(message, log_widget=None):
    """Write a message to the UI log if provided."""
    if log_widget:
        try:
            log_widget.insert("end", f"> {message}\n")
            log_widget.see("end")
        except Exception:
            # avoid noisy exceptions from UI
            pass


def _inc_loop(name, log_widget=None):
    """Increment a named loop counter stored in state['loop_counts'] and return the new value.

    This is defensive: if the key doesn't exist we create it.
    """
    if "loop_counts" not in state:
        state["loop_counts"] = {}
    state["loop_counts"][name] = state["loop_counts"].get(name, 0) + 1
    val = state["loop_counts"][name]
    log_msg(f"Loop counter [{name}] = {val}", log_widget)
    return val


# --- Power Management Helpers (Windows) -----------------
try:
    import ctypes
    _ES_CONTINUOUS = 0x80000000
    _ES_SYSTEM_REQUIRED = 0x00000001
    _ES_DISPLAY_REQUIRED = 0x00000002

    def prevent_sleep():
        """Prevent the system from sleeping and the display from turning off.

        Uses SetThreadExecutionState on Windows. Safe to call multiple times.
        """
        try:
            ctypes.windll.kernel32.SetThreadExecutionState(
                _ES_CONTINUOUS | _ES_SYSTEM_REQUIRED | _ES_DISPLAY_REQUIRED
            )
            return True
        except Exception:
            return False

    def allow_sleep():
        """Restore normal sleep behavior."""
        try:
            ctypes.windll.kernel32.SetThreadExecutionState(_ES_CONTINUOUS)
            return True
        except Exception:
            return False
except Exception:
    # Non-Windows or ctypes not available: provide no-op fallbacks
    def prevent_sleep():
        return False

    def allow_sleep():
        return False


def find_and_click(image, confidence=CONFIDENCE, timeout=1.0, optional=False, log_widget=None, robust=True):
    """Find an image on screen and click it.
    """
    if not image:
        return False

    # friendly name for logs
    try:
        name = os.path.basename(image)
    except Exception:
        name = str(image)
        
    log_msg(f"Searching for {name}", log_widget)

    start_time = time.time()
    
    while state.get("running", False): 
        btn = pyautogui.locateOnScreen(image, confidence=confidence)

        if btn and not robust:
            log_msg(f"Found {name} (Non Robust), clicking", log_widget) 
            try:
                time.sleep(SLEEP)
                pyautogui.click(pyautogui.center(btn))
            except Exception:
                # fallback: click top-left of the located box
                time.sleep(SLEEP)
                pyautogui.click(btn.left + 5, btn.top + 5)
            log_msg(f"Clicked {name}", log_widget)
            wait(log_widget=log_widget)
            return True

        if btn and robust:
            log_msg(f"Found {name} (Robust), attempting click", log_widget)
            
            region = (btn.left, btn.top, btn.width, btn.height)

            try:
                time.sleep(SLEEP)
                pyautogui.click(pyautogui.center(btn))
            except Exception:
                time.sleep(SLEEP)
                pyautogui.click(btn.left + 5, btn.top + 5)

            found_still = pyautogui.locateOnScreen(image, region=region, confidence=confidence)
                    
            if not found_still:
                log_msg(f"Button {name} disappeared, assumed success.", log_widget)
                wait(log_widget=log_widget)
                return True
            else:
                start_time = time.time()
        
        if optional: 
            elapsed = time.time() - start_time 
            if elapsed >= timeout: 
                return False 
            
        # Prevent CPU hogging 
        time.sleep(0.1)


def find_and_click_all(image, confidence=CONFIDENCE, timeout=1.0, optional=False, log_widget=None):
    log_msg("Searching for available raids...", log_widget)
    
    # 1. Find all instances of the raid banner
    # grayscale=True and confidence help with speed and slight color variations
    all_raids = list(pyautogui.locateAllOnScreen(image, confidence=confidence))
    
    if not all_raids:
        log_msg("No raids found on screen.", log_widget)
        return False

    for raid_box in all_raids:
        # raid_box is (left, top, width, height)
        
        # 2. Check if 'In Battle' exists INSIDE this specific raid banner area
        # We limit the search region to speed it up and avoid finding other raids
        is_busy = pyautogui.locateOnScreen(
            IMAGES['in_battle'], 
            region=(raid_box.left- 20, raid_box.top - 20, raid_box.width + 20, raid_box.height + 20),
            confidence=CONFIDENCE
        )
        
        if is_busy is None:
            log_msg(f"Found available raid at {raid_box.left}, {raid_box.top}. Clicking...", log_widget)
            # Click the center of the available raid
            pyautogui.click(pyautogui.center(raid_box))
            if find_and_click(IMAGES['ok'], log_widget=log_widget, optional=True, confidence=0.99) is True:
                log_msg("Only 3 raid battle at once allowed. Waiting...", log_widget)
                return False
            if find_and_click(IMAGES['batch'], log_widget=log_widget, optional=True):
                log_msg("Completing batch raid...", log_widget)

                wait(log_widget=log_widget)

                # for in case of rank up
                find_and_click(IMAGES['ok'], optional=True, timeout=3.0, log_widget=log_widget)
                pyautogui.click(pyautogui.center(raid_box))
            if pyautogui.locateOnScreen(IMAGES['cancel'], confidence=CONFIDENCE) \
                and not pyautogui.locateOnScreen(IMAGES['stamina_use'], confidence=CONFIDENCE) \
                and not pyautogui.locateOnScreen(IMAGES['batch'], confidence=CONFIDENCE):
                find_and_click(IMAGES['cancel'], log_widget=log_widget)
                find_and_click(IMAGES['ok'], log_widget=log_widget)
                find_and_click(IMAGES['start_game'], log_widget=log_widget)
                find_and_click(IMAGES['raid_quest_available'], log_widget=log_widget)
                return False

            return True
        else:
            log_msg("Raid found, but it is already 'In Battle'. Skipping...", log_widget)

    log_msg("All visible raids are currently occupied.", log_widget)
    return False


def post_battle(IMAGES, timeout=5.0, confidence=CONFIDENCE, log_widget=None):
    ok = IMAGES.get("ok")
    start_time = time.time()

    while state.get("running", False):
        if (time.time() - start_time) >= timeout:
            return True
        else:
            if find_and_click(ok, confidence=confidence, optional=True, timeout=1.0, log_widget=log_widget):
                start_time = time.time()
            
        time.sleep(SLEEP)
        
    return False


def next_page(IMAGES, log_widget=None):
    """Go to the next page in menus.
    """
    log_msg("Navigating to next page", log_widget)
    if IMAGES.get('down_max') and pyautogui.locateOnScreen(IMAGES['down_max'], confidence=0.99):
        log_msg("Reached end of page.")
        return False
    else:
        log_msg("Searching the down button...")
        if find_and_click(IMAGES.get('down'), log_widget=log_widget, robust=False):
            time.sleep(1.0)
            return True


def find_text(texts, log_widget=None):
    screenshot = pyautogui.screenshot()
    text_image = pytesseract.image_to_string(screenshot).lower()

    for t in texts:
        if t.lower() in text_image:
            return True

    return False


def find_and_click_text(texts, timeout=1.0, optional=False, log_widget=None):
    screenshot = pyautogui.screenshot()
    data = pytesseract.image_to_data(screenshot, output_type=pytesseract.Output.DICT)
    start_time = time.time()

    log_msg(f"Searching text {texts}...", log_widget)
    while state.get("running", False):
        for i, word in enumerate(data["text"]):
            if word in texts:
                x, y, w, h = data["left"][i], data["top"][i], data["width"][i], data["height"][i]
                center_x, center_y = x + w // 2, y + h // 2

                log_msg(f"Found text '{word}', clicking", log_widget)
                pyautogui.click(center_x, center_y)
                return True

        if optional: 
            elapsed = time.time() - start_time 
            if elapsed >= timeout: 
                return False 

        time.sleep(SLEEP)
        
        
def wait(timeout=5.0, sleep=0.1, log_widget=None, attempts=4):
    time.sleep(SLEEP)
    misses = 0
    start_time = time.time()
    
    while state.get("running", False):
        is_detected = CONNECTING and pyautogui.locateOnScreen(CONNECTING, confidence=CONFIDENCE)
        
        if is_detected:
            misses = 0
            log_msg("Detected CONNECTING, waiting...", log_widget)
            while CONNECTING and pyautogui.locateOnScreen(CONNECTING, confidence=CONFIDENCE):
                time.sleep(sleep)
                if (time.time() - start_time) > timeout:
                    return
        else:
            misses += 1
            if misses >= attempts:
                return

        if (time.time() - start_time) > timeout:
            return

        time.sleep(sleep)


def test_function(texts, timeout=1.0, optional=False, log_widget=None):
    screenshot = pyautogui.screenshot()
    data = pytesseract.image_to_data(screenshot, output_type=pytesseract.Output.DICT)
    start_time = time.time()
    log_msg(f"Searching text {texts}...", log_widget)

    while state.get("running", False):
        for i, word in enumerate(data["text"]):
            if word in texts:
                x, y, w, h = data["left"][i], data["top"][i], data["width"][i], data["height"][i]
                center_x, center_y = x + w // 2, y + h // 2

                log_msg(f"Found text '{word}', clicking", log_widget)
                pyautogui.click(center_x, center_y)
                return True

        if optional: 
            elapsed = time.time() - start_time 
            if elapsed >= timeout: 
                return False 

        time.sleep(SLEEP)

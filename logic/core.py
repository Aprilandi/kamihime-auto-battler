import time
import pyautogui
import numpy as np
import os
from config import CONFIDENCE, IMAGES, SLEEP, CONNECTING, resource_path
from PIL import Image
import pytesseract
import re
import logging

# Path relative to your project
pytesseract.pytesseract.tesseract_cmd = resource_path(
    os.path.join("tesseract", "tesseract.exe")
)


# Shared state and common constants
state = {"running": False, "raid_settings": {}, "completed_raids": {}}
CONFIDENCE = 0.8
SLEEP = 1.0

# Configure logging once at the start of your program
logging.basicConfig(
    level=logging.DEBUG,  # change to DEBUG if you want more detail
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("debug.log")]
)

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


def find_and_click(image, confidence=CONFIDENCE, timeout=1.0, optional=False, log_widget=None, robust=True, offset=0):
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
    clicked = False
    
    while state.get("running", False): 
        btn = pyautogui.locateOnScreen(image, confidence=confidence)

        if btn and not robust:
            log_msg(f"Found {name} (Non Robust), clicking", log_widget) 
            try:
                time.sleep(SLEEP)
                center = pyautogui.center(btn)
                target_x = center.x
                target_y = center.y + offset
                
                pyautogui.click(target_x, target_y)
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
                center = pyautogui.center(btn)
                target_x = center.x
                target_y = center.y + offset
                
                pyautogui.click(target_x, target_y)
                clicked = True
            except Exception:
                time.sleep(SLEEP)
                pyautogui.click(btn.left + 5, btn.top + 5)
                clicked = True

            found_still = pyautogui.locateOnScreen(image, region=region, confidence=confidence)
                    
            if not found_still:
                log_msg(f"Button {name} disappeared, assumed success.", log_widget)
                wait(log_widget=log_widget)
                return True
            else:
                log_msg(f"Button {name} still visible, will try clicking again...", log_widget)
        
        if optional: 
            elapsed = time.time() - start_time 
            if elapsed >= timeout: 
                if robust and clicked:
                    log_msg(f"Button {name} vanished after a click, assumed success.", log_widget=log_widget)
                    return True
                return False 
            
        # Prevent CPU hogging 
        time.sleep(0.1)


def find_and_click_all(image, confidence=CONFIDENCE, timeout=1.0, optional=False, log_widget=None):
    try:
        name = os.path.basename(image)
    except Exception:
        name = str(image)
        
    log_msg(f"Searching for {name}", log_widget)

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
            wait(log_widget=log_widget)
            # Click the center of the available raid
            pyautogui.click(pyautogui.center(raid_box))
            while state.get('running', False):
                
                check_stamina(IMAGES, log_widget=log_widget, timeout=0.5)
                
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
                    and find_text(['an error'], log_widget=log_widget) is True \
                    and not pyautogui.locateOnScreen(IMAGES['stamina_use'], confidence=CONFIDENCE) \
                    and not pyautogui.locateOnScreen(IMAGES['batch'], confidence=CONFIDENCE):
                    find_and_click(IMAGES['cancel'], log_widget=log_widget)
                    find_and_click(IMAGES['ok'], log_widget=log_widget, optional=True)
                    find_and_click(IMAGES['start_game'], log_widget=log_widget, optional=True)
                    find_and_click(IMAGES['raid_quest_available'], log_widget=log_widget)
                    return False

                if pyautogui.locateOnScreen(IMAGES['support'], confidence=CONFIDENCE):
                    return True

                time.sleep(SLEEP)
        else:
            log_msg("Raid found, but it is already 'In Battle'. Skipping...", log_widget)

    log_msg("All visible raids are currently occupied.", log_widget)
    return False


def post_battle(IMAGES, timeout=5.0, confidence=CONFIDENCE, log_widget=None):
    ok = IMAGES.get("ok")
    start_time = time.time()
    isOk = False

    while state.get("running", False):
        if find_and_click(ok, confidence=confidence, optional=True, timeout=1.0, log_widget=log_widget):
            start_time = time.time()
            isOk = True

        elif (time.time() - start_time) >= timeout or isOk:
            return True
            
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
        log_msg("Searching the down button...", log_widget=log_widget)
        if find_and_click(IMAGES.get('down'), log_widget=log_widget, robust=False):
            time.sleep(1.0)
            return True


def scroll_down(list_region, log_widget=None, scroll_x = 600, scroll_y = 420):
    log_msg("Scrolling down...", log_widget=log_widget)
    before = pyautogui.screenshot()

    pyautogui.moveTo(scroll_x, scroll_y)
    pyautogui.scroll(-150)
    time.sleep(SLEEP)
    
    after = pyautogui.screenshot()
    
    # if screenshots are identical, we've hit the bottom
    if screenshots_are_same(before, after, list_region):
        log_msg("Reached bottom of list", log_widget)
        return False
    else:
        return True


def screenshots_are_same(img1, img2, region, threshold=0.99):
    x, y, w, h = region
    crop1 = np.array(img1.crop((x, y, x+w, y+h)))
    crop2 = np.array(img2.crop((x, y, x+w, y+h)))
    similarity = np.mean(crop1 == crop2)
    return similarity >= threshold


def find_text(texts, log_widget=None):
    screenshot = pyautogui.screenshot()
    text_image = pytesseract.image_to_string(screenshot).lower()

    # Return True only when all provided words are present in the screen text
    for t in texts:
        if t.lower() not in text_image:
            # log_msg(f"Tagged Word: {t.lower()} (False)", log_widget=log_widget)
            return False
        # log_msg(f"Tagged Word: {t.lower()} (True)", log_widget=log_widget)

    return True


def find_and_click_text(texts, timeout=1.0, optional=False, log_widget=None, index=0, phrase=False):
    screenshot = pyautogui.screenshot()
    data = pytesseract.image_to_data(screenshot, output_type=pytesseract.Output.DICT)
    start_time = time.time()

    log_msg(f"Searching text {texts}...", log_widget)
    while state.get("running", False):
        matches = []

        if phrase and len(texts) > 1:
            # Look for consecutive words matching the phrase in order
            words = [w.lower() for w in data["text"]]
            phrase_words = [w.lower() for w in texts]

            for i in range(len(words) - len(phrase_words) + 1):
                if words[i:i+len(phrase_words)] == phrase_words:
                    # Bounding box spanning all matched words
                    x = data["left"][i]
                    y = data["top"][i]
                    x2 = data["left"][i + len(phrase_words) - 1] + data["width"][i + len(phrase_words) - 1]
                    y2 = max(data["top"][j] + data["height"][j] for j in range(i, i + len(phrase_words)))
                    matches.append(((x + x2) // 2, (y + y2) // 2, " ".join(texts)))
        else:
            for i, word in enumerate(data["text"]):
                if word in texts:
                    x, y, w, h = data["left"][i], data["top"][i], data["width"][i], data["height"][i]
                    matches.append((x + w // 2, y + h // 2, word))

        if len(matches) > index:
            center_x, center_y, word = matches[index]
            log_msg(f"Found '{word}' (match #{index}), clicking", log_widget)
            pyautogui.click(center_x, center_y)
            return True

        if optional:
            if time.time() - start_time >= timeout:
                return False

        time.sleep(SLEEP)
        
        
def get_all_visible_text(log_widget=None):
    """Capture a screenshot and extract all visible text using OCR for debugging purposes."""
    screenshot = pyautogui.screenshot()
    text = pytesseract.image_to_string(screenshot)
    log_msg(f"All visible text on screen:\n{text}", log_widget)
    # if find_text(['element'], log_widget=log_widget):
    #     log_msg("True", log_widget=log_widget)
    # else:
    #     log_msg("False", log_widget=log_widget)
        
def wait(timeout=3.0, sleep=0.1, log_widget=None, attempts=2):
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


def check_stamina(IMAGES, log_widget=None, timeout=1.5):
    start_time = time.time()

    while state.get("running", False):

        elapsed = time.time() - start_time 
        if elapsed >= timeout:
            log_msg("Stamina or BP is still sufficient", log_widget)
            return False

        if (IMAGES.get('stamina_check') and pyautogui.locateOnScreen(IMAGES['stamina_check'], confidence=CONFIDENCE)) or (IMAGES.get('bp_check') and pyautogui.locateOnScreen(IMAGES['bp_check'], confidence=CONFIDENCE)):
            log_msg("Stamina or BP low detected", log_widget)
            if find_and_click(IMAGES['stamina_use'], log_widget=log_widget) is True:
                find_and_click(IMAGES['ok'], log_widget=log_widget)
                return True

        time.sleep(SLEEP)


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

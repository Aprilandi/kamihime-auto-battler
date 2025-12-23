import time
import pyautogui
import os


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


def find_and_click(image, confidence=CONFIDENCE, timeout=1.0, optional=False, log_widget=None):
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
        # Example condition: replace with your actual check 
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
        
        if optional: 
            elapsed = time.time() - start_time 
            if elapsed >= timeout: 
                return False 
            
        # Prevent CPU hogging 
        time.sleep(0.1)

        
def post_battle(IMAGES, timeout=1.0, confidence=CONFIDENCE, log_widget=None):
    start_time = time.time()
    ok = IMAGES.get("ok")
    time.sleep(3.0)
    while state.get("running", False):
        if not pyautogui.locateOnScreen(ok, confidence=confidence):
            return True
        else:
            find_and_click(ok, confidence=confidence, timeout=timeout, log_widget=log_widget)
            
        time.sleep(0.5)
        
    return False

def next_page(IMAGES, log_widget=None):
    """Go to the next page in menus.
    """
    log_msg("Navigating to next page", log_widget)
    if IMAGES.get('down_max') and pyautogui.locateOnScreen(IMAGES['down_max'], confidence=0.95):
        return False
    else:
        if find_and_click(IMAGES.get('down'), log_widget=log_widget):
            time.sleep(1.0)
            return True
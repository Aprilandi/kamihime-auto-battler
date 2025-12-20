import pyautogui
import time

# Shared state
state = {"RUNNING": False, "raid_settings": {}, "completed_raids": {}}

def log_msg(message, log_widget):
    if log_widget:
        log_widget.insert("end", f"> {message}\n")
        log_widget.see("end")

# --- COMBAT HELPERS ---
def combat_sequence(IMAGES):
    if pyautogui.locateOnScreen(IMAGES["attack"], confidence=0.8):
        pyautogui.click(pyautogui.center(pyautogui.locateOnScreen(IMAGES["attack"])))

# --- MODE 1: RETRY FARM ---
def farm_loop(log_widget, IMAGES):
    log_msg("STARTING FARM LOOP", log_widget)
    while state["RUNNING"]:
        combat_sequence(IMAGES)
        if pyautogui.locateOnScreen(IMAGES["retry"], confidence=0.8):
            pyautogui.click(pyautogui.center(pyautogui.locateOnScreen(IMAGES["retry"])))
            time.sleep(2)

# --- MODE 2: EPIC QUEST RUSH ---
def epic_quest_rush(log_widget, IMAGES):
    log_msg("STARTING EPIC RUSH", log_widget)
    while state["RUNNING"]:
        if pyautogui.locateOnScreen(IMAGES["story_start"], confidence=0.8):
            pyautogui.click(pyautogui.center(pyautogui.locateOnScreen(IMAGES["story_start"])))
        if pyautogui.locateOnScreen(IMAGES["skip"], confidence=0.8):
            pyautogui.click(pyautogui.center(pyautogui.locateOnScreen(IMAGES["skip"])))
            time.sleep(0.5)
            # Try to click OK if a skip confirmation appears
            ok_btn = pyautogui.locateOnScreen(IMAGES["ok"], confidence=0.8)
            if ok_btn: pyautogui.click(ok_btn)
        combat_sequence(IMAGES)
        if pyautogui.locateOnScreen(IMAGES["return"], confidence=0.8):
            pyautogui.click(pyautogui.center(pyautogui.locateOnScreen(IMAGES["return"])))
            time.sleep(2)

# --- MODE 3: RAID ROTATION ---
def raid_host_rotation(log_widget, ELEMENTS, IMAGES, get_img):
    log_msg("STARTING RAID ROTATION", log_widget)
    for index, el in enumerate(ELEMENTS):
        if not state["RUNNING"]: break
        
        # Tab selection
        if index > 0:
            tab_img = get_img(f"KHR_raid_{el}")
            tab_loc = pyautogui.locateCenterOnScreen(tab_img, confidence=0.8)
            if tab_loc:
                pyautogui.click(tab_loc)
                time.sleep(2.5)
        
        element_finished = False
        while not element_finished and state["RUNNING"]:
            found_any = False
            for diff in state["raid_settings"][el]:
                if not state["raid_settings"][el][diff] or state["completed_raids"][el][diff]:
                    continue

                btn = pyautogui.locateOnScreen(get_img(f"KHR_{el}_{diff}"), confidence=0.75)
                if btn:
                    found_any = True
                    pyautogui.click(pyautogui.center(btn))
                    time.sleep(2)
                    
                    # Handles Level Requirement, Limit, or Stamina OK buttons
                    ok_btn = pyautogui.locateOnScreen(IMAGES["ok"], confidence=0.8)
                    if ok_btn:
                        log_msg(f"Skipping {diff} (OK popup)", log_widget)
                        pyautogui.click(ok_btn)
                        state["completed_raids"][el][diff] = True 
                    else:
                        state["completed_raids"][el][diff] = True
                    break 

            if not found_any:
                down_loc = pyautogui.locateOnScreen(IMAGES["down"], confidence=0.7)
                if down_loc and not pyautogui.locateOnScreen(IMAGES["down_max"], region=down_loc, confidence=0.9):
                    pyautogui.click(down_loc)
                    time.sleep(1.2)
                else:
                    element_finished = True
    state["RUNNING"] = False
    log_msg("RAID ROTATION DONE", log_widget)

# --- MODE 4: FARM RAID (Future Placeholder) ---
def farm_raid_placeholder(log_widget, IMAGES):
    log_msg("FARM RAID NOT IMPLEMENTED YET", log_widget)
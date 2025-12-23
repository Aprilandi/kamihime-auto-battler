import time
import pyautogui
from .core import state, CONFIDENCE, SLEEP, log_msg, _inc_loop, find_and_click, post_battle

def combat_sequence(IMAGES, log_widget=None):
    if find_and_click(IMAGES['support']):
        log_msg("Support found and clicked", log_widget)
        
        find_and_click(IMAGES['go_quest'])
        
        while state.get("running", False):
            if find_and_click(IMAGES['support_req'], optional=True, log_widget=log_widget):
                log_msg("Support request found and clicked", log_widget)
            
            if find_and_click(IMAGES['attack'], log_widget=log_widget):
                log_msg("Attack button found and clicked", log_widget)
                break
            
            time.sleep(0.5)
            
        user_allows_rescue = state.get("rescue", True)
        rescue_present = IMAGES.get("rescue") and pyautogui.locateOnScreen(IMAGES["rescue"], confidence=CONFIDENCE)
        rescue_active = bool(user_allows_rescue and rescue_present)

        if rescue_present:
            if user_allows_rescue:
                log_msg("Rescue available and enabled - clicking rescue", log_widget)
                time.sleep(SLEEP)
                find_and_click(IMAGES["rescue"], timeout=0.6, max_attempts=3, log_widget=log_widget)
            else:
                log_msg("Rescue available but user disabled rescue - not clicking", log_widget)

        state["rescue_active_for_current_battle"] = rescue_active
        wait_for_battle_end(IMAGES, log_widget)


def wait_for_battle_end(IMAGES, log_widget=None):
    while state.get("running", False):
        if IMAGES.get("return") and pyautogui.locateOnScreen(IMAGES["return"], confidence=CONFIDENCE):
            log_msg("Battle ended - Return button found", log_widget)
            break
        
        if IMAGES.get("retry") and pyautogui.locateOnScreen(IMAGES["retry"], confidence=CONFIDENCE):
            log_msg("Battle ended - Retry button found", log_widget)
            break
        
        if IMAGES.get("ok") and pyautogui.locateOnScreen(IMAGES["ok"], confidence=CONFIDENCE):
            log_msg("Battle ended or rescue is available - OK button found", log_widget)
            break
        
        if IMAGES.get("return_raid") and pyautogui.locateOnScreen(IMAGES["return_raid"], confidence=CONFIDENCE):
            log_msg("Battle ended - Return Raid button found", log_widget)
            break
        
        if IMAGES.get("defeat_elixir") and pyautogui.locateOnScreen(IMAGES["defeat_elixir"], confidence=CONFIDENCE):
            log_msg("Defeated detected cancelling the revive...", log_widget)
            if find_and_click(IMAGES["cancel"], log_widget=log_widget):
                if state.get("rescue", False):
                    log_msg("Rescue is exist and enabled - clicking cancel to wait for rescue", log_widget)
                    find_and_click(IMAGES['cancel'], log_widget=log_widget)
                    break
                else:
                    log_msg("Rescue is disabled or doesn't exist - returning to quest list", log_widget)
                    find_and_click(IMAGES['quest_list'], log_widget=log_widget)
                    return
            break

        time.sleep(0.5)
        
    post_battle(IMAGES, log_widget=log_widget)
    
    return

def check_stamina(IMAGES, log_widget=None, timeout=1.5):
    start_time = time.time()

    while state.get("running", False):

        elapsed = time.time() - start_time 
        if elapsed >= timeout:
            log_msg("Stamina is still sufficient", log_widget)
            return False

        if IMAGES.get('stamina_check') and pyautogui.locateOnScreen(IMAGES['stamina_check'], confidence=CONFIDENCE):
            log_msg("Stamina low detected", log_widget)
            if find_and_click(IMAGES['stamina_use'], log_widget=log_widget):
                find_and_click(IMAGES['ok'], log_widget=log_widget)
                return True

        time.sleep(0.5)
        
def ongoing_battle(IMAGES, log_widget=None, timeout=1.5):
    start_time = time.time()
    
    while state.get("running", False):
        elapsed = time.time() - start_time 
        if elapsed >= timeout:
            log_msg("No ongoing battle detected", log_widget)
            return False

        if IMAGES.get("ongoing") and pyautogui.locateOnScreen(IMAGES["ongoing"], confidence=CONFIDENCE):
            log_msg("Ongoing battle detected", log_widget)
            find_and_click(IMAGES['cancel'], log_widget=log_widget)
            return True
        
        if IMAGES.get("batch") and pyautogui.locateOnScreen(IMAGES["batch"], confidence=CONFIDENCE):
            log_msg("Completed battle detected, completing via batch...", log_widget)
            find_and_click(IMAGES['batch'], log_widget=log_widget)
            return True
                
        time.sleep(0.5)


def handle_raid_entry(IMAGES, element, difficulty, get_img, log_widget=None):
    """Handle entering a raid.
    """
    log_msg("Handling raid entry", log_widget)
    raid_image = get_img(f"raid_{element}_{difficulty}")

    if pyautogui.locateOnScreen(raid_image, confidence=0.95):
        if find_and_click(raid_image, log_widget=log_widget):
            
            if IMAGES.get("limit") and pyautogui.locateOnScreen(IMAGES["limit"], confidence=CONFIDENCE):
                log_msg("Entry blocked: limit reached", log_widget)
                find_and_click(IMAGES.get("ok"), log_widget=log_widget)
                state["completed_raids"][element][difficulty] += 1
                return False
                
            if IMAGES.get("condition") and pyautogui.locateOnScreen(IMAGES["condition"], confidence=CONFIDENCE):
                log_msg("Entry blocked: condition not met", log_widget)
                find_and_click(IMAGES.get("ok"), log_widget=log_widget)
                state["completed_raids"][element][difficulty] += 1
                return False
                
            if IMAGES.get("challenge") and pyautogui.locateOnScreen(IMAGES["challenge"], confidence=CONFIDENCE):
                log_msg("Entry is possible", log_widget)
                find_and_click(IMAGES.get("challenge"), log_widget=log_widget)
                return True
                    
            if IMAGES.get("ok") and pyautogui.locateOnScreen(IMAGES["ok"], confidence=CONFIDENCE):
                log_msg("Entry is possible", log_widget)
                find_and_click(IMAGES.get("ok"), log_widget=log_widget)
                return True

        log_msg("Raid could not enter", log_widget)
        return False
    log_msg("Raid not found on screen", log_widget)
    return False
import time
import pyautogui
from .core import state, log_msg, _inc_loop, find_and_click, post_battle, find_text, find_and_click_text
from config import SLEEP, CONFIDENCE

def combat_sequence(IMAGES, log_widget=None, host_raid=False):
    if find_and_click(IMAGES['support']):
        log_msg("Support found and clicked", log_widget)
        
        find_and_click(IMAGES['go_quest'])
        
        while state.get("running", False):
            if find_and_click(IMAGES['ok'], optional=True, log_widget=log_widget):
                log_msg("Raid already ended - OK button found", log_widget)
                break
            
            if find_and_click(IMAGES['support_req'], optional=True, log_widget=log_widget):
                log_msg("Support request found and clicked", log_widget)
            
            if find_and_click(IMAGES['attack'], log_widget=log_widget, optional=True):
                log_msg("Attack button found and clicked", log_widget)
                break
            
            time.sleep(SLEEP)
            
        user_allows_rescue = state.get("rescue", True)
        rescue_present = IMAGES.get("rescue") and pyautogui.locateOnScreen(IMAGES["rescue"], confidence=CONFIDENCE)
        rescue_active = bool(user_allows_rescue and rescue_present)

        if rescue_present:
            if user_allows_rescue:
                log_msg("Rescue available and enabled - clicking rescue", log_widget)
                time.sleep(SLEEP)
                find_and_click(IMAGES["rescue"], log_widget=log_widget)
            else:
                log_msg("Rescue available but user disabled rescue - not clicking", log_widget)

        wait_for_battle_end(IMAGES, log_widget, rescue_active=rescue_active, host_raid=host_raid)


def wait_for_battle_end(IMAGES, log_widget=None, rescue_active=False, host_raid=False):
    log_msg("Waiting for battle to end...", log_widget)
    
    if rescue_active:
        log_msg("Waiting for rescue active.", log_widget)
        while state.get("running", False):
            if IMAGES.get("rescue_prompt") and pyautogui.locateOnScreen(IMAGES['rescue_prompt'], confidence=CONFIDENCE):
                if find_and_click(IMAGES['ok'], optional=True):
                    break
            else:
                break

    while state.get("running", False):
        if IMAGES.get("defeat_elixir") and pyautogui.locateOnScreen(IMAGES["defeat_elixir"], confidence=CONFIDENCE):
            log_msg("Defeated detected cancelling the revive...", log_widget)
            # if find_and_click(IMAGES["cancel"], log_widget=log_widget):
            if find_and_click_text(['Cancel'], log_widget=log_widget):
                if rescue_active or host_raid:
                    log_msg("Rescue is exist and enabled or Hosting a raid - clicking cancel to wait for battle end", log_widget)
                    # find_and_click(IMAGES['cancel'], log_widget=log_widget)
                    find_and_click_text(['Cancel'], log_widget=log_widget)
                    break
                else:
                    log_msg("Rescue is disabled or doesn't exist - returning to quest list", log_widget)
                    find_and_click(IMAGES['quest_list'], log_widget=log_widget)
            break
        
        if IMAGES.get("return") and pyautogui.locateOnScreen(IMAGES["return"], confidence=CONFIDENCE):
            log_msg("Battle ended - Return button found", log_widget)
            break
        
        if IMAGES.get("retry") and pyautogui.locateOnScreen(IMAGES["retry"], confidence=CONFIDENCE):
            log_msg("Battle ended - Retry button found", log_widget)
            break
        
        if IMAGES.get("return_raid") and pyautogui.locateOnScreen(IMAGES["return_raid"], confidence=CONFIDENCE):
            log_msg("Battle ended - Return Raid button found", log_widget)
            break

        if IMAGES.get("ok") and pyautogui.locateOnScreen(IMAGES["ok"], confidence=CONFIDENCE) and not find_text(['left to requet', 'sec'], log_widget=log_widget):
            log_msg("Battle ended - OK button found", log_widget)
            break

        time.sleep(SLEEP)

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

        time.sleep(SLEEP)
        
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
            time.sleep(2.5)
            return True
                
        time.sleep(SLEEP)

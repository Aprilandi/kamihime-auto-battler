import time
import pyautogui
from .core import state, log_msg, _inc_loop, find_and_click, post_battle, find_text, find_and_click_text, wait
from config import SLEEP, CONFIDENCE

def combat_sequence(IMAGES, log_widget=None, host_raid=False, is_raid=False, is_support=True, isPostBattle = True):
    if host_raid is True:
        is_raid = True
    if find_and_click(IMAGES['support'], log_widget=log_widget, robust=False):
        log_msg("Support found and clicked", log_widget)
        
        find_and_click(IMAGES['go_quest'], log_widget=log_widget)
        
        # if there is failed raid it shows up after go quest
        if find_and_click(IMAGES['batch'], optional=True, log_widget=log_widget):
            find_and_click(IMAGES['support'], log_widget=log_widget)
            find_and_click(IMAGES['go_quest'], log_widget=log_widget)
        
        time.sleep(1.0)
        if pyautogui.locateOnScreen(IMAGES['ok'], confidence=CONFIDENCE):
            # incase of off element
            if find_text(['about', 'enemy', 'attribute', 'resistance'], log_widget=log_widget):
                find_and_click(IMAGES['ok'], log_widget=log_widget)
            
            if find_and_click(IMAGES['ok'], log_widget=log_widget): 
                log_msg("Raid already ended - OK button found.", log_widget=log_widget)
                return False

        while state.get("running", False):
            if find_and_click(IMAGES['ok'], optional=True, log_widget=log_widget):
                log_msg("Raid already ended - OK button found", log_widget)
                find_and_click(IMAGES['reload'], optional=True, log_widget=log_widget)
                break
            
            if pyautogui.locateOnScreen(IMAGES.get('support_req'), confidence=CONFIDENCE):
                if is_support:
                    find_and_click(IMAGES['support_req'], log_widget=log_widget, robust=False)
                else:
                    find_and_click(IMAGES['cancel'], log_widget=log_widget, robust=False)
                log_msg("Support request found and clicked or closed", log_widget)
            
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
                # time.sleep(SLEEP)
                find_and_click(IMAGES["rescue"], log_widget=log_widget, robust=False)
            else:
                log_msg("Rescue available but user disabled rescue - not clicking", log_widget)

        if wait_for_battle_end(IMAGES, log_widget, rescue_active=rescue_active, host_raid=host_raid, is_raid=is_raid, isPostBattle=isPostBattle) is False:
            return False
        else:
            return True


def wait_for_battle_end(IMAGES, log_widget=None, rescue_active=False, host_raid=False, is_raid=False, timeout=600, isPostBattle = True):
    log_msg("Waiting for battle to end...", log_widget)

    start_time = time.time()

    while state.get("running", False):
        if IMAGES.get("defeat_elixir") and pyautogui.locateOnScreen(IMAGES["defeat_elixir"], confidence=CONFIDENCE):
            log_msg("Defeated detected cancelling the revive...", log_widget)
            # if find_and_click(IMAGES["cancel"], log_widget=log_widget):
            if find_and_click(IMAGES['cancel'], log_widget=log_widget):
                if rescue_active or host_raid:
                    log_msg("Rescue is exist and enabled or Hosting a raid - clicking cancel to wait for battle end", log_widget)
                    # find_and_click(IMAGES['cancel'], log_widget=log_widget)
                    find_and_click(IMAGES['cancel'], log_widget=log_widget)
                    continue
                else:
                    log_msg("Rescue is disabled or doesn't exist - returning to quest list", log_widget)
                    # this is to make sure return to quest list is exist
                    # because there is a chance that the raid is ended just after player died
                    # so that it wont stuck looking for return to quest list button
                    wait(log_widget=log_widget)
                    if find_and_click(IMAGES['quest_list'], log_widget=log_widget, optional=True, robust=False):
                        return False
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
        
        if IMAGES.get("ok") and pyautogui.locateOnScreen(IMAGES["ok"], confidence=CONFIDENCE):
            if find_text(['subjugation?'], log_widget=log_widget):
                log_msg("Rescue available, completing...", log_widget)
                find_and_click(IMAGES['ok'], log_widget=log_widget, robust=False, optional=True)
            elif find_text(['sec left', 'sec', 'left', 'requet', 'request', 'continue'], log_widget=log_widget) is False:
                log_msg("Battle ended - Ok button found", log_widget)
                if is_raid is True:
                    find_and_click(IMAGES['ok'], log_widget=log_widget)
                break

        if (time.time() - start_time) >= timeout:
            log_msg("Probably connection lost, reloading...", log_widget)
            if find_and_click(IMAGES['reload'], log_widget=log_widget):
                time.sleep(5.0)

                if find_and_click(IMAGES['ok'], optional=True, timeout=3.0, log_widget=log_widget):
                    log_msg("Battle either ended or connection lost...", log_widget=log_widget)
                    while state.get("running", False):
                        find_and_click(IMAGES['ok'], log_widget=log_widget, optional=True) # If there are scoreboard
                        if find_and_click(IMAGES['return_raid_battle'], log_widget=log_widget, optional=True):
                            log_msg("Battle already ended, returning to raid quest list", log_widget=log_widget)
                            return False
                        if find_and_click(IMAGES['start_game'], log_widget=log_widget, optional=True):
                            log_msg("Connection lost, returning to main page going to raid quests", log_widget=log_widget)
                            if find_and_click(IMAGES['raid_quest_available'], log_widget=log_widget):
                                return False

                if find_and_click(IMAGES['attack'], optional=True, timeout=3.0, log_widget=log_widget):
                    log_msg("Battle is still on going, continuing...", log_widget=log_widget)

                if find_and_click(IMAGES['support_btn'], confidence=0.95, optional=True, robust=False, log_widget=log_widget):
                    find_and_click(IMAGES['support_req'], optional=True, log_widget=log_widget)

                start_time = time.time()
                    
        time.sleep(SLEEP)

    if isPostBattle:
        post_battle(IMAGES, log_widget=log_widget, confidence=0.85)

    return True

        
def ongoing_battle(IMAGES, log_widget=None, timeout=1.5):
    start_time = time.time()
    
    while state.get("running", False):
        elapsed = time.time() - start_time 
        if elapsed >= timeout:
            log_msg("No ongoing battle detected", log_widget)
            return False

        if IMAGES.get("ongoing") and pyautogui.locateOnScreen(IMAGES["ongoing"], confidence=0.99):
            log_msg("Ongoing battle detected", log_widget)
            find_and_click(IMAGES['cancel'], log_widget=log_widget)
            return True
        
        if IMAGES.get("batch") and pyautogui.locateOnScreen(IMAGES["batch"], confidence=CONFIDENCE):
            log_msg("Completed battle detected, completing via batch...", log_widget)
            find_and_click(IMAGES['batch'], log_widget=log_widget)
            # time.sleep(2.5)
            return True
                
        time.sleep(SLEEP)

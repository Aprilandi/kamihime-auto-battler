import time
import pyautogui
from .core import state, _inc_loop, log_msg, find_and_click, next_page, find_text, find_and_click_text
from .battle import check_stamina, combat_sequence, ongoing_battle
from config import SLEEP, CONFIDENCE

def farm_loop(IMAGES, log_widget=None):
    """Main farming loop to run battles continuously.
    """
    loop_count = 0
    log_msg("Starting farming loop", log_widget)
    while state.get("running", False):
        if find_and_click(IMAGES.get('retry'), log_widget=log_widget):
            loop_count = _inc_loop("farm_loop", log_widget)

            time.sleep(SLEEP)
            check_stamina(IMAGES, log_widget=log_widget)

            combat_sequence(IMAGES, log_widget)
        
        time.sleep(SLEEP)


def quest_rush(IMAGES, log_widget=None):
    """Epic Quest Rush mode farming loop.
    """
    log_msg("Starting Epic Quest Rush mode", log_widget)
    while state.get("running", False):
        if find_and_click(IMAGES.get('story_start'), log_widget=log_widget, timeout=5.0, optional=True):
            loop_count = _inc_loop("epic_quest_rush", log_widget)
            
            time.sleep(SLEEP)
            check_stamina(IMAGES, log_widget=log_widget)

            while state.get("running", False):
                if IMAGES.get('skip') and pyautogui.locateOnScreen(IMAGES['skip'], confidence=CONFIDENCE):
                    log_msg("Branch: Story, skipping...", log_widget)
                    find_and_click(IMAGES['skip'], log_widget=log_widget)
                    find_and_click(IMAGES['skip_confirm'], log_widget=log_widget)
                    break
                if IMAGES.get('support') and pyautogui.locateOnScreen(IMAGES['support'], confidence=CONFIDENCE):
                    log_msg("Branch: Battle, starting combat sequence...", log_widget)
                    combat_sequence(IMAGES, log_widget)
                    break
                time.sleep(SLEEP)
            
            find_and_click(IMAGES.get('return'), log_widget=log_widget)
            find_and_click(IMAGES.get('ok'), log_widget=log_widget)

        else:
            log_msg("No more new Quests, stopping bot...", log_widget)
            break


def raid_host(IMAGES, ELEMENTS, get_img, log_widget=None):
    """Raid hosting loop.
    """
    log_msg("Starting Raid Host mode", log_widget)
    pyautogui.screenshot("test.png")
    for index, element in enumerate(ELEMENTS):
        if not state.get("running", False):
            return
        
        element_cfg = state["raid_settings"].get(element, {})
        # skip whole element if disabled
        if not element_cfg.get("enable", True):
            log_msg(f"Element {element_cfg} is not enabled. Skipping")
            continue

        log_msg(f"Selecting element: {element}", log_widget)

        if index > 0:
            find_and_click(get_img(f"KHR_raid_{element}"), log_widget=log_widget, confidence=0.98)

        for difficulty, enabled in element_cfg.get("difficulty", {}).items():
            if not enabled:
                log_msg(f"Element {element_cfg} Difficulty {difficulty} is not enabled. Skipping")
                continue
            
            completed_raid = state['completed_raids'].get(element, {}).get(difficulty, 0)

            if completed_raid > 0 and completed_raid == state['max_runs'].get(element, 1):
                log_msg(f"Skipping already completed raid: {element} - {difficulty}", log_widget)
                continue

            while state.get("running", False):
                
                log_msg("Handling raid entry", log_widget)
                raid_image = get_img(f"KHR_{element}_{difficulty}")

                if find_and_click(raid_image, confidence=0.85, log_widget=log_widget, optional=True):
                    if ongoing_battle(IMAGES, log_widget=log_widget):
                        continue
                    
                    blocked = False

                    log_msg("Checking for entry block...", log_widget=log_widget)
                    
                    time.sleep(1.0)
                    if find_text(['[Condition]', 'Challenge limit']):
                        blocked = True

                    if blocked:
                        log_msg("Entry blocked", log_widget)
                        find_and_click(IMAGES.get("ok"), log_widget=log_widget)
                        # Wait until the OK button disappears before continuing
                        while pyautogui.locateOnScreen(IMAGES["ok"], confidence=CONFIDENCE):
                            time.sleep(0.2)
                        state["completed_raids"][element][difficulty] += 1
                        break

                    # Only check for challenge/ok if not blocked
                    if IMAGES.get("challenge") and pyautogui.locateOnScreen(IMAGES["challenge"], confidence=CONFIDENCE):
                        log_msg("Entry is possible (challenge)", log_widget)
                        find_and_click(IMAGES["challenge"], log_widget=log_widget)
                        
                        time.sleep(SLEEP)
                        check_stamina(IMAGES, log_widget)
                        
                        combat_sequence(IMAGES, log_widget=log_widget, host_raid=True)
                        
                        # find_and_click_text(['Return'], log_widget=log_widget)
                        find_and_click(IMAGES['return_raid'])
                        state["completed_raids"][element][difficulty] += 1
                        continue

                    elif IMAGES.get("ok") and pyautogui.locateOnScreen(IMAGES["ok"], confidence=CONFIDENCE):
                        log_msg("Entry is possible (ok)", log_widget)
                        find_and_click(IMAGES["ok"], log_widget=log_widget)
                        
                        time.sleep(SLEEP)
                        check_stamina(IMAGES, log_widget)
                        
                        combat_sequence(IMAGES, log_widget=log_widget, host_raid=True)
                        
                        # find_and_click_text(['Return'], log_widget=log_widget)
                        find_and_click(IMAGES['return_raid'])
                        state["completed_raids"][element][difficulty] += 1
                        continue

                else:
                    if next_page(IMAGES, log_widget=log_widget):
                        log_msg("Navigated to next page of raids", log_widget)
                    else:
                        log_msg("Going to next element", log_widget)
                        break
            
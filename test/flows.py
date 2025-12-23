import time
import pyautogui
from .core import _inc_loop, state, log_msg, SLEEP, find_and_click, CONFIDENCE, next_page
from .battle import check_stamina, combat_sequence, ongoing_battle, handle_raid_entry

def farm_loop(IMAGES, log_widget=None):
    """Main farming loop to run battles continuously.
    """
    loop_count = 0
    log_msg("Starting farming loop", log_widget)
    while state.get("running", False):
        if find_and_click(IMAGES.get('retry'), log_widget=log_widget):
            loop_count = _inc_loop("farm_loop", log_widget)

            check_stamina(IMAGES, log_widget=log_widget)

            combat_sequence(IMAGES, log_widget)

        time.sleep(SLEEP)


def quest_rush(IMAGES, log_widget=None):
    """Epic Quest Rush mode farming loop.
    """
    log_msg("Starting Epic Quest Rush mode", log_widget)
    while state.get("running", False):
        if find_and_click(IMAGES.get('story_start'), log_widget=log_widget):
            loop_count = _inc_loop("epic_quest_rush", log_widget)
            
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

        time.sleep(SLEEP)


def raid_host(IMAGES, ELEMENTS, get_img, log_widget=None):
    """Raid hosting loop.
    """
    log_msg("Starting Raid Host mode", log_widget)
    
    for index, element in enumerate(ELEMENTS):
        if not state.get("running", False):
            return
        
        find_and_click(get_img(f"KHR_raid_{element}"), log_widget=log_widget)
        
        while state.get("running", False):
            for difficulty, enabled in state["raid_settings"].get(element, {}).items():
                if not enabled:
                    continue
                
                if state['completed_raids'].get(element, {}).get(difficulty, 0) > 0:
                    log_msg(f"Skipping already completed raid: {element} - {difficulty}", log_widget)
                    continue
                
                if handle_raid_entry(IMAGES, element=element, difficulty=difficulty, get_img=get_img, log_widget=log_widget):
                    check_stamina(IMAGES, log_widget=log_widget)
                    combat_sequence(IMAGES, log_widget=log_widget)
                    state["completed_raids"][element][difficulty] += 1
                    log_msg(f"Completed raid: {element} - {difficulty}", log_widget)
                    continue

            if next_page(IMAGES, log_widget=log_widget):
                log_msg("Navigated to next page of raids", log_widget)
            else:
                log_msg("Going to next element", log_widget)
                break
            
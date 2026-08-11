import time
import pyautogui
from .core import state, _inc_loop, log_msg, find_and_click, next_page, find_text, find_and_click_all, wait, check_stamina, post_battle, scroll_down, find_and_click_text, click_union_stage_slot
from .battle import combat_sequence, ongoing_battle
from config import SLEEP, CONFIDENCE, CONNECTING, DIFFICULTIES, ALL_POSSIBLE_DIFFS

def farm_loop(IMAGES, log_widget=None):
    """Main farming loop to run battles continuously.
    """
    loop_count = 0
    log_msg("Starting farming loop", log_widget)
    while state.get("running", False):
        if find_and_click(IMAGES.get('retry'), log_widget=log_widget, robust=False):

            check_stamina(IMAGES, log_widget=log_widget)
            find_and_click(IMAGES['ok'], log_widget=log_widget, optional=True)
            find_and_click(IMAGES['challenge'], log_widget=log_widget, timeout=0.5, optional=True)

            combat_sequence(IMAGES, log_widget, is_raid=True)
            
        
        time.sleep(SLEEP)

def quest_rush(IMAGES, log_widget=None):
    """Quest Rush mode farming loop.
    """
    log_msg("Starting Quest Rush mode", log_widget)
    while state.get("running",  False):
        if find_and_click(IMAGES['story_start'], log_widget=log_widget, timeout=5.0, optional=True, robust=False):
            new_chapter = False
            find_and_click(IMAGES['ok'], optional=True, log_widget=log_widget)
            check_stamina(IMAGES, log_widget=log_widget)
            while state.get("running", False):
                # main loop inside the episode
                if find_and_click(IMAGES['support'], log_widget=log_widget, optional=True, robust=False):
                    find_and_click(IMAGES['go_quest'], log_widget=log_widget)
                if find_and_click(IMAGES['skip'], log_widget=log_widget, robust=False, optional=True):
                    find_and_click(IMAGES['skip_confirm'], log_widget=log_widget)
                if find_and_click(IMAGES['ep_skip'], log_widget=log_widget, optional=True, robust=False):
                    find_and_click(IMAGES['ok'], log_widget=log_widget)

                find_and_click(IMAGES['attack'], log_widget=log_widget, optional=True)
                
                # indicator when that episode is finished
                if find_and_click(IMAGES['next_episode'], log_widget=log_widget, optional=True, robust=False):
                    # find_and_click(IMAGES['ok'], optional=True, log_widget=log_widget)
                    check_stamina(IMAGES, log_widget=log_widget)
                    
                    # check if the chapter is finised
                    if find_and_click(IMAGES['ok'], optional=True, log_widget=log_widget):
                        find_and_click(IMAGES['ok'], log_widget=log_widget)
                        new_chapter = True
                        
                        # check if the world is finished
                        if pyautogui.locateOnScreen(IMAGES['next_page'], confidence=CONFIDENCE):
                            OFFSET = -120 # for 1920x1080 resolution currently (negative = above ; positive = below)
                            find_and_click(IMAGES['new_world'], log_widget=log_widget, offset=OFFSET, robust=False)
                            find_and_click(IMAGES['go'], log_widget=log_widget)
                            find_and_click(IMAGES['ok'], log_widget=log_widget)

                        break
                    continue

            if new_chapter:
                continue



def epic_quest_rush(IMAGES, log_widget=None):
    """Epic Quest Rush mode farming loop.
    """
    log_msg("Starting Epic Quest Rush mode", log_widget)
    while state.get("running", False):
        if find_and_click(IMAGES.get('story_start'), log_widget=log_widget, timeout=5.0, optional=True):
            loop_count = _inc_loop("epic_quest_rush", log_widget)
            
            # time.sleep(SLEEP)
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
        
        
def episode_rush(IMAGES, log_widget=None):
    log_msg("Starting episode rush", log_widget)
    
    while state.get("running", False):
        if find_and_click(IMAGES['ep_start'], log_widget=log_widget, optional=True, timeout=4.0):
        
            log_msg("Finding the option", log_widget)
            branch = False
            encounter = True
            episode1 = True
            episode2 = True

            while state.get("running", False) and (encounter or episode1 or episode2):
                while state.get("running", False):
                    if find_and_click(IMAGES['cancel'], optional=True):
                        log_msg("Countermeasure loading too long already completed episode")
                    
                    if pyautogui.locateOnScreen(IMAGES['ep_encounter'], confidence=0.99) and encounter:
                        find_and_click(IMAGES['ep_encounter'], log_widget=log_widget, confidence=0.99)
                        encounter = False
                        if find_and_click(IMAGES['cancel'], optional=True, log_widget=log_widget, timeout=3.0):
                            log_msg("Encounter already completed. Skipping...", log_widget=log_widget)
                        else:
                            log_msg("Found the encounter episode", log_widget)
                            break
                            

                    if find_and_click(IMAGES['ep_1'], log_widget=log_widget, optional=True, confidence=0.99) and episode1:
                        episode1 = False
                        if find_and_click(IMAGES['ok'], optional=True, timeout=3.0):
                            log_msg("Episode 1 requirements unmet. Skipping...", log_widget)
                        elif find_and_click(IMAGES['cancel'], optional=True, log_widget=log_widget, timeout=3.0):
                            log_msg("Episode 1 already completed. Skipping...", log_widget=log_widget)
                        else:
                            log_msg("Found the first episode (Ability unlocked)", log_widget)
                            branch = True
                            break
                        

                    if find_and_click(IMAGES['ep_2'], log_widget=log_widget, optional=True, confidence=0.99) and episode2:
                        episode2 = False
                        if find_and_click(IMAGES['ok'], optional=True, timeout=3.0):
                            log_msg("Episode 2 requirements unmet. Skipping...", log_widget)
                        elif find_and_click(IMAGES['cancel'], optional=True, log_widget=log_widget, timeout=3.0):
                            log_msg("Episode 2 already completed. Skipping...", log_widget=log_widget)
                        else:
                            log_msg("Found the second episode (Magic Jewel)", log_widget)
                            branch = True
                            break
                    
                    time.sleep(SLEEP)
                
                find_and_click(IMAGES['skip'], log_widget=log_widget)
                
                find_and_click(IMAGES['skip_confirm'], log_widget=log_widget)
                
                if branch:
                    find_and_click(IMAGES['ep_skip'], log_widget=log_widget, robust=False)
                    
                    find_and_click(IMAGES['ok'], log_widget=log_widget)
                
                find_and_click(IMAGES['ok'], log_widget=log_widget)
                
                time.sleep(SLEEP)
            
            time.sleep(SLEEP)
            
            find_and_click(IMAGES['back'], log_widget=log_widget)
        else:
            log_msg("All episode has been completed.", log_widget)
            break


def raid_host(IMAGES, ELEMENTS, get_img, log_widget=None):
    """Raid hosting loop.
    """
    log_msg("Starting Raid Host mode", log_widget)
    
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
            find_and_click(get_img(f"KHR_raid_{element}"), log_widget=log_widget, confidence=0.98, robust=False)

        for difficulty, enabled in element_cfg.get("difficulty", {}).items():
            if not enabled:
                log_msg(f"Element {element_cfg} Difficulty {difficulty} is not enabled. Skipping")
                continue
            
            # completed_raid = state['completed_raids'].get(element, {}).get(difficulty, 0)

            # if completed_raid > 0 and completed_raid == state['max_runs'].get(element, 1):
            #     log_msg(f"Skipping already completed raid: {element} - {difficulty}", log_widget)
            #     continue

            while state.get("running", False):
                
                log_msg("Handling raid entry", log_widget)
                raid_image = get_img(f"KHR_{element}_{difficulty}")
                
                if find_and_click(raid_image, confidence=0.95, log_widget=log_widget, optional=True, robust=False):
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
                        state["completed_raids"][element][difficulty] += 1
                        log_msg("Entry is possible (challenge)", log_widget)
                        find_and_click(IMAGES["challenge"], log_widget=log_widget)
                        
                        # time.sleep(SLEEP)
                        check_stamina(IMAGES, log_widget)
                        
                        combat_sequence(IMAGES, log_widget=log_widget, host_raid=True)
                        
                        # find_and_click_text(['Return'], log_widget=log_widget)
                        find_and_click(IMAGES['return_raid'], optional=True, log_widget=log_widget) #making this optional because the post battle sometimes false positive the return button as ok button
                        continue

                    elif IMAGES.get("ok") and pyautogui.locateOnScreen(IMAGES["ok"], confidence=CONFIDENCE):
                        state["completed_raids"][element][difficulty] += 1
                        log_msg("Entry is possible (ok)", log_widget)
                        find_and_click(IMAGES["ok"], log_widget=log_widget)
                        
                        # time.sleep(SLEEP)
                        check_stamina(IMAGES, log_widget)
                        
                        combat_sequence(IMAGES, log_widget=log_widget, host_raid=True)
                        
                        # find_and_click_text(['Return'], log_widget=log_widget)
                        find_and_click(IMAGES['return_raid'], optional=True, log_widget=log_widget) #making this optional because the post battle sometimes false positive the return button as ok button
                        continue

                else:
                    if next_page(IMAGES, log_widget=log_widget):
                        log_msg("Navigated to next page of raids", log_widget)
                    else:
                        log_msg("Going to next element", log_widget)
                        break

        
def farm_raid(IMAGES, ELEMENTS, get_img, log_widget=None):
    log_msg("Starting Raid Farm", log_widget)

    while state.get("running", False):
        # New scanning order for farm raid: iterate difficulties first, then elements.
        # This scans all elements for a given difficulty before moving to the next
        # difficulty which can be useful when farming a specific difficulty across
        # elements.
        for difficulty in ALL_POSSIBLE_DIFFS:
            for index, element in enumerate(ELEMENTS):
                defeat = False
                if not state.get("running", False):
                    return

                element_cfg = state["raid_settings"].get(element, {})
                # skip whole element if disabled
                if not element_cfg.get("enable", True):
                    continue

                # skip this difficulty for this element if disabled
                if not element_cfg.get("difficulty", {}).get(difficulty, False):
                    continue

                raid_image = get_img(f"KHR_{element}_{difficulty}")
                
                if find_and_click_all(raid_image, confidence=0.95, log_widget=log_widget) is True:
                    if combat_sequence(IMAGES, log_widget=log_widget, is_raid=True) is not False:
                        find_and_click(IMAGES['return_raid_battle'], log_widget=log_widget, optional=True, timeout=2.0)
                        while pyautogui.locateOnScreen(IMAGES['raid_event']) is False and state.get("running", False):
                            post_battle(IMAGES, log_widget=log_widget, confidence=0.85)
                            find_and_click(IMAGES['return_raid_battle'], log_widget=log_widget, optional=True)
                            time.sleep(SLEEP)
                    else:
                        defeat = True
                        break

            if defeat:
                break

        # if next_page(IMAGES, log_widget=log_widget):
        if scroll_down(
                scroll_x=680,
                scroll_y=420,
                list_region=(493, 270, 375, 300)  # x, y, w, h of just the game list area
            ):
            log_msg("Navigated to next page of raids", log_widget)
        else:
            log_msg("No selected raid found. Refreshing...", log_widget)
            find_and_click(IMAGES['raid_event'], log_widget=log_widget)
            find_and_click(IMAGES['raid_regular'], log_widget=log_widget)
            if find_and_click(IMAGES['unconfirmed_battles'], log_widget=log_widget, optional=True):
                if find_and_click(IMAGES['batch'], log_widget=log_widget):
                    wait(log_widget=log_widget)
                    # for in case of rank up
                    find_and_click(IMAGES['ok'], optional=True, timeout=3.0, log_widget=log_widget)


def union_event(IMAGES, log_widget=None, index=0):
    """Union Event mode - runs union event battles.
    
    Args:
        IMAGES: Dictionary of image paths
        log_widget: Optional log widget for displaying messages
    """
    # array start from 0 and the frontend index start from 1
    index_arr = index - 1
    
    # if user choose index 4-6 that means next page
    if index > 3:
        index_arr = index_arr - 3    

    while state.get("running", False):
        log_msg(f"Starting Union Event mode {index}", log_widget)
        if index > 3:
            next_page(IMAGES, log_widget=log_widget)
            time.sleep(SLEEP)
        if click_union_stage_slot(index_arr, log_widget=log_widget) is True:
            check_stamina(IMAGES, log_widget=log_widget)
            if combat_sequence(IMAGES, log_widget=log_widget, is_raid=True) is True:
                find_and_click(IMAGES['return_union_event'], log_widget=log_widget, optional=True, timeout=2.0)
        time.sleep(SLEEP)

    return True
    # Fallback: keep the OCR path in place for future correctness.
    return find_and_click_text(
        ['seraph', 'temperance'],
        index=index,
        log_widget=log_widget,
        phrase=True,
        optional=True,
        timeout=3.0
    )
    
    # Backend implementation to be added by user
    pass

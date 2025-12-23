import time
from .core import _inc_loop, state, log_msg, SLEEP
from .vision import find_and_click, wait_for_image
from .battle import check_stamina, combat_sequence


def farm_loop(log_widget, IMAGES):
    log_msg("STARTING FARM LOOP", log_widget)
    while state.get("running", False):
        # increment farm loop counter
        _inc_loop("farm", log_widget)

        # Retry if retry button present
        if IMAGES.get("retry") and wait_for_image(IMAGES["retry"]):
            log_msg("Retry button detected, clicking retry", log_widget)
            find_and_click(IMAGES["retry"], timeout=0.9, max_attempts=3, log_widget=log_widget)
            time.sleep(0.35)
            # handle stamina check that can appear after retry
            time.sleep(3)
            check_stamina(IMAGES, log_widget)

            time.sleep(0.35)
            combat_sequence(log_widget, IMAGES)


def epic_quest_rush(log_widget, IMAGES):
    log_msg("STARTING EPIC RUSH", log_widget)
    while state.get("running", False):
        # increment epic loop counter (each iteration corresponds to one story/combat attempt)
        _inc_loop("epic", log_widget)
        # Start story if available
        if IMAGES.get("story_start") and find_and_click(IMAGES["story_start"], timeout=4.0, max_attempts=2, log_widget=log_widget):
            log_msg("starting story...", log_widget)

            # stamina check after starting a story/quest
            time.sleep(2.0)
            check_stamina(IMAGES, log_widget)

            # Story skip flow
            time.sleep(2)
            while state.get("running", False):
                if IMAGES.get("skip") and find_and_click(IMAGES["skip"], timeout=0.5, max_attempts=2, log_widget=log_widget):
                    log_msg("Branch story...", log_widget)
                    time.sleep(0.5)
                    find_and_click(IMAGES["skip_confirm"], timeout=0.5, max_attempts=2, log_widget=log_widget)
                    break
                    
                elif IMAGES.get("support") and find_and_click(IMAGES["support"], timeout=0.5, max_attempts=2, log_widget=log_widget):
                    # Normal combat branch
                    log_msg("Branch combat...", log_widget)
                    combat_sequence(log_widget, IMAGES)
                    break

                time.sleep(2.0)

            time.sleep(SLEEP)
            find_and_click(IMAGES["return"], timeout=2.0, max_attempts=3, log_widget=log_widget)
            time.sleep(SLEEP)
            find_and_click(IMAGES["ok"], max_attempts=2, log_widget=log_widget)

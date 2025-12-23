import time
import pyautogui
from .core import state, CONFIDENCE, SLEEP, log_msg, _inc_loop
from .vision import find_and_click, wait_for_image, _clear_ok_multiple, ongoing_raids


def check_stamina(IMAGES, log_widget=None):
    """If a stamina check appears, use stamina (if button present) and return True.

    Returns True when a stamina dialog was handled (or not present).
    """
    if IMAGES.get("stamina_check") and pyautogui.locateOnScreen(IMAGES["stamina_check"], confidence=CONFIDENCE):
        log_msg("Stamina check detected, using stamina...", log_widget)
        if IMAGES.get("stamina_use"):
            if find_and_click(IMAGES["stamina_use"], timeout=0.8, confidence=CONFIDENCE, max_attempts=3, log_widget=log_widget):
                time.sleep(SLEEP)
                find_and_click(IMAGES["ok"], timeout=0.6, max_attempts=2, log_widget=log_widget)
        time.sleep(0.6)
        return True
    return False


def wait_for_battle_end(IMAGES, log_widget=None):
    """Wait for the battle result dialogs and click OK(s). Handles defeat/rescue flow lightly.

    This function is intentionally defensive: it tries several known dialogs then clicks OK up to 6 times.
    """
    end_time = time.time() + 60
    while time.time() < end_time and state.get("running", False):
        if IMAGES.get("return") and pyautogui.locateOnScreen(IMAGES["return"], confidence=CONFIDENCE):
            log_msg("Return button detected - finishing battle end handling", log_widget)
            break

        if IMAGES.get("retry") and pyautogui.locateOnScreen(IMAGES["retry"], confidence=CONFIDENCE):
            log_msg("Retry detected - finishing battle end handling", log_widget)
            break

        if IMAGES.get("ok") and pyautogui.locateOnScreen(IMAGES["ok"], confidence=9.5):
            log_msg("OK detected - clearing OK dialogs...", log_widget)
            _clear_ok_multiple(IMAGES, log_widget=log_widget, max_clicks=8)
            time.sleep(0.4)
            continue

        if IMAGES.get("defeat_elixir") and pyautogui.locateOnScreen(IMAGES["defeat_elixir"], confidence=CONFIDENCE):
            log_msg("Defeat - revive (elixir) prompt detected during battle end", log_widget)
            if IMAGES.get("cancel"):
                find_and_click(IMAGES["cancel"], timeout=0.6, max_attempts=3, log_widget=log_widget)
            time.sleep(0.4)
            if IMAGES.get("defeat") and pyautogui.locateOnScreen(IMAGES["defeat"], confidence=CONFIDENCE):
                log_msg("Defeat screen present after revive cancel", log_widget)
                rescue_active = state.get("rescue_active_for_current_battle", False)
                if not rescue_active:
                    log_msg("Rescue not active for this battle - pressing quest_list", log_widget)
                    if IMAGES.get("quest_list"):
                        find_and_click(IMAGES["quest_list"], timeout=0.6, max_attempts=3, log_widget=log_widget)
                    return
                if IMAGES.get("cancel"):
                    find_and_click(IMAGES["cancel"], timeout=0.6, max_attempts=3, log_widget=log_widget)
                time.sleep(0.6)
            continue

        if IMAGES.get("defeat") and pyautogui.locateOnScreen(IMAGES["defeat"], confidence=CONFIDENCE):
            log_msg("Defeat screen detected during battle end", log_widget)
            rescue_active = state.get("rescue_active_for_current_battle", False)
            if not rescue_active:
                log_msg("Rescue not active for this battle - pressing quest_list", log_widget)
                if IMAGES.get("quest_list"):
                    find_and_click(IMAGES["quest_list"], timeout=0.6, max_attempts=3, log_widget=log_widget)
                return
            if IMAGES.get("cancel"):
                find_and_click(IMAGES["cancel"], timeout=0.6, max_attempts=3, log_widget=log_widget)
            time.sleep(0.6)

        time.sleep(0.3)


def combat_sequence(log_widget, IMAGES, get_img=None, RESCUE=True):
    """Perform the combat flow:
    - select support
    - go to quest
    - handle support request prompt
    - if rescue exists, click it and wait for OK active or handle according to RESCUE
    - click attack and wait for battle end
    """
    log_msg("Starting combat sequence", log_widget)

    # Choose support (if available)
    if IMAGES.get("support") and wait_for_image(IMAGES["support"]):
        log_msg("Selecting support...", log_widget)
        time.sleep(SLEEP)
        find_and_click(IMAGES["support"], timeout=0.5, max_attempts=2, log_widget=log_widget)

        # Go to quest (some flows click a GO_QUEST button)
        if IMAGES.get("go_quest"):
            log_msg("Going to quest...", log_widget)
            time.sleep(SLEEP)
            find_and_click(IMAGES["go_quest"], timeout=0.6, max_attempts=2, log_widget=log_widget)
            attack_clicked = False
            while state.get("running", False):
                if IMAGES.get("support_req") and pyautogui.locateOnScreen(IMAGES["support_req"], confidence=CONFIDENCE):
                    log_msg("Support request detected, sending...", log_widget)
                    time.sleep(SLEEP)
                    find_and_click(IMAGES["support_req"], timeout=0.5, max_attempts=3, log_widget=log_widget)
                    time.sleep(0.35)
                    continue

                if IMAGES.get("attack") and pyautogui.locateOnScreen(IMAGES["attack"], confidence=CONFIDENCE):
                    log_msg("Attack button detected, performing attack...", log_widget)
                    if find_and_click(IMAGES["attack"], timeout=0.5, max_attempts=4, log_widget=log_widget):
                        attack_clicked = True
                    time.sleep(0.4)
                    break

                time.sleep(0.25)

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

    wait_for_battle_end(IMAGES, log_widget)


def run_combat(el, diff, IMAGES, log_widget, host=True):
    log_msg("In Battle...", log_widget)

    while state.get("running"):
        combat_sequence(log_widget, IMAGES)

        if IMAGES.get("return_raid") and pyautogui.locateOnScreen(IMAGES["return_raid"], confidence=0.8):
            find_and_click(IMAGES["return_raid"], max_attempts=3, log_widget=log_widget)
            if host:
                state["completed_raids"][el][diff] += 1
            _inc_loop("raid", log_widget)
            return

        time.sleep(1.5)

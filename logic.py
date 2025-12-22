import pyautogui
import time
import os

# Shared state
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


def find_and_click(image, timeout=SLEEP, confidence=CONFIDENCE, max_attempts=1, log_widget=None):
    """Try locateOnScreen and click the center. Returns True if clicked.

    Will attempt up to max_attempts times (useful for transient UIs). Sleeps `timeout` after click.
    """
    if not image:
        return False

    # friendly name for logs
    try:
        name = os.path.basename(image)
    except Exception:
        name = str(image)

    log_msg(f"Searching for {name}", log_widget)

    attempts = 0
    while attempts < max_attempts and state.get("running", False):
        try:
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
            time.sleep(timeout)
        except Exception as e:
            log_msg(f"Error locating {name}: {e}", log_widget)
        attempts += 1
        time.sleep(0.12)
    log_msg(f"Did not find {name} after {attempts} attempts", log_widget)
    return False


def _clear_ok_multiple(IMAGES, log_widget=None, max_clicks=6):
    """Click OK repeatedly (up to max_clicks) while it appears on screen.

    Returns the number of OK clicks performed.
    """
    clicks = 0
    while clicks < max_clicks and state.get("running", False):
        ok = IMAGES.get("ok")
        if ok and pyautogui.locateOnScreen(ok, confidence=CONFIDENCE):
            find_and_click(ok, timeout=0.3, confidence=CONFIDENCE, max_attempts=3, log_widget=log_widget)
            clicks += 1
            time.sleep(0.3)
            continue
        break
    return clicks

def ongoing_raids(IMAGES, log_widget=None, timeout=1.0, attempts=1):
    """Check for ongoing raids dialog and click resume if found.

    Returns True if an ongoing raid was detected and resumed.
    """
    log_msg("Checking for ongoing or completed raids...", log_widget)
    tried = 0
    while tried < attempts and state.get("running", False):
        start_time = time.time()
        while time.time() - start_time < timeout and state.get("running", False):
            if IMAGES.get("ongoing") and pyautogui.locateOnScreen(IMAGES["ongoing"], confidence=CONFIDENCE):
                log_msg("Ongoing raid detected, cancelling", log_widget)
                find_and_click(IMAGES["cancel"], timeout=0.5, max_attempts=3, log_widget=log_widget)
                time.sleep(SLEEP)
                return False
            elif IMAGES.get("batch") and pyautogui.locateOnScreen(IMAGES["batch"], confidence=CONFIDENCE):
                log_msg("Batch raid detected, completing", log_widget)
                find_and_click(IMAGES["batch"], timeout=0.5, max_attempts=3, log_widget=log_widget)
                time.sleep(SLEEP)
                return True
            time.sleep(0.3)
        tried += 1
    return False



def wait_for_image(image, confidence=CONFIDENCE, timeout=10):
    """Wait until an image appears on screen or timeout expires."""
    start = time.time()
    while time.time() - start < timeout and state.get("running", False):
        if pyautogui.locateOnScreen(image, confidence=confidence):
            return True
        time.sleep(0.25)  # avoid busy loop
    return False


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
    # Click OK multiple times to clear rewards/scoreboard/first-time dialogs.
    # The function now also handles defeat/rescue flow centrally (if a defeat
    # dialog appears during the waiting period).
    end_time = time.time() + 60
    while time.time() < end_time and state.get("running", False):
        # If return is present, battle finished and we can break
        if IMAGES.get("return") and pyautogui.locateOnScreen(IMAGES["return"], confidence=CONFIDENCE):
            log_msg("Return button detected - finishing battle end handling", log_widget)
            break

        # If retry appears (some flows show retry instead of return), treat as finished
        if IMAGES.get("retry") and pyautogui.locateOnScreen(IMAGES["retry"], confidence=CONFIDENCE):
            log_msg("Retry detected - finishing battle end handling", log_widget)
            break

        # If OK appears, clear OK repeatedly (rewards / multiple dialogs)
        if IMAGES.get("ok") and pyautogui.locateOnScreen(IMAGES["ok"], confidence=CONFIDENCE):
            log_msg("OK detected - clearing OK dialogs...", log_widget)
            _clear_ok_multiple(IMAGES, log_widget=log_widget, max_clicks=8)
            # after clearing OKs, continue to re-evaluate other end conditions
            time.sleep(0.4)
            continue

        # If defeat/dialogs appear, handle rescue/defeat here (centralized)
        # NOTE: the combat_sequence should set state['rescue_active_for_current_battle'] before calling this
        if IMAGES.get("defeat_elixir") and pyautogui.locateOnScreen(IMAGES["defeat_elixir"], confidence=CONFIDENCE):
            log_msg("Defeat - revive (elixir) prompt detected during battle end", log_widget)
            if IMAGES.get("cancel"):
                find_and_click(IMAGES["cancel"], timeout=0.6, max_attempts=3, log_widget=log_widget)
            time.sleep(0.4)
            # check for defeat screen next
            if IMAGES.get("defeat") and pyautogui.locateOnScreen(IMAGES["defeat"], confidence=CONFIDENCE):
                log_msg("Defeat screen present after revive cancel", log_widget)
                # If rescue was not active for this battle, press quest_list and stop
                rescue_active = state.get("rescue_active_for_current_battle", False)
                if not rescue_active:
                    log_msg("Rescue not active for this battle - pressing quest_list", log_widget)
                    if IMAGES.get("quest_list"):
                        find_and_click(IMAGES["quest_list"], timeout=0.6, max_attempts=3, log_widget=log_widget)
                    return
                # otherwise, cancel defeat screen and continue waiting for rescue flow
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
        find_and_click(IMAGES["support"], timeout=0.5, max_attempts=2, log_widget=log_widget)

        # Go to quest (some flows click a GO_QUEST button)
        if IMAGES.get("go_quest"):
            log_msg("Going to quest...", log_widget)
            time.sleep(SLEEP)
            find_and_click(IMAGES["go_quest"], timeout=0.6, max_attempts=2, log_widget=log_widget)
            # After going to quest, wait until either support_request or attack appears.
            # This loop will keep checking until one of them is visible (or the bot is stopped).
            attack_clicked = False
            while state.get("running", False):
                # If support request shows up, accept it and continue waiting for attack
                if IMAGES.get("support_req") and pyautogui.locateOnScreen(IMAGES["support_req"], confidence=CONFIDENCE):
                    log_msg("Support request detected, accepting...", log_widget)
                    time.sleep(SLEEP)
                    find_and_click(IMAGES["support_req"], timeout=0.5, max_attempts=3, log_widget=log_widget)
                    time.sleep(0.35)
                    continue

                # If attack button appears, click it and break out
                if IMAGES.get("attack") and pyautogui.locateOnScreen(IMAGES["attack"], confidence=CONFIDENCE):
                    log_msg("Attack button detected, performing attack...", log_widget)
                    if find_and_click(IMAGES["attack"], timeout=0.5, max_attempts=4, log_widget=log_widget):
                        attack_clicked = True
                    time.sleep(0.4)
                    break

                # small sleep to avoid busy-looping
                time.sleep(0.25)

            # Determine whether rescue handling should be active for this battle.
            # Rescue is active only if both: the rescue button is shown on-screen AND
            # the user has the RESCUE checkbox enabled in the UI (state['rescue']).
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

            # Set a transient state flag that tells the battle-end handler whether
            # rescue is allowed for this battle. This will be read by
            # `wait_for_battle_end` to decide defeat behavior.
            state["rescue_active_for_current_battle"] = rescue_active
            # Wait for the battle to finish and let wait_for_battle_end handle OKs/defeat
            wait_for_battle_end(IMAGES, log_widget)
            

    # Wait for battle to finish and clear dialogs
    wait_for_battle_end(IMAGES, log_widget)


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
        if IMAGES.get("story_start") and pyautogui.locateOnScreen(IMAGES["story_start"], confidence=CONFIDENCE):
            log_msg("starting story...", log_widget)
            time.sleep(SLEEP)
            find_and_click(IMAGES["story_start"], timeout=4.0, max_attempts=2, log_widget=log_widget)

            # stamina check after starting a story/quest
            time.sleep(2.0)
            check_stamina(IMAGES, log_widget)

            # Story skip flow
            time.sleep(2)
            while state.get("running", False):
                if IMAGES.get("skip") and pyautogui.locateOnScreen(IMAGES["skip"], confidence=CONFIDENCE):
                    log_msg("Branch story...", log_widget)
                    find_and_click(IMAGES["skip"], timeout=0.5, max_attempts=2, log_widget=log_widget)
                    time.sleep(0.5)
                    find_and_click(IMAGES["skip_confirm"], timeout=0.5, max_attempts=2, log_widget=log_widget)
                    break
                    
                elif IMAGES.get("support") and pyautogui.locateOnScreen(IMAGES["support"], confidence=CONFIDENCE):
                    # Normal combat branch
                    log_msg("Branch combat...", log_widget)
                    combat_sequence(log_widget, IMAGES)
                    break

                time.sleep(2.0)

            time.sleep(SLEEP)
            find_and_click(IMAGES["return"], timeout=2.0, max_attempts=3, log_widget=log_widget)
            time.sleep(SLEEP)
            find_and_click(IMAGES["ok"], max_attempts=2, log_widget=log_widget)



def try_page_down(IMAGES):
    down = IMAGES.get("down") and pyautogui.locateOnScreen(
        IMAGES["down"],
        confidence=0.88
    )

    if not down:
        return False

    if IMAGES.get("down_max") and pyautogui.locateOnScreen(
        IMAGES["down_max"],
        region=down,
        confidence=0.9
    ):
        return False

    pyautogui.click(down)
    time.sleep(1.2)
    return True

def try_enter_raid(el, diff, IMAGES, log_widget):
    log_msg(f"Entering {el} {diff}", log_widget)

    # 1️⃣ Ongoing raid must appear first
    for _ in range(3):
        if not state.get("running"):
            return "abort"

        if ongoing_raids(IMAGES, log_widget):
            break
        time.sleep(0.4)
    else:
        log_msg("No ongoing raid detected", log_widget)
        return "abort"

    # 2️⃣ Resolve entry outcome
    for _ in range(4):
        if not state.get("running"):
            return "abort"

        if IMAGES.get("limit") and pyautogui.locateOnScreen(IMAGES["limit"], confidence=CONFIDENCE):
            log_msg("Entry blocked: limit reached", log_widget)
            find_and_click(IMAGES.get("ok"), timeout=0.6, max_attempts=2, log_widget=log_widget)
            return "limit"

        if IMAGES.get("condition") and pyautogui.locateOnScreen(IMAGES["condition"], confidence=CONFIDENCE):
            log_msg("Entry blocked: condition not met", log_widget)
            for key in ("ok", "challenge", "cancel"):
                if IMAGES.get(key):
                    find_and_click(IMAGES[key], timeout=0.6, max_attempts=2, log_widget=log_widget)
                    break
            return "condition"

        if IMAGES.get("challenge") and pyautogui.locateOnScreen(IMAGES["challenge"], confidence=CONFIDENCE):
            find_and_click(IMAGES["challenge"], timeout=0.6, max_attempts=2, log_widget=log_widget)
            check_stamina(IMAGES, log_widget)
            return "start"

        if IMAGES.get("ok") and pyautogui.locateOnScreen(IMAGES["ok"], confidence=CONFIDENCE):
            find_and_click(IMAGES["ok"], timeout=0.6, max_attempts=2, log_widget=log_widget)
            check_stamina(IMAGES, log_widget)
            return "start"

        time.sleep(0.4)

    return "abort"

def run_combat(el, diff, IMAGES, log_widget, host=True):
    log_msg("In Battle...", log_widget)

    while state.get("running"):
        combat_sequence(log_widget, IMAGES, get_img)

        if IMAGES.get("return_raid") and pyautogui.locateOnScreen(IMAGES["return_raid"], confidence=0.8):
            find_and_click(IMAGES["return_raid"], max_attempts=3, log_widget=log_widget)
            if host:
                state["completed_raids"][el][diff] += 1
            _inc_loop("raid", log_widget)
            return

        time.sleep(1.5)


def raid_host_rotation(log_widget, ELEMENTS, IMAGES, get_img):
    log_msg("STARTING RAID ROTATION", log_widget)

    for idx, el in enumerate(ELEMENTS):
        if not state.get("running"):
            return

        # Select element tab
        if idx > 0:
            tab = pyautogui.locateCenterOnScreen(
                get_img(f"KHR_raid_{el}"),
                confidence=0.9
            )
            if tab:
                pyautogui.click(tab)
                time.sleep(1.5)

        while state.get("running"):
            raid_found = False

            for diff, enabled in state["raid_settings"].get(el, {}).items():
                if not enabled:
                    continue

                if state["completed_raids"][el].get(diff, 0) >= 1:
                    continue

                raid_img = get_img(f"KHR_{el}_{diff}")
                loc = pyautogui.locateOnScreen(raid_img, confidence=0.92)
                if not loc:
                    continue

                raid_found = True
                pyautogui.click(pyautogui.center(loc))
                time.sleep(2)

                result = try_enter_raid(el, diff, IMAGES, log_widget)

                if result in ("limit", "condition"):
                    state["completed_raids"][el][diff] += 1
                    continue

                if result == "start":
                    run_combat(el, diff, IMAGES, log_widget)

            # Page down if nothing found
            if not raid_found:
                if not try_page_down(IMAGES):
                    break

    state["running"] = False
    log_msg("ROTATION FINISHED", log_widget)
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


def wait_for_ok(IMAGES, log_widget=None, times=1, timeout=20, rescue_active=False):
    """Click OK up to `times` times, waiting up to `timeout` seconds for each OK to appear.

    Returns True if at least one OK was clicked, False otherwise.
    """
    clicked_any = False
    end_time = time.time() + timeout
    while times > 0 and time.time() < end_time and state.get("running", False):
        log_msg(f"Waiting for result interaction (OK)...", log_widget)
        # Only look for the active OK button. While waiting, also watch for
        # defeat-related dialogs (death/elixir) so we can handle the died-in-raid
        # sequence centrally here.
        ok = IMAGES.get("ok")
        if ok and pyautogui.locateOnScreen(ok, confidence=CONFIDENCE):
            find_and_click(ok, timeout=0.4, confidence=CONFIDENCE, max_attempts=3, log_widget=log_widget)
            clicked_any = True
            times -= 1
            # short pause between clicks
            time.sleep(0.4)
            continue

        # If a defeat-with-revive prompt appears (elixir prompt), handle the died-in-raid flow:
        # 1) defeat_elixir (revive using elixir) -> press cancel
        # 2) defeat (defeat screen / give up prompt) -> press cancel
        # After both cancels, if rescue is enabled we continue waiting for OK (rescue prompt will reappear).
        # If rescue is disabled, press quest_list and stop waiting.
        if IMAGES.get("defeat_elixir") and pyautogui.locateOnScreen(IMAGES["defeat_elixir"], confidence=CONFIDENCE):
            log_msg("Defeat - revive (elixir) prompt shown while waiting for OK, cancelling revive...", log_widget)
            if IMAGES.get("cancel"):
                time.sleep(SLEEP)
                find_and_click(IMAGES["cancel"], timeout=0.6, max_attempts=3, log_widget=log_widget)
            time.sleep(0.4)

            # Now if the defeat/give-up screen appears, handle it
            if IMAGES.get("defeat") and pyautogui.locateOnScreen(IMAGES["defeat"], confidence=CONFIDENCE):
                log_msg("Defeat screen present after revive cancel, handling...", log_widget)
                # If rescue was not active for this battle (either image absent or user disabled),
                # press quest_list (give up) and stop waiting.
                if not rescue_active:
                    log_msg("Rescue not active - pressing quest_list and aborting wait_for_ok", log_widget)
                    if IMAGES.get("quest_list"):
                        time.sleep(SLEEP)
                        find_and_click(IMAGES["quest_list"], timeout=0.6, max_attempts=3, log_widget=log_widget)
                    return clicked_any

                # Otherwise press cancel to close the defeat screen and continue waiting for rescue OK
                if IMAGES.get("cancel"):
                    time.sleep(SLEEP)
                    find_and_click(IMAGES["cancel"], timeout=0.6, max_attempts=3, log_widget=log_widget)
                time.sleep(0.6)

            # After handling revive/defeat, continue waiting for OK (rescue prompt)
            time.sleep(0.3)
            continue

        # If a plain defeat screen appears (without elixir prompt), handle similarly
        if IMAGES.get("defeat") and pyautogui.locateOnScreen(IMAGES["defeat"], confidence=CONFIDENCE):
            log_msg("Defeat screen detected while waiting for OK", log_widget)
            if not rescue_active:
                log_msg("Rescue not active - pressing quest_list and aborting wait_for_ok", log_widget)
                if IMAGES.get("quest_list"):
                    time.sleep(SLEEP)
                    find_and_click(IMAGES["quest_list"], timeout=0.6, max_attempts=3, log_widget=log_widget)
                return clicked_any
            # rescue active -> cancel defeat screen and continue waiting
            if IMAGES.get("cancel"):
                time.sleep(SLEEP)
                find_and_click(IMAGES["cancel"], timeout=0.6, max_attempts=3, log_widget=log_widget)
            time.sleep(0.6)

        # fallback: small sleep until OK appears
        time.sleep(0.3)

    return clicked_any


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
    # Click OK multiple times to clear rewards/scoreboard/first-time dialogs
    # defeat/elixir handling has been centralized in wait_for_ok so here we only
    # repeatedly attempt to clear remaining OK dialogs.
    wait_clicks = 6
    for _ in range(wait_clicks):
        if not state.get("running", False):
            break
        clicked = wait_for_ok(IMAGES, log_widget=log_widget, times=1, timeout=6)
        if not clicked:
            # if no OK found for a while, break
            break


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

            # Wait for OK and let wait_for_ok handle the defeat/rescue sequence. Pass the computed
            # `rescue_active` so the function knows whether to attempt rescue flow or abort to quest list.
            wait_for_ok(IMAGES, log_widget=log_widget, rescue_active=rescue_active)
            

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
            time.sleep(0.25)
            # stamina check after starting a story/quest
            check_stamina(IMAGES, log_widget)

            # Story skip flow
            time.sleep(2)
            if IMAGES.get("skip") and pyautogui.locateOnScreen(IMAGES["skip"], confidence=CONFIDENCE):
                log_msg("Branch story...", log_widget)
                find_and_click(IMAGES["skip"], timeout=0.5, max_attempts=2, log_widget=log_widget)
                time.sleep(0.18)
                # Skip confirmation
                if IMAGES.get("skip_confirm") and pyautogui.locateOnScreen(IMAGES["skip_confirm"], confidence=CONFIDENCE):
                    if find_and_click(IMAGES["skip_confirm"], timeout=0.5, max_attempts=2, log_widget=log_widget):
                        find_and_click(IMAGES["return"], timeout=2.0, max_attempts=3, log_widget=log_widget)
                        time.sleep(0.9)
                        find_and_click(IMAGES["ok"], max_attempts=2, log_widget=log_widget)
            else:
                # Normal combat branch
                log_msg("Branch combat...", log_widget)
                combat_sequence(log_widget, IMAGES)
                time.sleep(SLEEP)
                find_and_click(IMAGES["return"], max_attempts=3, log_widget=log_widget)


def raid_host_rotation(log_widget, ELEMENTS, IMAGES, get_img):
    log_msg("STARTING RAID ROTATION", log_widget)

    for index, el in enumerate(ELEMENTS):
        if not state.get("running", False):
            break

        # Tab selection
        if index > 0:
            tab_img = get_img(f"KHR_raid_{el}")
            tab_loc = pyautogui.locateCenterOnScreen(tab_img, confidence=0.8)
            if tab_loc:
                pyautogui.click(tab_loc)
                time.sleep(2.5)

        element_finished = False
        while not element_finished and state.get("running", False):
            found_any = False
            for diff in list(state["raid_settings"].get(el, {})):
                # support counters: completed_raids stores an int count per difficulty
                max_runs = state.get("max_runs", {}).get(el, 1)
                completed = state["completed_raids"].get(el, {}).get(diff, 0)
                if not state["raid_settings"][el][diff] or completed >= max_runs:
                    continue

                # Ragnarok/Ultimate precision check
                conf = 0.92 if diff in ["ragnarok", "ultimate"] else 0.75

                raid_img = get_img(f"KHR_{el}_{diff}")
                btn = pyautogui.locateOnScreen(raid_img, confidence=conf)
                if btn:
                    found_any = True
                    log_msg(f"Entering {el} {diff}", log_widget)
                    pyautogui.click(pyautogui.center(btn))
                    time.sleep(2)
                    # After clicking entry, check for several possible outcomes:
                    # - max limit reached (IMAGES['limit'])
                    # - doesn't meet condition (IMAGES['condition'])
                    # - stamina check (IMAGES['stamina_check'])
                    # - OK popup (entry blocked)

                    entry_handled = False
                    # short loop to allow transient dialogs to appear
                    for _ in range(8):
                        if not state.get("running", False):
                            entry_handled = True
                            break

                        # MAX LIMIT
                        if IMAGES.get("limit") and pyautogui.locateOnScreen(IMAGES["limit"], confidence=CONFIDENCE):
                            log_msg("Entry blocked: max limit reached.", log_widget)
                            # dismiss with OK if available
                            if IMAGES.get("ok"):
                                find_and_click(IMAGES["ok"], timeout=0.6, max_attempts=2, log_widget=log_widget)
                            # mark as consumed so we don't try again
                            state["completed_raids"][el][diff] = state["completed_raids"][el].get(diff, 0) + state.get("max_runs", {}).get(el, 1)
                            entry_handled = True
                            break

                        # CONDITION NOT MET (these dialogs usually have an OK or CHALLENGE button)
                        if IMAGES.get("condition") and pyautogui.locateOnScreen(IMAGES["condition"], confidence=CONFIDENCE):
                            log_msg("Entry blocked: condition not met.", log_widget)
                            # prefer to press OK or CHALLENGE if available
                            if IMAGES.get("ok") and pyautogui.locateOnScreen(IMAGES["ok"], confidence=CONFIDENCE):
                                find_and_click(IMAGES["ok"], timeout=0.6, max_attempts=2, log_widget=log_widget)
                            elif IMAGES.get("challenge") and pyautogui.locateOnScreen(IMAGES["challenge"], confidence=CONFIDENCE):
                                find_and_click(IMAGES["challenge"], timeout=0.6, max_attempts=2, log_widget=log_widget)
                            else:
                                # fallback to cancel if nothing else
                                if IMAGES.get("cancel"):
                                    find_and_click(IMAGES["cancel"], timeout=0.6, max_attempts=2, log_widget=log_widget)
                            state["completed_raids"][el][diff] = state["completed_raids"][el].get(diff, 0) + 1
                            entry_handled = True
                            break

                        # STAMINA CHECK: try to handle (use stamina) and then re-evaluate
                        if check_stamina(IMAGES, log_widget):
                            log_msg("Stamina dialog handled for raid entry; re-evaluating...", log_widget)
                            time.sleep(0.6)
                            continue

                        # Check for OK popup (generic blocked popup)
                        ok_btn = IMAGES.get("ok") and pyautogui.locateOnScreen(IMAGES["ok"], confidence=0.8)
                        if ok_btn:
                            log_msg("Entry blocked by popup.", log_widget)
                            find_and_click(IMAGES["ok"], timeout=0.6, max_attempts=2, log_widget=log_widget)
                            # count this as an attempted/consumed hosting
                            state["completed_raids"][el][diff] = state["completed_raids"][el].get(diff, 0) + 1
                            entry_handled = True
                            break

                        # nothing yet, wait a bit
                        time.sleep(0.4)

                    if entry_handled:
                        # go back to scanning diffs for this element
                        break

                    # else: no blocking dialog detected -> treat as successful entry
                    else:
                        # SUCCESSFUL ENTRY -> Do combat until we can return
                        log_msg("In Battle...", log_widget)
                        in_battle = True
                        while in_battle and state.get("running", False):
                            # Use the combat sequence (raid may present support_request etc.)
                            combat_sequence(log_widget, IMAGES, get_img)
                            # Check if we can return to list
                            ret_btn = IMAGES.get("return") and pyautogui.locateOnScreen(IMAGES["return"], confidence=0.8)
                            if ret_btn:
                                find_and_click(IMAGES["return"], max_attempts=3, log_widget=log_widget)
                                in_battle = False
                                state["completed_raids"][el][diff] = state["completed_raids"].get(el, {}).get(diff, 0) + 1
                                # increment raid loop counter for a completed raid run
                                _inc_loop("raid", log_widget)
                            time.sleep(1.5)
                    break

            if not found_any:
                down_loc = IMAGES.get("down") and pyautogui.locateOnScreen(IMAGES["down"], confidence=0.7)
                if down_loc and not (IMAGES.get("down_max") and pyautogui.locateOnScreen(IMAGES["down_max"], region=down_loc, confidence=0.9)):
                    pyautogui.click(down_loc)
                    time.sleep(1.2)
                else:
                    element_finished = True

    state["running"] = False
    log_msg("ROTATION FINISHED", log_widget)
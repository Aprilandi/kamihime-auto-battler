import time
import pyautogui
from .core import state, log_msg, _inc_loop, CONFIDENCE
from .vision import find_and_click, ongoing_raids, try_page_down
from .battle import check_stamina, run_combat


def try_enter_raid(el, diff, IMAGES, log_widget):
    log_msg(f"Entering {el} {diff}", log_widget)

    # 1️⃣ Ongoing raid must appear first
    if not state.get("running"):
        return "abort"
        
    if not ongoing_raids(IMAGES, log_widget, attempts=2):
        return "abort"


    # 2️⃣ Resolve entry outcome
    for _ in range(4):
        log_msg("Checking raid entry outcome...", log_widget)

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
            time.sleep(1.0)
            check_stamina(IMAGES, log_widget)
            return "start"

        if IMAGES.get("ok") and pyautogui.locateOnScreen(IMAGES["ok"], confidence=CONFIDENCE):
            find_and_click(IMAGES["ok"], timeout=0.6, max_attempts=2, log_widget=log_widget)
            time.sleep(1.0)
            check_stamina(IMAGES, log_widget)
            return "start"

        time.sleep(0.4)

    return "abort"



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

        page_down_attempts = 0
        max_page_down = 12
        while state.get("running"):
            raid_found = False

            for diff, enabled in state["raid_settings"].get(el, {}).items():
                if not enabled:
                    continue

                if state["completed_raids"][el].get(diff, 0) >= 1:
                    continue

                raid_img = get_img(f"KHR_{el}_{diff}")
                try:
                    loc = pyautogui.locateOnScreen(raid_img, confidence=0.92)
                except ValueError as e:
                    # sometimes region/needle size issues can raise ValueError from the imaging lib
                    log_msg(f"Image locate error for {el} {diff}: {e}", log_widget)
                    loc = None
                except Exception as e:
                    log_msg(f"Unexpected error locating raid image {el} {diff}: {e}", log_widget)
                    loc = None

                if not loc:
                    continue

                log_msg(f"Found raid: {el} {diff}", log_widget)
                raid_found = True
                try:
                    pyautogui.click(pyautogui.center(loc))
                except Exception:
                    pyautogui.click(loc.left + 5, loc.top + 5)

                time.sleep(2)
                result = try_enter_raid(el, diff, IMAGES, log_widget)

                if result in ("limit", "condition"):
                    state["completed_raids"][el][diff] += 1
                    continue

                if result == "start":
                    run_combat(el, diff, IMAGES, log_widget)
                    # small pause to avoid tight re-entry
                    time.sleep(3)
                elif result == "abort":
                    # avoid infinite retry loops on the same raid entry
                    log_msg(f"Abort detected for {el} {diff}, marking as attempted", log_widget)
                    state["completed_raids"][el][diff] = state["completed_raids"][el].get(diff, 0) + 1
                    continue

            # Page down if nothing found
            if not raid_found:
                if try_page_down(IMAGES):
                    page_down_attempts += 1
                    log_msg(f"Paged down ({page_down_attempts}/{max_page_down})", log_widget)
                    # if we've paged many times without finding anything, stop this element
                    if page_down_attempts >= max_page_down:
                        log_msg("Max page-down attempts reached, moving to next element", log_widget)
                        break
                    # continue scanning after page down
                    continue
                else:
                    break

    state["running"] = False
    log_msg("ROTATION FINISHED", log_widget)

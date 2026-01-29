import os
import pyautogui
import json

import sys, os

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller exe"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


PREFS_FILENAME = "raid_prefs.json"

pyautogui.useImageNotFoundException(False)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Image folders root (inside project) and selected folder name. The default
# folder matches the shipped templates; users can add other folders (e.g.
# '1080x920') and the UI will detect them.
IMAGES_ROOT = resource_path("images")
SELECTED_IMAGE_FOLDER = "1920x1080"


def list_image_folders():
    """Return a sorted list of subfolder names inside the images/ folder.

    These folder names are intended to be resolution identifiers (e.g.
    '1920x1080')."""
    try:
        names = [n for n in os.listdir(IMAGES_ROOT) if os.path.isdir(os.path.join(IMAGES_ROOT, n))]
        return sorted(names)
    except Exception:
        return [SELECTED_IMAGE_FOLDER]


def get_img(name):
    """Return the full path to an image in the currently selected image folder.

    The selected folder is controlled by `SELECTED_IMAGE_FOLDER` and can be
    changed at runtime by calling `set_image_folder(folder)`.
    """
    return resource_path(os.path.join("images", SELECTED_IMAGE_FOLDER, f"{name}.png"))


def set_image_folder(folder_name):
    """Set the active image folder and rebuild the IMAGES mapping used by the
    rest of the program. Returns True on success.
    """
    global SELECTED_IMAGE_FOLDER, IMAGES, CONNECTING
    try:
        # basic validation
        target = os.path.join(IMAGES_ROOT, folder_name)
        if not os.path.isdir(target):
            return False
        SELECTED_IMAGE_FOLDER = folder_name
        # rebuild IMAGES mapping so callers using config.IMAGES see updated paths
        if 'IMAGES' in globals() and isinstance(IMAGES, dict):
            new_imgs = {}
            for k, v in IMAGES.items():
                try:
                    # v is a previously-built path like '.../KHR_skip.png'
                    base = os.path.splitext(os.path.basename(v))[0]
                    new_imgs[k] = get_img(base)
                except Exception:
                    # fallback: try using the key name
                    new_imgs[k] = get_img(k)
            IMAGES = new_imgs
        else:
            IMAGES = {}
        # update CONNECTING if present
        CONNECTING = get_img('KHR_connecting')
        return True
    except Exception:
        return False

CONFIDENCE = 0.8
SLEEP = 0.5

# config.py
ELEMENTS = ["fire", "water", "wind", "thunder", "light", "dark", "phantom"]
DIFFICULTIES = ["malicious_plus", "malicious", "guardian_plus", "guardian", "ragnarok", "ultimate", "expert", "standard"]
CONNECTING = get_img('KHR_connecting')

# Per-element difficulty lists. Most elements use the shared DIFFICULTIES list,
# but some (like 'phantom') have a different naming/ordering for difficulties.
# Feel free to edit PHANTOM_DIFFICULTIES to match your game.
# Phantom difficulties currently only include these three names. Do not
# automatically append the regular DIFFICULTIES list — phantom has a different
# naming set that should be kept separate.
PHANTOM_DIFFICULTIES = ["jester", "och_plus", "och"]

ELEMENT_DIFFICULTIES = {
    el: (PHANTOM_DIFFICULTIES if el == 'phantom' else DIFFICULTIES)
    for el in ELEMENTS
}

IMAGES = {
    "story_start": get_img('KHR_gems(start)'),
    "skip": get_img('KHR_skip'),
    "skip_confirm": get_img('KHR_skip_confirmation'),
    "support": get_img('KHR_support'),
    "support_req": get_img('KHR_support_request'),
    "go_quest": get_img('KHR_gotoquest'),
    "attack": get_img('KHR_attack'),
    "rescue": get_img('KHR_rescue'),
    "rescue_prompt": get_img('KHR_rescue_prompt'),
    "condition": get_img('KHR_condition'),
    "challenge": get_img('KHR_challenge'),
    "cancel": get_img('KHR_cancel'),
    "ok": get_img('KHR_ok'),
    "ok_inactive": get_img('KHR_ok_inactive'),
    "return": get_img('KHR_return'),
    "return_raid": get_img('KHR_return_raid'),
    "return_raid_battle": get_img('KHR_return_raid_battle'),
    "retry": get_img('KHR_retry'),
    "defeat": get_img('KHR_defeat_screen'),
    "defeat_elixir": get_img('KHR_defeat_continue'),
    "stamina_check": get_img('KHR_stamina_check'),
    "bp_check": get_img('KHR_bp_check'),
    "stamina_use": get_img('KHR_stamina_use'),
    "ongoing": get_img('KHR_give_up_resume'),
    "quest": get_img('KHR_quest'),
    "raid_quest": get_img('KHR_raid_quests'),
    "raid_quest_available": get_img('KHR_raid_quest_available'),
    "quest_list": get_img('KHR_quest_list'),
    "batch": get_img('KHR_batch_check'),
    "down": get_img('KHR_down'),
    "down_max": get_img('KHR_down_max'),
    "limit": get_img('KHR_limit'),
    "in_battle": get_img('KHR_in_battle'),
    "ep_start": get_img('KHR_episode_notif'),
    "ep_encounter": get_img('KHR_episode_encounter'),
    "ep_1": get_img('KHR_episode_1'),
    "ep_2": get_img('KHR_episode_2'),
    "ep_skip": get_img('KHR_episode_skip'),
    "ep_return": get_img('KHR_episode_return'),
    "reload": get_img('KHR_reload'),
    "raid_event": get_img('KHR_raid_event'),
    "raid_regular": get_img('KHR_raid_regular'),
    "unconfirmed_battles": get_img('KHR_unconfirmed_battles'),
    "start_game": get_img("KHR_start_game")
}


PREFS_PATH = resource_path(os.path.join(PREFS_FILENAME))


def load_prefs():
    """Load persisted raid preferences (raid_settings, completed_raids, max_runs, rescue).

    Returns a dict with saved keys or an empty dict when none exists.
    """
    if not os.path.exists(PREFS_PATH):
        return {}
    try:
        with open(PREFS_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def save_prefs(state_dict):
    """Persist selected parts of runtime state to PREFS_PATH.

    We only persist raid_settings, completed_raids, max_runs, and rescue so the file
    remains small and focused on user preferences/progress.
    """
    try:
        data = {
            'raid_settings': state_dict.get('raid_settings', {}),
            'completed_raids': state_dict.get('completed_raids', {}),
            'max_runs': state_dict.get('max_runs', {}),
            'rescue': state_dict.get('rescue', True),
            # optional UI prefs
            'image_folder': state_dict.get('image_folder'),
        }
        with open(PREFS_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception:
        return False
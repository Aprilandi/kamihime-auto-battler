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

def get_img(name): 
    # This joins'images' + 'filename.png'
    return resource_path(os.path.join("images", "1920x1080", f"{name}.png"))

CONFIDENCE = 0.8
SLEEP = 0.5

# config.py
ELEMENTS = ["fire", "water", "wind", "thunder", "light", "dark", "phantom"]
DIFFICULTIES = ["malicious", "guardian_plus", "guardian", "ragnarok", "ultimate", "expert", "standard"]
CONNECTING = get_img('KHR_connecting')

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
    "unconfirmed_battles": get_img('KHR_unconfirmed_battles')
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
        }
        with open(PREFS_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception:
        return False
import os
import pyautogui

pyautogui.useImageNotFoundException(False)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIDENCE = 0.8
SLEEP = 0.5

# config.py
ELEMENTS = ["fire", "water", "wind", "thunder", "light", "dark", "phantom"]
DIFFICULTIES = ["guardian_plus", "guardian", "ragnarok", "ultimate", "expert", "standard"]

def get_img(name): 
    # This joins BASE_DIR + 'images' + 'filename.png'
    return os.path.join(BASE_DIR, "images", f"{name}.png")

IMAGES = {
    "story_start": get_img('KHR_gems(start)'),
    "skip": get_img('KHR_skip'),
    "skip_confirm": get_img('KHR_skip_confirmation'),
    "support": get_img('KHR_support'),
    "support_req": get_img('KHR_support_request'),
    "go_quest": get_img('KHR_gotoquest'),
    "attack": get_img('KHR_attack'),
    "rescue": get_img('KHR_rescue'),
    "condition": get_img('KHR_condition'),
    "challenge": get_img('KHR_challenge'),
    "cancel": get_img('KHR_cancel'),
    "ok": get_img('KHR_ok'),
    "ok_inactive": get_img('KHR_ok_inactive'),
    "return": get_img('KHR_return'),
    "retry": get_img('KHR_retry'),
    "defeat": get_img('KHR_defeat_screen'),
    "defeat_elixir": get_img('KHR_defeat_continue'),
    "stamina_check": get_img('KHR_stamina_check'),
    "stamina_use": get_img('KHR_stamina_use'),
    "ongoing": get_img('KHR_give_up_resume'),
    "quest_list": get_img('KHR_quest_list'),
    "batch": get_img('KHR_batch_check'),
    "down": get_img('KHR_down'),
    "down_max": get_img('KHR_down_max'),
    "limit": get_img('KHR_limit')
}
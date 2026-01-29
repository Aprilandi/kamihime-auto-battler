import customtkinter as ctk
import threading, logic, os, keyboard, config

# Use configuration module (single source of truth for images and lists)
ELEMENTS = config.ELEMENTS
# Use per-element difficulties mapping when available (phantom differs)
ELEMENT_DIFFICULTIES = getattr(config, 'ELEMENT_DIFFICULTIES', {el: config.DIFFICULTIES for el in ELEMENTS})
DIFFICULTIES = config.DIFFICULTIES

# Images mapping will be built from the selected image folder. We start with
# the folder persisted in prefs (if any) or fall back to the default that
# shipped with the repo.
IMAGES = dict(config.IMAGES)
# local get_img will be replaced once we build the selected-folder wrapper
get_img = config.get_img

# Initialize State with defaults; override from persisted prefs when available
default_raid_settings = {}
default_completed = {}
for el in ELEMENTS:
    diffs = ELEMENT_DIFFICULTIES.get(el, config.DIFFICULTIES)
    default_raid_settings[el] = {"enable": True, "difficulty": {d: True for d in diffs}}
    default_completed[el] = {d: 0 for d in diffs}

default_max_runs = {el: (2 if el == "phantom" else 1) for el in ELEMENTS}

logic.state["raid_settings"] = default_raid_settings
logic.state["completed_raids"] = default_completed
logic.state["max_runs"] = default_max_runs
logic.state["rescue"] = True
# loop counters: track how many iterations each sequence has performed
logic.state["loop_counts"] = {"farm_loop": 0, "quest_rush": 0, "raid_host": 0}
# active sequence name (or None)
logic.state["active_sequence"] = None

# Load persisted preferences (if any) and merge them into runtime state
try:
    prefs = config.load_prefs()
    if prefs.get("raid_settings"):
        # merge nested format: {el: {"enable": bool, "difficulty": { ... }}}
        for el, data in prefs.get("raid_settings", {}).items():
            if el in logic.state["raid_settings"] and isinstance(data, dict):
                # merge enable flag
                if "enable" in data:
                    logic.state["raid_settings"][el]["enable"] = bool(data.get("enable"))
                # merge difficulty map
                if isinstance(data.get("difficulty"), dict):
                    logic.state["raid_settings"][el]["difficulty"].update(data.get("difficulty"))
    if prefs.get("completed_raids"):
        # Defensive merge: ensure every element/difficulty key is present and
        # prefer persisted values when available. Cast values to int to avoid
        # accidental string types from external edits.
        persisted = prefs.get("completed_raids", {}) or {}
        for el in ELEMENTS:
            diffs = ELEMENT_DIFFICULTIES.get(el, config.DIFFICULTIES)
            for d in diffs:
                try:
                    val = persisted.get(el, {}).get(d, default_completed[el].get(d, 0))
                    logic.state["completed_raids"][el][d] = int(val)
                except Exception:
                    # if casting fails, fallback to the default
                    logic.state["completed_raids"][el][d] = default_completed[el].get(d, 0)
    if prefs.get("max_runs"):
        logic.state["max_runs"].update(prefs.get("max_runs", {}))
    if "rescue" in prefs:
        logic.state["rescue"] = bool(prefs.get("rescue"))
    # selected image folder (optional)
    sel_img_folder = prefs.get('image_folder')
    if sel_img_folder:
        logic.state['image_folder'] = sel_img_folder
except Exception:
    # ignore prefs errors and continue with defaults
    pass

# --- Controller Functions ---
def _set_mode_buttons_state(state_value):
    # helper to enable/disable the main mode buttons
    try:
        btn_raid.configure(state=state_value)
        btn_epic.configure(state=state_value)
        btn_retry.configure(state=state_value)
        btn_episode.configure(state=state_value)
        btn_raid_farm.configure(state=state_value)
        # btn_tower.configure(state=state_value)
    except Exception:
        pass


def start_mode(mode_func, mode_name, *args):
    # Only allow starting when nothing else is running
    if not logic.state.get("running", False):
        logic.state["running"] = True
        logic.state["active_sequence"] = mode_name
        status_lbl.configure(text="RUNNING", text_color="green")
        # disable other buttons
        _set_mode_buttons_state("disabled")
        # try to prevent the system from sleeping while the bot runs
        try:
            logic.prevent_sleep()
        except Exception:
            pass

        t = threading.Thread(target=mode_func, args=args, daemon=True)
        t.start()

        # watcher thread to re-enable buttons and clear state when the mode finishes
        def _watch():
            t.join()
            logic.state["running"] = False
            logic.state["active_sequence"] = None
            # allow normal sleep behavior again
            try:
                logic.allow_sleep()
            except Exception:
                pass
            _set_mode_buttons_state("normal")
            try:
                status_lbl.configure(text="STOPPED", text_color="red")
            except Exception:
                pass

        threading.Thread(target=_watch, daemon=True).start()

def stop_bot():
    logic.state["running"] = False
    status_lbl.configure(text="STOPPED", text_color="red")
    # restore normal sleep behavior when the user stops the bot
    try:
        logic.allow_sleep()
    except Exception:
        pass

def reset_list():
    for el in ELEMENTS:
        diffs = ELEMENT_DIFFICULTIES.get(el, config.DIFFICULTIES)
        for d in diffs:
            logic.state["completed_raids"][el][d] = 0
    # also reset loop counters
    if "loop_counts" in logic.state:
        for k in logic.state["loop_counts"].keys():
            logic.state["loop_counts"][k] = 0
    log.insert("end", ">>> PROGRESS RESET <<<\n")
    log.see("end")
    # persist reset
    try:
        config.save_prefs(logic.state)
    except Exception:
        pass

keyboard.add_hotkey('f7', stop_bot)

# --- UI Setup ---
app = ctk.CTk()
app.title("K-Bot")
app.geometry("280x800")
app.attributes("-topmost", True)

status_lbl = ctk.CTkLabel(app, text="IDLE", font=("Arial", 12, "bold"))
status_lbl.pack(pady=5)

# Image resolution selector (detect subfolders inside the images/ directory)
folders = config.list_image_folders()

# if a persisted folder exists in prefs (or logic.state) apply it to config
if logic.state.get('image_folder'):
    try:
        config.set_image_folder(logic.state.get('image_folder'))
    except Exception:
        pass

# apply initial mapping from config (config.IMAGES is rebuilt by set_image_folder)
IMAGES = dict(getattr(config, 'IMAGES', {}))
get_img = config.get_img

# selected image folder for the UI dropdown
selected_image_folder = getattr(config, 'SELECTED_IMAGE_FOLDER', (folders[0] if folders else "1920x1080"))

def _on_image_folder_change(new):
    # update config's selected image folder and persist
    global IMAGES, get_img, selected_image_folder
    if config.set_image_folder(new):
        IMAGES = dict(getattr(config, 'IMAGES', {}))
        get_img = config.get_img
        selected_image_folder = new
        logic.state['image_folder'] = selected_image_folder
        try:
            config.save_prefs(logic.state)
        except Exception:
            pass
        # UI log feedback for image folder change
        try:
            msg = "> Image folder set to " + str(new) + "\n"
            log.insert("end", msg)
            log.see("end")
        except Exception:
            pass
        # persisted image folder updated

if folders:
    res_frame = ctk.CTkFrame(app)
    res_frame.pack(fill="x", padx=10, pady=(0,6))
    ctk.CTkLabel(res_frame, text="Images:", anchor="w").pack(side="left", padx=(0,8))
    res_menu = ctk.CTkOptionMenu(res_frame, values=folders, command=_on_image_folder_change)
    try:
        res_menu.set(selected_image_folder)
    except Exception:
        pass
    res_menu.pack(side="left")

# Control Buttons
ctrl_frame = ctk.CTkFrame(app)
ctrl_frame.pack(fill="x", padx=10, pady=5)
ctk.CTkButton(ctrl_frame, text="STOP (F7)", fg_color="red", width=120, command=stop_bot).grid(row=0, column=0, padx=2)
ctk.CTkButton(ctrl_frame, text="RESET", fg_color="orange", width=120, command=reset_list).grid(row=0, column=1, padx=2)

# Mode Grid
mode_frame = ctk.CTkFrame(app)
mode_frame.pack(fill="x", padx=10, pady=5)
# create buttons and keep references so we can disable/enable them while a sequence runs
btn_raid = ctk.CTkButton(mode_frame, text="Raid Host", width=120, command=lambda: start_mode(logic.raid_host, "raid_host", IMAGES, ELEMENTS, get_img, log))
btn_raid.grid(row=0, column=0, padx=2, pady=2)
btn_epic = ctk.CTkButton(mode_frame, text="Epic Quest Rush", width=120, command=lambda: start_mode(logic.quest_rush, "quest_rush", IMAGES, log))
btn_epic.grid(row=0, column=1, padx=2, pady=2)
btn_retry = ctk.CTkButton(mode_frame, text="Retry Farm", width=120, command=lambda: start_mode(logic.farm_loop, "farm_loop", IMAGES, log))
btn_retry.grid(row=1, column=0, padx=2, pady=2)
btn_raid_farm = ctk.CTkButton(mode_frame, text="Farm Raid", width=120, command=lambda: start_mode(logic.farm_raid, "farm_raid", IMAGES, ELEMENTS, get_img, log))
btn_raid_farm.grid(row=1, column=1, padx=2, pady=2)
btn_tower = ctk.CTkButton(mode_frame, text="Tower Farm", width=120, state="disabled")
btn_tower.grid(row=2, column=0, padx=2, pady=2)
btn_episode = ctk.CTkButton(mode_frame, text="Episode Rush", width=120, command=lambda: start_mode(logic.episode_rush, "episode_rush", IMAGES, log))
btn_episode.grid(row=2, column=1, padx=2, pady=2)


# RESCUE toggle checkbox (controls logic.state['RESCUE'])
rescue_var = ctk.BooleanVar(value=logic.state.get("rescue", True))
def _toggle_rescue():
    logic.state["rescue"] = rescue_var.get()

ctk.CTkCheckBox(mode_frame, text="RESCUE", variable=rescue_var, command=_toggle_rescue).grid(row=3, column=0, columnspan=2, pady=6)

# Raid Config
scroll = ctk.CTkScrollableFrame(app, height=300, label_text="Raid Config")
scroll.pack(fill="both", expand=True, padx=10, pady=5)

# store child vars so we can sync parent <> children
element_child_vars = {}
element_parent_vars = {}
element_all_btns = {}

for el in ELEMENTS:
    # Parent checkbox for the whole element (persisted under raid_settings[el]['__element_enabled__'])
    parent_init = logic.state.get("raid_settings", {}).get(el, {}).get("enable", True)
    parent_var = ctk.BooleanVar(value=parent_init)

    def make_parent_cb(e=el, pv=parent_var):
        def _on_parent():
            val = pv.get()
            # set all child vars and update runtime state
            for cv, diff in element_child_vars.get(e, []):
                cv.set(val)
                logic.state["raid_settings"][e]["difficulty"][diff] = val
            # persist enable flag
            logic.state["raid_settings"][e]["enable"] = val
            try:
                config.save_prefs(logic.state)
            except Exception:
                pass
        return _on_parent

    # header row for element: parent checkbox (children are created below)
    header_row = ctk.CTkFrame(scroll)
    header_row.pack(fill="x", padx=6, pady=(6,2))
    parent_cb = ctk.CTkCheckBox(header_row, text=el.upper(), font=("Arial", 10, "bold"), variable=parent_var, command=make_parent_cb())
    parent_cb.pack(side="left")

    element_parent_vars[el] = parent_var

    # prepare list for this element
    element_child_vars[el] = []

    # iterate per-element difficulty list (phantom has different difficulties)
    for d in ELEMENT_DIFFICULTIES.get(el, DIFFICULTIES):
        # initialize checkbox state from persisted runtime state
        init_val = logic.state.get("raid_settings", {}).get(el, {}).get("difficulty", {}).get(d, True)
        var = ctk.BooleanVar(value=init_val)

        def make_cb_command(e=el, di=d, v=var, pv=parent_var):
            def _cb():
                logic.state["raid_settings"][e]["difficulty"][di] = v.get()
                # update parent: checked if any child checked
                any_checked = any(cv.get() for cv, _ in element_child_vars.get(e, []))
                pv.set(any_checked)
                logic.state["raid_settings"][e]["enable"] = any_checked
                # persist change immediately
                try:
                    config.save_prefs(logic.state)
                except Exception:
                    pass
            return _cb

        cb = ctk.CTkCheckBox(scroll, text=d, font=("Arial", 9), height=16, variable=var, command=make_cb_command())
        if init_val:
            cb.select()
        cb.pack(anchor="w", padx=20)
        element_child_vars[el].append((var, d))

    # After children are created, add a toggle-all button for this element that
    # switches between enabling all difficulties and disabling all.
    def _toggle_all_for_element(e=el, btn_ref=None):
        # determine if all currently enabled
        all_on = all(cv.get() for cv, _ in element_child_vars.get(e, []))
        new_val = not all_on
        for cv, diff in element_child_vars.get(e, []):
            cv.set(new_val)
            logic.state["raid_settings"][e]["difficulty"][diff] = new_val
        logic.state["raid_settings"][e]["enable"] = any(cv.get() for cv, _ in element_child_vars.get(e, []))
        try:
            element_parent_vars.get(e).set(logic.state["raid_settings"][e]["enable"])
        except Exception:
            pass
        # update button label
        try:
            if btn_ref:
                btn_ref.configure(text=("None" if new_val else "All"))
        except Exception:
            pass
        try:
            config.save_prefs(logic.state)
        except Exception:
            pass
        # UI log feedback for element toggle
        try:
            msg = "> Toggled all difficulties for " + str(e) + ": " + ("enabled" if new_val else "disabled") + "\n"
            log.insert("end", msg)
            log.see("end")
        except Exception:
            pass

    all_btn = ctk.CTkButton(header_row, text="All", width=44, height=20)
    # bind command later with a reference to the button so it can update text
    all_btn.configure(command=lambda e=el, b=all_btn: _toggle_all_for_element(e, b))
    # set initial label to 'None' if all already enabled
    try:
        if all(cv.get() for cv, _ in element_child_vars.get(el, [])):
            all_btn.configure(text="None")
    except Exception:
        pass
    all_btn.pack(side="left", padx=(6,0))
    # remember the button so global actions can update its label
    element_all_btns[el] = all_btn

    # Global helpers to enable/disable sets of options
def enable_all_elements():
    for el in ELEMENTS:
        logic.state["raid_settings"][el]["enable"] = True
        try:
            element_parent_vars.get(el).set(True)
        except Exception:
            pass
    try:
        config.save_prefs(logic.state)
    except Exception:
        pass

# Controls under Raid Config: global toggles and "enable specific difficulty for all elements"
controls_frame = ctk.CTkFrame(app)
controls_frame.pack(fill="x", padx=10, pady=(6,8))

def _any_diff_disabled():
    for el in ELEMENTS:
        for cv, _ in element_child_vars.get(el, []):
            if not cv.get():
                return True
    return False

def _set_global_all_btn_text(btn):
    try:
        if _any_diff_disabled():
            btn.configure(text="Enable All Diffs")
        else:
            btn.configure(text="Disable All Diffs")
    except Exception:
        pass

def toggle_all_difficulties(btn=None):
    enable = _any_diff_disabled()
    for el in ELEMENTS:
        # enable/disable every difficulty this element supports
        for cv, diff in element_child_vars.get(el, []):
            cv.set(enable)
            logic.state["raid_settings"][el]["difficulty"][diff] = enable
        try:
            element_parent_vars.get(el).set(any(cv.get() for cv, _ in element_child_vars.get(el, [])))
            logic.state["raid_settings"][el]["enable"] = any(cv.get() for cv, _ in element_child_vars.get(el, []))
        except Exception:
            pass

    # update per-element All button labels
    for e, btn_ref in element_all_btns.items():
        try:
            if all(cv.get() for cv, _ in element_child_vars.get(e, [])):
                btn_ref.configure(text="None")
            else:
                btn_ref.configure(text="All")
        except Exception:
            pass

    try:
        config.save_prefs(logic.state)
    except Exception:
        pass

    if btn:
        _set_global_all_btn_text(btn)

# Global toggle button (placed under Raid Config)
global_all_btn = ctk.CTkButton(controls_frame, text="", width=160, command=lambda: toggle_all_difficulties(global_all_btn))
global_all_btn.pack(side="left", padx=(0,8))
_set_global_all_btn_text(global_all_btn)

# Difficulty selector + action: enable/disable selected difficulty across all elements (skip elements that don't support it)
# Keep the order defined in DIFFICULTIES so the dropdown is predictable.
diffs_for_all = [d for d in DIFFICULTIES if any(d in ELEMENT_DIFFICULTIES.get(el, DIFFICULTIES) for el in ELEMENTS if el != 'phantom')]
if diffs_for_all:
    # OptionMenu will call toggle_specific_diff when a value is selected.
    def toggle_specific_diff(selected):
        sel = selected
        # if any non-phantom element has this diff disabled, we'll enable it across non-phantom elements
        # use the correct path into logic.state['raid_settings'] when checking current values
        should_enable = any(
            not logic.state.get('raid_settings', {}).get(el, {}).get('difficulty', {}).get(sel, False)
            for el in ELEMENTS if el != 'phantom'
        )
        for el in ELEMENTS:
            if el == 'phantom':
                continue
            # if this element doesn't have that difficulty, skip
            if sel not in [d for _, d in element_child_vars.get(el, [])]:
                continue
            # find the checkbox var and set it
            for cv, d in element_child_vars.get(el, []):
                if d == sel:
                    cv.set(should_enable)
                    logic.state["raid_settings"][el]["difficulty"][d] = should_enable
                    break
            # update parent
            try:
                element_parent_vars.get(el).set(any(cv.get() for cv, _ in element_child_vars.get(el, [])))
                logic.state["raid_settings"][el]["enable"] = any(cv.get() for cv, _ in element_child_vars.get(el, []))
            except Exception:
                pass

        # update per-element All button labels
        for e, btn_ref in element_all_btns.items():
            try:
                if all(cv.get() for cv, _ in element_child_vars.get(e, [])):
                    btn_ref.configure(text="None")
                else:
                    btn_ref.configure(text="All")
            except Exception:
                pass

        try:
            config.save_prefs(logic.state)
        except Exception:
            pass

    diff_menu = ctk.CTkOptionMenu(controls_frame, values=diffs_for_all, command=toggle_specific_diff)
    try:
        diff_menu.set(diffs_for_all[0])
    except Exception:
        pass
    diff_menu.pack(side="left", padx=(0,8))

    # keep a small apply button in case user prefers clicking it
    diff_apply_btn = ctk.CTkButton(controls_frame, text="Apply Diff To All", width=160, command=lambda: toggle_specific_diff(diff_menu.get()))
    diff_apply_btn.pack(side="left")

log = ctk.CTkTextbox(app, height=100, font=("Arial", 10))
log.pack(fill="x", padx=10, pady=5)

# Start an autosave thread to persist completed_raids and raid_settings periodically.
def _autosave_loop(interval=5.0):
    while True:
        try:
            config.save_prefs(logic.state)
        except Exception:
            pass
        time.sleep(interval)

import time
threading.Thread(target=_autosave_loop, daemon=True).start()

app.mainloop()
import customtkinter as ctk
import threading, logic, os, keyboard, config

# Use configuration module (single source of truth for images and lists)
ELEMENTS = config.ELEMENTS
DIFFICULTIES = config.DIFFICULTIES
IMAGES = config.IMAGES
get_img = config.get_img

# Initialize State with defaults; override from persisted prefs when available
default_raid_settings = {
    el: {"enable": True, "difficulty": {d: True for d in DIFFICULTIES}}
    for el in ELEMENTS
}
default_completed = {el: {d: 0 for d in DIFFICULTIES} for el in ELEMENTS}
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
        for el, diffs in prefs.get("completed_raids", {}).items():
            if el in logic.state["completed_raids"]:
                logic.state["completed_raids"][el].update(diffs)
    if prefs.get("max_runs"):
        logic.state["max_runs"].update(prefs.get("max_runs", {}))
    if "rescue" in prefs:
        logic.state["rescue"] = bool(prefs.get("rescue"))
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
        # btn_raid_farm.configure(state=state_value)
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

        t = threading.Thread(target=mode_func, args=args, daemon=True)
        t.start()

        # watcher thread to re-enable buttons and clear state when the mode finishes
        def _watch():
            t.join()
            logic.state["running"] = False
            logic.state["active_sequence"] = None
            _set_mode_buttons_state("normal")
            try:
                status_lbl.configure(text="STOPPED", text_color="red")
            except Exception:
                pass

        threading.Thread(target=_watch, daemon=True).start()

def stop_bot():
    logic.state["running"] = False
    status_lbl.configure(text="STOPPED", text_color="red")

def reset_list():
    for el in ELEMENTS:
        for d in DIFFICULTIES:
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
app.geometry("280x700")
app.attributes("-topmost", True)

status_lbl = ctk.CTkLabel(app, text="IDLE", font=("Arial", 12, "bold"))
status_lbl.pack(pady=5)

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
btn_raid_farm = ctk.CTkButton(mode_frame, text="Farm Raid", width=120, state="disabled")
btn_raid_farm.grid(row=1, column=1, padx=2, pady=2)
btn_tower = ctk.CTkButton(mode_frame, text="Tower Farm", width=120, state="disabled")
btn_tower.grid(row=2, column=0, padx=2, pady=2)
btn_test = ctk.CTkButton(mode_frame, text="Test", width=120, command=lambda: start_mode(logic.combat_sequence, IMAGES, log, True))
btn_test.grid(row=2, column=1, padx=2, pady=2)

# Loop counters display
counter_frame = ctk.CTkFrame(app)
counter_frame.pack(fill="x", padx=10, pady=(0, 6))
farm_count_lbl = ctk.CTkLabel(counter_frame, text="Farm: 0", anchor="w")
farm_count_lbl.pack(side="left", padx=6)
epic_count_lbl = ctk.CTkLabel(counter_frame, text="Epic: 0", anchor="w")
epic_count_lbl.pack(side="left", padx=6)
raid_count_lbl = ctk.CTkLabel(counter_frame, text="Raid: 0", anchor="w")
raid_count_lbl.pack(side="left", padx=6)

def _update_loop_counters():
    counts = logic.state.get("loop_counts", {})
    farm_count_lbl.configure(text=f"Farm: {counts.get('farm', 0)}")
    epic_count_lbl.configure(text=f"Epic: {counts.get('epic', 0)}")
    raid_count_lbl.configure(text=f"Raid: {counts.get('raid', 0)}")
    # schedule next update
    try:
        app.after(1000, _update_loop_counters)
    except Exception:
        pass

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

    parent_cb = ctk.CTkCheckBox(scroll, text=el.upper(), font=("Arial", 10, "bold"), variable=parent_var, command=make_parent_cb())
    parent_cb.pack(anchor="w", padx=6, pady=(6,2))

    # prepare list for this element
    element_child_vars[el] = []

    for d in DIFFICULTIES:
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
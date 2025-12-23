import customtkinter as ctk
import threading, logic, os, keyboard, config

# Use configuration module (single source of truth for images and lists)
ELEMENTS = config.ELEMENTS
DIFFICULTIES = config.DIFFICULTIES
IMAGES = config.IMAGES
get_img = config.get_img

# Initialize State
logic.state["raid_settings"] = {el: {d: True for d in DIFFICULTIES} for el in ELEMENTS}
# completed_raids: counters per element/difficulty (0..N). Phantom allowed twice by default.
logic.state["completed_raids"] = {el: {d: 0 for d in DIFFICULTIES} for el in ELEMENTS}
# max_runs per element (phantom=2, others=1)
logic.state["max_runs"] = {el: (2 if el == "phantom" else 1) for el in ELEMENTS}
# RESCUE behavior (True = wait for rescue OK to be active; False = cancel on death)
logic.state["rescue"] = True
# loop counters: track how many iterations each sequence has performed
logic.state["loop_counts"] = {"farm": 0, "epic": 0, "raid": 0}
# active sequence name (or None)
logic.state["active_sequence"] = None

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
btn_raid = ctk.CTkButton(mode_frame, text="Raid Host", width=120, command=lambda: start_mode(logic.raid_host, "raid", log, ELEMENTS, IMAGES, get_img))
btn_raid.grid(row=0, column=0, padx=2, pady=2)
btn_epic = ctk.CTkButton(mode_frame, text="Epic Quest Rush", width=120, command=lambda: start_mode(logic.quest_rush, "epic", log, IMAGES))
btn_epic.grid(row=0, column=1, padx=2, pady=2)
btn_retry = ctk.CTkButton(mode_frame, text="Retry Farm", width=120, command=lambda: start_mode(logic.farm_loop, "farm", log, IMAGES))
btn_retry.grid(row=1, column=0, padx=2, pady=2)
btn_raid_farm = ctk.CTkButton(mode_frame, text="Farm Raid", width=120, state="disabled")
btn_raid_farm.grid(row=1, column=1, padx=2, pady=2)
btn_tower = ctk.CTkButton(mode_frame, text="Tower Farm", width=120, state="disabled")
btn_tower.grid(row=2, column=0, padx=2, pady=2)

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

for el in ELEMENTS:
    ctk.CTkLabel(scroll, text=el.upper(), font=("Arial", 10, "bold")).pack()
    for d in DIFFICULTIES:
        var = ctk.BooleanVar(value=True)
        cb = ctk.CTkCheckBox(scroll, text=d, font=("Arial", 9), height=16, variable=var,
                             command=lambda e=el, di=d, v=var: logic.state["raid_settings"][e].update({di: v.get()}))
        cb.select()
        cb.pack(anchor="w", padx=10)

log = ctk.CTkTextbox(app, height=100, font=("Arial", 10))
log.pack(fill="x", padx=10, pady=5)

app.mainloop()
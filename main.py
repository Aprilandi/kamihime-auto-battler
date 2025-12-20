import customtkinter as ctk
import threading, logic, os, keyboard

# --- Configuration ---
ELEMENTS = ["fire", "water", "wind", "thunder", "light", "dark", "phantom"]
DIFFICULTIES = ["guardian_plus", "guardian", "ragnarok", "ultimate", "expert", "standard"]
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def get_img(name): 
    return os.path.join(BASE_DIR, "images", f"{name}.png")

# Map all required images
IMAGES = {k: get_img(f"KHR_{k}") for k in ["ok", "down", "down_max", "attack", "retry", "return", "skip"]}
IMAGES["story_start"] = get_img("KHR_gems(start)")

# Initialize State
logic.state["raid_settings"] = {el: {d: True for d in DIFFICULTIES} for el in ELEMENTS}
logic.state["completed_raids"] = {el: {d: False for d in DIFFICULTIES} for el in ELEMENTS}

# --- Controller Functions ---
def start_mode(mode_func, *args):
    if not logic.state["RUNNING"]:
        logic.state["RUNNING"] = True
        status_lbl.configure(text="RUNNING", text_color="green")
        threading.Thread(target=mode_func, args=args, daemon=True).start()

def stop_bot():
    logic.state["RUNNING"] = False
    status_lbl.configure(text="STOPPED", text_color="red")

def reset_list():
    for el in ELEMENTS:
        for d in DIFFICULTIES:
            logic.state["completed_raids"][el][d] = False
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
ctk.CTkButton(mode_frame, text="Raid Rot", width=120, command=lambda: start_mode(logic.raid_host_rotation, log, ELEMENTS, IMAGES, get_img)).grid(row=0, column=0, padx=2, pady=2)
ctk.CTkButton(mode_frame, text="Epic Rush", width=120, command=lambda: start_mode(logic.epic_quest_rush, log, IMAGES)).grid(row=0, column=1, padx=2, pady=2)
ctk.CTkButton(mode_frame, text="Retry Farm", width=120, command=lambda: start_mode(logic.farm_loop, log, IMAGES)).grid(row=1, column=0, padx=2, pady=2)
ctk.CTkButton(mode_frame, text="Farm Raid", width=120, state="disabled").grid(row=1, column=1, padx=2, pady=2)

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
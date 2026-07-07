import tkinter as tk
import random

# ----------------------------
# CONFIG
# ----------------------------
roads = ["North", "South", "East", "West"]

traffic = {r: random.randint(5, 15) for r in roads}
waiting = {r: random.uniform(1, 5) for r in roads}

current_green = None
total_cleared = 0
cycle_count = 0

# ----------------------------
# AI DECISION (HEURISTIC)
# ----------------------------
def choose_road():
    priority = {}
    for r in roads:
        priority[r] = traffic[r] + (waiting[r] * 0.7)
    return max(priority, key=priority.get)

# ----------------------------
# SIGNAL CONTROL
# ----------------------------
def set_signal(road, color):
    canvas.itemconfig(signal_lights[road], fill=color)

def switch_signal(next_road):
    global current_green

    if current_green:
        set_signal(current_green, "yellow")
        root.after(800, lambda: set_red(next_road))
    else:
        set_red(next_road)

def set_red(next_road):
    global current_green

    if current_green:
        set_signal(current_green, "red")

    root.after(500, lambda: set_green(next_road))

def set_green(road):
    global current_green
    current_green = road
    set_signal(road, "green")

    # start processing traffic gradually
    process_green(road, duration=4)

# ----------------------------
# REALISTIC TRAFFIC FLOW
# ----------------------------
def process_green(road, duration):
    global total_cleared

    def step(t):
        global total_cleared

        if t == 0:
            return

        # cars pass gradually
        flow = min(traffic[road], random.randint(1, 3))
        traffic[road] -= flow
        total_cleared += flow

        # waiting logic
        if traffic[road] > 0:
            waiting[road] = max(waiting[road] - 0.5, 0)
        else:
            waiting[road] = 0

        # other roads accumulate waiting
        for r in roads:
            if r != road:
                waiting[r] += 1

        update_display()

        root.after(1000, lambda: step(t - 1))

    step(duration)

# ----------------------------
# MAIN SIMULATION LOOP
# ----------------------------
def update_simulation():
    global cycle_count

    cycle_count += 1

    # new incoming cars
    for r in roads:
        traffic[r] += random.randint(0, 3)

    # emergency event
    emergency = None
    if random.random() < 0.1:
        emergency = random.choice(roads)

    if emergency:
        chosen = emergency
        status_label.config(text=f"🚑 Emergency at {emergency}", fg="red")
    else:
        chosen = choose_road()
        status_label.config(text=f"AI Selected: {chosen}", fg="white")

    switch_signal(chosen)

    root.after(5000, update_simulation)

# ----------------------------
# DISPLAY UPDATE
# ----------------------------
def update_display():
    for r in roads:
        cars_visual = "🚗" * min(traffic[r], 10)

        labels[r].config(
            text=f"{r}\n{cars_visual}\nCars: {traffic[r]}\nAvg Wait: {waiting[r]:.1f}s"
        )

    avg_wait = sum(waiting.values()) / 4

    stats_label.config(
        text=f"Total Cleared: {total_cleared}   |   Avg Wait: {avg_wait:.2f}   |   Cycles: {cycle_count}"
    )

# ----------------------------
# GUI SETUP
# ----------------------------
root = tk.Tk()
root.title("🚦 AI Traffic Controller")
root.geometry("720x720")
root.configure(bg="#1e1e1e")

title = tk.Label(root, text="AI Traffic Signal Controller",
                 font=("Helvetica", 18, "bold"),
                 bg="#1e1e1e", fg="#00ffcc")
title.pack(pady=10)

canvas = tk.Canvas(root, width=500, height=500, bg="#2b2b2b", highlightthickness=0)
canvas.pack()

# intersection
canvas.create_line(250, 0, 250, 500, fill="white", width=2)
canvas.create_line(0, 250, 500, 250, fill="white", width=2)

positions = {
    "North": (250, 80),
    "South": (250, 420),
    "West": (80, 250),
    "East": (420, 250)
}

labels = {}
signal_lights = {}

for r in roads:
    x, y = positions[r]

    labels[r] = tk.Label(root,
                         text="",
                         font=("Arial", 10),
                         bg="#1e1e1e",
                         fg="white",
                         justify="center")
    labels[r].place(x=x + 90, y=y)

    signal_lights[r] = canvas.create_oval(
        x - 20, y - 20, x + 20, y + 20,
        fill="red"
    )

# status
status_label = tk.Label(root, text="", font=("Arial", 12),
                        bg="#1e1e1e", fg="white")
status_label.pack(pady=10)

# stats
stats_label = tk.Label(root, text="", font=("Arial", 12),
                       bg="#1e1e1e", fg="#00ffcc")
stats_label.pack(pady=10)

# initial display
update_display()

# start simulation
update_simulation()

root.mainloop()
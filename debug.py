import tkinter as tk
import ttkbootstrap as ttk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# --- 1. The Main Update Function (Unchanged) ---
def update_graph(*args):
    try:
        value = shared_var.get()
    except tk.TclError:
        # This handles when the box is empty (user deleted all text)
        value = 0

    ax.clear()
    ax.bar(['Value'], [value], color='#007bff', width=0.4)
    ax.set_ylim(0, 100)
    ax.set_title(f"Current Value: {value:.2f}")
    canvas.draw()


# --- NEW: 2. The Validation Function ---
def validate_input(new_value):
    """
    Validates the text input to only allow numbers between 0 and 100.
    """
    # Allow the user to clear the box (empty string)
    if new_value == "":
        return True

    try:
        # Try to convert the new value to a float
        value = float(new_value)

        # Check if the value is within the allowed range (0 to 100)
        if 0 <= value <= 100:
            return True  # Change is allowed
        else:
            return False # Change is not allowed (out of range)

    except ValueError:
        # The new value is not a valid float (e.g., "abc")
        return False # Change is not allowed


# --- 3. Setup the Application Window ---
window = ttk.Window(themename="litera")
window.title("Slider, Text, and Graph Sync (with Validation)")
window.geometry("500x500")

# --- 4. Create the Shared Variable (Unchanged) ---
shared_var = tk.DoubleVar(value=25)

# --- 5. Create the Controls ---
controls_frame = ttk.Frame(window, padding=15)
controls_frame.pack(fill='x')

# Slider (Unchanged)
ttk.Label(controls_frame, text="Slider Control").pack()
slider = ttk.Scale(
    controls_frame,
    from_=0,
    to=100,
    orient="horizontal",
    variable=shared_var
)
slider.pack(fill='x', expand=True, pady=(5, 15))

# --- NEW: Register the validation function with the window ---
# We must register the function to get a command name that Tkinter
# can use internally.
validation_wrapper = (window.register(validate_input), '%P')
# '%P' is a special code that passes the "potential new value"
# to our validate_input function.


# Spinbox (with validation added)
ttk.Label(controls_frame, text="Numeric Input (Spinbox)").pack()
spinbox = ttk.Spinbox(
    controls_frame,
    from_=0,
    to=100,
    textvariable=shared_var,
    validate="key",  # <-- Tell the widget to validate on 'key' press
    validatecommand=validation_wrapper  # <-- Set the validation function
)
spinbox.pack(fill='x', expand=True)


# --- 6. Setup the Matplotlib Graph (Unchanged) ---
graph_frame = ttk.Frame(window, padding=15)
graph_frame.pack(fill='both', expand=True)

fig = Figure(figsize=(4, 3), dpi=100)
ax = fig.add_subplot(111)

canvas = FigureCanvasTkAgg(fig, master=graph_frame)
canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

# --- 7. Link the Variable to the Graph Function (Unchanged) ---
shared_var.trace_add("write", update_graph)

# --- 8. Initial Graph Draw (Unchanged) ---
update_graph()

# --- 9. Run the App ---
window.mainloop()
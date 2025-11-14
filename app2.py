import ttkbootstrap as tb
from ttkbootstrap.constants import BOTH, TOP, LEFT, RIGHT, HORIZONTAL, YES, X, NSEW, EW

import numpy as np
from matplotlib.pyplot import rcParams, style
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

class FabryPerotApp(tb.Frame):
    # Class variables
    NM = 1e-9  # nanometer in meters
    MM = 1e-3  # millimeter in meters
    
    def __init__(self, root):
        # GUI window
        super().__init__(root)
        self.pack(fill=BOTH, expand=YES, padx=20, pady=20)
        
        # Parameters
        self.labda = tb.DoubleVar(master=self, value=550 * self.NM)   # Wavelength
        self.size  = tb.DoubleVar(master=self, value=5 * self.MM)     # Size of grid
        self.N     = tb.IntVar(master=self, value=300)                # Grid dimension
        self.f     = tb.DoubleVar(master=self, value=100 * self.MM)   # Lens focal length
        self.R     = tb.DoubleVar(master=self, value=0.85)            # Reflectivity
        self.d     = tb.DoubleVar(master=self, value=6 * self.MM)     # Separation
        self.k     = tb.DoubleVar(master=self, value=2 * np.pi / (550 * self.NM))  
        self.n     = tb.DoubleVar(master=self, value=1.0)             # Refractive index
        
        # k depends on labda -> initalise and set up trace
        self.k = tb.DoubleVar(master=self)
        self.update_k()
        
        # Pre-calculated values for interference and finesse plotting
        self.I0 = 1.0                  # Obtain initial intensity
        self.radius = None             # Radius array
        self.theta = None              # Theta array
        self.finesse = None            # Finesse value
        self.intensity = None          # Normalised intensity (all generated points have equal intensity)
        self.calculate_radius_theta()  # Calculate radius and theta arrays
        self.calculate_intensity()     # Calculate intensity distribution and finesse
        self.R_arr = (np.arange(0, 100, 1)) * 0.01 # Reflectivity array for plotting finesse graph
        self.F_arr = (np.pi * np.sqrt(self.R_arr)) / (1 - self.R_arr) # Finesse array for plotting finesse graph
        
        # Ttkbootstrap Style
        self.style = tb.Style()
        
        # Create validity functions
        R_params = ('R', 0.0, 0.99, 2) 
        n_params = ('n', 1.00, 3.00, 2)
        self.validate_R = self.create_validator_method(*R_params)
        self.validate_n = self.create_validator_method(*n_params)
        
        # Validation commands
        self.vcmd_R = root.register(self.validate_R)
        self.vcmd_n = root.register(self.validate_n)
        
        # Build UI
        self.create_header()
        self.create_main()
        self.create_graphs()
        self.create_sliders()
        
    # ---------- GUI creation ----------
        
    def create_header(self):
        # 1. Header label
        header_frame = tb.Frame(self)
        header_frame.pack(fill=X, pady=(0, 10))
        
        header_label = tb.Label(
            header_frame,
            text=f"Fabry-Perot Interferometer Simulator",
            font=("Liberation Sans", 22, "bold"),
            bootstyle="danger"
        )
        header_label.pack(side=LEFT, padx=(5, 10))
        
        # 2. Theme Selector
        themes = self.style.theme_names()
        self.theme_dropdown = tb.Combobox(
            header_frame,
            values=themes,
            state="readonly",
            bootstyle="danger",
            font=("Liberation Sans", 10)
        )
        self.theme_dropdown.pack(side=RIGHT, padx=5)
        self.theme_dropdown.set(self.style.theme.name)
        self.theme_dropdown.bind("<<ComboboxSelected>>", self.change_theme)
        
        tb.Separator(self, orient=HORIZONTAL, bootstyle="danger").pack(fill=X, pady=(0, 0))
        
    def create_main(self):
        # Main frame
        self.main_frame = tb.Frame(self)
        self.main_frame.pack(fill=BOTH, expand=YES)
        
        # 3X2 Grid Layout
        for i in range(3): self.main_frame.rowconfigure(i, weight=0)
        for j in range(2): self.main_frame.columnconfigure(j, weight=1)
        self.main_frame.rowconfigure(1, weight=1, uniform="row")  # Graph row expands
        
        # Description box
        description_box = tb.Text(
            self.main_frame,
            height=2,
            wrap="word",
            font=("Liberation Sans", 10, "bold"),
        )
        description_box.insert("end",
            "Fabry-Perot cavity is an optical resonator formed by two parallel reflecting mirrors. It is a common cavity found within lasers that enable laser light to gain energy through repeated relections. Move the sliders to adjust the parameters of the cavity and observe how the intensity distribution and finesse change accordingly."
        )
        description_box.configure(state="disabled")  # make it read-only
        description_box.grid(row=0, column=0, columnspan=3, sticky=EW, padx=10, pady=5)
        
    def create_graphs(self):
        # Creation of graph frame
        self.graph_frame = tb.Labelframe(self.main_frame, text="Interference Pattern and Finesse", bootstyle="danger")
        self.graph_frame.grid(row=1, column=0, columnspan=3, pady=0, padx=0, sticky=NSEW)
        
        # MPL customization
        rcParams['text.usetex'] = False
        rcParams['font.family'] = ['Liberation Serif', 'serif']
        rcParams['mathtext.fontset'] = 'cm'
        rcParams['figure.dpi'] = 100
        # style.use('seaborn-v0_8')
        
        # Create figure and axes
        self.fig1 = Figure(figsize=(8, 4))
        self.ax1 = self.fig1.add_subplot(121)
        self.ax2 = self.fig1.add_subplot(122)
        
        # 1. Intensity Distribution Plot
        self.ax1.set_title(r"Intensity Distribution, $\mathbf{I}$", fontsize=12)
        fringes = self.ax1.imshow(self.intensity, cmap='hot', aspect='equal')
        self.fig1.colorbar(fringes, ax=self.ax1, orientation='vertical', fraction=0.05, pad=0.05)
        
        # 2. Finesse Plot
        print(self.R_arr)
        print(self.F_arr)
        self.ax2.set_title(r"Plot of Finesse against Reflectivity $(\mathcal{F}\text{ vs }\mathcal{R})$")
        self.ax2.plot(self.R_arr, self.F_arr, color='royalblue')
        self.ax2.scatter(self.R.get(), self.finesse, color='navy', marker='^')
        self.ax2.grid(ls=':', alpha=0.8)
    
        # Set aspect ratio to make plot area square
        data_ratio = (self.F_arr.max() - self.F_arr.min()) / (self.R_arr.max() - self.R_arr.min())
        self.ax2.set_aspect(1.0 / data_ratio)
        
        # 3. Stability curve (TODO)
        
        # Add canvas to tkinter
        self.canvas = FigureCanvasTkAgg(self.fig1, master=self.graph_frame)
        self.canvas.get_tk_widget().pack(side=TOP, fill=BOTH, expand=1)
        
    def create_sliders(self):
        # Slider frame
        self.slider_frame = tb.Labelframe(self.main_frame, text="Cavity Parameters", bootstyle="info")
        self.slider_frame.grid(row=2, column=0, sticky=EW, padx=5, pady=5)
        for i in range(3): self.slider_frame.rowconfigure(i, weight=0)
        self.slider_frame.columnconfigure(0, weight=1)
        self.slider_frame.columnconfigure(1, weight=1)
        
        # 1. Reflectivity
        self.R_frame = tb.Frame(self.slider_frame)
        self.R_frame.grid(row=0, column=0, sticky=EW, padx=10, pady=5)
        for i in range(3): self.R_frame.columnconfigure(i, weight=0)
        self.R_frame.columnconfigure(1, weight=1) # only slider frame is expandable
        self.R_frame.rowconfigure(0, weight=0)
        
        label_R = tb.Label(self.R_frame,
                           text=r"Reflectivity, R:",
                           font=("Liberation Sans", 10))
        slider_R = tb.Scale(self.R_frame,
                            bootstyle="info",
                            variable=self.R,
                            from_=0.0,
                            to_=0.99,
                            orient=HORIZONTAL,
                            command=self.round_scale,)
        entry_R = tb.Entry(self.R_frame,
                           textvariable= self.R,
                           width=8,
                           font=("Liberation Sans", 10),
                           justify="center",
                           validate='key', # Validate on every key press
                           validatecommand=(self.vcmd_R, '%P')) # Pass the future value (%P) to validator
        
        label_R.grid(row=0, column=0, sticky=EW, padx=(10, 5))
        slider_R.grid(row=0, column=1, sticky=EW, padx=(10, 5))
        entry_R.grid(row=0, column=2, sticky=EW, padx=(5, 10))
        
        # 2. Refractive Index
        self.n_frame = tb.Frame(self.slider_frame)
        self.n_frame.grid(row=0, column=1, sticky=EW, padx=10, pady=5)
        for i in range(3): self.n_frame.columnconfigure(i, weight=0)
        self.n_frame.columnconfigure(1, weight=1) # only slider frame is expandable
        self.n_frame.rowconfigure(0, weight=0)
        
        label_n = tb.Label(self.n_frame,
                           text=r"Refractive Index, n:",
                           font=("Liberation Sans", 10))
        slider_n = tb.Scale(self.n_frame,
                            bootstyle="info",
                            variable=self.n,
                            from_=1.00,
                            to_=3.00,
                            orient=HORIZONTAL,
                            command=self.round_scale_n,)
        entry_n = tb.Entry(self.n_frame,
                           textvariable= self.n,
                           width=8,
                           font=("Liberation Sans", 10),
                           justify="center",
                           validate='key', # Validate on every key press
                           validatecommand=(self.vcmd_n, '%P')) # Pass the future value (%P) to validator
        
        label_n.grid(row=0, column=0, sticky=EW, padx=(10, 5))
        slider_n.grid(row=0, column=1, sticky=EW, padx=(10, 5))
        entry_n.grid(row=0, column=2, sticky=EW, padx=(5, 10))
        
        
    # ---------- Validate ----------
    
    def create_validator_method(self, field_name, min_val, max_val, decimal_places):
        """
        A factory function that generates a specialized UI input validator method.

        The generated method validates a string 's' to ensure it represents a float
        within the specified [min_val, max_val] range and does not exceed the 
        maximum number of decimal places. It also allows for 'partially' valid 
        UI inputs (e.g., "1." for a number between 1.0 and 3.0) as long as the 
        integer part is within the accepted range.

        Args:
            field_name (str): The name of the field (e.g., 'R', 'n') for documentation.
            min_val (float): The minimum valid float value (inclusive).
            max_val (float): The maximum valid float value (inclusive).
            decimal_places (int): The maximum allowed number of digits after the decimal point.

        Returns:
            function: A new validation method named 'validate_{field_name}'.
        """
        
        docstring = (
            f"Validate input {field_name} to be a float {min_val:.{decimal_places}f} "
            f"<= {field_name} <= {max_val:.{decimal_places}f} with max {decimal_places} decimal places."
        )

        # We use a nested function to create the method
        def validator(s):
            """The generated validator function."""
            # 1. Don't allow empty string
            if s == "": return True
            # 2. Partial CheckL allow "0" but reject "1", "2", etc., or "01"
            if s.isdigit() and int(s) > 0: return False # Also handles cases like "01" by converting to int(1)
            # 3. Check for numeric validity first (or a partial entry)
            try: value = float(s)
            except ValueError:
                # Not a number (e.g., "hello")
                if s.count('.') > 1 or s.startswith('-'): return False
                # If the user input is only '.' reject
                if s == ".": return False
                # If it's a failed conversion and not "."' or "0.", reject
                return False
            # 4. Check range 0. 0 < s < 0.99
            if not (min_val <= value <= max_val): return False #
            # 5. Check Decimal Limit (2 d.p.)
            if '.' in s:
                integer_part, decimal_part = s.split('.', 1)
                # Check for invalid integer part (already partially handled by 1.5, but for completeness)
                # if integer_part and int(integer_part) > 0: return False # Catches "1.0", "2.5", etc.
                # Check the length of the fractional part
                if len(decimal_part) > decimal_places: return False # Reject if there are more than 2 decimal digits (e.g., "0.123")\
                    
            # The number is valid, within range, and has an acceptable format/length.
            return True

        # Set the generated function's name and documentation
        validator.__name__ = f"validate_{field_name}"
        validator.__doc__ = docstring
        return validator
    
    def round_scale(self, value):
        """Round the scale value to 2 decimal places."""
        self.R.set(round(float(value), 2))
        
    def round_scale_n(self, value):
        
        self.n.set(round(float(value), 2))
    

    # ---------- Helpers ----------
    
    def change_theme(self, event=None):
        """Change the theme of the application."""
        new_theme = self.theme_dropdown.get()
        self.style.theme_use(new_theme)
        
    def update_k(self):
        # Automatically update k when labda changes
        lam = self.labda.get()
        self.k.set(2 * np.pi / lam)
          
    def calculate_radius_theta(self):
        # Calculate radius and theta values for each point on the grid
        step = self.size.get() / self.N.get()          # Iteration step size = 0.0167mm
        center_offset = self.size.get() / 2.0    # center middle, i.e. {x: -size/2.0 <= x <= size/2.0, or -R <= x <= R}
        indices = np.arange(0, self.N.get() + 1)   # create indices for each point on grid
        Ray_positions = indices * step     # 1D axis
        X_arr, Y_arr = np.meshgrid(Ray_positions, Ray_positions)  # 2D grid 
        
        # Calculate centered X and Y
        X = X_arr - center_offset  # moving the grid to be centered at (0,0)
        Y = Y_arr - center_offset
        
        # Assign the final results back to the instance
        self.radius = np.sqrt(X**2 + Y**2)       # obtain radius from the center of each point
        self.theta = self.radius / self.f.get()  # Small angle approximation for divergence, theta = tan(theta)
    
    def calculate_intensity(self):
        R = self.R.get()
        k = self.k.get()
        n = self.n.get()
        d = self.d.get()

        # Calculate the fineese at a certain point
        F_prime = (4.0 * R) / (1.0 - R)**2  # F'
        self.finesse = (np.pi * np.sqrt(R)) / (1 - R) 
        
        # Calculate intensity distibution I at every point on the grid
        Phi = 2 * k * n * d* np.cos(self.theta) # Phi angle (round trip)
        Inten = 1 / (1 + F_prime * np.sin(Phi/2)**2) # Assuming no loss and T + R = 1
        self.intensity = self.I0 * Inten
        
    
    
if __name__ == "__main__":
    root = tb.Window("Fabry-Perot Interferometer Simulator", "morph", resizable=(True, True))
    FabryPerotApp(root)
    root.mainloop()
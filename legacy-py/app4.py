import ttkbootstrap as tb
from ttkbootstrap.constants import BOTH, TOP, LEFT, RIGHT, HORIZONTAL, YES, X, NSEW, EW
from tkinter import TclError

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
        self.labda   = tb.DoubleVar(master=self, value=550)            # Wavelength
        self.size    = tb.DoubleVar(master=self, value=5 * self.MM)    # Size of grid
        self.N       = tb.IntVar(master=self, value=300)               # Grid dimension
        self.f       = tb.DoubleVar(master=self, value=100 * self.MM)  # Lens focal length
        self.R       = tb.DoubleVar(master=self, value=0.85)           # Reflectivity
        self.d       = tb.DoubleVar(master=self, value=5.5)            # Separation
        self.n       = tb.DoubleVar(master=self, value=1.0)            # Refractive index
        self.k       = tb.DoubleVar(master=self)                       # k depends on labda 
        self.radius1 = tb.DoubleVar(master=self)                       # Radius of curvature mirror 1
        self.update_k()
        
        # Adds trace to update graph whenever any parameter changes
        self.labda.trace_add("write", self.update_k)
        self.R.trace_add("write", self.update_graph)
        self.d.trace_add("write", self.update_graph)
        self.n.trace_add("write", self.update_graph)
        self.k.trace_add("write", self.update_graph)
        
        # Pre-calculated values for interference, finesse and stability plotting
        self.I0 = 1.0                  # Obtain initial intensity
        self.radius = None             # Radius array
        self.theta = None              # Theta array
        self.finesse = None            # Finesse value
        self.intensity = None          # Normalised intensity (all generated points have equal intensity)
        self.calculate_radius_theta()  # Calculate radius and theta arrays
        self.calculate_intensity()     # Calculate intensity distribution and finesse
        self.R_arr = (np.arange(0, 100, 1)) * 0.01 # Reflectivity array for plotting finesse graph
        self.F_arr = (np.pi * np.sqrt(self.R_arr)) / (1 - self.R_arr) # Finesse array for plotting finesse graph
        self.g_arr_left = -np.arange(-6.0, 0, 0.1)  # g1 values for stability plot
        self.g_arr_right = np.arange(0.1, 6.1, 0.1) 
        self.g_max = self.g_arr_right.max() # max g value for setting axis limits
        
        # Ttkbootstrap Style
        self.style = tb.Style()
        
        # Validation commands
        self.vcmd_R = (root.register(self.validate_R), '%P')
        self.vcmd_n = (root.register(self.validate_n), '%P')
        self.vcmd_d = (root.register(self.validate_d), '%P')
        self.vcmd_labda = (root.register(self.validate_labda), '%P')
        
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
        self.fig = Figure(figsize=(8, 4))
        self.ax1 = self.fig.add_subplot(131)
        self.ax2 = self.fig.add_subplot(132)
        self.ax3 = self.fig.add_subplot(133)
        
        # 1. Intensity Distribution Plot
        self.ax1.set_title(r"Intensity Distribution, $\mathbf{I}$", fontsize=12)
        self.fringes = self.ax1.imshow(self.intensity, cmap='hot', aspect='equal')
        self.colorbar = self.fig.colorbar(self.fringes, ax=self.ax1, orientation='vertical', fraction=0.05, pad=0.05)
        
        # 2. Finesse Plot
        self.ax2.set_title(r"Plot of Finesse against Reflectivity $(\mathcal{F}\text{ vs }\mathcal{R})$")
        (self.finesse_line,) = self.ax2.plot(self.R_arr, self.F_arr, color='royalblue')
        self.finesse_marker = self.ax2.scatter(self.R.get(), self.finesse, color='navy', marker='^', label=r'Finesse, $\mathcal{F}$')
        self.ax2.axhline(y=0.0, color='black', ls='--', lw=0.8)
        self.ax2.axvline(x=1.0, color='black', ls='--', lw=0.8)
        self.ax2.grid(ls=':', alpha=0.8)
        self.ax2.legend(loc='upper left')
        # Set aspect ratio to make plot area square
        data_ratio = (self.F_arr.max() - self.F_arr.min()) / (self.R_arr.max() - self.R_arr.min())
        self.ax2.set_aspect(1.0 / data_ratio)
        
        # 3. Stability curve (TODO)
        self.ax3.set_title("Stability Curve, ($g_2$ vs $g_1$)")
        self.ax3.plot(self.g_arr_right, 1 / self.g_arr_right, color='darkorange', label=r"$g_2 = 1 - g_1$")
        self.ax3.plot(-self.g_arr_right, - 1 / self.g_arr_right, color='darkorange')
        self.ax3.set_xlim(-self.g_max, self.g_max)
        self.ax3.set_ylim(-self.g_max, self.g_max)
        self.ax3.axhline(y=0.0, color='black', ls='--', lw=0.8)
        self.ax3.axvline(x=0.0, color='black', ls='--', lw=0.8)
        self.ax3.grid(ls=':', alpha=0.8)
        self.ax3.set_aspect('equal')
        
        # Add canvas to tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.graph_frame)
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
                            )
        entry_R = tb.Spinbox(self.R_frame,
                           textvariable= self.R,
                           width=4,
                           from_=0.0,
                           to=0.99,
                           increment=0.01,
                           format="%.2f",
                           validate="key", # validate on key press
                           validatecommand=self.vcmd_R, # Set validation function
                           )
        
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
                            )
        entry_n = tb.Spinbox(self.n_frame,
                           textvariable= self.n,
                           width=4,
                           from_=1.00,
                           to=3.00,
                           increment=0.1,
                           format="%.2f",
                           validate="key",
                           validatecommand=self.vcmd_n,
                           )
        
        label_n.grid(row=0, column=0, sticky=EW, padx=(10, 5))
        slider_n.grid(row=0, column=1, sticky=EW, padx=(10, 5))
        entry_n.grid(row=0, column=2, sticky=EW, padx=(5, 10))
        
        # 3. Separation distance
        self.d_frame = tb.Frame(self.slider_frame)
        self.d_frame.grid(row=1, column=0, sticky=EW, padx=10, pady=5)
        for i in range(3): self.d_frame.columnconfigure(i, weight=0)
        self.d_frame.columnconfigure(1, weight=1) # only slider frame is expandable
        self.d_frame.rowconfigure(0, weight=0)
        
        label_d = tb.Label(self.d_frame,
                           text=r"Separation, d (mm):",
                           font=("Liberation Sans", 10))
        slider_d = tb.Scale(self.d_frame,
                            bootstyle="info",
                            variable=self.d,
                            from_=0.00,
                            to_=10.00,
                            orient=HORIZONTAL,
                            )
        entry_d = tb.Spinbox(self.d_frame,
                           textvariable= self.d,
                           width=4,
                           from_=0,
                           to=10.00,
                           increment=0.1,
                           format="%.2f",
                           validate="key",
                           validatecommand=self.vcmd_d,
                           )
        
        label_d.grid(row=0, column=0, sticky=EW, padx=(10, 5))
        slider_d.grid(row=0, column=1, sticky=EW, padx=(10, 5))
        entry_d.grid(row=0, column=2, sticky=EW, padx=(5, 10))
        
        # 3. Wavelength distance
        self.labda_frame = tb.Frame(self.slider_frame)
        self.labda_frame.grid(row=1, column=1, sticky=EW, padx=10, pady=5)
        for i in range(3): self.labda_frame.columnconfigure(i, weight=0)
        self.labda_frame.columnconfigure(1, weight=1) # only slider frame is expandable
        self.labda_frame.rowconfigure(0, weight=0)
        
        label_labda = tb.Label(self.labda_frame,
                           text=r"Wavelength, λ (nm):",
                           font=("Liberation Sans", 10))
        slider_labda = tb.Scale(self.labda_frame,
                            bootstyle="info",
                            variable=self.labda,
                            from_=10,
                            to_=1000,
                            orient=HORIZONTAL,
                            )
        entry_labda = tb.Spinbox(self.labda_frame,
                           textvariable= self.labda,
                           width=4,
                           from_=10,
                           to=1000,
                           increment=10,
                           format="%.0f",
                           validate="key",
                           validatecommand=self.vcmd_labda,
                           )
        
        label_labda.grid(row=0, column=0, sticky=EW, padx=(10, 5))
        slider_labda.grid(row=0, column=1, sticky=EW, padx=(10, 5))
        entry_labda.grid(row=0, column=2, sticky=EW, padx=(5, 10))
        
    # ---------- Validate ----------
    
    def validate_R(self, R):
        """Validate Reflectivity input R to be a float 0.0 <= R <= 0.99 with max 2 decimal places."""
        if R == "": return True #  Don't allow empty box (empty string)
        try: # Try convert value to float
            value = float(R)
            # Check if 0 <= R <= 0.99, and max 2 d.p.
            if 0 <= value <= 0.99 and len(R.split('.')[-1]) <= 2: return True 
            else: return False
        except ValueError: # The new value is not a valid float (e.g., "abc")
            return False 
    
    # TODO: Modularize this function.
    # - Float version: Have decimal and 2 d.p. 
    # - Int version: Have no decimal
    # - Perhaps some logi like: if 0 < x < 1000 then auto-int and if 0 < x < 10.00 then float with 2 d.p.
    # - Still need take into account units i.e. nm, mm, etc. 
    # - Right now validation is within textbox, so its usage might be clunky. Update validation to calculation, if invalid values then just use the previous valid value.
    # Rushing so no time now.
    def validate_n(self, n):
        """Validate Refractive Index input n to be a float 1.00 <= n <= 3.00 with max 2 decimal places."""
        if n == "": return True 
        try: 
            value = float(n)
            if 1.00 <= value <= 3.00 and len(n.split('.')[-1]) <= 2: return True 
            else: return False
        except ValueError:
            return False 
    
    def validate_d(self, d):
        """Validate Refractive Index input d to be an float 0.0 <= d <= 10.00mm with max 2 decimal places."""
        if d == "": return True 
        try: 
            value = float(d)
            # Check if 1.00 <= n <= 3.00, and max 2 d.p.
            if 0.0 <= value <= 10.00 and len(d.split('.')[-1]) <= 2: return True 
            else: return False
        except ValueError:
            return False 
    
    def validate_labda(self, labda):
        """Validate wavelength input: integer only, 10 <= λ <= 1000 (nm)."""
        if labda == "": return False
        if '.' in labda: return False  # No decimals allowed
        try: 
            value = int(labda)
            if 10 <= value <= 1000 and len(labda) <= 4: return True 
            else: return False
        except ValueError:
            return False 
    
    # ---------- Update dependent variables ----------
    
    def update_k(self, *args):
        ''' Automatically update k when labda changes'''
        self.k.set(2 * np.pi / (self.labda.get() * self.NM))
    
    
    # ---------- Update graphs ----------
    
    def update_graph(self, *args):
        """
        Recalculate all values and update both graphs.
        """
        try:
            # Recalculate intensity distribution and finesse
            self.calculate_intensity()
            
            # 1. Update Intensity Distribution Plot
            self.fringes.set_data(self.intensity) # never update colorbar because causes issues near R = 0.
            
            # 2. Update Finesse Plot
            self.finesse_marker.set_offsets([self.R.get(), self.finesse]) # update scatter point
            
            self.canvas.draw_idle()  
        except TclError: pass

    def calculate_intensity(self):
        """
        Calculate intensity distribution and finesse based on current parameters.
        """
        R = self.R.get()
        k = self.k.get()
        n = self.n.get()
        d = self.d.get() * self.MM

        # Calculate the fineese at a certain point
        F_prime = (4.0 * R) / (1.0 - R)**2  # F'
        self.finesse = (np.pi * np.sqrt(R)) / (1 - R) 
        
        # Calculate intensity distibution I at every point on the grid
        Phi = 2 * k * n * d* np.cos(self.theta) # Phi angle (round trip)
        Inten = 1 / (1 + F_prime * np.sin(Phi/2)**2) # Assuming no loss and T + R = 1
        self.intensity = self.I0 * Inten


    # ---------- Helpers ----------
    
    def change_theme(self, event=None):
        """Change the theme of the application."""
        new_theme = self.theme_dropdown.get()
        self.style.theme_use(new_theme)
          
    def calculate_radius_theta(self):
        '''Calculate radius and theta values for each point on the grid'''
        
        step = self.size.get() / self.N.get()    # Iteration step size = 0.0167mm
        center_offset = self.size.get() / 2.0    # center middle, i.e. {x: -size/2.0 <= x <= size/2.0, or -R <= x <= R}
        indices = np.arange(0, self.N.get() + 1) # create indices for each point on grid
        Ray_positions = indices * step           # 1D axis
        X_arr, Y_arr = np.meshgrid(Ray_positions, Ray_positions)  # 2D grid 
        
        # Calculate centered X and Y
        X = X_arr - center_offset  # moving the grid to be centered at (0,0)
        Y = Y_arr - center_offset
        
        # Assign the final results back to the instance
        self.radius = np.sqrt(X**2 + Y**2)       # obtain radius from the center of each point
        self.theta = self.radius / self.f.get()  # Small angle approximation for divergence, theta = tan(theta)
        
    
    
if __name__ == "__main__":
    root = tb.Window("Fabry-Perot Interferometer Simulator", "morph", resizable=(True, True))
    FabryPerotApp(root)
    root.mainloop()
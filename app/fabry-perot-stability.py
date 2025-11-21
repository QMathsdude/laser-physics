import ttkbootstrap as tb
from ttkbootstrap.constants import BOTH, TOP, LEFT, RIGHT, HORIZONTAL, YES, X, Y, NSEW, EW
from tkinter import TclError

import numpy as np
import matplotlib.patches as patches
from matplotlib.path import Path
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.pyplot import rcParams, style

class FabryPerotApp(tb.Frame):
    # Class variables
    NM = 1e-9  # nanometer in meters
    MM = 1e-3  # millimeter in meters
    
    def __init__(self, root):
        # GUI window
        super().__init__(root)
        self.pack(fill=BOTH, expand=YES, padx=20, pady=20)
        
        # Parameters
        self.labda = tb.DoubleVar(master=self, value=550)            # Wavelength
        self.size  = tb.DoubleVar(master=self, value=5 * self.MM)    # Size of grid
        self.N     = tb.IntVar(master=self, value=300)               # Grid dimension
        self.f     = tb.DoubleVar(master=self, value=100 * self.MM)  # Lens focal length
        self.R     = tb.DoubleVar(master=self, value=0.85)           # Reflectivity
        self.d     = tb.DoubleVar(master=self, value=5.5)            # Separation
        self.n     = tb.DoubleVar(master=self, value=1.0)            # Refractive index
        self.k     = tb.DoubleVar(master=self)                       # k depends on labda 
        self.curv1 = tb.DoubleVar(master=self, value=5)              # Radius of curvature mirror 1
        self.curv2 = tb.DoubleVar(master=self, value=5)              # Radius of curvature mirror 1
        self.g1    = tb.DoubleVar(master=self)                       # g1 depends on curv1
        self.g2    = tb.DoubleVar(master=self)                       # g2 stability parameter
        self.update_k()
        self.update_g1g2()
        
        # Adds trace to update graph whenever any parameter changes
        self.labda.trace_add("write", self.update_k)
        self.k.trace_add("write", self.update_graph_intensity)
        self.R.trace_add("write", self.update_graph_intensity_and_finesse)
        self.d.trace_add("write", self.update_graph_intensity)
        self.d.trace_add("write", self.update_g1g2)
        self.d.trace_add("write", self.update_graph_stability)
        self.d.trace_add("write", self.update_cavity_diagram)
        self.n.trace_add("write", self.update_graph_intensity)
        self.curv1.trace_add("write", self.update_g1g2)
        self.curv2.trace_add("write", self.update_g1g2)
        self.curv1.trace_add("write", self.update_cavity_diagram)
        self.curv2.trace_add("write", self.update_cavity_diagram)
        self.g1.trace_add("write", self.update_graph_stability)
        self.g2.trace_add("write", self.update_graph_stability)
        
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
        self.g_arr_left = np.arange(-6.0, 0, 0.1)  # g1 values for stability plot
        self.g_arr_right = np.arange(0.1, 6.1, 0.1) 
        self.g_max = self.g_arr_right.max() # max g value for setting axis limits
        
        # Validation commands
        self.vcmd_R = (root.register(self.validate_R), '%P')
        self.vcmd_n = (root.register(self.validate_n), '%P')
        self.vcmd_d = (root.register(self.validate_d), '%P')
        self.vcmd_labda = (root.register(self.validate_labda), '%P')
        self.vcmd_curv1 = (root.register(self.validate_curv1), '%P')
        self.vcmd_curv2 = (root.register(self.validate_curv2), '%P')
        
        # Ttkbootstrap Style
        self.style = tb.Style()
        
        # Build UI
        self.create_header()
        self.create_main()
        self.create_graphs()
        self.create_sliders()
        self.create_graph_cavity()
        
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
        self.graph_frame.grid(row=1, column=0, columnspan=2, pady=10, padx=10, sticky=NSEW)
        
        # MPL customization
        rcParams['text.usetex'] = False
        rcParams['font.family'] = ['Liberation Serif', 'serif']
        rcParams['mathtext.fontset'] = 'cm'
        rcParams['figure.dpi'] = 100
        
        # Create figure and axes
        self.fig = Figure(figsize=(15, 5))
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
        self.finesse_marker = self.ax2.scatter(self.R.get(), self.finesse, color='navy', marker='^', label=rf'Finesse, $\mathcal{{F}}={self.finesse:.2f}$')
        self.ax2.axhline(y=0.0, color='black', ls='--', lw=0.8)
        self.ax2.axvline(x=1.0, color='black', ls='--', lw=0.8)
        self.ax2.grid(ls=':', alpha=0.8)
        self.ax2.legend(loc='upper left')
        # Set aspect ratio to make plot area square
        data_ratio = (self.F_arr.max() - self.F_arr.min()) / (self.R_arr.max() - self.R_arr.min())
        self.ax2.set_aspect(1.0 / data_ratio)
        
        # 3. Stability curve 
        self.ax3.set_title("Stability Curve, ($g_2$ vs $g_1$)")
        self.ax3.fill_between(self.g_arr_right, 1 / self.g_arr_right, color="seagreen", edgecolor="seagreen", alpha=0.3, linewidth=1.5, zorder=0) # fill are beneath curve
        self.ax3.fill_between(self.g_arr_left, 1 / self.g_arr_left, color="royalblue", edgecolor="royalblue", alpha=0.3, linewidth=1.5, zorder=0)
        self.g1g2_marker = self.ax3.scatter(self.g1.get(), self.g2.get(), color='crimson', marker='o', s=10, label=rf'($g_1,g_2$)$=$({self.g1.get():.2f}, {self.g2.get():.2f})', zorder=1)
        self.ax3.set_xlim(-self.g_max, self.g_max)
        self.ax3.set_ylim(-self.g_max, self.g_max)
        self.ax3.axhline(y=0.0, color='black', ls='--', lw=0.8)
        self.ax3.axvline(x=0.0, color='black', ls='--', lw=0.8)
        self.ax3.grid(ls=':', alpha=0.8)
        self.ax3.legend(loc='upper left')
        self.ax3.set_aspect('equal')
        
        # Add canvas to tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.graph_frame)
        self.canvas.get_tk_widget().pack(side=TOP, fill=BOTH, expand=1)
        
    def create_sliders(self):
        # Slider frame
        self.slider_frame = tb.Labelframe(self.main_frame, text="Cavity Parameters", bootstyle="info")
        self.slider_frame.grid(row=2, column=0, sticky=NSEW, padx=10, pady=10)
        for i in range(7): self.slider_frame.rowconfigure(i, weight=1)
        self.slider_frame.columnconfigure(0, weight=1)
        
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
        self.n_frame.grid(row=1, column=0, sticky=EW, padx=10, pady=5)
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
        self.d_frame.grid(row=2, column=0, sticky=EW, padx=10, pady=5)
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
        
        # 4. Wavelength distance
        self.labda_frame = tb.Frame(self.slider_frame)
        self.labda_frame.grid(row=3, column=0, sticky=EW, padx=10, pady=5)
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
        
        # 5. Curvature 1 
        self.curv1_frame = tb.Frame(self.slider_frame)
        self.curv1_frame.grid(row=4, column=0, sticky=EW, padx=10, pady=5)
        for i in range(3): self.curv1_frame.columnconfigure(i, weight=0)
        self.curv1_frame.columnconfigure(1, weight=1) # only slider frame is expandable
        self.curv1_frame.rowconfigure(0, weight=0)
        
        label_curv1 = tb.Label(self.curv1_frame,
                           text=r"Mirror 1 Curvature, (mm):",
                           font=("Liberation Sans", 10))
        slider_curv1 = tb.Scale(self.curv1_frame,
                            bootstyle="info",
                            variable=self.curv1,
                            from_=1.1,
                            to_=100,
                            orient=HORIZONTAL,
                            )
        entry_curv1 = tb.Spinbox(self.curv1_frame,
                           textvariable= self.curv1,
                           width=4,
                           from_=1.1,
                           to=100,
                           increment=0.1,
                           format="%.2f",
                           validate="key",
                           validatecommand=self.vcmd_curv1,
                           )
        
        label_curv1.grid(row=0, column=0, sticky=EW, padx=(10, 5))
        slider_curv1.grid(row=0, column=1, sticky=EW, padx=(10, 5))
        entry_curv1.grid(row=0, column=2, sticky=EW, padx=(5, 10))
        
        # 6. Curvature 2 
        self.curv2_frame = tb.Frame(self.slider_frame)
        self.curv2_frame.grid(row=5, column=0, sticky=EW, padx=10, pady=5)
        for i in range(3): self.curv2_frame.columnconfigure(i, weight=0)
        self.curv2_frame.columnconfigure(1, weight=1) # only slider frame is expandable
        self.curv2_frame.rowconfigure(0, weight=0)
        
        label_curv2 = tb.Label(self.curv2_frame,
                           text=r"Mirror 2 Curvature, (mm):",
                           font=("Liberation Sans", 10))
        slider_curv2 = tb.Scale(self.curv2_frame,
                            bootstyle="info",
                            variable=self.curv2,
                            from_=1.1,
                            to_=100,
                            orient=HORIZONTAL,
                            )
        entry_curv2 = tb.Spinbox(self.curv2_frame,
                           textvariable= self.curv2,
                           width=4,
                           from_=1.1,
                           to=100,
                           increment=0.1,
                           format="%.2f",
                           validate="key",
                           validatecommand=self.vcmd_curv2,
                           )
        
        label_curv2.grid(row=0, column=0, sticky=EW, padx=(10, 5))
        slider_curv2.grid(row=0, column=1, sticky=EW, padx=(10, 5))
        entry_curv2.grid(row=0, column=2, sticky=EW, padx=(5, 10))
        
        # 7. Reset Button
        self.reset_button_frame = tb.Frame(self.slider_frame)
        self.reset_button_frame.grid(row=6, column=0, sticky=EW, padx=10, pady=5)
        reset_btn = tb.Button(
            self.reset_button_frame,
            text="Reset",
            bootstyle="info",
            command=self.reset_parameters,
            )
        reset_btn.pack(fill=BOTH)
    
    def create_graph_cavity(self):
        # Creation of graph frame
        self.cavity_frame = tb.Labelframe(self.main_frame, text="Laser Cavity (Mirrors Only)", bootstyle="success")
        self.cavity_frame.grid(row=2, column=1, pady=10, padx=10, sticky=NSEW)
        
        # Create figure and axes
        self.fig2 = Figure(figsize=(6, 4))
        self.ax4 = self.fig2.add_subplot(111)
        
        # 4. Cavity diagram
        self.ax4.set_title("Cavity with Mirror Diagram")
        self.ax4.set_xlabel("Distance (mm)")
        self.ax4.set_ylabel("Height (mm)")
        lens_patch_left, lens_patch_right = self.create_lenses_patches(self.curv1.get(), self.curv2.get(), self.d.get())
        self.ax4.add_patch(lens_patch_left)
        self.ax4.add_patch(lens_patch_right)
        self.ax4.axhline(y=0.0, color='black', ls='--', lw=0.8)
        self.ax4.set_xlim(-2,13)
        self.ax4.set_ylim(-1.5, 1.5)
        # Focal points
        d = self.d.get()
        f1, f2 = self.curv1.get() * 0.5, self.curv2.get() * 0.5
        self.f1_point = self.ax4.scatter(f1, 0, color='blue', marker='o', s=15, alpha=0.8, label=rf'Focal Point $f_1={f1}$')
        self.f2_point = self.ax4.scatter(d - f2, 0, color='red', marker='o', s=15, alpha=0.8, label=rf'Focal Point $f_2={f2}$')
        self.ax4.legend(loc='upper right')
        # Ray diagrams
        initial_1 = [0.5, 0.7]
        final_1 = [f1, 0]
        point_1 = self.find_ray(initial_1, final_1, x=100)
        (self.horizontal_ray1,) = self.ax4.plot([0.5, d - 0.5], [0.7, 0.7], color='blue', ls='-', lw=1.0, alpha=0.5)
        (self.travelling_ray1,) = self.ax4.plot([0.5, 100], [0.7, point_1], color='blue', ls='-', lw=1.0, alpha=0.5)
        initial_2 = [d - f2, 0]
        final_2 = [d - 0.5, -0.7]
        point_2 = self.find_ray(initial_2, final_2, x=-100)
        (self.horizontal_ray2,) = self.ax4.plot([0.5, d - 0.5], [-0.7, -0.7], color='red', ls='-', lw=1.0, alpha=0.5)
        (self.travelling_ray2,) = self.ax4.plot([-100, d - 0.5], [point_2, -0.7], color='red', ls='-', lw=1.0, alpha=0.5)
        
        # Add canvas to tkinter
        self.canvas2 = FigureCanvasTkAgg(self.fig2, master=self.cavity_frame)
        self.canvas2.get_tk_widget().pack(side=TOP, fill=BOTH, expand=1)
        
        
    
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
            # Check if 1.00 <= d <= 3.00, and max 2 d.p.
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
        
    def validate_curv1(self, curv1):
        """Validate Refractive Index input curv1 to be an float 1.00 <= curv1 <= 20.00mm with max 2 decimal places."""
        if curv1 == "": return True 
        try: 
            value = float(curv1)
            # Check if 1.00 <= curv1 <= 20.00, and max 2 d.p.
            if 1.10 <= value <= 20.00 and len(curv1.split('.')[-1]) <= 2: return True 
            else: return False
        except ValueError:
            return False 
        
    def validate_curv2(self, curv2):
        """Validate Refractive Index input curv2 to be an float 1.00 <= curv2 <= 20.00mm with max 2 decimal places."""
        if curv2 == "": return True 
        try: 
            value = float(curv2)
            # Check if 1.00 <= curv2 <= 20.00, and max 2 d.p.
            if 1.10 <= value <= 20.00 and len(curv2.split('.')[-1]) <= 2: return True 
            else: return False
        except ValueError:
            return False 
    
    # ---------- Update dependent variables ----------
    
    def update_k(self, *args):
        ''' Automatically update k when labda changes'''
        self.k.set(2 * np.pi / (self.labda.get() * self.NM))
        
    def update_g1g2(self, *args):
        ''' Automatically update g1 and g2 when curv1, curv2 or d changes'''
        R1, R2 = self.curv1.get(), self.curv2.get() # Radius of curvature
        d, n = self.d.get() , self.n.get()         # Separation and refractive index
        self.g1.set(1 - ( d / R1))
        self.g2.set(1 - ( d / R2))
    
    # ---------- Update graphs ----------
    
    def update_graph_intensity_and_finesse(self, *args):
        """
        Recalculate all values and update both graphs.
        """
        try:
            self.update_graph_intensity()
            self.update_graph_finesse()
        except TclError: pass
        
    def update_graph_intensity(self, *args):
        """Recalculates"""
        try: 
            self.calculate_intensity()
            self.fringes.set_data(self.intensity)
            
            self.canvas.draw_idle()
        except TclError: pass
        
    def update_graph_finesse(self, *args):
        """Recalculates"""
        try:
            self.finesse_marker.set_offsets([self.R.get(), self.finesse]) # update scatter point
            new_label_finnesse = rf'Finesse, $\mathcal{{F}}={self.finesse:.2f}$' # update legend
            self.finesse_marker.set_label(new_label_finnesse)
            self.ax2.legend(loc='upper left')
            
            self.canvas.draw_idle()  
        except TclError: pass

    def update_graph_stability(self, *args):
        """Recalculates"""
        try:
            self.g1g2_marker.set_offsets([self.g1.get(), self.g2.get()]) # update scatter point
            new_label_g1g2 = rf'($g_1,g_2$)$=$({self.g1.get():.2f}, {self.g2.get():.2f})' # update legend
            self.g1g2_marker.set_label(new_label_g1g2)
            self.ax3.legend(loc='upper left')
            
            self.canvas.draw_idle()
        except TclError: pass

    def update_cavity_diagram(self, *args):
        '''Recalculates '''
        try:
            # Update lens patches
            d = self.d.get()
            curv1, curv2 = self.curv1.get(), self.curv2.get()
            f1, f2 = curv1 * 0.5, curv2 * 0.5
            lens_patch_left, lens_patch_right = self.create_lenses_patches(curv1, curv2, d)
            for patch in self.ax4.patches:
                patch.remove()  # Remove existing patches
            self.ax4.add_patch(lens_patch_left)
            self.ax4.add_patch(lens_patch_right)
            
            # Update focal points
            self.f1_point.set_offsets([curv1 * 0.5, 0])
            self.f2_point.set_offsets([d - (curv2 * 0.5), 0])
            new_label_f1 = rf'Focal Point $f_1={f1:.2f}$' # update legend
            self.f1_point.set_label(new_label_f1)
            new_label_f2 = rf'Focal Point $f_2={d-f2:.2f}$' # update legend
            self.f2_point.set_label(new_label_f2)
            self.ax4.legend(loc='upper right')
            
            # Update ray diagrams
            initial_1 = [0.5, 0.7]
            final_1 = [f1, 0]
            point_1 = self.find_ray(initial_1, final_1, x=100)
            self.horizontal_ray1.set_data([0.5, d - 0.5], [0.7, 0.7])
            self.travelling_ray1.set_data([0.5, 100], [0.7, point_1])
            
            initial_2 = [d - f2, 0]
            final_2 = [d - 0.5, -0.7]
            point_2 = self.find_ray(initial_2, final_2, x=-100)
            self.horizontal_ray2.set_data([0.5, d - 0.5], [-0.7, -0.7])
            self.travelling_ray2.set_data([-100, d - 0.5], [point_2, -0.7])
            
            self.canvas2.draw_idle()
        except TclError: pass

    # ---------- Helpers ----------
    
    def change_theme(self, event=None):
        """Change the theme of the application."""
        new_theme = self.theme_dropdown.get()
        self.style.theme_use(new_theme)
          
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

    def calculate_radius_theta(self):
        '''
        Calculate radius and theta values for each point on the grid
        '''
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
        
    def create_lenses_patches(self, curv1, curv2, d):
        '''
        Create lens patches for the cavity diagram.
        '''
        # Normalise to [-1, 1] as quadratic bezier constant
        C1 = -1 + (curv1 - 1.0) * (2 / (100 - 1.0))
        C2 = -1 + (curv2 - 1.0) * (2 / (100 - 1.0))
        
        # Creating lenses
        # Note: Lens always have width = 1 and height = 2 of 
        verts_left = [ 
            (0, -1.0),   # P1: Start bottom left
            (1.0, -1.0), # P2: bottom right
            (0+C1, 0.0), # C1: control
            (1.0, 1.0),  # P3: top right
            (0, 1.0),    # P4: top left
            (0, -1.0),   # P1 again for close
        ]
        
        verts_right = [
            (1.0+d-1, -1.0), # P1: Start bottom right
            (0+d-1, -1.0),   # P2: Move bottom left
            (d+1-C2-1, 0.0), # C1: control
            (0+d-1, 1.0),    # P3: top right
            (1.0+d-1, 1.0),  # P4: top left
            (1.0+d-1, -1.0), # P1: Start bottom right
        ]
        
        codes = [
            Path.MOVETO,   # P1
            Path.LINETO,   # P2 horizontal
            Path.CURVE3,   # C1 control
            Path.CURVE3,   # P3 end point of curve
            Path.LINETO,   # P4 horizontal
            Path.CLOSEPOLY # back to P1
        ]
        
        path_left = Path(verts_left, codes) # Use first 4 vertices
        path_right = Path(verts_right, codes) # Use first 4 vertices
        
        lens_patch_left = patches.PathPatch(
            path_left,
            facecolor='royalblue',
            edgecolor='navy',
            lw=1,
            alpha=0.4
        )
        lens_patch_right = patches.PathPatch(
            path_right,
            facecolor='lightcoral',
            edgecolor='red',
            lw=1,
            alpha=0.4
        )
        
        return lens_patch_left, lens_patch_right
    
    def reset_parameters(self):
        """Reset all parameters to default values."""
        self.labda.set(550)
        self.R.set(0.85)
        self.d.set(5.5)
        self.n.set(1.0)
        self.curv1.set(5)
        self.curv2.set(5)
            
    def find_ray(self, initial, final, x=100):
        """Calculate gradient for focal length lines in cavity diagram."""
        x1, y1 = initial
        x2, y2 = final
        grad = (y2 - y1) / (x2 - x1)
        point = grad * x + y1
        return point
        
            
if __name__ == "__main__":
    root = tb.Window("Fabry-Perot Interferometer Simulator", "morph", resizable=(True, True))
    FabryPerotApp(root)
    root.mainloop()
# Laser Simulations
This repository consists of projects I have made for Laser Physics. Currently, it consists of two projects :
- Fabry-Pero Interferometer
- Self Healing Properties of Airy Beam

## Fabry-Perot Interferometer 

The following simulation was made using `Python` and `Ttkbootstrap`. This GUI application allows users to investigate how finesse, $\mathcal{F}$ of a laser changes when modifying the reflectivity of mirror, $R$. Moreover, users can also modify other parameters such as refractive index cavity medium $n$, separation between cavity mirrors $d$, wavelength of light $\lambda$, and the curvature of mirror, $R_1$ and $R_2$. Plots of stability curve and also the actual cavity diagram are also provided, which enable users to easily visualise and understand what eactly happens within the laser cavity.

https://github.com/user-attachments/assets/96eaa38e-df3f-46f6-81ac-a275aa1c551e

### 🛠️ Introduction

This was the first simulation created while I was taking Modern Optics and Laser Physics course as the group assignment. 

### 🚀 Setting-Up Environment

In order to run this application using Python, perform the following steps after cloning the environment :

1. Open terminal, and change to project directory — `cd laser-physics`.
2. Create new environment with installed dependencies — `conda env create -f environment.yml`.
3. Activate the environment — `conda activate laser`.
4. Change to app directory — `cd app`.
5. Use python to run the file — `python fabry-perot.py`.

### 📦 Packaging into Executable

Packaging the simulation into a single executable file has been tested for both Linux and Windows, peform the following :

1. While in double-p environment, change to app directory — `cd app`.
2. Package the py file alongside it's dependencies — `pyinstaller double-pendulum.spec`.

### ⚠️ Known Issues
The following are some know issues within the application :

1. Rescaling on low resolution computers (namely, monitors with low vertical height) squeezes the application somewhat tightly.

<p style="text-align: center;">【<b>I make no promises to fix these issues in the future</b>】</p>

---

## Self-Healing Properties of Airy Beam

The simulations below used the [LightPipes](https://opticspy.github.io/lightpipes/) library for optical field simulations. LightPipes provides powerful tools for modeling the propagation of light, interference, diffraction, and other wave-optics phenomena, making it especially useful for experiments such as interferometry and beam shaping. 

https://github.com/user-attachments/assets/c63416cf-cb95-4a47-bab9-21d15e8805c9

<p align="center">
  Figure 1: Self-Healing Properties of Airy Beam
</p>

### 🛠️ Introduction

This was the second simulation created while I was taking Modern Optics and Laser Physics course as the group assignment. 

### 🚀 Setting-Up Environment

In order to run this application using Jupyter Notebook, perform the following steps after cloning the environment :

1. Open terminal, and change to project directory — `cd laser-physics`.
2. Create new environment with installed dependencies — `conda env create -f environment.yml`.
3. Activate the environment — `conda activate laser`.
4. Change to app directory — `cd legacy-airy`.
5. Run — `self-healing-airy-beam.ipynb`.

## 📄 License

[MIT License](LICENSE)

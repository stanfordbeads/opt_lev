## load a file containing values of the voltage vs beta and remake it, assuming
## that the force scales like the square of the voltage

import numpy as np
import matplotlib.pyplot as plt

#freqs = [5,7,9,13,17,23,29,37,43,51,57,69,71,111,]
#freqs = np.linspace(5,150,10)


Fsamp = 5000.
cutsamp = 2000
Npoints = 250000
drive_elec1 = 3
drive_elec2 = 5
drive_voltage = 2.
freq = 147.


######################################


dt = 1. / Fsamp
t = np.linspace(0, (Npoints-1) * dt, Npoints)

drive_arr1 = drive_voltage * np.sin(2 * np.pi * freq * t)
drive_arr2 = drive_voltage * np.sin(2 * np.pi * freq * t + np.pi / 2)



out_arr = []
for ind in range(8):
    if ind == drive_elec1:
        out_arr.append(drive_arr1)
    elif ind == drive_elec2:
        out_arr.append(drive_arr2)
    else:
        out_arr.append(np.zeros(Npoints))

out_arr = np.array(out_arr)
#print out_arr.shape

np.savetxt(r'C:\GitHub\opt_lev\labview\DAQ_settings\spin_bead_147_Hz.txt', out_arr, fmt='%.5e', delimiter=",")
    

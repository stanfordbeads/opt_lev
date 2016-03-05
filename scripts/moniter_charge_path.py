## load all files in a directory and plot the correlation of the resonse
## with the drive signal versus time

import numpy as np
import matplotlib, calendar
import matplotlib.pyplot as plt
import os, re, time, glob
import bead_util as bu
import scipy.signal as sp
import scipy.optimize as opt
import cPickle as pickle

path = r"C:\Data\20160227\Bead1\chareglp_course"
ts = 10.

fdrive = 41.
make_plot = True
reprocess_file = True

data_columns = [0, 1] ## column to calculate the correlation against
drive_column = 12 ## column containing drive signal




def getdata(fname, maxv):

	print "Processing ", fname
        dat, attribs, cf = bu.getdata(os.path.join(path, fname))

        if( len(attribs) > 0 ):
            fsamp = attribs["Fsamp"]

        xdat = dat[:,data_columns[1]]

        lentrace = len(xdat)
        ## zero pad one cycle
        corr_full = bu.corr_func( dat[:,drive_column], xdat, fsamp, fdrive)

        #plt.figure()
        #plt.plot( xdat)
        #plt.plot(dat[:,drive_column])
        #plt.show()
        

        return corr_full[0], np.max(corr_full)


best_phase = None
corr_data = []

if make_plot:
    fig0 = plt.figure()
    


if reprocess_file:

    init_list = glob.glob(path + "\*.h5")
    files = sorted(init_list, key = bu.find_str)
    print files
    for f in files[::1]:
        try:    
                cfile = f
                corr = getdata( cfile, 10. )
                corr_data.append(corr )
        except:
                print "uninformative error message"
    
cal = 2.3e-14/(0.01*1.6e-19*2525)
tarr = np.linspace(0, 10*len(np.array(corr_data)[:, 0]), len(np.array(corr_data)[:, 0]))
       
if make_plot:
        plt.plot(tarr, np.array(corr_data)[:, 0]*cal,'o', markersize = 4, label = "Response at Max Phase")
        plt.plot(tarr, np.array(corr_data)[:, 1]*cal,'o',markersize = 4, label = "Response at 0 deg Phase")
        plt.xlabel("Time [s]")
        plt.ylabel("Bead charge [e]")
        plt.legend()
        plt.show()

 

    

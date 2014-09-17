
## load all files in a directory and plot the correlation of the resonse
## with the drive signal versus time

import numpy as np
import matplotlib, calendar
import matplotlib.pyplot as plt
import os, re, glob
import bead_util as bu
import scipy.signal as sp
import scipy.optimize as opt
import cPickle as pickle


path = "/data/20140724/Bead3/no_charge_chirp"
cal_path = ["/data/20140724/Bead3/chargelp_fine_calib", "/data/20140724/Bead3/recharge"]
noise_path = "" 
single_charge_fnums = [13, 14]
ref_2mbar = "/data/20140724/Bead3/2mbar_zcool_50mV_40Hz.h5"
scale_fac = 1./470.

# path = "/data/20140728/Bead5/no_charge_chirp"
# cal_path = "/data/20140728/Bead5/chargelp_chirp_calib"
# noise_path = "" 
# single_charge_fnums = [11,28]
# ref_2mbar = "/data/20140728/Bead5/2mbar_zcool_50mV_40Hz.h5"
# scale_fac = 1.
# cut_off_val = 130

# path = "/data/20140729/Bead4/no_charge_chirp"
# cal_path = ["/data/20140729/Bead4/chargelp_cal", "/data/20140729/Bead4/recharge"]
# noise_path = "/data/20140729/Bead4/chargelp_noise"
# single_charge_fnums = [0, 50]
# ref_2mbar = "/data/20140729/Bead4/2mbar_zcool_50mV_40Hz.h5"
# scale_fac = -1.

# path = "/data/20140801/Bead6/no_charge"
# cal_path = ["/data/20140801/Bead6/chargelp_cal", "/data/20140801/Bead6/recharge"]
# noise_path = "/data/20140801/Bead6/plates_terminated"
# single_charge_fnums = [0, 60]
# ref_2mbar = "/data/20140801/Bead6/2mbar_zcool_50mV_41Hz.h5"
# scale_fac = -1./111 * 1.03

# path = "/data/20140803/Bead8/no_charge"
# cal_path = ["/data/20140803/Bead8/chargelp_cal", "/data/20140803/Bead8/recharge"]
# noise_path = "/data/20140803/Bead8/plates_terminated"
# single_charge_fnums = [0, 60]
# ref_2mbar = "/data/20140803/Bead8/2mbar_zcool_50mV_41Hz.h5"
# scale_fac = 1/355.

# path = "/data/20140804/Bead1/no_charge"
# cal_path = ["/data/20140804/Bead1/chargelp_cal", "/data/20140804/Bead1/recharge"]
# noise_path = "/data/20140804/Bead1/plates_terminated"
# single_charge_fnums = [0,34]
# ref_2mbar = "/data/20140804/Bead1/2mbar_zcool_50mV_41Hz.h5"
# scale_fac = 1.

# path = "/data/20140805/Bead1/no_charge"
# cal_path = ["/data/20140805/Bead1/chargelp_cal", "/data/20140805/Bead1/recharge"]
# noise_path = "/data/20140805/Bead1/plates_terminated"
# single_charge_fnums = [12,22]
# ref_2mbar = "/data/20140805/Bead1/2mbar_zcool_50mV_2500Hz.h5"
# scale_fac = -1.

# path = "/data/20140806/Bead1/no_charge"
# cal_path = ["/data/20140806/Bead1/chargelp_cal", "/data/20140806/Bead1/recharge"]
# noise_path = "/data/20140806/Bead1/plates_terminated"
# single_charge_fnums = [52, 62]
# ref_2mbar = "/data/20140806/Bead1/2mbar_zcool_50mV_41Hz.h5"
# scale_fac = -1./80

# path = "/data/20140807/Bead1/no_charge"
# cal_path = ["/data/20140807/Bead1/chargelp_cal", "/data/20140807/Bead1/recharge"]
# noise_path = "/data/20140807/Bead1/plates_terminated"
# single_charge_fnums = [24, 130]
# ref_2mbar = "/data/20140807/Bead1/2mbar_zcool_50mV_41Hz.h5"
# scale_fac = -1.

# path = "/data/20140808/Bead7/no_charge"
# cal_path = ["/data/20140808/Bead7/chargelp_cal", "/data/20140808/Bead7/recharge"]
# noise_path = "/data/20140808/Bead7/plates_terminated"
# single_charge_fnums = [36, 102]
# ref_2mbar = ""
# scale_fac = -1.

# path = "/data/20140811/Bead4/chargelp_cal"
# cal_path = ["/data/20140808/Bead7/chargelp_cal", "/data/20140808/Bead7/recharge"]
# noise_path = "/data/20140808/Bead7/plates_terminated"
# single_charge_fnums = [36, 102]
# ref_2mbar = ""
# scale_fac = 1.

filestr = "RANDFREQ"

## path to save plots and processed files (make it if it doesn't exist)
outpath = "/home/dcmoore/analysis" + path[5:]
if( not os.path.isdir( outpath ) ):
    os.makedirs(outpath)

reprocessfile = True
plot_angle = False
plot_phase = False
remove_laser_noise = False
remove_outliers = True
plot_flashes = False
ref_file = 0 ## index of file to calculate angle and phase for

file_start = 0

scale_file = 1.

## These gains should always be left as one as long as
## the voltage_div setting was set correctly when taking data
## Otherwise, they are the ratio of the true gain to the gain
## that was set
amp_gain = 1. ## gain to use for files in path
amp_gain_cal = 1.  ## gain to use for files in cal_path

fsamp = 5000.
fdrive = 41.
fref = 1027
NFFT = 2**14
phaselen = int(fsamp/fdrive) #number of samples used to find phase
plot_scale = 1. ## scaling of corr coeff to units of electrons
plot_offset = 1.
laser_column = 3

def getdata(fname, gain, resp_fit, resp_dat, orth_pars):

	print "Processing ", fname
        dat, attribs, cf = bu.getdata(os.path.join(path, fname))

        ## make sure file opened correctly
        if( len(dat) == 0 ):
            return {}

        if( len(attribs) > 0 ):
            fsamp = attribs["Fsamp"]
            drive_amplitude = attribs["drive_amplitude"]

        ## now get the drive recorded by the other computer (if available)
        fname_drive = fname.replace("/data", "/data_slave")
        fname_drive = fname_drive.replace(".h5", "_drive.h5")            

        ## gain is not set in the drive file, so use the one from the data file
        if( os.path.isfile( fname_drive ) ):
            drive_dat, drive_attribs, drive_cf = bu.getdata(fname_drive, gain_error=attribs['volt_div']*gain)
        else:
            drive_dat = None

        ## is this a calibration file?
        cdir,_ = os.path.split(fname)
        if( isinstance(cal_path, list ) ):
            is_cal = False
            for cstr in cal_path:
                if( cdir == cstr ):
                    is_cal = True
                    break
        else:
            is_cal = cdir == cal_path

        ## now insert the drive column from the drive file (ignore for calibrations)
        if( not is_cal and drive_dat != None):
            dat[:,-1] = drive_dat[:,-1]

        if( "Hz" in filestr):
            curr_drive_freq = float(re.findall("\d+", filestr)[0])
        else:
            curr_drive_freq = "chirp"
        
        drive_amp,_ = bu.get_drive_amp( dat[:,bu.drive_column], fsamp, drive_freq = curr_drive_freq, make_plot = False)


        ## now double check that the rescaled drive amp seems reasonable
        ## and warn the user if not
        curr_gain = bu.gain_fac( attribs['volt_div']*gain )
        offset_frac = np.abs( drive_amp/(curr_gain * attribs['drive_amplitude']/1e3 )-1.0)
        if( curr_gain != 1.0 and offset_frac > 0.1):
            print "Warning, voltage_div setting doesn't appear to match the expected gain for ", fname
            print "Measured voltage was: ", drive_amp, ", expected was: ", curr_gain * attribs['drive_amplitude']/1e3
            print "Skipping this point"
            return {}

        xdat, ydat, zdat = dat[:,bu.data_columns[0]], dat[:,bu.data_columns[1]], dat[:,bu.data_columns[2]]

        if( orth_pars ):
            xdat, ydat, zdat = bu.orthogonalize( xdat, ydat, zdat,
                                                 orth_pars[0], orth_pars[1], orth_pars[2] )

        ## make correlation in time domain with predicted drive (fixed to known phase)
        corr_fit = bu.corr_func(np.fft.irfft(resp_fit), xdat, fsamp, fsamp)[0]/drive_amp
        corr_dat = bu.corr_func(np.fft.irfft(resp_dat), xdat, fsamp, fsamp)[0]/drive_amp

        ## calculate optimal filter
        vt = np.fft.rfft( xdat )
        st = resp_fit
        ## throw out some frequencies
        Jfreq = np.fft.rfftfreq( len(xdat), 1./fsamp )
        ##J[Jfreq > 100] = 1e10        
        ## only count frequencies containing the drive
        ##J[ np.logical_not(bu.get_drive_bins( Jfreq )) ] = 1e10
        of_fit = np.real(np.sum( np.conj(st) * vt / J)/np.sum( np.abs(st)**2/J ))/drive_amp

        st = resp_dat
        of_dat = np.real(np.sum( np.conj(st) * vt / J)/np.sum( np.abs(st)**2/J ))/drive_amp

        ## now y and z directions as well
        vt = np.fft.rfft( ydat )
        st = resp_fit
        of_fit_y = np.real(np.sum( np.conj(st) * vt / J)/np.sum( np.abs(st)**2/J ))/drive_amp
        st = resp_dat
        of_dat_y = np.real(np.sum( np.conj(st) * vt / J)/np.sum( np.abs(st)**2/J ))/drive_amp

        vt = np.fft.rfft( zdat )
        st = resp_fit
        of_fit_z = np.real(np.sum( np.conj(st) * vt / J)/np.sum( np.abs(st)**2/J ))/drive_amp
        st = resp_dat
        of_dat_z = np.real(np.sum( np.conj(st) * vt / J)/np.sum( np.abs(st)**2/J ))/drive_amp

        # plt.figure()
        # plt.plot( xdat )
        # plt.plot( of_fit*drive_amp*np.fft.irfft(resp_fit) )
        # plt.show()

        # _,drive_pred = bu.get_drive_amp( dat[:,bu.drive_column], fsamp )
        # xpsd, df = matplotlib.mlab.psd( xdat, NFFT=2**20, Fs=fsamp )
        # dpsd, df = matplotlib.mlab.psd( drive_pred/drive_amp * of_dat, NFFT=2**20, Fs=fsamp )

        # plt.figure()
        # plt.loglog( df, xpsd)
        # plt.loglog( Jfreq, np.abs(resp_fit/drive_amp * of_dat)**2 )
        # plt.show()

        ctime = attribs["time"]

        ## make a dictionary containing the various calculations
        out_dict = {"corr": [corr_fit, corr_dat],
                    "of": [of_fit, of_dat, of_fit_y, of_dat_y, of_fit_z, of_dat_z],
                    "temps": attribs["temps"],
                    "time": bu.labview_time_to_datetime(ctime),
                    "num_flashes": attribs["num_flashes"],
                    "is_cal": is_cal,
                    "drive_amp": drive_amp}

        cf.close()
        return out_dict

if reprocessfile:

  init_list = glob.glob(path + "/*"+filestr+"*.h5")
  files = sorted(init_list, key = bu.find_str)

  if(cal_path):
      if( isinstance( cal_path, str ) ):
          cal_list = glob.glob(cal_path + "/*"+filestr+"*.h5")
          cal_files = sorted( cal_list, key = bu.find_str )
      elif( isinstance( cal_path, list ) ):
          cal_files=[]
          for cstr in cal_path:
              cal_list = glob.glob(cstr + "/*"+filestr+"*.h5")
              cal_files += sorted( cal_list, key = bu.find_str )
      files = zip(cal_files[:-1],np.zeros(len(cal_files[:-1]))+amp_gain_cal) \
              + zip(files[:-1],np.zeros(len(files[:-1]))+amp_gain)

      ## make the transfer function from the calibration files with one
      ## charge
      tf_fit, tf_dat, orth_pars = bu.get_avg_trans_func( cal_files, single_charge_fnums )

  else:
      print "Warning, no calibration path defined.  Assuming default response function"
      
      files = zip(files[:-1],np.zeros(len(files[:-1]))+amp_gain)      

  ## get the noise from the 0 charge files at 10V      
  if( noise_path):
      noise_list = glob.glob(noise_path + "/*"+filestr+"*.h5")
      noise_files = sorted( noise_list, key = bu.find_str )
      J, Jy, Jz = bu.get_avg_noise( noise_files, 0, orth_pars, make_plot = False )
  else:
      J, Jy, Jz = bu.get_avg_noise( cal_files, single_charge_fnums[1]+1, orth_pars, make_plot = False )

  corrs_dict = {}
  for f,gain in files[file_start:]:
    curr_dict = getdata(f, gain, tf_fit, tf_dat, orth_pars)

    for k in curr_dict.keys():
        if k in corrs_dict:
            corrs_dict[k].append( curr_dict[k] )
        else:
            corrs_dict[k] = [curr_dict[k],]
    
  corrs_dict["weight_func_fit"] = tf_fit/J
  corrs_dict["weight_func_dat"] = tf_dat/J

  of = open(os.path.join(outpath, "processed.pkl"), "wb")
  pickle.dump( corrs_dict, of )
  of.close()
else:
  of = open(os.path.join(outpath, "processed.pkl"), "rb")
  corrs_dict = pickle.load( of )
  of.close()

    
## first plot the variation versus time

## apply rough calibration to the various metrics by 
## assuming ~1 charge on the calibration points
is_cal = np.array(corrs_dict["is_cal"])

good_cal = is_cal
sfac_rel = [ 1./np.median(np.array(corrs_dict["corr"])[good_cal,0]),
             1./np.median(np.array(corrs_dict["corr"])[good_cal,1]), 
             1./np.median(np.array(corrs_dict["of"])[good_cal,0]), 
             1./np.median(np.array(corrs_dict["of"])[good_cal,1]) ]



dates = matplotlib.dates.date2num(corrs_dict["time"])
corr_fit = np.array(corrs_dict["corr"])[:,0]*scale_fac*sfac_rel[0]
corr_dat = np.array(corrs_dict["corr"])[:,1]*scale_fac*sfac_rel[1]
of_fit = np.array(corrs_dict["of"])[:,0]*scale_fac*sfac_rel[2]
of_dat = np.array(corrs_dict["of"])[:,1]*scale_fac*sfac_rel[3]
temp1 = np.array(corrs_dict["temps"])[:,0]
temp2 = np.array(corrs_dict["temps"])[:,1]
num_flashes = np.array(corrs_dict["num_flashes"])
drive_amp = np.array(corrs_dict["drive_amp"])

fig = plt.figure() 
plt.plot_date(dates, corr_fit, 'r.', label="Corr from fit")
plt.plot_date(dates, corr_dat, 'g.', label="Corr from dat")
plt.plot_date(dates, of_fit, 'k.', label="OF from fit")
plt.plot_date(dates, of_dat, 'b.', label="OF from dat")
plt.legend(numpoints=1)
plt.xlabel("Time")
plt.ylabel("Correlation with drive [e]")
plt.title("Comparison of correlation calculations")

## check if cut off is defined, for runs where the bead fell out
try:
    amp_for_plotting = of_fit[:cut_off_val]
    dates = dates[:cut_off_val]
    is_cal = is_cal[:cut_off_val]
except:  
    amp_for_plotting = of_fit
  
cweight = corrs_dict["weight_func_fit"]

## fit the data
def gauss_fun(x, A, mu, sig):
    return A*np.exp( -(x-mu)**2/(2*sig**2) )

of_data_xyz = np.array(corrs_dict["of"])[:,0::2]*scale_fac*sfac_rel[2]
## get the ratio of the amplitudes in each direction from the noise data
if( noise_path):
    noise_list = glob.glob(noise_path + "/*"+filestr+"*.h5")
    noise_files = sorted( noise_list, key = bu.find_str )
    amp_corr = bu.get_noise_direction_ratio( noise_files, np.abs(cweight) )
else:
    amp_corr = [1.0, 1.0, 1.0]

for i in range(3):
    of_data_xyz[:,i] /= amp_corr[i]

#amp_for_plotting = np.sqrt(np.sum(of_data_xyz**2, axis=1 ) )

## first figure out the windows for each charge
plt.figure()
plt.plot(of_data_xyz[:,0], '.')
window_bnds = np.argwhere(np.abs(np.diff( of_data_xyz[:,0] ) ) > 0.5)
yy = plt.ylim()
window_bnds = np.append(window_bnds, len(of_data_xyz[:,0]) )
window_bnds = np.append([0], window_bnds)
for i,w in enumerate(window_bnds[:-1]):
    plt.plot( [w, w], yy, 'k')

def run_mc( ang_dat, nmc=1e5 ):
    rand_x = ang_dat[0,0] + np.random.randn(nmc)*ang_dat[0,1]
    rand_y = ang_dat[1,0] + np.random.randn(nmc)*ang_dat[1,1]
    rand_z = ang_dat[2,0] + np.random.randn(nmc)*ang_dat[2,1]

    ## first get the sin of the angle
    cang = np.arccos(rand_x/np.sqrt(rand_x**2 + rand_y**2 + rand_z**2))
    #cang = np.arctan2( np.sqrt( rand_y**2+rand_z**2 ), rand_x )
    #cang[ rand_y < 0] *= -1.
    
    mu = np.mean( cang )
    std = np.std( cang )
    return mu, std

#ang_data_0 =  np.mean(of_data_xyz[good_points,0]/np.sqrt( np.sum( of_data_xyz[good_points,:]**2, axis=1) ))
of_data_xyz = np.hstack( (of_data_xyz, np.transpose([np.sqrt(np.sum(of_data_xyz**2,axis=1))])) )
out_arr = []
for j, w in enumerate(window_bnds[:-1]):
    good_points = np.zeros_like(of_data_xyz[:,0]) > 1
    good_points[window_bnds[j]:window_bnds[j+1]] = True
    if(np.sum(good_points) < 5 ):
        continue
    curr_dat = []
    for i in range(4):
        mu, std = bu.iterstat( of_data_xyz[good_points,i] )

        nbins = 20
        while( True ):
            fit_range = [mu-5*std, mu+5*std] 
            ha, ba = np.histogram( of_data_xyz[good_points,i], bins=nbins, range=[fit_range[0], fit_range[1]])

            if np.sum(ha > 0 ) < 6 or np.max( ha) > 20:
                std /= 2.0
            else:
                break
            
            if( std < 1e-4 ): break

        bac = ba[:-1] + np.diff(ba)/2.0
        #plt.errorbar(bac, ha, yerr=np.sqrt(ha), fmt='.')
        try:
            bp, bc = opt.curve_fit(gauss_fun, bac, ha, p0=[np.sum(ha)/(nbins*np.sqrt(6*std)), mu, std])
        except:
            bp = [0,0,0]
            bc = 0.
        xx = np.linspace(fit_range[0], fit_range[1], 1e3)
        #plt.plot(xx, gauss_fun(xx, bp[0], bp[1], bp[2]), 'r')
        gpts = np.sum( good_points)
        if( not isinstance(bc, float) ):
            curr_dat.append([bp[1], np.sqrt( np.abs(bc[1,1])) ])
        else:
            curr_dat.append([mu, std/np.sqrt( gpts ) ])



    curr_dat = np.array(curr_dat)
    ## now calculate the angle
    curr_ang, curr_ang_err = run_mc(curr_dat)
    
    out_arr.append( [gpts, curr_dat[0,0], curr_ang, curr_ang_err] )
    
print out_arr
np.save(os.path.join(outpath, "resid_data.npy"), out_arr)

#fig = plt.figure()
#plt.plot_date(dates, ang_data_xyz, '.')

## now do absolute calibration as well
if(ref_2mbar):
    abs_cal, fit_bp, fit_cov = bu.get_calibration(ref_2mbar, [1,200],
                                                  make_plot=True,
                                                  NFFT=2**14,
                                                  exclude_peaks=False)

    print "Abs cal [V/m]: ", abs_cal

    scale_fac_abs = (bu.bead_mass*(2*np.pi*fit_bp[1])**2)*bu.plate_sep/(bu.e_charge) * abs_cal
    corr_abs = np.array(corrs_dict["of"])[:,0]*scale_fac_abs
    fig2 = plt.figure()
    plt.plot(dates, amp_for_plotting, 'r.', label="Step calibration")
    #plt.plot(dates, corr_abs, 'k.', label="Absolute calibration")
    plt.legend(numpoints=1)
    plt.xlabel("Time")
    plt.ylabel("Correlation with drive [e]")
    plt.title("Comparison of calibrations")


plt.close('all')

fig1 = plt.figure() 
plt.subplot(1,2,1)

resid_data = amp_for_plotting-np.round(amp_for_plotting)
plt.plot_date(dates, resid_data, 'r.', markersize=2, label="Max corr")
## set limits at +/- 5 sigma
cmu, cstd = np.median(resid_data), np.std(resid_data)
yy = plt.ylim([cmu-5*cstd, cmu+5*cstd])
plt.ylim(yy)
plt.xlabel("Time")
plt.ylabel("Residual to nearest integer charge [$e$]")
ax = plt.gca()

hh, be = np.histogram( resid_data, bins = np.max([30, len(resid_data)/50]), range=yy )
bc = be[:-1]+np.diff(be)/2.0

amp0 = np.sum(hh)/np.sqrt(2*np.pi*cstd)
bp, bcov = opt.curve_fit( gauss_fun, bc, hh, p0=[amp0, cmu, cstd] )

if( remove_outliers ):

    ## throw out any bad times before doing the fit
    time_window = 5 ## mins
    nsig = 5
    bad_points = np.argwhere(np.abs(resid_data > bp[1]+nsig*bp[2]))
    pts_to_use = np.logical_not(is_cal)
    #pts_to_use = np.logical_and(np.logical_not(is_cal), bu.inrange(drive_amp, 5, 2000))
    print np.sum(pts_to_use)
    for p in bad_points:
        pts_to_use[ np.abs(dates - dates[p]) < time_window/(24.*60.)] = False

    plt.plot_date(dates[pts_to_use], resid_data[pts_to_use], 'k.', markersize=2, label="Max corr")
    cmu, cstd = np.median(resid_data[pts_to_use]), np.std(resid_data[pts_to_use])
    hh, be = np.histogram( resid_data[pts_to_use], bins=50, range=[cmu-5*cstd, cmu+5*cstd] )
    bc = be[:-1]+np.diff(be)/2.0
    amp0 = np.sum(hh)/np.sqrt(2*np.pi*cstd)
    bp, bcov = opt.curve_fit( gauss_fun, bc, hh, p0=[amp0, cmu, cstd] )
    plt.ylim( [cmu-5*cstd, cmu+5*cstd] )


plt.subplot(1,2,2)
ax2 = plt.gca()
ax2.yaxis.set_visible(False)
ax.set_position(matplotlib.transforms.Bbox(np.array([[0.125,0.1],[0.675,0.9]])))
ax2.set_position(matplotlib.transforms.Bbox(np.array([[0.725,0.1],[0.9,0.9]])))

yy = [cmu-5*cstd, cmu+5*cstd]
xx = np.linspace(yy[0], yy[1], 1e3)
plt.errorbar( hh, bc, xerr=np.sqrt(hh), yerr=0, fmt='k.', linewidth=1.5 )
plt.plot( gauss_fun(xx, bp[0], bp[1], bp[2]), xx, 'r', linewidth=1.5, label="$\mu$ = %.3e $\pm$ %.3e $e$"%(bp[1], np.sqrt(bcov[1,1])))
plt.legend()
plt.ylim( [cmu-5*cstd, cmu+5*cstd] )
#plt.ylim(yy)

plt.xlabel("Counts")

np.save(os.path.join(outpath, "resid_data_0e.npy"), [bp[1], np.sqrt(bcov[1,1])])

plt.figure()
#plt.plot_date( dates, amp_for_plotting, '.', markersize=1)
plt.plot( amp_for_plotting, '.', markersize=1)

plt.show()


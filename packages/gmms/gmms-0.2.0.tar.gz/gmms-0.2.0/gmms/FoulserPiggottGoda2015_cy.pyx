""" Ground motion model by Faulser-Piggott and Goda (2015) for Ia and CAV. 
"""

from shapely.geometry import Point
from shapely.geometry import Polygon
import numpy as np
cimport numpy as np
cimport cython
from libc.math cimport pow, sqrt, log, fmax

__author__ = 'A. Renmin Pretell Ductram'

#===================================================================================================
# Arc location
#===================================================================================================
@cython.boundscheck(False)
@cython.wraparound(False)
@cython.nonecheck(False)
@cython.cdivision(True)
cdef get_arc_loc(double hypo_lat,double hypo_lon):
    
    cdef double[:] poly_lon = np.array([147.0777923, 150.1155649,153.715191,149.8283212,114.0231292,121.3748207,
                                        125.7824353,127.1678612,129.7868373,129.8424854,130.5254764,130.9213526,
                                        130.9667855,131.5974992,131.7631234,132.0491377,137.2849268,138.1554838,
                                        138.3532866,138.9145833,139.5017784,139.7139014,139.9509957,140.3328265,
                140.4766196,140.8062929,140.8994366,140.9138458,140.9319158,141.0155034,141.0471475,141.0655764,
                141.164649,141.1113146,141.2269001,141.4874362,141.7938255,142.097868,142.3806856,142.7870678,
                143.0922912,143.5186725,143.9243411,144.1509098,144.3736708,145.2255306,145.8458331,146.5058656,
                147.0804238,147.0777923])
    
    cdef double[:] poly_lat = np.array([44.54928084,45.94757299,48.41645565,50.1970842,44.06079242,26.99925918,
                                        26.15702014,27.20073396,29.87585092,29.9897597,30.96859286,31.977676,
                                        32.7566247,33.26338696,33.40597398,34.64826527,35.90546185,36.30798631,
                                        36.4376539,36.45663279,36.58422099,36.7567189,37.0497487,37.53364026,
                37.91648909,38.74967624,39.03135054,39.20718386,39.29564995,39.56379066,39.89703578,40.37143077,
                40.59907844,40.73468826,41.45114975,43.03663806,43.02558574,43.0232214,43.10818802,43.13640394,
                43.18293361,43.24243307,43.33814962,43.37320904,43.49759091,43.73033601,43.93993635,44.25417222,
                44.55763457,44.54928084])

    hypo_loc     = Point(hypo_lon,hypo_lat)
    poly_backarc = [(x,y) for x,y in zip(poly_lon,poly_lat)]
    poly_backarc = Polygon(poly_backarc)

    if poly_backarc.contains(hypo_loc):
        return 0,1
    else:
        return 1,0

#===================================================================================================
# Ia/CAV: phi
#===================================================================================================
@cython.boundscheck(False)
@cython.wraparound(False)
@cython.nonecheck(False)
@cython.cdivision(True)
cdef get_phi(int IM):
    if IM == 0:
        return 1.035
    elif IM == 1:
        return 0.49

#===================================================================================================
# Ia/CAV: tau
#===================================================================================================
@cython.boundscheck(False)
@cython.wraparound(False)
@cython.nonecheck(False)
@cython.cdivision(True)
cdef get_tau(int IM):
    if IM == 0:
        return 0.9015
    elif IM == 1:
        return 0.4114

#===================================================================================================
# Ia/CAV: mu
#===================================================================================================
@cython.boundscheck(False)
@cython.wraparound(False)
@cython.nonecheck(False)
@cython.cdivision(True)
cdef get_mu(int IM,double M,double hypo_depth,double R_rup,double Vs30,int ffore,int fback,int fins,int fint,int fnm,int frv):
    
    cdef int e_1 = 0
    cdef double c_0, c_1, c_2, c_3, c_4, c_5, c_6, c_7, c_8, c_9, c_10, c_11, nu_1
    cdef double lnI_ref
    cdef double mu
    
    if IM == 1:
        c_0  =  2.643261
        c_1  =  1.60688
        c_2  = -0.754765
        c_3  = -0.072283
        c_4  = 12.626135
        c_5  =  0.003811
        c_6  = -0.00059
        c_7  = -0.002767
        c_8  =  0.877694
        c_9  =  0.822831
        c_10 =  0.286527
        c_11 =  0.918286
        nu_1 = -0.65776
    elif IM == 0:
        c_0  =  3.056224
        c_1  =  2.639315
        c_2  = -2.352244
        c_3  = -0.080591
        c_4  = 12.682338
        c_5  =  0.009653
        c_6  = -0.001436
        c_7  = -0.006374
        c_8  =  1.869827
        c_9  =  1.639023
        c_10 =  0.573052
        c_11 =  1.856785
        nu_1 = -1.030608
    
    # Reference GM intensity
    lnI_ref  = c_0+c_1*(M-5)+(c_2+c_3*M)*log(sqrt(pow(R_rup,2)+pow(c_4,2)))
    lnI_ref += c_5*fmax(hypo_depth-30,0)+(c_6*ffore+c_7*fback)*R_rup
    lnI_ref += c_8*fins+c_9*fint+c_10*frv+c_11*fnm
    
    # Compute mean
    return lnI_ref + e_1 + nu_1*log(Vs30/1100.)

#===================================================================================================
# Ia/CAV: mu, phi, tau
#===================================================================================================
@cython.boundscheck(False)
@cython.wraparound(False)
@cython.nonecheck(False)
@cython.cdivision(True)
def FoulserPiggottGoda2015(int IM,double M,double hypo_lat,double hypo_lon,double hypo_depth,
                              double[:] R_rup,double[:] Vs30,int fins,int fint,int fnm,int frv):

    """
    Parameter
    =========
    IM: 0 for Ia, and 1 for CAV.
    M: Earthquake magnitude.
    hypo_lat: Hypocenter latitude
    hypo_lon: Hypocenter longitude
    hypo_depth: Hypocentral depth
    R_rup: Rupture distance in km.
    Vs30: Site Vs30.
    fins: 1 if inslab event, else 0.
    fint: 0 if interface or crustal 	event, else 1.
    fnm: '1' for normal/normal-oblique fault, '0' otherwise.
    frv: '1' for reverse/reverse-oblique fault, '0' otherwise.

    Returns
    =======
    mean, phi, tau for the selected IM.
    """

    cdef int N_sites = len(R_rup)
    cdef double[:] mu_im = np.zeros(N_sites, dtype='float64')
    cdef double[:] phi_im = np.zeros(N_sites, dtype='float64')
    cdef double[:] tau_im = np.zeros(N_sites, dtype='float64')
    cdef int ffore, fback
    cdef int i

    [ffore,fback] = get_arc_loc(hypo_lat,hypo_lon)

    for i in range(N_sites):
        mu_im[i]  = get_mu(IM,M,hypo_depth,R_rup[i],Vs30[i],ffore,fback,fins,fint,fnm,frv)
        phi_im[i] = get_phi(IM)
        tau_im[i] = get_tau(IM)

    return np.asarray(mu_im),np.asarray(phi_im),np.asarray(tau_im)

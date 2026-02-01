""" Ground motion model by Campbell and Bozorgnia (2010) for CAVgm and CAVdp.
"""

import numpy as np
cimport numpy as np
cimport cython
from libc.math cimport pow, sqrt, log, exp, fmin, fmax

__author__ = 'A. Renmin Pretell Ductram'

#===================================================================================================
# PGA [0]/CAVgm [1]
#===================================================================================================
# Note: PGA implemented for Vs30=1100. only. Need to work on "f_site" term for lower Vs30 
@cython.boundscheck(False)
@cython.wraparound(False)
@cython.nonecheck(False)
@cython.cdivision(True)
def get_mu(int IM, double M,double fdip,double fZtor,double R_JB,double R_rup,double R_x,double Vs30,double Z2p5,int fnm,int frv):
    
    cdef double val
    cdef double f_mag, f_dis, f_flt_Z, f_hng_R, f_hng_M, f_site, f_sed, mu
    cdef double c_0, c_1, c_2, c_3, c_4, c_5, c_6, c_7, c_8, c_9, c_10, c_11, c_12, k_1, k_2, k_3, c, n

    if IM == 0: # PGA
        c_0  = -1.715
        c_1  =  0.500
        c_2  = -0.530
        c_3  = -0.262
        c_4  = -2.118
        c_5  =  0.170
        c_6  =  5.600
        c_7  =  0.280
        c_8  = -0.120
        c_9  =  0.490
        c_10 =  1.058
        c_11 =  0.040
        c_12 =  0.610
        k_1  =  865.0
        k_2  = -1.186
        k_3  =  1.839
        c    =  1.880
        n    =  1.180
    elif IM == 1: # CAVgm
        c_0  = -4.354
        c_1  =  0.942
        c_2  = -0.178
        c_3  = -0.346
        c_4  = -1.309
        c_5  =  0.087
        c_6  =  7.240
        c_7  =  0.111
        c_8  = -0.108
        c_9  =  0.362
        c_10 =  2.549
        c_11 =  0.090
        c_12 =  1.277
        k_1  =  400.0
        k_2  = -2.690
        k_3  =  1.000
        c    =  1.880
        n    =  1.180

    # Magnitude term
    if M <= 5.5:
        f_mag = c_0+c_1*M
    elif M <= 6.5:
        f_mag = c_0+c_1*M+c_2*(M-5.5)
    else:
        f_mag = c_0+c_1*M+c_2*(M-5.5)+c_3*(M-6.5)

    # Geometric attenuation term
    f_dis = (c_4+c_5*M)*log(sqrt(pow(R_rup,2)+pow(c_6,2)))

    # Style of faulting term
    f_flt_Z = fmin(fZtor,1)
    f_flt   = c_7*frv*f_flt_Z+c_8*fnm
    
    # Hanging wall term
    f_hng_R = 1
    if R_JB > 0:
        val = R_rup*1
        if fZtor < 1:
            val = fmax(R_rup,sqrt(pow(R_JB,2)+1))
        f_hng_R = (val-R_JB)/val

    f_hng_M = 1
    if M <= 6.:
        f_hng_M = 0
    elif M <= 6.5:
        f_hng_M = 2*(M-6.)
        
    if fZtor >= 20:
        f_hng_Z = 0
    else:
        f_hng_Z = (20-fZtor)/20

    if fdip <= 70:
        f_hng_dip = 1
    else:
        f_hng_dip = (90-fdip)/20
    
    f_hng = c_9*f_hng_R*f_hng_M*f_hng_Z*f_hng_dip

    # Shallow site response term
    if IM == 0: # PGA 
        f_site = (c_10+k_2*n)*log(Vs30/k_1)

    elif IM == 1: # CAVgm
        A_1100 = get_mu(0,M,fdip,fZtor,R_JB,R_rup,R_x,1100.,Z2p5,fnm,frv)
        A_1100 = exp(A_1100)

        if Vs30 < k_1:
            f_site = c_10*log(Vs30/k_1)+k_2*(log(A_1100+c*pow(Vs30/k_1,n))-log(A_1100+c))
        elif Vs30 < 1100.:
            f_site = (c_10+k_2*n)*log(Vs30/k_1)
        else:
            f_site = (c_10+k_2*n)*log(1100./k_1)

    # Basin site response term
    if Z2p5 <= 1:
        f_sed = c_11*(Z2p5-1)
    elif Z2p5 <= 3:
        f_sed = 0
    else:
        f_sed = c_12*k_3*exp(-0.75)*(1-exp(-0.25*(Z2p5-3)))

    # Compute mean
    return f_mag+f_dis+f_flt+f_hng+f_site+f_sed

#===================================================================================================
# Get CB10 alpha
#===================================================================================================
@cython.boundscheck(False)
@cython.wraparound(False)
@cython.nonecheck(False)
@cython.cdivision(True)
def get_alpha(double Vs30,double A_1100):
    
    cdef double k_1 =  400.0
    cdef double k_2 = -2.690
    cdef double c   =  1.880
    cdef double n   =  1.180

    if Vs30 < k_1:
        return k_2*A_1100*(pow(A_1100+c*pow(Vs30/k_1,n),-1)-pow(A_1100+c,-1))
    else:
        return 0

#===================================================================================================
# CAVgm: phi
#===================================================================================================
@cython.boundscheck(False)
@cython.wraparound(False)
@cython.nonecheck(False)
@cython.cdivision(True) 
def get_phi(double alpha):

    cdef double phi_lnAF_PGA   = 0.3
    cdef double phi_lnPGA      = 0.478
    cdef double phi_lnAF_CAVgm = 0.300
    cdef double phi_lnCAVgm    = 0.371
    cdef double rho_lnCAVgm    = 0.735

    cdef double phi_lnCAVgm_B = sqrt(pow(phi_lnCAVgm,2)-pow(phi_lnAF_CAVgm,2))
    cdef double phi_lnPGA_B   = sqrt(pow(phi_lnPGA,2)-pow(phi_lnAF_PGA,2))

    return sqrt(pow(phi_lnCAVgm_B,2)+pow(phi_lnAF_CAVgm,2)+pow(alpha,2)*pow(phi_lnPGA_B,2)+2*alpha*rho_lnCAVgm*phi_lnCAVgm_B*phi_lnPGA_B)

#===================================================================================================
# CAVgm: tau
#===================================================================================================
@cython.boundscheck(False)
@cython.wraparound(False)
@cython.nonecheck(False)
@cython.cdivision(True) 
def get_tau():
    return 0.196

#===================================================================================================
# CAVgm: mu, phi, tau
#===================================================================================================
@cython.boundscheck(False)
@cython.wraparound(False)
@cython.nonecheck(False)
@cython.cdivision(True)
def CampbellBozorgnia2010(double M,double fdip,double fZtor,R_JB, R_rup, R_x, Vs30, Z2p5,int fnm,int frv):
    
    """
    Parameter
    =========
    M: Earthquake magnitude.
    fdip: Fault dip in deg.
    fZtor: Depth to top of fault rupture in km.
    R_JB: Joyner-Boore distance in km.
    R_rup: Rupture distance in km.
    R_x: Rx distance in km.
    Vs30: Site Vs30. 
    Z2p5: Depth to Vs = 2.5 km/s.
    fnm: '1' for normal/normal-oblique fault, '0' otherwise.
    frv: '1' for reverse/reverse-oblique fault, '0' otherwise.

    Returns
    =======
    CAVgm mean, phi, tau.
    """
    
    cdef np.ndarray[np.double_t, ndim=1] R_JB_arr  = np.ascontiguousarray(np.atleast_1d(R_JB),  dtype=np.float64)
    cdef np.ndarray[np.double_t, ndim=1] R_rup_arr = np.ascontiguousarray(np.atleast_1d(R_rup), dtype=np.float64)
    cdef np.ndarray[np.double_t, ndim=1] R_x_arr   = np.ascontiguousarray(np.atleast_1d(R_x),   dtype=np.float64)
    cdef np.ndarray[np.double_t, ndim=1] Vs30_arr  = np.ascontiguousarray(np.atleast_1d(Vs30),  dtype=np.float64)
    cdef np.ndarray[np.double_t, ndim=1] Z2p5_arr  = np.ascontiguousarray(np.atleast_1d(Z2p5),  dtype=np.float64)

    cdef double[:] R_JB_arr2  = R_JB_arr
    cdef double[:] R_rup_arr2 = R_rup_arr
    cdef double[:] R_x_arr2   = R_x_arr
    cdef double[:] Vs30_arr2  = Vs30_arr
    cdef double[:] Z2p5_arr2  = Z2p5_arr

    cdef int N_sites = len(R_JB_arr2)
    cdef int i

    if R_rup_arr2.shape[0] != N_sites or R_x_arr2.shape[0] != N_sites or Vs30_arr2.shape[0] != N_sites or Z2p5_arr2.shape[0] != N_sites:
        raise ValueError('R_JB, R_rup, R_x, Vs30, Z2p5 must have the same length (or be scalars).')
    
    cdef double[:] A_1100 = np.zeros(N_sites, dtype='float64')
    cdef double[:] alpha  = np.zeros(N_sites, dtype='float64')
    cdef double[:] mu_im  = np.zeros(N_sites, dtype='float64')
    cdef double[:] phi_im = np.zeros(N_sites, dtype='float64')
    cdef double[:] tau_im = np.zeros(N_sites, dtype='float64')

    for i in range(N_sites):
        A_1100[i] = get_mu(0,M,fdip,fZtor,R_JB_arr2[i],R_rup_arr2[i],R_x_arr2[i],1100.,Z2p5_arr2[i],fnm,frv)
        A_1100[i] = exp(A_1100[i])
        alpha[i]  = get_alpha(Vs30_arr2[i],A_1100[i])
    
        mu_im[i]  = get_mu(1,M,fdip,fZtor,R_JB_arr2[i],R_rup_arr2[i],R_x_arr2[i],Vs30_arr2[i],Z2p5_arr2[i],fnm,frv)
        phi_im[i] = get_phi(alpha[i])
        tau_im[i] = get_tau()

    return np.asarray(mu_im), np.asarray(phi_im), np.asarray(tau_im)

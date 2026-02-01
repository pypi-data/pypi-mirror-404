""" Ground motion model by Campbell and Bozorgnia (2014) for PGA; functional form used for Ia and CAV. 
"""

import numpy as np
cimport numpy as np
cimport cython
from libc.math cimport pi, cos, pow, sqrt, exp, fmax, log

__author__ = 'A. Renmin Pretell Ductram'

#===================================================================================================
# Ia [0]/CAV [1]/PGA [2]: Mean
#===================================================================================================
@cython.boundscheck(False)
@cython.wraparound(False)
@cython.nonecheck(False)
@cython.cdivision(True)
def get_mu(int IM,double M,double fwidth,double fdip,double Ztor,double Z_hyp,double R_JB,double R_rup,double R_x,double Vs30,double Z2p5,double A_1100,int fnm,int frv,region):

    cdef double c_0,c_1,c_2,c_3,c_4,c_5,c_6,c_7,c_8,c_9,c_10,c_11,c_12,c_13,c_14,c_15,c_16,c_17,c_18,c_19, c_20
    cdef double dc_20ji, dc_20ch, a_2, h_1, h_2, h_3, h_4, h_5, h_6, k_1, k_2, k_3, c, n
    cdef double dc_20, S_J
    cdef double f_mag, f_dis, f_flt, f_hng, f_site, f_sed, f_hyp, f_dip, f_atn, mu

    #==============================================================================
    # Coefficients
    #==============================================================================
    if IM == 2:
        c_0     = -4.416
        c_1     =  0.984
        c_2     =  0.537
        c_3     = -1.499
        c_4     = -0.496
        c_5     = -2.773
        c_6     =  0.248
        c_7     =  6.768
        c_8     =  0.
        c_9     = -0.212
        c_10    =  0.72
        c_11    =  1.09
        c_12    =  2.186
        c_13    =  1.42
        c_14    = -0.0064
        c_15    = -0.202
        c_16    =  0.393
        c_17    =  0.0977
        c_18    =  0.0333
        c_19    =  0.00757
        c_20    = -0.0055
        dc_20ji = -0.0035
        dc_20ch =  0.0036
        a_2     =  0.167
        h_1     =  0.241
        h_2     =  1.474
        h_3     = -0.715
        h_4     =  1.
        h_5     = -0.337
        h_6     = -0.27
        k_1     =  865.
        k_2     = -1.186
        k_3     =  1.839
        c       =  1.88
        n       =  1.18
    elif IM == 1:
        c_0     = -4.75
        c_1     =  1.397
        c_2     =  0.282
        c_3     = -1.062
        c_4     = -0.17
        c_5     = -1.624
        c_6     =  0.134
        c_7     =  6.325
        c_8     =  0.054
        c_9     = -0.1
        c_10    =  0.469
        c_11    =  1.015
        c_12    =  1.208
        c_13    =  1.777
        c_14    =  0.1248
        c_15    = -0.191
        c_16    =  1.087
        c_17    =  0.0432
        c_18    =  0.0127
        c_19    =  0.00429
        c_20    = -0.0043
        dc_20ji = -0.0024
        dc_20ch =  0.0027
        a_2     =  0.167
        h_1     =  0.241
        h_2     =  1.474
        h_3     = -0.715
        h_4     =  1.
        h_5     = -0.337
        h_6     = -0.27
        k_1     =  400.
        k_2     = -1.311
        k_3     =  1.
        c       =  1.88
        n       =  1.18
    elif IM == 0:
        c_0     = -10.272
        c_1     =  2.318
        c_2     =  0.88
        c_3     = -2.672
        c_4     = -0.837
        c_5     = -4.441
        c_6     =  0.416
        c_7     =  4.869
        c_8     =  0.187
        c_9     = -0.196
        c_10    =  1.165
        c_11    =  1.596
        c_12    =  2.829
        c_13    =  2.76
        c_14    =  0.1081
        c_15    = -0.315
        c_16    =  1.612
        c_17    =  0.1311
        c_18    =  0.0453
        c_19    =  0.01242
        c_20    = -0.0103
        dc_20ji = -0.0051
        dc_20ch =  0.0064
        a_2     =  0.167
        h_1     =  0.241
        h_2     =  1.474
        h_3     = -0.715
        h_4     =  1.
        h_5     = -0.337
        h_6     = -0.27
        k_1     =  400.
        k_2     = -1.982
        k_3     =  1.
        c       =  1.88
        n       =  1.18
    
    # Regional coefficients
    [dc_20,S_J] = [0, 0]
    
    if region == 'japan' or region == 'italy':
        dc_20 = dc_20ji*1
    elif region == 'china':
        dc_20 = dc_20ch*1
    if region == 'japan':
        S_J = 1

    # Magnitude term
    if M <= 4.5:
        f_mag = c_0+c_1*M
    elif M <= 5.5:
        f_mag = c_0+c_1*M+c_2*(M-4.5)
    elif M <= 6.5:
        f_mag = c_0+c_1*M+c_2*(M-4.5)+c_3*(M-5.5)
    else:
        f_mag = c_0+c_1*M+c_2*(M-4.5)+c_3*(M-5.5)+c_4*(M-6.5)

    # Geometric attenuation term
    f_dis = (c_5+c_6*M)*log(sqrt(pow(R_rup,2)+pow(c_7,2)))

    # Style of faulting term
    if M <= 4.5:
        f_flt_M = 0
    elif M <= 5.5:
        f_flt_M = M-4.5
    else:
        f_flt_M = 1

    f_flt_F = c_8*frv + c_9*fnm
    f_flt   = f_flt_F*f_flt_M

    # Hanging wall term
    R_1 = fwidth*cos(fdip*pi/180)
    R_2 = 62*M-350

    if R_x < 0:
        f_hng_Rx = 0
    elif R_x < R_1:
        f_hng_Rx = h_1 + h_2*(R_x/R_1) + h_3*pow(R_x/R_1,2)
    else:
        R_rat = (R_x-R_1)/(R_2-R_1)
        f_hng_Rx = fmax(0,h_4 + h_5*R_rat + h_6*pow(R_rat,2))

    if R_rup == 0:
        f_hng_Rrup = 1
    else:
        f_hng_Rrup = (R_rup-R_JB)/R_rup

    if M <= 5.5:
        f_hng_M = 0
    elif M <= 6.5:
        f_hng_M = (M-5.5)*(1+a_2*(M-6.5))
    else:
        f_hng_M = 1+a_2*(M-6.5)

    f_hng_Z   = fmax(0,1-0.06*Ztor)
    f_hng_dip = (90-fdip)/45

    f_hng = c_10*f_hng_Rx*f_hng_Rrup*f_hng_M*f_hng_Z*f_hng_dip

    # Shallow site response term
    if Vs30 <= k_1:
        f_site_G = c_11*log(Vs30/k_1)+k_2*(log(A_1100+c*pow(Vs30/k_1,n))-log(A_1100+c))
    else:
        f_site_G = (c_11+k_2*n)*log(Vs30/k_1)

    if Vs30 <= 200:
        f_site_J = (c_12+k_2*n)*(log(Vs30/k_1)-log(200/k_1))
        f_site_J = f_site_J+(c_13+k_2*n)*log(Vs30/k_1)
    else:
        f_site_J = (c_13+k_2*n)*log(Vs30/k_1)

    f_site = f_site_G+S_J*f_site_J

    # Basin site response term
    if Z2p5 <= 1:
        f_sed = (c_14 + c_15*S_J)*(Z2p5-1)
    elif Z2p5 <= 3:
        f_sed = 0
    else:
        f_sed = c_16*k_3*exp(-0.75)*(1-exp(-0.25*(Z2p5-3)))

    # Hypocentral term
    if Z_hyp <= 7:
        f_hyp_H = 0
    elif Z_hyp <= 20:
        f_hyp_H = Z_hyp-7
    else:
        f_hyp_H = 13

    if M <= 5.5:
        f_hyp_M = c_17
    elif M <= 6.5:
        f_hyp_M = c_17+(c_18-c_17)*(M-5.5)
    else:
        f_hyp_M = c_18

    f_hyp = f_hyp_H*f_hyp_M

    # Fault dip term
    f_dip = 0
    if M <= 4.5:
        f_dip = c_19*fdip
    elif Z_hyp <= 5.5:
        f_dip = c_19*(5.5-M)*fdip

    # Anelastic attenuation term
    f_atn = 0
    if R_rup > 80:
        f_atn = (c_20+dc_20)*(R_rup-80)

    # Compute mean
    return f_mag+f_dis+f_flt+f_hng+f_site+f_sed+f_hyp+f_dip+f_atn

#===================================================================================================
# PGA: phi
#===================================================================================================
@cython.boundscheck(False)
@cython.wraparound(False)
@cython.nonecheck(False)
@cython.cdivision(True)
def get_phi(double M):

    cdef double phi_lnPGA, phi_lnPGA_B
    cdef double phi_lnAF = 0.3
    cdef double phi_1    = 0.734
    cdef double phi_2    = 0.492
    
    if M <= 4.5:
        phi_lnPGA = phi_1*1
    elif M <= 5.5:
        phi_lnPGA = phi_2+(phi_1-phi_2)*(5.5-M)
    else:
        phi_lnPGA = phi_2*1
    
    return sqrt(pow(phi_lnPGA,2)-pow(phi_lnAF,2))

#===================================================================================================
# PGA: tau
#===================================================================================================
@cython.boundscheck(False)
@cython.wraparound(False)
@cython.nonecheck(False)
@cython.cdivision(True)
def get_tau(double M):

    cdef double tau_lnPGA, tau_lnPGA_B
    cdef double tau_1 = 0.409
    cdef double tau_2 = 0.322

    if M <= 4.5:
        tau_lnPGA = tau_1*1
    elif M <= 5.5:
        tau_lnPGA = tau_2+(tau_1-tau_2)*(5.5-M)
    else:
        tau_lnPGA = tau_2*1

    tau_lnPGA_B = tau_lnPGA*1
    
    return tau_lnPGA_B

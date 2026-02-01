""" Ground motion model by Campbell and Bozorgnia (2010) for CAVgm and CAVdp.
"""

import numpy as np
import math

__author__ = 'A. Renmin Pretell Ductram'

#===================================================================================================
# PGA [0]/CAVgm [1]
#===================================================================================================
# Note: PGA implemented for Vs30=1100. only (f_site).
def get_mu(IM, M, fdip, fZtor, R_JB, R_rup, R_x, Vs30, Z2p5, fnm, frv):
    
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
    f_dis = (c_4+c_5*M)*np.log(np.sqrt(np.power(R_rup,2)+np.power(c_6,2)))


    # Style of faulting term
    f_flt_Z = min(fZtor,1)
    f_flt   = c_7*frv*f_flt_Z+c_8*fnm

    
    # Hanging wall term
    f_hng_R = np.ones_like(R_JB, dtype=float)
    val     = R_rup.astype(float).copy()
    
    boo1 = (R_JB>0)
    boo2 = boo1 & (fZtor>1) 
    
    val[boo2]     = np.maximum(R_rup[boo2],np.sqrt(np.power(R_JB[boo2],2)+1))
    f_hng_R[boo1] = (val[boo1]-R_JB[boo1])/val[boo1]

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
        f_site = (c_10+k_2*n)*np.log(Vs30/k_1)

    elif IM == 1: # CAVgm
        A_1100 = get_mu(0,M,fdip,fZtor,R_JB,R_rup,R_x,1100.,Z2p5,fnm,frv)
        A_1100 = np.exp(A_1100)
        
        f_site = np.zeros_like(R_JB, dtype=float)
        
        boo         = (Vs30<k_1)
        f_site[boo] = c_10*np.log(Vs30[boo]/k_1)+k_2*(np.log(A_1100[boo]+c*np.power(Vs30[boo]/k_1,n))-np.log(A_1100[boo]+c))

        boo         = (Vs30>=k_1) & (Vs30<1100)
        f_site[boo] = (c_10+k_2*n)*np.log(Vs30[boo]/k_1)
        
        boo         = (Vs30>=k_1) & (Vs30>=1100)
        f_site[boo] = (c_10+k_2*n)*np.log(1100./k_1)


    # Basin site response term
    f_sed = np.zeros_like(R_JB, dtype=float)
    
    boo        = (Z2p5<=1)
    f_sed[boo] = c_11*(Z2p5[boo]-1)
    
    boo        = (Z2p5>3)
    f_sed[boo] = c_12*k_3*np.exp(-0.75)*(1-np.exp(-0.25*(Z2p5[boo]-3)))


    # Compute mean
    return f_mag+f_dis+f_flt+f_hng+f_site+f_sed

#===================================================================================================
# Get CB10 alpha
#===================================================================================================
def get_alpha(Vs30, A_1100):

    k_1 =  400.0
    k_2 = -2.690
    c   =  1.880
    n   =  1.180

    alpha      = np.zeros_like(Vs30, dtype=float)
    boo        = (Vs30<k_1)
    alpha[boo] = k_2*A_1100[boo]*(np.power(A_1100[boo]+c*np.power(Vs30[boo]/k_1,n),-1)-np.power(A_1100[boo]+c,-1))
        
    return alpha

#===================================================================================================
# CAVgm: phi
#===================================================================================================
def get_phi(alpha):
    
    phi_lnAF_PGA   = 0.3
    phi_lnPGA      = 0.478
    phi_lnAF_CAVgm = 0.300
    phi_lnCAVgm    = 0.371
    rho_lnCAVgm    = 0.735

    phi_lnCAVgm_B = np.sqrt(np.power(phi_lnCAVgm,2)-np.power(phi_lnAF_CAVgm,2))
    phi_lnPGA_B   = np.sqrt(np.power(phi_lnPGA,2)  -np.power(phi_lnAF_PGA,2))

    return np.sqrt(np.power(phi_lnCAVgm_B,2)+np.power(phi_lnAF_CAVgm,2)+np.power(alpha,2)*np.power(phi_lnPGA_B,2)+2*alpha*rho_lnCAVgm*phi_lnCAVgm_B*phi_lnPGA_B)

#===================================================================================================
# CAVgm: tau
#===================================================================================================
def get_tau():
    return 0.196

#===================================================================================================
# CAVgm: mu, phi, tau
#===================================================================================================
def CampbellBozorgnia2010(M, fdip, fZtor, R_JB, R_rup, R_x, Vs30, Z2p5, fnm, frv):
    
    """
    Parameter
    =========
    M: Earthquake magnitude.
    fdip: Fault dip (deg).
    fZtor: Depth to top of fault rupture (km).
    R_JB: Joyner-Boore distance (km).
    R_rup: Rupture distance (km).
    R_x: Rx distance (km).
    Vs30: Site Vs30 (m/s). 
    Z2p5: Depth to Vs = 2.5 km/s (km).
    fnm: '1' for normal/normal-oblique fault, '0' otherwise.
    frv: '1' for reverse/reverse-oblique fault, '0' otherwise.

    Returns
    =======
    CAVgm mean, phi, tau.
    """

    R_JB_arr  = np.atleast_1d(R_JB)
    R_rup_arr = np.atleast_1d(R_rup)
    R_x_arr   = np.atleast_1d(R_x)
    Vs30_arr  = np.atleast_1d(Vs30)
    Z2p5_arr  = np.atleast_1d(Z2p5)
    
    N_sites = len(R_JB_arr)
    
    Vs30_R = np.full(N_sites, 1100.)
    A_1100 = get_mu(0, M, fdip, fZtor, R_JB_arr, R_rup_arr, R_x_arr, Vs30_R, Z2p5_arr, fnm, frv)
    A_1100 = np.exp(A_1100)
    alpha  = get_alpha(Vs30_arr, A_1100)

    mu_im  = get_mu(1, M, fdip, fZtor, R_JB_arr, R_rup_arr, R_x_arr, Vs30_arr, Z2p5_arr, fnm, frv)
    phi_im = get_phi(alpha)
    tau_im = get_tau()

    return mu_im, phi_im, tau_im

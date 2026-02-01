""" Ground motion model by Campbell and Bozorgnia (2011) for CAVdp. 
"""

import numpy as np
from gmms import CampbellBozorgnia2010

__author__         = 'A. Renmin Pretell Ductram'

#===================================================================================================
# CAVdp: mu
#===================================================================================================
def get_mu(PSVcheck, M, fdip, fZtor, R_JB, R_rup, R_x, Vs30, Z1p0, Z2p5, fnm, frv):
    
    if PSVcheck == 1:
        c_0 =  0.0072
        c_1 =  1.115
        c_2 = -0.067
        c_3 = -0.00330
    else:
        c_0 =  0.0152
        c_1 =  1.105
        c_2 = -0.044
        c_3 = -0.00369
    
    lnCAVgm = CampbellBozorgnia2010.get_mu(1,M,fdip,fZtor,R_JB,R_rup,R_x,Vs30,Z2p5,fnm,frv)
    return c_0+c_1*lnCAVgm+c_2*(M-6.5)*(M>=6.5)+c_3*R_rup

#===================================================================================================
# CAVdp: phi
#===================================================================================================
def get_phi(CAVgmType, PSVcheck, Vs30, A_1100):

    if CAVgmType == 0:
        if PSVcheck == 1:
            return 0.147
        else:
            return 0.131
    
    elif CAVgmType == 1:
    
        alpha = CampbellBozorgnia2010.get_alpha(Vs30, A_1100)
        
        if PSVcheck == 1:
            phi_lnCAVdp = 0.439
        else:
            phi_lnCAVdp = 0.430
            
        c_1            = 0     # CB11 Section 4.2 & to match Fig. 5
        phi_lnAF_PGA   = 0.300
        phi_lnPGA      = 0.478
        phi_lnAF_CAVgm = 0.300
        phi_lnCAVgm    = 0.371
        rho_lnCAVgm    = 0.735
        
        phi_lnPGA_B   = np.sqrt(np.power(phi_lnPGA,2)-np.power(phi_lnAF_PGA,2))
        phi_lnCAVgm_B = np.sqrt(np.power(phi_lnCAVgm,2)-np.power(phi_lnAF_CAVgm,2))
        
        phi_1 = np.power(phi_lnCAVgm_B,2)
        phi_2 = np.power(phi_lnAF_CAVgm,2)
        phi_3 = np.power(alpha,2)*np.power(phi_lnPGA_B,2)
        phi_4 = 2*alpha*rho_lnCAVgm*phi_lnCAVgm_B*phi_lnPGA_B
        
        return np.sqrt(np.power(phi_lnCAVdp,2)+(np.power(c_1,2))*(phi_1+phi_2+phi_3+phi_4))

#===================================================================================================
# CAVdp: tau
#===================================================================================================
def get_tau(CAVgmType, PSVcheck):
    
    if CAVgmType == 0:
        return 0.115
    
    elif CAVgmType == 1:

        if PSVcheck == 1:
            tau_lnCAVdp = 0.247
        else:
            tau_lnCAVdp = 0.245
        
        c_1         = 0     # CB11 Section 4.2 & to match Fig. 5
        tau_lnCAVgm = 0.196

        return np.sqrt(np.power(tau_lnCAVdp,2)+(np.power(c_1,2))*(np.power(tau_lnCAVgm,2)))

#===================================================================================================
# CAVdp: mu, phi, tau
#===================================================================================================
def CampbellBozorgnia2011(M, fdip, fZtor, R_JB, R_rup, R_x, Vs30, Z1p0, Z2p5, fnm, frv, CAVgmType, PSVcheck):

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
    Z1p0: Depth to Vs = 1 km/s (m).
    Z2p5: Depth to Vs = 2.5 km/s (km).
    fnm: '1' for normal/normal-oblique fault, '0' otherwise.
    frv: '1' for reverse/reverse-oblique fault, '0' otherwise.
    CAVgm_type: 0 for recorded, and 1 for gmm-based.
    PSV_check: 0 for no check, and 1 for yes.

    Returns
    =======
    CAVdp mean, phi, tau (ln units).
    """

    R_JB_arr  = np.atleast_1d(R_JB)
    R_rup_arr = np.atleast_1d(R_rup)
    R_x_arr   = np.atleast_1d(R_x)
    Vs30_arr  = np.atleast_1d(Vs30)
    Z1p0_arr  = np.atleast_1d(Z1p0)
    Z2p5_arr  = np.atleast_1d(Z2p5)
    
    N_sites  = len(R_JB_arr)
    A_1100_R = np.full(N_sites, 1100.)
    
    A_1100 = CampbellBozorgnia2010.get_mu(0, M, fdip, fZtor, R_JB_arr, R_rup_arr, R_x_arr, A_1100_R, Z2p5_arr, fnm, frv)
    A_1100 = np.exp(A_1100)
    
    mu_im  = get_mu(PSVcheck, M, fdip, fZtor, R_JB_arr, R_rup_arr, R_x_arr, Vs30_arr, Z1p0_arr, Z2p5_arr, fnm, frv)
    phi_im = get_phi(CAVgmType, PSVcheck, Vs30_arr, A_1100)
    tau_im = get_tau(CAVgmType, PSVcheck)

    return mu_im, phi_im, tau_im

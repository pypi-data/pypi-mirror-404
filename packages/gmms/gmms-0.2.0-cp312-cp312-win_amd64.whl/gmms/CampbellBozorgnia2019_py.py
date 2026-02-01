""" Ground motion model by Campbell and Bozorgnia (2019) for Ia and CAV . 
"""

import numpy as np
from gmms import CampbellBozorgnia2014

__author__         = 'A. Renmin Pretell Ductram'

#===================================================================================================
# Ia (0)/CAV (1): phi
#===================================================================================================
def get_phi(IM, M, Vs30, A_1100):
    
    if IM == 1:
        k_1      =  400.
        k_2      = -1.311
        c        =  1.88
        n        =  1.18
        phi_lnAF =  0.3 
        phi_1    =  0.514
        phi_2    =  0.394
        rho_1    =  0.842
        rho_2    =  0.78
    elif IM == 0:
        k_1      =  400.
        k_2      = -1.982
        c        =  1.88
        n        =  1.18
        phi_lnAF =  0.616
        phi_1    =  1.174
        phi_2    =  0.809
        rho_1    =  0.948
        rho_2    =  0.911

    if M <= 4.5:
        phi_lnY       = phi_1*1
        rho_lnPGA_lnY = rho_1*1
    elif M <= 5.5:
        phi_lnY = phi_2+(phi_1-phi_2)*(5.5-M)
        rho_lnPGA_lnY = rho_2+(rho_1-rho_2)*(5.5-M)
    else:
        phi_lnY       = phi_2*1
        rho_lnPGA_lnY = rho_2*1
    
    phi_lnY_B = np.sqrt(np.power(phi_lnY,2)-np.power(phi_lnAF,2))

    alpha      = np.zeros_like(Vs30, dtype='float')
    boo        = (Vs30<k_1)
    alpha[boo] = k_2*A_1100[boo]*(np.power(A_1100[boo]+c*np.power(Vs30[boo]/k_1,n),-1)-np.power(A_1100[boo]+c,-1))
    
    phi_lnPGA_B = CampbellBozorgnia2014.get_phi(M)

    return np.sqrt(np.power(phi_lnY_B,2)+np.power(phi_lnAF,2)+np.power(alpha,2)*np.power(phi_lnPGA_B,2)+2*alpha*rho_lnPGA_lnY*phi_lnY_B*phi_lnPGA_B)

#===================================================================================================
# Ia (0)/CAV (1): phi
#===================================================================================================
def get_tau(IM, M, Vs30, A_1100):

    if IM == 1:
        k_1   =  400.
        k_2   = -1.311
        c     =  1.88
        n     =  1.18
        tau_1 =  0.276
        tau_2 =  0.257
        rho_1 =  0.842
        rho_2 =  0.78
    elif IM == 0:
        k_1   =  400.
        k_2   = -1.982
        c     =  1.88
        n     =  1.18
        tau_1 =  0.614
        tau_2 =  0.435
        rho_1 =  0.948
        rho_2 =  0.911

    if M <= 4.5:
        tau_lnY       = tau_1*1
        rho_lnPGA_lnY = rho_1*1
    elif M <= 5.5:
        tau_lnY       = tau_2+(tau_1-tau_2)*(5.5-M)
        rho_lnPGA_lnY = rho_2+(rho_1-rho_2)*(5.5-M)
    else:
        tau_lnY       = tau_2*1
        rho_lnPGA_lnY = rho_2*1
    
    tau_lnY_B = tau_lnY*1

    alpha      = np.zeros_like(Vs30, dtype='float')
    boo        = (Vs30<k_1)
    alpha[boo] = k_2*A_1100[boo]*(np.power(A_1100[boo]+c*np.power(Vs30[boo]/k_1,n),-1)-np.power(A_1100[boo]+c,-1))
    
    tau_lnPGA_B = CampbellBozorgnia2014.get_tau(M)
        
    return np.sqrt(np.power(tau_lnY_B,2)+np.power(alpha,2)*np.power(tau_lnPGA_B,2)+2*alpha*rho_lnPGA_lnY*tau_lnY_B*tau_lnPGA_B)

#===================================================================================================
# Ia (0)/CAV (1): mu, phi, tau
#===================================================================================================
def CampbellBozorgnia2019(IM, M, fwidth, fdip, Z_tor,  Z_hyp, R_JB, R_rup, R_x, Vs30, Z2p5, fnm, frv, region):
	
    """
    Parameter
    =========
    IM: 0 for Ia, and 1 for CAV.
    M: Earthquake magnitude.
    fwidth: Fault width (km).
    fdip: Fault dip (deg).
    Z_hyp: Hypocentral depth (km).
    Z_tor: Depth to top of fault rupture (km).
    R_JB: Joyner-Boore distance (km).
    R_rup: Rupture distance (km).
    R_x: Rx distance (km).
    Vs30: Site Vs30 (m/s). 
    Z2p5: Depth to Vs = 2.5 km/s (km).
    fnm: 1 for normal/normal-oblique fault, 0 otherwise.
    frv: 1 for reverse/reverse-oblique fault, 0 otherwise.
    region: Earthquake country.

    Returns
    =======
    mean, phi, tau for the selected IM (ln units).
    """
    R_JB_arr  = np.atleast_1d(R_JB)
    R_rup_arr = np.atleast_1d(R_rup)
    R_x_arr   = np.atleast_1d(R_x)
    Vs30_arr  = np.atleast_1d(Vs30)
    Z2p5_arr  = np.atleast_1d(Z2p5)
    
    N_sites = len(R_rup_arr)

    A_1100_R = np.full(N_sites, 0.)
    Vs30_R   = np.full(N_sites, 1100.)
    Z2p5_R   = np.exp(7.089-1.144*np.log(Vs30_R))
    
    mu_pga = CampbellBozorgnia2014.get_mu(2, M, fwidth, fdip, Z_tor, Z_hyp, R_JB_arr, R_rup_arr, R_x_arr, Vs30_R, Z2p5_R, A_1100_R, fnm, frv, region)
    A_1100 = np.exp(mu_pga)
    
    mu_im  = CampbellBozorgnia2014.get_mu(IM, M, fwidth, fdip, Z_tor, Z_hyp, R_JB_arr, R_rup_arr, R_x_arr, Vs30_arr, Z2p5_arr, A_1100, fnm, frv, region)
    phi_im = get_phi(IM, M, Vs30_arr, A_1100)
    tau_im = get_tau(IM, M, Vs30_arr, A_1100)

    return mu_im, phi_im, tau_im

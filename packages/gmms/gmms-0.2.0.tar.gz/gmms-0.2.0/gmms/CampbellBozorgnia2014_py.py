""" Ground motion model by Campbell and Bozorgnia (2014) for PGA; functional form used for Ia and CAV. 
"""

import numpy as np

__author__ = 'A. Renmin Pretell Ductram'

#===================================================================================================
# Ia [0]/CAV [1]/PGA [2]: Mean
#===================================================================================================
def get_mu(IM, M, fwidth, fdip, Ztor, Z_hyp, R_JB, R_rup, R_x, Vs30, Z2p5, A_1100, fnm, frv,region):

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
    f_dis = (c_5+c_6*M)*np.log(np.sqrt(np.power(R_rup,2)+np.power(c_7,2)))


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
    R_1 = fwidth*np.cos(fdip*np.pi/180)
    R_2 = 62*M-350

    f_hng_Rx   = np.zeros_like(R_JB, dtype=float)
    f_hng_Rrup = np.ones_like(R_JB, dtype=float)
    
    boo           = (R_x>=0) & (R_x<R_1)
    f_hng_Rx[boo] = h_1 + h_2*(R_x[boo]/R_1) + h_3*np.power(R_x[boo]/R_1,2)
    boo           = (R_x>=R_1)
    rat           = (R_x[boo]-R_1)/(R_2-R_1)
    f_hng_Rx[boo] = np.maximum(0., h_4 + h_5*rat + h_6*np.power(rat,2))
  
    boo             = (R_rup!=0)
    f_hng_Rrup[boo] = (R_rup[boo]-R_JB[boo])/R_rup[boo]

    if M <= 5.5:
        f_hng_M = 0
    elif M <= 6.5:
        f_hng_M = (M-5.5)*(1+a_2*(M-6.5))
    else:
        f_hng_M = 1+a_2*(M-6.5)

    f_hng_Z   = max(0,1-0.06*Ztor)
    f_hng_dip = (90-fdip)/45

    f_hng = c_10*f_hng_Rx*f_hng_Rrup*f_hng_M*f_hng_Z*f_hng_dip


    # Shallow site response term
    f_site_G = np.zeros_like(R_JB, dtype=float)
    f_site_J = np.zeros_like(R_JB, dtype=float)
    
    boo            = (Vs30<=k_1)
    f_site_G[boo]  = c_11*np.log(Vs30[boo]/k_1)+k_2*(np.log(A_1100[boo]+c*np.power(Vs30[boo]/k_1,n))-np.log(A_1100[boo]+c))
    f_site_G[~boo] = (c_11+k_2*n)*np.log(Vs30[~boo]/k_1)    
    
    boo            = (Vs30<=200)
    f_site_J[boo]  = (c_12+k_2*n)*(np.log(Vs30[boo]/k_1)-np.log(200/k_1))+(c_13+k_2*n)*np.log(Vs30[boo]/k_1)
    f_site_J[~boo] = (c_13+k_2*n)*np.log(Vs30[~boo]/k_1)

    f_site = f_site_G+S_J*f_site_J


    # Basin site response term
    f_sed = np.zeros_like(R_JB, dtype=float)
    
    boo        = (Z2p5<=1)
    f_sed[boo] = (c_14 + c_15*S_J)*(Z2p5[boo]-1)
    
    boo        = (Z2p5>3)
    f_sed[boo] = c_16*k_3*np.exp(-0.75)*(1-np.exp(-0.25*(Z2p5[boo]-3)))


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
    f_atn = np.zeros_like(R_JB, dtype=float)
    
    boo        = (R_rup>80)
    f_atn[boo] = (c_20+dc_20)*(R_rup[boo]-80)


    # Compute mean
    return f_mag+f_dis+f_flt+f_hng+f_site+f_sed+f_hyp+f_dip+f_atn

#===================================================================================================
# PGA: phi
#===================================================================================================
def get_phi(M):

    phi_lnAF = 0.3
    phi_1    = 0.734
    phi_2    = 0.492
    
    if M <= 4.5:
        phi_lnPGA = phi_1*1
    elif M <= 5.5:
        phi_lnPGA = phi_2+(phi_1-phi_2)*(5.5-M)
    else:
        phi_lnPGA = phi_2*1
    
    return np.sqrt(np.power(phi_lnPGA,2)-np.power(phi_lnAF,2))

#===================================================================================================
# PGA: tau
#===================================================================================================
def get_tau(M):

    tau_1 = 0.409
    tau_2 = 0.322

    if M <= 4.5:
        tau_lnPGA = tau_1*1
    elif M <= 5.5:
        tau_lnPGA = tau_2+(tau_1-tau_2)*(5.5-M)
    else:
        tau_lnPGA = tau_2*1

    tau_lnPGA_B = tau_lnPGA*1
    
    return tau_lnPGA_B

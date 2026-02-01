""" A suite of functions to handle fault geometries for ground motion model distance calculations.
"""

import numpy as np
import geopy
from geopy.distance import GeodesicDistance

__author__ = 'A. Renmin Pretell Ductram'

#===================================================================================================
# Get fault URC
#===================================================================================================
def get_fault_URC(ULC_lat,ULC_lon,segm_length,segm_strike):

	"""
	Parameter
	=========
	ULC_lat/ULC_lon: Fault segment upper left corner coordinates in deg.
	segm_length: Fault segment lengths.
	segm_strike: Fault segment strike angles in deg. 

	Returns
	=======
	Fault URC lat/lon.
	"""
	
	try:
		N_segm = len(ULC_lat)
	except TypeError:
		N_segm  = 1
		ULC_lat = np.array([ULC_lat])
		ULC_lon = np.array([ULC_lon])
		segm_length = np.array([segm_length])
		segm_strike = np.array([segm_strike])

	URC_lat = np.zeros(N_segm)
	URC_lon = np.zeros(N_segm)
	
	for i in range(N_segm):
		origin = geopy.Point(ULC_lat[i],ULC_lon[i])
		URC    = GeodesicDistance(kilometers=(segm_length[i])).destination(origin,segm_strike[i])
		URC_lat[i] = URC.latitude
		URC_lon[i] = URC.longitude

	return URC_lat,URC_lon

#===================================================================================================
	# Get fault style
#===================================================================================================
def get_faulting_style(rake):

	"""
	Parameter
	=========
	rake: Fault rake in deg.

	Returns
	=======
	Flags: f_normal, f_reverse, and fault mechanism label
	"""

	if (rake>=-150.)*(rake<-30.):
		f_nor = 1
		f_rev = 0
		f_mec = 'NS'
	elif (rake>=30.)*(rake<150.):
		f_nor = 0
		f_rev = 1
		f_mec = 'RS'
	else:
		f_nor = 0
		f_rev = 0
		f_mec = 'SS'

	return f_nor,f_rev,f_mec

#===================================================================================================
# Get representat fault
#===================================================================================================
def get_representative_fault(segm_rake,segm_width,segm_length,segm_dip,segm_Ztor):

	"""
	Parameter
	=========
	segm_rake: Array of segment rake values.
	segm_width: Array of segment width values.
	segm_length: Array of segment length values.
	segm_dip: Array of segment dip values.
	segm_Ztor: Array of segment depth-to-top-of-rupture values.

	Returns
	=======
	Fault representative rake, width, fip, and Ztor in same units as input. 
	"""
	
	segm_rake   = np.atleast_1d(segm_rake)
	segm_width  = np.atleast_1d(segm_width)
	segm_length = np.atleast_1d(segm_length)
	segm_dip    = np.atleast_1d(segm_dip)
	segm_Ztor   = np.atleast_1d(segm_Ztor)

	try:
		N_segm = len(segm_rake)
	except TypeError:
		N_segm = 1

	if N_segm == 1:
		return segm_rake, segm_width, segm_dip, segm_Ztor
	else:
		frake = segm_rake[0]
		boo = [rake == frake for rake in segm_rake]
		if np.sum(boo) != 0:
			frake = segm_rake[segm_length==np.max(segm_length)][0]

		fwidth = np.sum(segm_length*segm_width)/np.sum(segm_length)
		fdip   = np.sum(segm_length*segm_dip)/np.sum(segm_length)
		fZtor  = np.sum(segm_length*segm_Ztor)/np.sum(segm_length)

		return frake,fwidth,fdip,fZtor

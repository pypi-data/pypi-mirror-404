""" A suite of functions to compute distances for ground motion model calculations.
"""

import numpy as np
import nvector as nv
from vincenty import vincenty

__author__         = 'A. Renmin Pretell Ductram'
__implementation__ = 'Python'

#===================================================================================================
# Supporting functions
#===================================================================================================
def get_bearing(lat1, lon1, lat2, lon2):
	conv    = np.pi/180
	lat1    = lat1*conv
	lon1    = lon1*conv
	lat2    = lat2*conv
	lon2    = lon2*conv
	y       = np.sin(lon2-lon1)*np.cos(lat2) 
	x       = np.cos(lat1)*np.sin(lat2)-np.sin(lat1)*np.cos(lat2)*np.cos(lon2-lon1)
	theta   = np.arctan2(y,x)
	bearing = (theta+2*np.pi)%(2*np.pi)
	return bearing


def cll2xy(flon, flat, slon, slat):

	N_sites = len(slon)
	X = np.zeros(N_sites, dtype='float64')
	Y = np.zeros(N_sites, dtype='float64')
	i = 0

	for lat,lon in zip(slat,slon):
		distance = vincenty((flat,flon),(lat,lon))
		bearing  = get_bearing(flat,flon,lat,lon)
		X[i] = distance*np.sin(bearing)
		Y[i] = distance*np.cos(bearing)
		i += 1
	return X,Y


def d2t(P):

	inside = 0
	P_clst = []
	
	B      = np.zeros(3, dtype = 'float64')
	E0     = np.zeros(3, dtype = 'float64')
	E1     = np.zeros(3, dtype = 'float64')
	E_clst = np.zeros([3,4], dtype = 'float64')

	B[0]  = P[0,0]
	B[1]  = P[1,0]
	B[2]  = P[2,0]
	E0[0] = P[0,1]-B[0]
	E0[1] = P[1,1]-B[1]
	E0[2] = P[2,1]-B[2]
	E1[0] = P[0,3]-B[0]
	E1[1] = P[1,3]-B[1]
	E1[2] = P[2,3]-B[2]
	a1 = E0[0]*E0[0]+E0[1]*E0[1]+E0[2]*E0[2]
	b1 = E0[0]*E1[0]+E0[1]*E1[1]+E0[2]*E1[2]
	c1 = E1[0]*E1[0]+E1[1]*E1[1]+E1[2]*E1[2]
	d1 = E0[0]*B[0]+E0[1]*B[1]+E0[2]*B[2]
	e1 = E1[0]*B[0]+E1[1]*B[1]+E1[2]*B[2]

	detinv = 1/(a1*c1-b1*b1)
	s1     = (b1*e1-c1*d1)*detinv
	t1     = (b1*d1-a1*e1)*detinv

	if np.isinf(detinv) == 0 and s1 >= 0 and s1 <= 1 and t1 >= 0 and t1 <= 1 and s1+t1 <= 1:
		inside = 1
		P_clst.append(B[0]+s1*E0[0]+t1*E1[0])
		P_clst.append(B[1]+s1*E0[1]+t1*E1[1])
		P_clst.append(B[2]+s1*E0[2]+t1*E1[2])
		dclst = P_clst[0]**2+P_clst[1]**2+P_clst[2]**2
		dclst = (dclst)**0.5
		return dclst, P_clst

	B[0]  = P[0,2]
	B[1]  = P[1,2]
	B[2]  = P[2,2]
	E0[0] = P[0,1]-B[0]
	E0[1] = P[1,1]-B[1]
	E0[2] = P[2,1]-B[2]
	E1[0] = P[0,3]-B[0]
	E1[1] = P[1,3]-B[1]
	E1[2] = P[2,3]-B[2]
	a2 = E0[0]*E0[0]+E0[1]*E0[1]+E0[2]*E0[2]
	b2 = E0[0]*E1[0]+E0[1]*E1[1]+E0[2]*E1[2]
	c2 = E1[0]*E1[0]+E1[1]*E1[1]+E1[2]*E1[2]
	d2 = E0[0]* B[0]+E0[1]* B[1]+E0[2]* B[2]
	e2 = E1[0]* B[0]+E1[1]* B[1]+E1[2]* B[2]

	detinv = 1/(a2*c2-b2*b2)
	s2 = (b2*e2-c2*d2)*detinv
	t2 = (b2*d2-a2*e2)*detinv

	if np.isinf(detinv) == 0 and s2 >= 0 and s2 <= 1 and t2 >= 0 and t2 <= 1 and s2+t2 <= 1:
		inside = 2
		P_clst.append(B[0]+s2*E0[0]+t2*E1[0])
		P_clst.append(B[1]+s2*E0[1]+t2*E1[1])
		P_clst.append(B[2]+s2*E0[2]+t2*E1[2])
		dclst = P_clst[0]**2+P_clst[1]**2+P_clst[2]**2
		dclst = (dclst)**0.5
		return dclst, P_clst

	if -d1 < 0:
		f = 0
	elif -d1 > a1:
		f = 1
	else:
		f = -d1/a1

	E_clst[0,0] = P[0,0]+f*(P[0,1]-P[0,0])
	E_clst[1,0] = P[1,0]+f*(P[1,1]-P[1,0])
	E_clst[2,0] = P[2,0]+f*(P[2,1]-P[2,0])

	if -d2 < 0:
		f = 0
	elif -d2 > a2:
		f = 1
	else:
		f = -d2/a2

	E_clst[0,1] = P[0,2]+f*(P[0,1]-P[0,2])
	E_clst[1,1] = P[1,2]+f*(P[1,1]-P[1,2])
	E_clst[2,1] = P[2,2]+f*(P[2,1]-P[2,2])

	if -e2 < 0:
		f = 0
	elif -e2 > c2:
		f = 1
	else:
		f = -e2/c2

	E_clst[0,2] = P[0,2]+f*(P[0,3]-P[0,2])
	E_clst[1,2] = P[1,2]+f*(P[1,3]-P[1,2])
	E_clst[2,2] = P[2,2]+f*(P[2,3]-P[2,2])

	if -e1 < 0:
		f = 0
	elif -e1 > c1:
		f = 1
	else:
		f = -e1/c1

	E_clst[0,3] = P[0,0]+f*(P[0,3]-P[0,0])
	E_clst[1,3] = P[1,0]+f*(P[1,3]-P[1,0])
	E_clst[2,3] = P[2,0]+f*(P[2,3]-P[2,0])
	dis1 = E_clst[0,0]**2+E_clst[1,0]**2+E_clst[2,0]**2
	dis2 = E_clst[0,1]**2+E_clst[1,1]**2+E_clst[2,1]**2
	dis3 = E_clst[0,2]**2+E_clst[1,2]**2+E_clst[2,2]**2
	dis4 = E_clst[0,3]**2+E_clst[1,3]**2+E_clst[2,3]**2

	dis_seq = [dis1, dis2, dis3, dis4]
	dclst = np.nanmin(dis_seq)
	iclst = np.argmin(dis_seq)
	dclst = (dclst)**0.5
	P_clst.append(E_clst[0,iclst])
	P_clst.append(E_clst[1,iclst])
	P_clst.append(E_clst[2,iclst])

	return dclst,P_clst

#===================================================================================================
# Joyner-Boore distance
#===================================================================================================
def get_Rjb(slat, slon, flat1, flon1, flat2, flon2, fwidth, fdip, fZtor):
	
	"""
	Parameter
	=========
	slat/slon: Site coordinates (deg).
	flat1/flon1: Fault ULC coordinates (deg).
	flat2/flon2: Fault URC coordinates (deg).
	fwidth: Fault width (km).
	fdip: Fault dip (deg).
	fZtor: Depth to top of fault rupture (km).
	
	Returns
	=======
	Joyner-Boore distance (km).
	"""

	# import warnings
	# warnings.filterwarnings('ignore', message='divide by zero encountered', category=RuntimeWarning,)

	N_sites = len(slat)
	conv    = np.pi/180
	Rjb     = np.zeros(N_sites, dtype = 'float64')
	pt      = np.zeros([3,4], dtype = 'float64')
	rwh     = fwidth*np.cos(fdip*conv)

	fdipDir = ''
	Sxy1    = cll2xy(flon1,flat1,slon,slat)
	Sxy2    = cll2xy(flon2,flat2,slon,slat)

	for i_sta in range(N_sites):
		pt[0,0] = -Sxy1[0][i_sta]
		pt[1,0] = -Sxy1[1][i_sta]
		pt[2,0] = 0.0
		pt[0,1] = -Sxy2[0][i_sta]
		pt[1,1] = -Sxy2[1][i_sta]
		pt[2,1] = 0.0

		if fdipDir == '':
			dX = pt[0,1]-pt[0,0]
			dY = pt[1,1]-pt[1,0]
			tmp_fstrike = np.arctan(dY/dX)/conv
			if dX == 0 and dY > 0:
				fstrike = 0
			elif dX == 0 and dY < 0:
				fstrike = 180
			elif dX > 0:
				fstrike = 90-tmp_fstrike
			elif dX < 0:
				fstrike = 270-tmp_fstrike

			if fstrike + 90 >= 360:
				fdipDir = fstrike+90-360
			else:
				fdipDir = fstrike+90

		dX = rwh*np.sin(fdipDir*conv)
		dY = rwh*np.cos(fdipDir*conv)
		pt[0,2] = pt[0,1]+dX
		pt[1,2] = pt[1,1]+dY
		pt[2,2] = 0.0
		pt[0,3] = pt[0,0]+dX
		pt[1,3] = pt[1,0]+dY
		pt[2,3] = 0.0
		a = d2t(pt)
		Rjb[i_sta] = a[0]

	# warnings.filterwarnings('default', category=RuntimeWarning)

	return np.asarray(Rjb)

#===================================================================================================
# Rupture distance
#===================================================================================================
def get_Rrup(slat, slon, flat1, flon1, flat2, flon2, fwidth, fdip, fZtor):
	
	"""
	Parameter
	=========
	slat/slon: Site coordinates (deg).
	flat1/flon1: Fault ULC coordinates (deg).
	flat2/flon2: Fault URC coordinates (deg).
	fwidth: Fault width (km).
	fdip: Fault dip (deg).
	fZtor: Depth to top of fault rupture (km).
	
	Returns
	=======
	Rupture distance (km).
	"""

	N_sites = len(slat)
	conv    = np.pi/180
	Rrup    = np.zeros(N_sites, dtype = 'float64')
	pt      = np.zeros([3,4], dtype = 'float64')
	botd    = fZtor + fwidth*np.sin(fdip*conv)
	rwh     = fwidth*np.cos(fdip*conv)
	
	fdipDir = ''
	Sxy1    = cll2xy(flon1,flat1,slon,slat)
	Sxy2    = cll2xy(flon2,flat2,slon,slat)

	for i_sta in range(N_sites):
		pt[0,0] = -Sxy1[0][i_sta]
		pt[1,0] = -Sxy1[1][i_sta]
		pt[2,0] = -fZtor
		pt[0,1] = -Sxy2[0][i_sta]
		pt[1,1] = -Sxy2[1][i_sta]
		pt[2,1] = -fZtor

		if fdipDir == '':
			dX = pt[0,1]-pt[0,0]
			dY = pt[1,1]-pt[1,0]
			tmp_fstrike = np.arctan(dY/dX)/conv
			if dX == 0 and dY > 0:
				fstrike = 0
			elif dX == 0 and dY < 0:
				fstrike = 180
			elif dX > 0:
				fstrike = 90-tmp_fstrike
			elif dX < 0:
				fstrike = 270-tmp_fstrike
			if fstrike + 90 >= 360:
				fdipDir = fstrike+90-360
			else:
				fdipDir = fstrike+90

		dX = rwh*np.sin(fdipDir*conv)
		dY = rwh*np.cos(fdipDir*conv)
		pt[0,2] = pt[0,1]+dX
		pt[1,2] = pt[1,1]+dY
		pt[2,2] = -botd
		pt[0,3] = pt[0,0]+dX
		pt[1,3] = pt[1,0]+dY
		pt[2,3] = -botd
		a = d2t(pt)
		Rrup[i_sta] = a[0]

	return np.asarray(Rrup)

#===================================================================================================
# Rx
#===================================================================================================
def get_Rx(slat, slon, flat1, flon1, flat2, flon2):

	"""
	Parameter
	=========
	slat/slon: Site coordinates (deg).
	flat1/flon1: Fault ULC coordinates (deg).
	flat2/flon2: Fault URC coordinates (deg).
	
	Returns
	=======
	Rx distance (km).
	"""
	
	N_sites = len(slon)
	Rx      = np.zeros(N_sites, dtype='float64')
	
	for i in range(N_sites):
		frame   = nv.FrameE(a=6371008.8, f=0)
		pointA1 = frame.GeoPoint(flat1,flon1,degrees=True)
		pointA2 = frame.GeoPoint(flat2,flon2,degrees=True)
		pointB  = frame.GeoPoint(slat[i],slon[i],degrees=True)
		pathA   = nv.GeoPath(pointA1, pointA2)
		Rx[i]   = pathA.cross_track_distance(pointB, method='greatcircle')/1000
	
	return np.asarray(Rx)

#===================================================================================================
# Get all distances (convenient to handle multi-segment fault)
#===================================================================================================
def get_distances(site_lat, site_lon, ULC_lat, ULC_lon, URC_lat, URC_lon, segm_width, segm_length, segm_dip, segm_strike, segm_Ztor):
	
	"""
	Parameter
	=========
	site_lat/site_lon: Site coordinates (deg).
	ULC_lat/ULC_lon: Fault ULC coordinates (deg).
	URC_lat/URC_lon: Fault URC coordinates (deg).
	segm_width: Fault segment width (km).
	segm_length: Fault segment length (km).
	segm_dip: Fault segment dip (deg).
	segm_strike: Fault segment strike (deg).
	segm_Ztor: Fault segment depth to top of rupture (km).
	
	Returns
	=======
	Joyner-Boore, rupture, and Rx distances (km).
	"""
	
	# Silence expected warnings
	import numpy as np
	np.seterr(divide='ignore', invalid='ignore', over='ignore')

	site_lat    = np.atleast_1d(site_lat)
	site_lon    = np.atleast_1d(site_lon)
	ULC_lat     = np.atleast_1d(ULC_lat)
	ULC_lon     = np.atleast_1d(ULC_lon)
	URC_lat     = np.atleast_1d(URC_lat)
	URC_lon     = np.atleast_1d(URC_lon)
	segm_width  = np.atleast_1d(segm_width)
	segm_length = np.atleast_1d(segm_length)
	segm_dip    = np.atleast_1d(segm_dip)
	segm_strike = np.atleast_1d(segm_strike)
	segm_Ztor   = np.atleast_1d(segm_Ztor)
    
	N_segms  = len(segm_dip)
	N_sites  = len(site_lat)
	tmp_Rjb  = np.zeros((N_sites, N_segms), dtype='float64')
	tmp_Rrup = np.zeros((N_sites, N_segms), dtype='float64')
	tmp_Rx   = np.zeros((N_sites, N_segms), dtype='float64')
	ALL_Rjb  = np.zeros(N_sites, dtype='float64')
	ALL_Rrup = np.zeros(N_sites, dtype='float64')
	ALL_Rx   = np.zeros(N_sites, dtype='float64')

	for i in range(N_segms):
		tmp_Rjb[:, i]  = get_Rjb(site_lat, site_lon, ULC_lat[i], ULC_lon[i], URC_lat[i], URC_lon[i], segm_width[i], segm_dip[i], segm_strike[i])
		tmp_Rrup[:, i] = get_Rrup(site_lat, site_lon, ULC_lat[i], ULC_lon[i], URC_lat[i], URC_lon[i], segm_width[i], segm_dip[i], segm_Ztor[i])
		tmp_Rx[:, i]   = get_Rx(site_lat, site_lon, ULC_lat[i], ULC_lon[i], URC_lat[i], URC_lon[i])

	ALL_Rjb  = np.min(tmp_Rjb,  axis=1)
	ALL_Rrup = np.min(tmp_Rrup, axis=1)
	ALL_Rx   = tmp_Rx[np.arange(N_sites), np.argmin(tmp_Rjb, axis=1)]

	old = np.seterr(invalid='ignore')
	np.seterr(**old)

	return ALL_Rjb, ALL_Rrup, ALL_Rx

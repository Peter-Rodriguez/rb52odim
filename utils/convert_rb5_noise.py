#!/usr/bin/env python

import struct
import numpy as np

###################################################################################################

def convert_uint_2_float(i_val):
    import struct
    packed_val = struct.pack('>I', i_val)
    return struct.unpack('>f',packed_val)[0]

i_val = 3236033536
f_val = convert_uint_2_float(i_val) #-7.06103515625

###################################################################################################

def rng_correct(inp_val,inp_km,out_km):
    import numpy as np
    return inp_val-20*np.log10(inp_km/out_km)

NEZH_001km=-47.5302 #at 1 km
NEZH_100km=rng_correct(NEZH_001km,1.,100.) #-7.5302000000000007

f_val_100km=f_val
f_val_001km=rng_correct(f_val_100km,100.,1.) #-47.06103515625

###################################################################################################

import _raveio
h5_file='../test/CASRA_20171215200514_scan.h5'
rio=_raveio.open(h5_file)

raw_noisepowerh_arr=rio.object.getAttribute('how/noisepowerh')
noisepowerh_100km_arr=[convert_uint_2_float(i_val) for i_val in raw_noisepowerh_arr]
noisepowerh_001km_arr=[rng_correct(f_val_100km,100.,1.) for f_val_100km in noisepowerh_100km_arr]

NEZH_001km=rio.object.getAttribute('how/NEZH')
print('NEZH_001km = {0:.4f} dBZ'.format(NEZH_001km))

min_noisepowerh_001km=np.min(noisepowerh_001km_arr)
print('min_noisepowerh_001km = {0:.4f} dBZ'.format(min_noisepowerh_001km))
max_noisepowerh_001km=np.max(noisepowerh_001km_arr)
print('max_noisepowerh_001km = {0:.4f} dBZ'.format(max_noisepowerh_001km))

import pdb; pdb.set_trace()

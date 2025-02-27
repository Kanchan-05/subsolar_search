import numpy as np
import h5py as h
import matplotlib.pyplot as plt
import pycbc.pnutils as pnu


bank = h.File('/home/ksoni01/work/proj_subsolar/o3_hierarchical_search/gen_banks/gen_coarsebank/buffer4_512s/O3_O4_SEOBNRv5HM_bank_mm_90_15Hz.hdf', 'r')

for i in range(len(bank['mass1'])):
    duration=(pnu.get_imr_duration(
            bank['mass1'][i], bank['mass2'][i], 
            bank['spin1z'][i],bank['spin2z'][i], 20, "IMRPhenomD"
        ))
    print (i,duration)
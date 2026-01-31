
import numpy as np
import matplotlib.pyplot as plt
from types import SimpleNamespace
import importlib 
from matplotlib.gridspec import GridSpec
from mpl_toolkits.axes_grid1 import make_axes_locatable
import sys
import os 
from pathlib import Path
if sys.version_info < (3, 0):
    import ConfigParser
else:
    import configparser as ConfigParser
    
import pyzelda.zelda as zelda
import pyzelda.ztools as ztools
import pyzelda.utils.aperture as aperture


from baldrapp.common import baldr_core as bldr
from baldrapp.common import DM_basis as gen_basis
from baldrapp.common import utilities as util

import aotools



### Set up manually 

grid_dict = {
    "telescope":'AT',
    "D":1.8, # diameter of beam 
    "N" : 64, # number of pixels across pupil diameter
    "dim": 64 * 8 #4 
    #"padding_factor" : 4, # how many pupil diameters fit into grid x axis
    # TOTAL NUMBER OF PIXELS = padding_factor * N 
    }

# I should include coldstop here!! 
optics_dict = {
    "wvl0" :1.65e-6, # central wavelength (m) 
    "F_number": 21.2, # F number on phasemask
    "mask_diam": 1.06, # diameter of phaseshifting region in diffraction limit units (physical unit is mask_diam * 1.22 * F_number * lambda)
    "theta": 1.57079, # phaseshift of phasemask 
    ### NEw have not consistenty propagate this in functions in baldr_core
    "coldstop_diam": 4, #1.22 lambda/D units
    "coldstop_offset":(1,0)
}

dm_dict = {
    "dm_model":"BMC-multi-3.5",
    "actuator_coupling_factor":0.7,# std of in actuator spacing of gaussian IF applied to each actuator. (e.g actuator_coupling_factor = 1 implies std of poke is 1 actuator across.)
    "dm_pitch":1,
    "dm_aoi":0, # angle of incidence of light on DM 
    "opd_per_cmd" : 3e-6, # peak opd applied at center of actuator per command unit (normalized between 0-1) 
    "flat_rmse" : 20e-9 # std (m) of flatness across Flat DM  
    }

grid_ns = SimpleNamespace(**grid_dict)
optics_ns = SimpleNamespace(**optics_dict)
dm_ns = SimpleNamespace(**dm_dict)

zwfs_ns = bldr.init_zwfs(grid_ns, optics_ns, dm_ns)


# propagate field 
phi, phi_internal,  N0, I0, Intensity = bldr.test_propagation( zwfs_ns )
util.nice_heatmap_subplots( im_list=[phi,N0,I0,Intensity])
plt.show() 




phi = 0 * zwfs_ns.grid.pupil_mask *  np.random.randn( *zwfs_ns.grid.pupil_mask.shape)

#opd_internal = 10e-9 * zwfs_ns.grid.pupil_mask * np.random.randn( *zwfs_ns.grid.pupil_mask.shape)

amp = 1e2 * zwfs_ns.grid.pupil_mask



t0 = time.time() 
I = bldr.get_pupil_intensity(
    phi=phi, 
    amp=amp, 
    theta=zwfs_ns.optics.theta, 
    phasemask_diameter = zwfs_ns.optics.mask_diam, 
    phasemask_mask = None, # generate the correct correct mask from the specified diameter
    pupil_diameter = None, # this is not used , should check if we can remove it from the signature 
    #fplane_pixels=300, 
    #pixels_across_mask=10,
    coldstop_diam=2, 
    coldstop_offset=(0.0, 0.0), 
    coldstop_mask=None, # generate the correct mask from the coldstop diam specified
    include_beta=True, 
    return_field=False, 
    return_terms=False, 
    debug=False,
    )
t1 = time.time() 
print( t1-t0 )
#plt.show()

plt.imshow( I );plt.colorbar();plt.show()


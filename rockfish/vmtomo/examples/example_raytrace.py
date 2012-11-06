#!/usr/bin/env python
"""
Raytracing example
==================
"""
import os
from rockfish.picking.database import PickDatabaseConnection
from rockfish.vmtomo.vm import VM

# Set filenames for model, pick database, etc.
pickdbfile = 'temp.pickdb.sqlite'
vmfile = '../tests/data/goc_l26.15.00.vm'

# Build an example pick database
uniq_picks = []
events =    ['Pg', 'Pg', 'Pg', 'Pn']
vm_branch = [3, 3, 3, 4]
ensembles = [100, 100, 100, 100]
traces =    [1, 2, 3, 1]
for i in range(0, len(events)):
    uniq_picks.append({
        'event':events[i],
        'ensemble':ensembles[i],
        'vm_branch':vm_branch[i],
        'vm_subid':0,
        'trace':traces[i],
        'time':12.3456789,
        'time_reduced':12.3456789,
        'source_x':-123.456,
        'source_y':-12.345,
        'source_z':0.006,
        'receiver_x':-654.321,
        'receiver_y':54.321,
        'receiver_z':1234.5678})
pickdb = PickDatabaseConnection(pickdbfile)
for pick in uniq_picks:
    pickdb.add_pick(**pick)
pickdb.commit()

# Raytrace the model
# TODO

# Plot model and rays
# TODO

# Clean up example files
for filename in [pickdbfile]:
    if os.path.isfile(filename):
        os.remove(filename)

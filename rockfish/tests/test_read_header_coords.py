
from rockfish import tests
from rockfish.segy import header


def print_headers(trs):

    for tr in trs[0:10]:

        print tr.header.source_coordinate_x,tr.header.source_coordinate_y,tr.header.group_coordinate_x,tr.header.group_coordinate_y


    return




segy = tests.load_example_segy('pos_neg.segy',readas='SEGYFile',unpack_headers=True)

trs = segy.traces[0:10]

print_headers(trs)



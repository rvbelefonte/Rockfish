.. _agc:

Automatic Gain Control (AGC)
============================

AGC based on windowed-RMS amplitude
-----------------------------------

    from rockfish.segy.segy import readSEGY
    from rockfish.core.util import get_example_file
    sgy = readSEGY(get_example_file('ew0210_o30.segy'))
    sgy.plot()

.. plot::

    from rockfish.segy.segy import readSEGY
    from rockfish.core.util import get_example_file
    sgy = readSEGY(get_example_file('ew0210_o30.segy'))
    sgy.plot(sphinx=True)



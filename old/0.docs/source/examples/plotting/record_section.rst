.. _record_section:

Record Sections
===============

All data in a SEG-Y file can be plotted easily with ``SEGYFile.plot()``::

    from rockfish.segy.segy import readSEGY
    from rockfish.core.util import get_example_file
    sgy = readSEGY(get_example_file('ew0210_o30.segy'))
    sgy.plot()

.. plot::

    from rockfish.segy.segy import readSEGY
    from rockfish.core.util import get_example_file
    sgy = readSEGY(get_example_file('ew0210_o30.segy'))
    sgy.plot(sphinx=True)


Plotting by offset
------------------

Data can also be plotted as a function of source-receiver offset by setting
``xplt_key='offset'`` in the call to ``SEGYFile.plot()``::

    sgy.plot(xplt_key='offset')

.. plot::

    from rockfish.segy.segy import readSEGY
    from rockfish.core.util import get_example_file
    sgy = readSEGY(get_example_file('ew0210_o30.segy'))
    sgy.plot(sphinx=True,xplt_key='offset')


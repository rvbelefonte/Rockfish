.. _linking:

Linking to Other Pages
======================

External links to other packages
--------------------------------

Sphinx can link to the documentation of other projects that are also documented using Sphinx.  To include external links, add :mod:`sphinx.ext.intersphinx` to the ``extensions`` list in :file:`conf.py`.

Then, configure links to other projects in :file:`conf.py` with::

     intersphinx_cache_limit = 10     # days to keep the cached inventories
     intersphinx_mapping = {
        'obspy':('http://docs.obspy.org',None)
        'sphinx':('http://sphinx.pocoo.org',  None),
        'python':('http://docs.python.org/2.7',None),
        'matplotlib':('http://matplotlib.sourceforge.net', None),
        'numpy':('http://docs.scipy.org/doc/numpy',None),
     }

Then, other documentation pages can be referenced like this:

=======================================   ===================================
reST source                                  render 
=======================================   ===================================
 ``:class:`obspy.segy.segy.SEGYFile```     :class:`obspy.segy.segy.SEGYFile`
 ``:meth:`obsy.segy.segy.readSEGY```       :meth:`obsy.segy.segy.readSEGY`
 ``:py:mod:`sphinx.ext.intersphinx```      :py:mod:`sphinx.ext.intersphinx`
 ``:mod:`sphinx.ext.intersphinx```         :mod:`sphinx.ext.intersphinx`
 ``:py:class:`zipfile.ZipFile```           :py:class:`zipfile.ZipFile` 
 ``:py:mod:`matplotlib.pyplot```           :py:mod:`matplotlib.pyplot`
 ``:mod:`numpy```                          :mod:`numpy` 
 ``:class:`numpy.ndarray```                :class:`numpy.ndarray` 
 ``:rst:dir:`math```                       :rst:dir:`math`  
 ``:rst:role:`math```                      :rst:role:`math`  
=======================================   ===================================

Note that the ``:py:`` is not strictly needed as **py** is the default domain.

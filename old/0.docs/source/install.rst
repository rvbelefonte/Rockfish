.. _install:

Installation Instructions
=========================

Get the source code
-------------------
   
Locally:
::

    svn checkout file:///Volumes/raid0/svnrepos/Rockfish

On WHOI VPN:
::

     svn checkout svn+ssh://ncm@chesapeake/Volumes/raid0/svnrepos/Rockfish

.. todo:: Get this code onto a public server once it is somewhat useful.


Add Rockfish to `PYTHONPATH` and `PATH`
---------------------------------------

Bash:
::

     export PATH=$PATH:/path/to/Rockfish/bin
     export PYTHONPATH=$PYTHONPATH:/path/to/Rockfish

csh:
::

     setenv PATH $PATH:/path/to/Rockfish/bin
     setenv PYTHONPATH $PYTHONPATH:/path/to/Rockfish

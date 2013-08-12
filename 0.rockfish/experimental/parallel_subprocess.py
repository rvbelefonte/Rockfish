"""
Example running subprocess.call(shell=True) in parallel
"""

from threading import Thread
import subprocess


def call_script(sh, i, n):
    print "starting job ", i, " thread ", n
    subprocess.call(sh, shell=True)
    print "done job ", i, " thread ", n

nproc = 2
njob = 20
ijob = -1
while ijob < njob:
    t = []
    for i in range(nproc):
        ijob += 1
        t.append(Thread(target=call_script, args=(['sleep 10', ijob, i])))
         
    [_t.start() for _t in t]
    [_t.join() for _t in t]





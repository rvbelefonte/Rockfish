#!/usr/bin/env python

from rockfish.messaging.netgrowl import *
import sys

def growlNotify(title = "Script Finished", message = ""):
    
    addr = ("10.1.104.26", GROWL_UDP_PORT)
    s = socket(AF_INET,SOCK_DGRAM)
    # 
    # p = GrowlRegistrationPacket(application="Network Demo", password="?")
    # p.addNotification("Script Finished", enabled=True)
    # 
    # s.sendto(p.payload(), addr)

    if not message:
        message = sys.argv[0]

    p = GrowlNotificationPacket(application="Network Demo",
        notification="Script Finished", title=title,
        description=message, priority=1,
        sticky=True, password="?")
    s.sendto(p.payload(),addr)
    s.close()

if __name__ == '__main__':
    growlNotify()

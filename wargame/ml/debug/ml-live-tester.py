#!/usr/bin/python
#    Missile launchers live tester
#    Copyright (C) 2013  Martin Dubé
#    Version: 2013-10-20:2020
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>. 
"""
    Prerequisite: python-usb > v1.0
    http://superb-dca2.dl.sourceforge.net/project/pyusb/PyUSB%201.0/1.0.0-alpha-3/pyusb-1.0.0a3.zip

    Doc: http://pyusb.sourceforge.net/docs/1.0/tutorial.html
"""
import os
import sys
import time
import usb.core
import termios
import fcntl

class MissileLauncher():
    """
    This is the missile launcher controller class. 
    """
    _dev = None

    def __init__(self,dev):
        self._dev = dev
        self._setupDevice()
    
    def _setupDevice(self):
        if self._dev is None:
            raise ValueError('Launcher not found.')
        if self._dev.is_kernel_driver_active(0) is True:
            self._dev.detach_kernel_driver(0)
            self._dev.set_configuration()

    def up(self,delay):
        self.stop()
        self._dev.ctrl_transfer(0x21,0x09,0,0,[0x02,0x02,0x00,0x00,0x00,0x00,0x00,0x00]) 
        time.sleep(delay)
        self.stop()
    
    def down(self,delay):
        self.stop()
        self._dev.ctrl_transfer(0x21,0x09,0,0,[0x02,0x01,0x00,0x00,0x00,0x00,0x00,0x00])
        time.sleep(delay)
        self.stop()
    
    def left(self,delay):
        self.stop()
        self._dev.ctrl_transfer(0x21,0x09,0,0,[0x02,0x04,0x00,0x00,0x00,0x00,0x00,0x00])
        time.sleep(delay)
        self.stop()
    
    def right(self,delay):
        self.stop()
        self._dev.ctrl_transfer(0x21,0x09,0,0,[0x02,0x08,0x00,0x00,0x00,0x00,0x00,0x00])
        time.sleep(delay)
        self.stop()
    
    def stop(self):
        self._dev.ctrl_transfer(0x21,0x09,0,0,[0x02,0x20,0x00,0x00,0x00,0x00,0x00,0x00])
    
    def fire(self):
        self._dev.ctrl_transfer(0x21,0x09,0,0,[0x02,0x10,0x00,0x00,0x00,0x00,0x00,0x00])
        time.sleep(3)
    
    def reset(self):
        self._dev.ctrl_transfer(0x21,0x09,0,0,[0x02,0x09,0x00,0x00,0x00,0x00,0x00,0x00])
        time.sleep(6)

    def quit(self):
        pass
    
    def aim(self, x, y, z):
        pass

class MissilesController():
    """

    """
    ID_VENDOR = 0x2123
    ID_PRODUCT = 0x1010
    MOVE_DURATION = 0.02

    _mlList = []
    enabledML = []

    def __init__(self):
        pass

    def _getDevice(self,no):
        devs = usb.core.find(find_all=True,idVendor=self.ID_VENDOR, idProduct=self.ID_PRODUCT)
        dev = None
        no = int(no)
        if len(devs) >= no + 1:
            dev = devs[no]
        else:
            print 'Launcher not found.'
        return dev

    def registerDevice(self,dev):
        if dev:
            print 'Registering device'
            oML = MissileLauncher(dev)
            self._mlList.append(oML)
        else:
            print 'Failed to register device'

    def registerDevices(self):
        devs = usb.core.find(find_all=True,idVendor=self.ID_VENDOR, idProduct=self.ID_PRODUCT)
        for dev in devs:
            self.registerDevice(dev)
    
    def up(self):
        for ml in self._mlList:
            ml.up(self.MOVE_DURATION)

    def down(self):
        for ml in self._mlList:
            ml.down(self.MOVE_DURATION)

    def left(self):
        for ml in self._mlList:
            ml.left(self.MOVE_DURATION)

    def right(self):
        for ml in self._mlList:
            ml.right(self.MOVE_DURATION)

    def fire(self):
        for ml in self._mlList:
            ml.fire()

    def reset(self):
        for ml in self._mlList:
            ml.reset()

    def getList(self):
        pass
    def select(self):
        pass
    def printHelp(self):
        pass
    def goLive(self):
        fd = sys.stdin.fileno()
        oldterm = termios.tcgetattr(fd)
        newattr = termios.tcgetattr(fd)
        newattr[3] = newattr[3] & ~termios.ICANON & ~termios.ECHO
        termios.tcsetattr(fd, termios.TCSANOW, newattr)
        
        oldflags = fcntl.fcntl(fd, fcntl.F_GETFL)
        fcntl.fcntl(fd, fcntl.F_SETFL, oldflags | os.O_NONBLOCK)
        
        try:
             while 1:
                  try:
                        c = sys.stdin.read(1)
                        print "Got character", repr(c)
                        if c == 'a':
                            self.left()
                        elif c == 'w':
                            self.down()
                        elif c == 'd':
                            self.right()
                        elif c == 's':
                            self.up()
                        elif c == 'f':
                            self.fire()
                        elif c == 'q':
                            break
                  except IOError: pass

                  # Add some random move if not controlled in the last 10 sec
        finally:
             termios.tcsetattr(fd, termios.TCSAFLUSH, oldterm)
             fcntl.fcntl(fd, fcntl.F_SETFL, oldflags)

class MissileInterface():
    def __init__(self):
        pass

    def startAsService(self):
        pass

    def startAsCli(self):
        pass

oMC = MissilesController()
oMC.registerDevices()
oMC.goLive()

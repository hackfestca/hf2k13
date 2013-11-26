#!/usr/bin/python
# -*- coding: utf-8 -*-
#    Light controller script for raspberry pi
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
import time
import RPi.GPIO as GPIO
import os, sys
import logging
import shelve
from threading import Thread
from logging.handlers import TimedRotatingFileHandler


# CLASSES
class LightController(Thread):
    _bState = 'notstarted'
    chan1 = 18
    pidFile = '/var/run/lightController/lc.pid'
    logDir = '/root/logs'
    logFile = 'lightController.log'

    def __init__(self):
        Thread.__init__(self)
        self.configLogs()
        GPIO.cleanup()
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.chan1, GPIO.OUT)

    def run(self):
        while self.isRunning():
            if self.getState() == 'dying':
                break
            if self.getState() == 'started':
                self.checkInput()
            if self.getState() == 'stopped':
                pass
            if self.getState() == 'starting':
                self.log.info('Starting')
                self.setState('started')
            if self.getState() == 'stopping':
                self.log.info('Stopping')
                self.setState('stopped')
            if self.getState() == 'notstarted':
                pass
            time.sleep(2)
        GPIO.cleanup()
        return 0

    def checkInput(self):
        oDB = DBController().getDB()
        if (oDB['lightStatus']):
            self.turnOn()
            #self.log.info('Light is turned on')
        else:
            self.turnOff()
            #self.log.info('Light is turned off')
        del oDB
        oDB = None

    def getState(self):
        """
        This method return the current state of the connector
        """
        return self._bState

    def setState(self, state):
        """
        This method change the state of the bot. 
        @param state: State to set
        @type state: String
        """
        self._bState = state

    def isRunning(self):
        """
        This method return True if the bot is running. Note: Running = the thread is started and not terminated yet.
        """
        if (self._bState in ['starting','stopping','started',\
                            'stopped', 'notstarted']):
            return True
        else:
            return False

    def startSensor(self):
        """
        This method connect the bot
        """
        self.log.info('Setting state to: starting')
        self.setState('starting')

    def stopSensor(self):
        """
        This method disconnect the bot
        """
        self.log.info('Setting state to: stopping')
        self.setState('stopping')

    def killSensor(self):
        """
        This method kill the bot by terminating the thread.
        """
        self.log.info('Setting state to: dying')
        self.setState('dying')

    def savePid(self):
        pid = str(os.getpid())
        self.log.info('Saving pid file: ' + str(pid))

        d = os.path.dirname(self.pidFile)
        if not os.path.exists(d):
            os.makedirs(d)

        file(self.pidFile,'w+').write("%s\n" % pid)

    def configLogs(self):
        """
        This method configure the logs for this object. 
        """
        logFormat = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        dateTimeFormat = '%Y-%m-%d %H:%M:%S'

        # Write also to file
        fh = TimedRotatingFileHandler(os.path.join(self.logDir,self.logFile), \
                                      backupCount=0, \
                                      when='d', \
                                      interval=1)
        fh.setFormatter(logging.Formatter(logFormat, dateTimeFormat))
        self.log = logging.getLogger('LightController')
        self.log.addHandler(fh)
       
        # Set log level
        self.log.setLevel(logging.DEBUG)
        #self.log.setLevel(logging.INFO)

    def turnOn(self):
        GPIO.output(self.chan1,True)

    def turnOff(self):
        GPIO.output(self.chan1,False)

class DBController():
    dbFile = '/home/ml/missile2k13.shelve'
    #dbFile = 'missile2k13.shelve'
    d = None

    def __init__(self):
        self._configLogs()
        #self.log.info('Opening shelve (' + str(self.dbFile) + ')')
        self.d = shelve.open(self.dbFile)
        #self.log.debug(self.d)

    def _configLogs(self):
        """
        This method configure the logs for this object. 
        """
        logFormat = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        dateTimeFormat = '%Y-%m-%d %H:%M:%S'
        logFile = 'lightController.log'
        logDir = '/root/logs'

        fh = TimedRotatingFileHandler(os.path.join(logDir,logFile), \
                                      backupCount=0, \
                                      when='d', \
                                      interval=1)
        fh.setFormatter(logging.Formatter(logFormat, dateTimeFormat))

        self.log = logging.getLogger('DBController')
        self.log.addHandler(fh)
        self.log.setLevel(logging.INFO)

    def getDB(self):
        return self.d

    def sync(self):
        self.d.sync()

    def close(self):
        self.d.close()

# MENU
bs = LightController()
bs.daemon=True
bs.start()
bs.savePid()
bs.startSensor()
try:
    while True: time.sleep(100)
except:
    GPIO.cleanup()


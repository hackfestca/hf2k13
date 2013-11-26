#!/usr/bin/env python
# coding: UTF-8
#    The missile launcher controller interface
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
# code extracted from nigiri
# This code needs urwid version: 1.0.1-2 (debian stable repo)
#
# Dependencies:
# 	aptitude update; aptitude install pip
# 	pip install pyusb
#
# ToDo: make a script that move missiles launchers randomly (turned off when someone login)
#

import os
import sys
import traceback
import re
import time
import copy
import logging
import locale
import commands
import inspect
import usb.core
import urwid
import shelve
import subprocess

import RPi.GPIO as GPIO
from logging.handlers import TimedRotatingFileHandler
from threading import Thread
from datetime import datetime,timedelta
from urwid import MetaSignals

class Singleton:
    """
    A non-thread-safe helper class to ease implementing singletons.
    This should be used as a decorator -- not a metaclass -- to the
    class that should be a singleton.

    The decorated class can define one `__init__` function that
    takes only the `self` argument. Other than that, there are
    no restrictions that apply to the decorated class.

    To get the singleton instance, use the `Instance` method. Trying
    to use `__call__` will result in a `TypeError` being raised.

    Limitations: The decorated class cannot be inherited from.
    """

    def __init__(self, decorated):
        self._decorated = decorated

    def getInstance(self):
        """
        Returns the singleton instance. Upon its first call, it creates a
        new instance of the decorated class and calls its `__init__` method.
        On all subsequent calls, the already created instance is returned.

        """
        try:
            return self._instance
        except AttributeError:
            self._instance = self._decorated()
            return self._instance

    def __call__(self):
        raise TypeError('Singletons must be accessed through `Instance()`.')

    def __instancecheck__(self, inst):
        return isinstance(inst, self._decorated)


class MissileLauncher(Thread):
    """
    This is the missile launcher controller class. 
    """
    _dev = None
    _shallEnd = False
    id = None

    def __init__(self,dev, id):
        Thread.__init__(self)
        self.daemon=True
        self._dev = dev
        self.id = id
        self._setupDevice()
    
    def _setupDevice(self):
        if self._dev is None:
            raise ValueError('Launcher not found.')
        if self._dev.is_kernel_driver_active(0) is True:
            self._dev.detach_kernel_driver(0)
            self._dev.set_configuration()

    def run(self):
        """
        """
        while not self._shallEnd:
            try:
                time.sleep(1)
            except KeyboardInterrupt:
                break

    def up(self,delay):
        self.stop()
        self._dev.ctrl_transfer(0x21,0x09,0,0,[0x02,0x02,0x00,0x00,0x00,0x00,0x00,0x00]) 
        time.sleep(delay/1000)
        self.stop()
    
    def down(self,delay):
        self.stop()
        self._dev.ctrl_transfer(0x21,0x09,0,0,[0x02,0x01,0x00,0x00,0x00,0x00,0x00,0x00])
        time.sleep(delay/1000)
        self.stop()
    
    def left(self,delay):
        self.stop()
        self._dev.ctrl_transfer(0x21,0x09,0,0,[0x02,0x04,0x00,0x00,0x00,0x00,0x00,0x00])
        time.sleep(delay/1000)
        self.stop()
    
    def right(self,delay):
        self.stop()
        self._dev.ctrl_transfer(0x21,0x09,0,0,[0x02,0x08,0x00,0x00,0x00,0x00,0x00,0x00])
        time.sleep(delay/1000)
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
        """
        Nice but will it really ever be coded...?
        """
        pass

class MissilesController():
    """

    """
    ID_VENDOR = 0x2123
    ID_PRODUCT = 0x1010
    TIME_WAIT_DELAY = 3    # in seconds

    _mlList = []
    _nextId = 0
    enabledML = set()

    def __init__(self, info_callback, warning_callback, error_callback):
        self.print_info = info_callback
        self.print_warning = warning_callback
        self.print_error = error_callback
        self._configLogs()

    def _configLogs(self):
        """
        This method configure the logs for this object. 
        """
        logFormat = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        dateTimeFormat = '%Y-%m-%d %H:%M:%S'
        logFile = 'missile2k13.log'
        logDir = 'logs'

        fh = TimedRotatingFileHandler(os.path.join(logDir,logFile), \
                                      backupCount=0, \
                                      when='d', \
                                      interval=1)
        fh.setFormatter(logging.Formatter(logFormat, dateTimeFormat))

        self.log = logging.getLogger('MissileController')
        self.log.addHandler(fh)
        self.log.setLevel(logging.DEBUG)

    def _getDevice(self,no):
        devs = usb.core.find(find_all=True,idVendor=self.ID_VENDOR, idProduct=self.ID_PRODUCT)
        dev = None
        no = int(no)
        if len(devs) >= no + 1:
            dev = devs[no]
        else:
            self.print_warning('Launcher not found.')
        return dev

    def registerDevice(self,dev):
        if dev:
            oML = MissileLauncher(dev, self._nextId)
            oML.start()
            self._mlList.append(oML)
            self._nextId = self._nextId + 1
        else:
            self.print_error('Failed to register device')

    def registerDevices(self):
        devs = usb.core.find(find_all=True,idVendor=self.ID_VENDOR, idProduct=self.ID_PRODUCT)
        for dev in devs:
            self.registerDevice(dev)
        self.print_info('%s device(s) are detected' % str(len(devs)))

    def enable(self, mlId):
        self.enabledML.add(int(mlId))
        self.print_info('Enabled missile #' + str(mlId))
        self.log.info('Enabled missile #' + str(mlId))
    
    def disable(self, mlId):
        iMlId = int(mlId)
        if iMlId in self.enabledML:
            self.enabledML.remove(iMlId)
            self.print_info('Disabled missile #' + str(mlId))
            self.log.info('Disabled missile #' + str(mlId))

    def up(self, duration):
        for ml in self._mlList:
            if ml.id in self.enabledML:
                ml.up(duration)

    def down(self, duration):
        for ml in self._mlList:
            if ml.id in self.enabledML:
                ml.down(duration)

    def left(self, duration):
        for ml in self._mlList:
            if ml.id in self.enabledML:
                ml.left(duration)

    def right(self, duration):
        for ml in self._mlList:
            if ml.id in self.enabledML:
                ml.right(duration)

    def fire(self):
        if self.isReady():
            hasFired = False
            for ml in self._mlList:
                mlShotLeft = DBController.getInstance().getDB()['remainingMissiles'][ml.id]
                if ml.id in self.enabledML and mlShotLeft > 0:
                    self.print_info('Firing #' + str(ml.id))
                    ml.fire()
    
                    self.print_info('Analyzing crashes...')
                    oCD = CrashDetector()
                    aResult = oCD.getCrashedBuildings()
                    del oCD
                    oCD = None
                    if len(aResult) > 0:
                        self.printFlags(aResult)
                        self.logCrash(aResult)
                    else:
                        self.print_warning('No crash was detected')
        
                    DBController.getInstance().launchMissile(ml.id, aResult)
            else:
                    self.print_warning('No missile was launched. Ensure that you have enabled missiles launchers and that there are remaining missiles.')
        else:
            self.print_warning('Missile Launchers not ready. Time left before next launch: ' + str(timedelta(seconds=self.getTimeLeftBeforeReady())))

    def reset(self):
        for ml in self._mlList:
            if ml.id in self.enabledML:
                ml.reset()

    def getList(self):
        pass

    def getPrintableList(self):
        result = "\n"
        result += "* Missiles Launchers informations * \n"
        for ml in self._mlList:
            result += '    id: ' + str(ml.id) + "\n"
            result += '    thread.isAlive(): ' + str(ml.isAlive()) + "\n"
            result += '    enabled: ' + str(ml.id in self.enabledML) + "\n"
            result += "\n"
        return result

    def getCount(self):
        return len(self._mlList)

    def printFlags(self, aResult):
        oDB = DBController.getInstance()
        for buildId in aResult:
            flag = oDB.getDB()['buildings'][buildId]['flag']
            self.print_info('Congratulation, you have successfuly crashed building #' + str(buildId) + ', here is a flag: ' + str(flag))
        #oDB.close()

    def logCrash(self, aResult):
        oDB = DBController.getInstance()
        for buildId in aResult:
            oDB.setBuildingAsCrashed(buildId)

    def getTimeLeftBeforeReady(self):
        launches = DBController.getInstance().getDB()['launches']
        if len(launches) > 0:
            timeLeft = self.TIME_WAIT_DELAY - (datetime.today() - launches[-1]['datetime']).seconds
            if timeLeft > 0:
                return timeLeft
            else:
                return 0
        else:
            return 0

    def isReady(self):
        timeLeft = self.getTimeLeftBeforeReady()
        if timeLeft <= 0:
            return True
        else:
            return False

def shellcmd(*args, **kwargs):
    """
    This function is a signature used to identify command methods in the Console class
    """
    def decorate(func, hidden=False, name=None, type=None):
        """
        Set some attribute to a method
        """
        setattr(func, '_console_cmd', True)
        setattr(func, '_console_hidden', hidden)
        setattr(func, '_console_cmd_name', name or func.__name__)
        return func

    if len(args):
        return decorate(args[0], **kwargs)
    else:
        return lambda func: decorate(func, **kwargs)

class MissileShell():
    """
    Shell of the missile controller
    """

    # Constants
    MSG_HELP_TAIL = 'Type help <command name> to get more info about that specific command.'
    MSG_HELP_UNDEFINED_COMMAND = 'That command is not defined.'
    MSG_TOP_OF_HELP = ''
    MSG_BOTTOM_OF_HELP = ''
    DEFAULT_MOVE_DURATION = 0.02
    MAX_MOVE_DURATION = 3000    # miliseconds

    _cmds = {}
    """ 
    @ivar: This hash table contains the list of commands the console can handle in main mode
    @type: hashtable
    """

    _secureMods = {} 
    """ 
    @ivar: This hash table contains the list of secure modules from the DB. A copy is made to ensure that the modules are locked every login.
    @type: hashtable
    """

    def __init__(self, info_callback, warning_callback, error_callback):
        self.print_info = info_callback 
        self.print_warning = warning_callback
        self.print_error = error_callback
        self._configLogs()

        self.oMC = MissilesController(info_callback, warning_callback, error_callback) 
        self.oMC.registerDevices()

        for name, value in inspect.getmembers(self):
            if inspect.ismethod(value) and getattr(value, '_console_cmd', False):
                name = getattr(value, '_console_cmd_name')
                self._cmds[name] = value

        # Setup secure modules array
        self._secureMods = copy.deepcopy(DBController.getInstance().getDB()['secureMods'])

        # Print a flag
        flag = DBController.getInstance().getDB()['loginFlag']
        self.print_info("Great job, you've reached a powerful interface but it's not over. Flag: " + str(flag))

    def _configLogs(self):
        """
        This method configure the logs for this object. 
        """
        logFormat = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        dateTimeFormat = '%Y-%m-%d %H:%M:%S'
        logFile = 'missile2k13.log'
        logDir = 'logs'

        fh = TimedRotatingFileHandler(os.path.join(logDir,logFile), \
                                      backupCount=0, \
                                      when='d', \
                                      interval=1)
        fh.setFormatter(logging.Formatter(logFormat, dateTimeFormat))

        self.log = logging.getLogger('MissileShell')
        self.log.addHandler(fh)
        self.log.setLevel(logging.DEBUG)

    def __del__(self):
        pass

    def processCmd(self, text):
        """
        This method wait for raw_input() and process the user command
        """
        
        if ' ' in text:
            cmd, args = text.split(' ', 1)
        else:
            cmd, args = text, ''

        if self._cmds.has_key(cmd):
            return self._cmds[cmd](cmd, args)

    def getUserInformations(self):
        """
        Print information about source and login time
        """
        result = "* User Informations *\n"
        result += "    User: ml\n"
        result += "    Source IP: " + getSourceIP() + "\n"
        result += "\n"
        return result

    def getGeneralInformations(self):
        """
        Print general informations
        """
        result = "* General Informations *\n"
        result += "    Missiles left: " + str(sum(DBController.getInstance().getDB()['remainingMissiles'])) + "\n"
        result += "    Number of launches: " + str(len(DBController.getInstance().getDB()['launches'])) + "\n"
        result += "    Current datetime: " + str(datetime.today()) + "\n"
        result += "    Time left before ready: " + str(timedelta(seconds=self.oMC.getTimeLeftBeforeReady())) + "\n"
        result += "    Light is on?: " + str(DBController.getInstance().getDB()['lightStatus']) + "\n"
        return result

    def getSecureModsInformations(self):
        """
        Print secure modules informations
        """
        result = "* Secure modules Informations *\n"
        modList = self._secureMods
        for modName in modList:
            result += '    name: ' + str(modName) + "\n"
            result += '    description: ' + str(modList[modName]['description']) + "\n"
            result += '    locked: ' + str(modList[modName]['locked']) + "\n"
            result += "\n"
        return result

    def getLaunchLogs(self):
        """
        Print launch logs
        """
        result = "* Launch Logs *\n"
        launches = DBController.getInstance().getDB()['launches']
        for l in launches:
            result += '    Missile Launcher ID: ' + str(l['mlId']) + "\n"
            result += '    Source: ' + str(l['source']) + "\n"
            result += '    Date: ' + str(l['datetime']) + "\n"
            result += '    Crashed Buildings: ' + str(l['cb']) + "\n"
            result += "\n"
        return result

    @shellcmd(name='help')
    def _help(self, cmd, args):
        """
        Returns a help string listing available options
        Usage: help [commands]
        Details: 
        """ 
        if not args:
            description = 'Available commands:'

            usage = '\n'.join(sorted([
                '    %s   %s' % (name, (command.__doc__ or '(undocumented)').strip().split('\n', 1)[0])
                for (name, command) in self._cmds.iteritems() if not command._console_hidden
            ]))
            usage = '\n'.join(filter(None, [usage, self.MSG_HELP_TAIL]))
        else:
            description = ''
            if args in self._cmds:
                usage = (self._cmds[args].__doc__ or 'undocumented').strip()
            else:
                usage = self.MSG_HELP_UNDEFINED_COMMAND

        return '\n'.join(filter(None, [self.MSG_TOP_OF_HELP, description, usage, self.MSG_BOTTOM_OF_HELP]))

    @shellcmd(name='enable')
    def _enable(self, cmd, args):
        '''
        Enable missile launchers to use
        Usage: enable ML_ID1 [ML_ID2 ...]
        '''
        if args != '': 
            result = ''
            aIds = args.split(' ')
            for mlId in aIds:
                try:
                    iMlId = int(mlId)
                    if iMlId >= 0 and iMlId < self.oMC.getCount():
                        self.oMC.enable(iMlId)
                        result += 'Missile Launcher #' + str(iMlId) + ' has been enabled' + "\n"
                except ValueError:
                    result = 'Invalid value'
        else:
            result = 'Please provide some arguments'
        return result

    @shellcmd(name='disable')
    def _disable(self, cmd, args):
        '''
        Disable missile launchers to use
        Usage: disable ML_ID1 [ML_ID2 ...]
        '''
        if args != '': 
            result = ''
            aIds = args.split(' ')
            for mlId in aIds:
                try:
                    iMlId = int(mlId)
                    if iMlId >= 0 and iMlId < self.oMC.getCount():
                        self.oMC.disable(iMlId)
                        result += 'Missile Launcher #' + str(iMlId) + ' has been disabled' + "\n"
                except ValueError:
                    result = 'Invalid value'
        else:
            result = 'Please provide some arguments'
        return result

    @shellcmd(name='unlock')
    def _unlock(self, cmd, args):
        '''
        Unlock a missile launcher module
        Usage: unlock MODULE_NAME KEY
        '''
        if args != '': 
            aArgs = args.split(' ')
            if len(aArgs) == 2:
                modName = str(aArgs[0])
                key = str(aArgs[1])
                oDB = DBController.getInstance()
                if self._secureMods.has_key(modName) and \
                   self._secureMods[modName]['key'] == key:
                    self._secureMods[modName]['locked'] = False
                    result = 'Module unlocked successfuly'
                else:
                    result = 'Invalid module/key pair'
            else:
                result = 'Invalid number of arguments'
        else:
            result = 'Please specify some arguments'
        return result

    @shellcmd(name='light')
    def _light(self, cmd, args):
        '''
        Light up the terrorist cavern
        Usage: light on|off
        '''
        if args != '': 
            aArgs = args.split(' ')
            if len(aArgs) == 1:
                state = str(aArgs[0])
                if state == 'on':
                    DBController.getInstance().getDB()['lightStatus'] = True
                    DBController.getInstance().sync()
                    result = 'Light is turned on'
                elif state == 'off':
                    DBController.getInstance().getDB()['lightStatus'] = False
                    DBController.getInstance().sync()
                    result = 'Light is turned off'
                else:
                    result = 'Invalid value'
            else:
                result = 'Invalid number of arguments'
        else:
            result = 'Please specify some arguments'
        return result

    @shellcmd(name='show')
    def _show(self, cmd, args):
        '''
        Display informations
        Usage: show
        '''
        return "\n" + \
               self.getUserInformations() + \
               self.getGeneralInformations() + \
               self.oMC.getPrintableList() + \
               self.getSecureModsInformations() + \
               self.getLaunchLogs()

#    @shellcmd(name='register_all')
#    def _registerAll(self, cmd, args):
#        '''
#        Force a register_all of the usb devices
#        Usage: register_all
#        '''
#        return self.oMC.registerDevices()

    @shellcmd(name='ml')
    def _moveLeft(self, cmd, args):
        '''
        Move left selected ML
        Usage: ml [duration (miliseconds)]
        '''
        if args != '' and float(args) > 0 and float(args) < self.MAX_MOVE_DURATION:
            duration = float(args)
            self.oMC.left(duration)
        else:
            self.oMC.left(self.DEFAULT_MOVE_DURATION)
        result = ''
        return result

    @shellcmd(name='mr')
    def _moveRight(self, cmd, args):
        '''
        Move right selected ML
        Usage: mr [duration (miliseconds)]
        '''
        if args != '' and float(args) > 0 and float(args) < self.MAX_MOVE_DURATION:
            duration = float(args)
            self.oMC.right(duration)
        else:
            self.oMC.right(self.DEFAULT_MOVE_DURATION)
        result = ''
        return result

    @shellcmd(name='mu')
    def _moveUp(self, cmd, args):
        '''
        Move up selected ML
        Usage: mu [duration (miliseconds)]
        '''
        if args != '' and float(args) > 0 and float(args) < self.MAX_MOVE_DURATION:
            duration = float(args)
            self.oMC.up(duration)
        else:
            self.oMC.up(self.DEFAULT_MOVE_DURATION)
        result = ''
        return result

    @shellcmd(name='md')
    def _moveDown(self, cmd, args):
        '''
        Move down selected ML
        Usage: md [duration (miliseconds)]
        '''
        if args != '' and float(args) > 0 and float(args) < self.MAX_MOVE_DURATION:
            duration = float(args)
            self.oMC.down(duration)
        else:
            self.oMC.down(self.DEFAULT_MOVE_DURATION)
        result = ''
        return result

    @shellcmd(name='fire')
    def _fire(self, cmd, args):
        '''
        Fire in tha hole!
        Usage: fire
        '''
        bLocked = self._secureMods['fire']['locked']
        if bLocked:
            result = 'Module is locked. Unlock it first with "unlock fire KEY"'
        else:
            self.oMC.fire()
            result = ''
        return result

class CrashDetector():
    bsLogFile = '/root/logs/buildingSensor.log'
    bsLogDateTimeFormat = '%Y-%m-%d %H:%M:%S'
    events = []
    curDateTime = None
    waitForTimeValue = 2
    recentTimeValue = 10
    #recentTimeValue = 60

    def __init__(self):
        self.curDateTime = datetime.now()
        self._configLogs()
        self.events = []

    def _configLogs(self):
        """
        This method configure the logs for this object. 
        """
        logFormat = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        dateTimeFormat = '%Y-%m-%d %H:%M:%S'
        logFile = 'missile2k13.log'
        logDir = 'logs'

        fh = TimedRotatingFileHandler(os.path.join(logDir,logFile), \
                                      backupCount=0, \
                                      when='d', \
                                      interval=1)
        fh.setFormatter(logging.Formatter(logFormat, dateTimeFormat))

        self.log = logging.getLogger('CrashDetector')
        self.log.addHandler(fh)
        self.log.setLevel(logging.DEBUG)

    def _importRecentCrashEvents(self):
        f = open(self.bsLogFile, 'r')
        for l in f:
            entry = l.split(' - ', 4)
            if len(entry) > 3 and\
               self._eventIsRecent(entry[0]) and\
               entry[3].startswith('Building'):
                self.events.append({'datetime': entry[0], 'source': entry[1], 'type': entry[2], 'text': entry[3]})
        f.close()

    def _eventIsRecent(self, sTime):
       #self.log.debug('eventIsRecent: ' + str(self.recentTimeValue - (datetime.strptime(sTime, self.bsLogDateTimeFormat) - self.curDateTime).seconds))
       return self.recentTimeValue - (datetime.strptime(sTime, self.bsLogDateTimeFormat) - self.curDateTime).seconds >= 0 

    def getCrashedBuildings(self):
        time.sleep(self.waitForTimeValue)
        aResult = set()
        self.log.info('Importing recent crash events')
        self._importRecentCrashEvents()
        self.log.info('Import done')
        for e in self.events:
            self.log.debug(str(e))
            if e['text'].startswith('Building #1 crashed'):
                self.log.info('Detected crash on building #1')
                aResult.add(0)
            if e['text'].startswith('Building #2 crashed'):
                self.log.info('Detected crash on building #2')
                aResult.add(1)
        self.events = []
        self.events = None
        return aResult

@Singleton
class DBController():
    #dbFile = '/root/missile2k13.shelve'
    dbFile = 'missile2k13.shelve'
    d = None

    def __init__(self):
        self._configLogs()
        self.log.info('Opening shelve (' + str(self.dbFile) + ')')
        self.d = shelve.open(self.dbFile, writeback=True)
        self.log.debug(self.d)

    def _configLogs(self):
        """
        This method configure the logs for this object. 
        """
        logFormat = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        dateTimeFormat = '%Y-%m-%d %H:%M:%S'
        logFile = 'missile2k13.log'
        logDir = 'logs'

        fh = TimedRotatingFileHandler(os.path.join(logDir,logFile), \
                                      backupCount=0, \
                                      when='d', \
                                      interval=1)
        fh.setFormatter(logging.Formatter(logFormat, dateTimeFormat))

        self.log = logging.getLogger('DBController')
        self.log.addHandler(fh)
        self.log.setLevel(logging.DEBUG)

    def getDB(self):
        return self.d

    def sync(self):
        self.d.sync()

    def close(self):
        self.d.close()

    def launchMissile(self, mlId, crashedBuildings):
        # Decrement remaining missiles number
        self.d['remainingMissiles'][mlId] -= 1

        # Log attempt
        self.d['launches'].append({'mlId': str(mlId), 'source': getSourceIP(), 'datetime': datetime.now(), 'cb': str(crashedBuildings)})

    def setBuildingAsCrashed(self, buildId):
        # Set building as crashed
        self.d['buildings'][buildId]['crashed'] = True

        # Set flag as given
        flag = self.d['buildings'][buildId]['flag']
        if self.d.has_key('flagsGiven'):
            self.d['flagsGiven'].append(flag)
            self.d.sync()
        else:
            self.log.debug('Could not append flag to flagsGiven')
        #self.d.close()

class ExtendedListBox(urwid.ListBox):
    """
        Listbow widget with embeded autoscroll
    """

    __metaclass__ = urwid.MetaSignals
    signals = ["set_auto_scroll"]


    def set_auto_scroll(self, switch):
        if type(switch) != bool:
            return
        self._auto_scroll = switch
        urwid.emit_signal(self, "set_auto_scroll", switch)


    auto_scroll = property(lambda s: s._auto_scroll, set_auto_scroll)


    def __init__(self, body):
        urwid.ListBox.__init__(self, body)
        self.auto_scroll = True


    def switch_body(self, body):
        if self.body:
            urwid.disconnect_signal(body, "modified", self._invalidate)

        self.body = body
        self._invalidate()

        urwid.connect_signal(body, "modified", self._invalidate)


    def keypress(self, size, key):
        urwid.ListBox.keypress(self, size, key)

        if key in ("page up", "page down"):
            logging.debug("focus = %d, len = %d" % (self.get_focus()[1], len(self.body)))
            if self.get_focus()[1] == len(self.body)-1:
                self.auto_scroll = True
            else:
                self.auto_scroll = False
            logging.debug("auto_scroll = %s" % (self.auto_scroll))


    def scroll_to_bottom(self):
        logging.debug("current_focus = %s, len(self.body) = %d" % (self.get_focus()[1], len(self.body)))

        if self.auto_scroll:
            # at bottom -> scroll down
            self.set_focus(len(self.body))



"""
 -------context-------
| --inner context---- |
|| HEADER            ||
||                   ||
|| BODY              ||
||                   ||
|| DIVIDER           ||
| ------------------- |
| FOOTER              |
 ---------------------

inner context = context.body
context.body.body = BODY
context.body.header = HEADER
context.body.footer = DIVIDER
context.footer = FOOTER

HEADER = Notice line (urwid.Text)
BODY = Extended ListBox
DIVIDER = Divider with information (urwid.Text)
FOOTER = Input line (Ext. Edit)
"""


class MainWindow(object):

    __metaclass__ = MetaSignals
    signals = ["quit","keypress"]

    _palette = [
            ('divider','black','dark cyan', 'standout'),
            ('text','light gray', 'default'),
            ('bold_text', 'light gray', 'default', 'bold'),
            ('client_text','light gray', 'default'),
            ('server_text', 'light blue', 'default'),
            ('info_text', 'light green', 'default'),
            ('warning_text', 'yellow', 'default'),
            ('error_text', 'light red', 'default'),
            ("body", "text"),
            ("footer", "text"),
            ("header", "text"),
        ]

    for type, bg in (
            ("div_fg_", "dark cyan"),
            ("", "default")):
        for name, color in (
                ("red","dark red"),
                ("blue", "dark blue"),
                ("green", "dark green"),
                ("yellow", "yellow"),
                ("magenta", "dark magenta"),
                ("gray", "light gray"),
                ("white", "white"),
                ("black", "black")):
            _palette.append( (type + name, color, bg) )


    def __init__(self, sender="1234567890"):
        self.shall_quit = False
        self.sender = sender
        self.shell = None


    def main(self):
        """ 
            Entry point to start UI 
        """

        self.ui = urwid.raw_display.Screen()
        self.ui.register_palette(self._palette)
        self.build_interface()
        self.shell = MissileShell(self.print_info, self.print_warning, self.print_error)
        self.ui.run_wrapper(self.run)


    def run(self):
        """ 
            Setup input handler, invalidate handler to
            automatically redraw the interface if needed.

            Start mainloop.
        """

        # I don't know what the callbacks are for yet,
        # it's a code taken from the nigiri project
        def input_cb(key):
            if self.shall_quit:
                raise urwid.ExitMainLoop
            self.keypress(self.size, key)

        self.size = self.ui.get_cols_rows()

        self.main_loop = urwid.MainLoop(
                self.context,
                screen=self.ui,
                handle_mouse=False,
                unhandled_input=input_cb,
            )

        def call_redraw(*x):
            self.draw_interface()
            invalidate.locked = False
            return True

        inv = urwid.canvas.CanvasCache.invalidate

        def invalidate (cls, *a, **k):
            inv(*a, **k)

            if not invalidate.locked:
                invalidate.locked = True
                self.main_loop.set_alarm_in(0, call_redraw)

        invalidate.locked = False
        urwid.canvas.CanvasCache.invalidate = classmethod(invalidate)

        try:
            self.main_loop.run()
        except KeyboardInterrupt:
            self.quit()


    def quit(self, exit=True):
        """ 
            Stops the ui, exits the application (if exit=True)
        """
        urwid.emit_signal(self, "quit")

        self.shall_quit = True

        if exit:
            sys.exit(0)


    def build_interface(self):
        """ 
            Call the widget methods to build the UI 
        """

        self.header = urwid.Text("HF City Missile Launcher control center")
        self.footer = urwid.Edit("> ")
        self.divider = urwid.Text("Initializing.")

        self.generic_output_walker = urwid.SimpleListWalker([])
        self.body = ExtendedListBox(self.generic_output_walker)
        self.header = urwid.AttrWrap(self.header, "divider")
        self.footer = urwid.AttrWrap(self.footer, "footer")
        self.divider = urwid.AttrWrap(self.divider, "divider")
        self.body = urwid.AttrWrap(self.body, "body")

        self.footer.set_wrap_mode("space")

        main_frame = urwid.Frame(self.body, 
                                header=self.header,
                                footer=self.divider)
        
        self.context = urwid.Frame(main_frame, footer=self.footer)

        self.divider.set_text(("divider",
                               ("Enter a command (help for list):")))

        self.context.set_focus("footer")



    def draw_interface(self):
        self.main_loop.draw_screen()


    def keypress(self, size, key):
        """ 
            Handle user inputs
        """

        urwid.emit_signal(self, "keypress", size, key)

        # scroll the top panel
        if key in ("page up","page down"):
            self.body.keypress (size, key)

        # resize the main windows
        elif key == "window resize":
            self.size = self.ui.get_cols_rows()

        elif key in ("ctrl d", 'ctrl c'):
            self.quit()

        elif key == "enter":
            # Parse data or (if parse failed)
            # send it to the current world
            text = self.footer.get_edit_text()

            self.footer.set_edit_text(" "*len(text))
            self.footer.set_edit_text("")

            if text in ('quit', 'q'):
                self.quit()

            if text.strip():
                self.print_sent_message(text)
                reply = self.shell.processCmd(text)
                if reply != None:
                    self.print_received_message(reply)

        else:
            self.context.keypress (size, key)

 
    def print_sent_message(self, text):
        """
            Print a received message
        """

        self.print_text(('client_text', ('[%s] You: %s' % (self.get_time(), text))))
 
 
    def print_received_message(self, text):
        """
            Print a sent message
        """
        self.print_text(('server_text', ('[%s] System: %s' % (self.get_time(), text))))

    def print_info(self, text):
        """
            Print an info message
        """
        self.print_text(('info_text', ('[%s] Info: %s' % (self.get_time(), text))))

    def print_warning(self, text):
        """
            Print a warning message
        """
        self.print_text(('warning_text', ('[%s] Warning: %s' % (self.get_time(), text))))


    def print_error(self, text):
        """
            Print an error message
        """
        self.print_text(('error_text', ('[%s] Error: %s' % (self.get_time(), text))))

        
    def print_text(self, text):
        """
            Print the given text in the _current_ window
            and scroll to the bottom. 
            You can pass a Text object or a string
        """

        walker = self.generic_output_walker

        if not isinstance(text, urwid.Text):
            text = urwid.Text(text)

        walker.append(text)

        self.body.scroll_to_bottom()


    def get_time(self):
        """
            Return formated current datetime
        """
        return datetime.now().strftime('%H:%M:%S')
        
def getSourceIP():
    cmd = "w | grep ^ml | awk '{ print $3 }'"
    p1 = subprocess.Popen(['w'], stdout=subprocess.PIPE)
    p2 = subprocess.Popen(['grep', '^ml'], stdin=p1.stdout, stdout=subprocess.PIPE)
    p3 = subprocess.Popen(['awk', '{ print $3 }'], stdin=p2.stdout, stdout=subprocess.PIPE)
    output = p3.communicate()[0]
    if output[-1] == "\n":
        output = output[:-1]
    return str(output)

def except_hook(extype, exobj, extb, manual=False):
    if not manual:
        try:
            main_window.quit(exit=False)
        except NameError:
            pass

    message = _("An error occured:\n%(divider)s\n%(traceback)s\n"\
        "%(exception)s\n%(divider)s" % {
            "divider": 20*"-",
            "traceback": "".join(traceback.format_tb(extb)),
            "exception": extype.__name__+": "+str(exobj)
        })

    logging.error(message)

    print >> sys.stderr, message


def setup_logging():
    """ set the path of the logfile to tekka.logfile config
        value and create it (including path) if needed.
        After that, add a logging handler for exceptions
        which reports exceptions catched by the logger
        to the tekka_excepthook. (DBus uses this)
    """
    try:
        class ExceptionHandler(logging.Handler):
            """ handler for exceptions caught with logging.error.
                dump those exceptions to the exception handler.
            """
            def emit(self, record):
                if record.exc_info:
                    except_hook(*record.exc_info)

        logfile = 'logs/missile2k13.log'
        logdir = os.path.dirname(logfile)

        if not os.path.exists(logdir):
            os.makedirs(logdir)

        logging.basicConfig(filename=logfile, level=logging.DEBUG,
            filemode="w")

        logging.getLogger("Missile2k13").addHandler(ExceptionHandler())

    except BaseException, e:
        print >> sys.stderr, "Logging init error: %s" % (e)


if __name__ == "__main__":
    setup_logging()
    main_window = MainWindow()
    sys.excepthook = except_hook
    main_window.main()

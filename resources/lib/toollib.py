# encoding=utf8

import sys
reload(sys)
sys.setdefaultencoding('utf8')

import random
import xbmcaddon
import xbmc
import xbmcgui
import json
import re
import platform
import os

ADDON = xbmcaddon.Addon()
ADDON_ID = ADDON.getAddonInfo('id')
ADDON_NAME = ADDON.getAddonInfo('name')
ADDON_VERSION = ADDON.getAddonInfo('version')
ADDON_LOC = ADDON.getLocalizedString

OSD = xbmcgui.Dialog()

# Constants

STRING = 0
BOOL = 1
NUM = 2

class CryptDecrypt(object):
    '''
    :param passw: ID/Name of the associated password item in settings.xml
    :param key: ID of the associated key in settings, will be generated at first run
    :param token: ID of the token in settings, generated from password/key
    :return: decrypted password if password in settings is empty or *, else set password to '*' and generates key/token,
             stores password into settings.xml, key/token within userdata/addon_data/addon_id/settings.xml
    '''

    def __init__(self, passw, key, token):

        self.passw = ADDON.getSetting(passw)

        self.__pw_item = passw
        self.__key = ADDON.getSetting(key)
        self.__key_item = key
        self.__token = ADDON.getSetting(token)
        self.__token_item = token


    def persist(self):
        ADDON.setSetting(self.__key_item, self.__key)
        ADDON.setSetting(self.__token_item, self.__token)
        ADDON.setSetting(self.__pw_item, '*')


    def crypt(self):

        if self.passw == '' or self.passw == '*':
            if len(self.__key) > 2: return "".join([chr(ord(self.__token[i]) ^ ord(self.__key[i])) for i in range(int(self.__key[-2:]))])
            return ''
        else:
            self.__key = ''
            for i in range((len(self.passw) / 16) + 1):
                self.__key += ('%016d' % int(random.random() * 10 ** 16))
            self.__key = self.__key[:-2] + ('%02d' % len(self.passw))
            __tpw = self.passw.ljust(len(self.__key), 'a')

            self.__token = "".join([chr(ord(__tpw[i]) ^ ord(self.__key[i])) for i in range(len(self.__key))])
            self.persist()
            return self.passw

class OsRelease(object):

    def __init__(self):
        self.platform = platform.system()
        self.hostname = platform.node()
        item = {}
        if self.platform == 'Linux':

            try:
                with open('/etc/os-release', 'r') as _file:
                    for _line in _file:
                        parameter, value = _line.split('=')
                        item[parameter] = value
            except IOError, e:
                KodiLib.writeLog(e.message, xbmc.LOGERROR)

        self.osname = item.get('NAME', 'unknown')
        self.osid = item.get('ID', 'unknown')
        self.osversion = item.get('VERSION_ID', 'unknown')

class KodiLib(object):
    '''
    several Kodi routines and functions
    '''

    def __strToBool(self, par):
        return True if par.upper() == 'TRUE' else False

    def writeLog(self, message, level=xbmc.LOGDEBUG):
        try:
            xbmc.log('[%s %s]: %s' % (ADDON_ID, ADDON_VERSION, message), level)
        except Exception:
            xbmc.log('[%s %s]: %s' % (ADDON_ID, ADDON_VERSION, 'Fatal: Could not log message'), xbmc.LOGERROR)

    def jsonrpc(self, query):
        querystring = {"jsonrpc": "2.0", "id": 1}
        querystring.update(query)
        try:
            response = json.loads(xbmc.executeJSONRPC(json.dumps(querystring, encoding='utf-8')))
            if 'result' in response: return response['result']
        except TypeError, e:
            self.writeLog('Error executing JSON RPC: %s' % (e.message), xbmc.LOGERROR)
        return False

    def getAddonSetting(self, setting, sType=STRING, multiplicator=1):
        if sType == BOOL:
            return self.__strToBool(ADDON.getSetting(setting))
        elif sType == NUM:
            try:
                return int(re.match('\d+', ADDON.getSetting(setting)).group()) * multiplicator
            except AttributeError:
                self.writeLog('Could not read setting type NUM: %s' % (setting), xbmc.LOGERROR)
                return 0
        else:
            return ADDON.getSetting(setting)

    def notify(self, title, message, icon=xbmcgui.NOTIFICATION_INFO, hide=False):
        if not hide:
            OSD.notification(title, message, icon)


class jsonIO(object):

    def __init__(self, path, file):
        self.path = path
        self.file = file
        if not os.path.exists(self.path): os.makedirs(self.path)
        self.path_and_file = os.path.join(path, file)

    def read(self):
        if os.path.exists(self.path_and_file):
            try:
                with open(self.path_and_file, 'r') as j_obj:
                    jl = json.load(j_obj)
                j_obj.close()
                return jl
            except ValueError as e:
                KodiLib().writeLog(e.message, xbmc.LOGERROR)
        return []

    def write(self, items):
        with open(self.path_and_file, 'w') as j_obj:
            json.dump(items, j_obj, ensure_ascii=False)
        j_obj.close()

    def delete(self):
        os.remove(self.path_and_file)

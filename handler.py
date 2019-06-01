from resources.lib.toollib import *

ADDON_PROFILE = xbmc.translatePath(ADDON.getAddonInfo('Profile'))
jIO = jsonIO(ADDON_PROFILE, 'bingelist.json')
kl = KodiLib()

OSDProgress = xbmcgui.DialogProgress()

gaps = [3, 5, 10, 15, 30]
s_gap = gaps[kl.getAddonSetting('gap', NUM)]
show_progress = kl.getAddonSetting('progress', BOOL)
skip = kl.getAddonSetting('skip_played', BOOL)

def bool2string(boolean, str4true, str4false):
    if boolean: return str4true
    return str4false


class ContextHandler():

    def __init__(self):
        self.bingelist = jIO.read()
        self.bl_count = len(self.bingelist)

    def create_bingelist(self):

        _li = []
        _idx = 0
        for bingeitem in self.bingelist:
            liz = xbmcgui.ListItem(label=bingeitem['item'].get('title', 'undefined'),
                                   label2=bool2string(bingeitem['item'].get('has_played', False), ADDON_LOC(32001), ADDON_LOC(32002)),
                                   iconImage=bingeitem['item'].get('thumb', xbmcgui.ICON_TYPE_VIDEOS))
            liz.setProperty('idx', str(_idx))
            _li.append(liz)
            _idx += 1
        return _li

    def binge_player(self, entry=0):

        player = xbmc.Player()
        monitor = xbmc.Monitor()
        has_played = 0
        for idx in range(entry, len(self.bingelist)):
            bl_item = self.bingelist[idx]
            if not bl_item['item'].get('has_played', False) or not skip:

                if show_progress:
                    countdown = s_gap
                    OSDProgress.create(ADDON_LOC(32000), ADDON_LOC(32006) % countdown)
                    while countdown >= 0:
                        OSDProgress.update(100 * countdown / s_gap, ADDON_LOC(32000), ADDON_LOC(32006) % countdown)
                        xbmc.sleep(1000)
                        countdown -= 1
                        if OSDProgress.iscanceled():
                            OSDProgress.close()
                            return False
                    OSDProgress.close()


                # play video
                kl.notify(ADDON_LOC(32003) % (idx + 1, self.bl_count), bl_item['item'].get('title'))
                kl.writeLog('Playing \'%s\'' % bl_item['item'].get('title'))
                player.play(bl_item['item'].get('path', None))

                while not monitor.waitForAbort(2):
                    if player.isPlaying():
                        if bl_item['item'].get('total_time', 0) == 0:
                            bl_item['item'].update({'total_time': player.getTotalTime()})
                        bl_item['item'].update({'position': player.getTime()})
                    else:
                        break
                has_played += 1
                bl_item['item'].update({'has_played': True})
                jIO.write(self.bingelist)

        if has_played < 1:
            OSD.ok(ADDON_LOC(32000), ADDON_LOC(32005))
            return False

    def add_item(self):

        bl_item = dict()
        bl_item.update({'item': {'path': xbmc.getInfoLabel('ListItem.FilenameAndPath'),
                                 'title': xbmc.getInfoLabel('ListItem.Label'),
                                 'thumb': xbmc.getInfoLabel('ListItem.Thumb'),
                                 'has_played': False,
                                 'position': 0,
                                 'total_time': 0}})
        self.bingelist.append(bl_item)
        jIO.write(self.bingelist)
        kl.writeLog('\'%s\' added as %s. item to binge list' % (bl_item['item'].get('title'), len(self.bingelist)))

    def play_all(self, list_only=False):

        if self.bl_count == 0 and not list_only:
            OSD.ok(ADDON_LOC(32000), ADDON_LOC(32004))
            return False

        if not list_only:
            self.binge_player(entry=0)
        else:
            _li = self.create_bingelist()
            _idx = OSD.select(ADDON_LOC(32000), _li, useDetails=True)

    def play_item(self):

        if self.bl_count == 0:
            OSD.ok(ADDON_LOC(32000), ADDON_LOC(32004))
            return False

        _li = self.create_bingelist()
        _idx = OSD.select(ADDON_LOC(32000), _li, useDetails=True)
        if _idx > -1:
            kl.writeLog('Play from pos %s' % (_idx + 1))
            self.binge_player(entry=_idx)

    def mark_item(self):

        _li = self.create_bingelist()
        _idx = OSD.select(ADDON_LOC(32000), _li, useDetails=True)
        if _idx > -1:
            bl_item = self.bingelist[_idx]
            kl.writeLog('Toggle item at pos %s' % (_idx + 1))
            _current = bl_item['item'].get('has_played', False)
            print str(_current)
            bl_item['item'].update({'has_played': not _current})
            jIO.write(self.bingelist)

    def clear_all(self):
        jIO.delete()
        kl.writeLog('Binge list deleted')

if __name__ == '__main__':
    ch = ContextHandler()
    if ch.bl_count > 0:
        _li = []
        for item in range(32012, 32017):
            liz = xbmcgui.ListItem(label=ADDON_LOC(item))
            _li.append(liz)
        _idx = OSD.select(ADDON_LOC(32000), _li)
        if _idx == 0:
            ch.play_all(list_only=True)
        elif _idx == 1:
            ch.play_all()
        elif _idx == 2:
            ch.play_item()
        elif _idx == 3:
            ch.mark_item()
        elif _idx == 4:
            ch.clear_all()
        else:
            pass
    else:
        OSD.ok(ADDON_LOC(32000), ADDON_LOC(32004))
    del ch


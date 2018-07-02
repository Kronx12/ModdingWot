""" *************************************
Mod autors: Kotyarko_O, Ktulho & night_dragon_on
Mod file name: mod_safeShot.pyc
Mod settings: safeShot.json
Url page: https://goo.gl/TJW6U0
Forum page: https://goo.gl/2XVCpP
************************************* """
from coreMods import cfgLoader, registerEvent, overrideMethod
import game
from BigWorld import player, target, serverTime
from Avatar import PlayerAvatar
from messenger import MessengerEntry
from gui.Scaleform.daapi.view.battle.classic.stats_exchange import FragsCollectableStats
config = cfgLoader('mods/configs/camAddons/safeShot.json', 'local')
safeShotConfig = config('safeShot')
safeShotEnabled = safeShotConfig['enabled']
deadBlockEnabled = safeShotConfig.get('deadShotBlock', False)
deadBlockTimeOut = safeShotConfig.get('deadShotBlockTimeOut', 2)
lastClientMessageTime = None
lastChatMessageTime = None
hotKeyPressed = False
deadDict = {}

def addClientMessage(msg):
    global lastClientMessageTime
    if len(msg) == 0:
        return
    if lastClientMessageTime is None:
        MessengerEntry.g_instance.gui.addClientMessage(msg)
    else:
        if serverTime() - lastClientMessageTime > 3:
            MessengerEntry.g_instance.gui.addClientMessage(msg)
    lastClientMessageTime = serverTime()
    return


def addChatMessage(msg):
    global lastChatMessageTime
    if len(msg) == 0:
        return
    if lastChatMessageTime is None:
        player().guiSessionProvider.shared.chatCommands.proto.arenaChat.broadcast(msg, 0)
    else:
        if serverTime() - lastChatMessageTime > 3:
            player().guiSessionProvider.shared.chatCommands.proto.arenaChat.broadcast(msg, 0)
    lastChatMessageTime = serverTime()
    return


@registerEvent(FragsCollectableStats, 'addVehicleStatusUpdate')
def FragsCollectableStats_addVehicleStatusUpdate(self, vInfoVO):
    global deadBlockEnabled
    global deadDict
    global safeShotEnabled
    if not vInfoVO.isAlive() and safeShotEnabled and deadBlockEnabled:
        deadDict.update({vInfoVO.vehicleID: serverTime()})


@registerEvent(game, 'handleKeyEvent')
def handleKeyEvent(event):
    global hotKeyPressed

    def changeSafeShotState():
        global safeShotEnabled
        safeShotEnabled = not safeShotEnabled
        if safeShotConfig['disableMessage']:
            addClientMessage(('SafeShot: {}.').format(safeShotEnabled))

    if not (safeShotConfig['enabled'] and safeShotConfig['disableKey'] == event.key and not event.isRepeatedEvent() and not MessengerEntry.g_instance.gui.isFocused()):
        return
    if safeShotConfig['onHold']:
        if not hotKeyPressed and event.isKeyDown():
            hotKeyPressed = True
            changeSafeShotState()
        elif hotKeyPressed and event.isKeyUp():
            hotKeyPressed = False
            changeSafeShotState()
    else:
        if event.isKeyDown():
            changeSafeShotState()
        else:
            return


@overrideMethod(PlayerAvatar, 'shoot')
def shoot(base, self, isRepeat=False):
    global deadBlockTimeOut
    if not (safeShotConfig['enabled'] and safeShotEnabled):
        return base(self, isRepeat)
    if target() is None:
        if safeShotConfig['wasteShotBlock']:
            addClientMessage(safeShotConfig['clientMessages']['wasteShotBlockedMessage'])
            return
    else:
        if hasattr(target().publicInfo, 'team'):
            if safeShotConfig['teamShotBlock'] and player().team is target().publicInfo.team and target().isAlive():
                if not (safeShotConfig['teamKillerShotUnblock'] and player().guiSessionProvider.getArenaDP().isTeamKiller(target().id)):
                    addChatMessage(safeShotConfig['chatMessages']['teamShotBlockedMessage'].replace('{{target-name}}', target().publicInfo.name).replace('{{target-vehicle}}', target().typeDescriptor.type.shortUserString))
                    addClientMessage(safeShotConfig['clientMessages']['teamShotBlockedMessage'])
                    return
            else:
                if deadBlockEnabled and not target().isAlive() and (deadBlockTimeOut == 0 or serverTime() - deadDict.get(target().id, 0) < deadBlockTimeOut):
                    addClientMessage(safeShotConfig['clientMessages']['deadShotBlockedMessage'])
                    return
    return base(self, isRepeat)


@registerEvent(PlayerAvatar, '_PlayerAvatar__destroyGUI')
def __destroyGUI(self):
    global deadBlockEnabled
    global deadBlockTimeOut
    global deadDict
    global hotKeyPressed
    global lastChatMessageTime
    global lastClientMessageTime
    global safeShotEnabled
    safeShotEnabled = safeShotConfig['enabled']
    deadBlockEnabled = safeShotConfig.get('deadShotBlock', False)
    deadBlockTimeOut = safeShotConfig.get('deadShotBlockTimeOut', 2)
    lastClientMessageTime = None
    lastChatMessageTime = None
    hotKeyPressed = False
    deadDict = {}
    return

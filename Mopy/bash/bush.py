# -*- coding: utf-8 -*-
#
# GPL License and Copyright Notice ============================================
#  This file is part of Wrye Bash.
#
#  Wrye Bash is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  Wrye Bash is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with Wrye Bash; if not, write to the Free Software Foundation,
#  Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
#  Wrye Bash copyright (C) 2005-2009 Wrye, 2010-2019 Wrye Bash Team
#  https://github.com/wrye-bash
#
# =============================================================================

"""This module defines static data for use by other modules in the Wrye Bash package.
Its use should generally be restricted to large chunks of data and/or chunks of data
that are used by multiple objects."""

# Imports ---------------------------------------------------------------------
import collections
import game as game_init
from bass import get_ini_option
from bolt import GPath, Path, deprint
from env import get_registry_game_path
from exception import BoltError

# Game detection --------------------------------------------------------------
game = None         # type: game_init.GameInfo
game_mod = None     # type: game_init
foundGames = {}     # {'name': Path} dict used by the Settings switch game menu

# Module Cache
_allGames = {}        # 'name' -> GameInfo
_allModules = {}      # 'name' -> module
_registryGames = {}   # 'name' -> path
_fsName_display = {}
_display_fsName = {}

def reset_bush_globals():
    global game, game_mod
    game = game_mod = None
    for d in (_allGames, _allModules, _registryGames, _fsName_display,
              _display_fsName):
        d.clear()

def _supportedGames(useCache=True):
    """Set games supported by Bash and return their paths from the registry."""
    if useCache and _allGames: return _registryGames.copy()
    # rebuilt cache
    _allGames.clear()
    _registryGames.clear()
    _fsName_display.clear()
    _display_fsName.clear()
    import pkgutil
    # Detect the known games
    for importer, modname, ispkg in pkgutil.iter_modules(game_init.__path__):
        if not ispkg: continue # game support modules are packages
        # Equivalent of "from game import <modname>"
        try:
            module = __import__('game',globals(),locals(),[modname],-1)
            submod = getattr(module,modname)
            game_type = submod.GAME_TYPE
            _allModules[game_type.fsName] = submod
            _allGames[game_type.fsName] = game_type
            _fsName_display[game_type.fsName] = game_type.displayName
            #--Get this game's install path
            game_path = get_registry_game_path(game_type)
        except (ImportError, AttributeError):
            deprint(u'Error in game support module:', modname, traceback=True)
            continue
        if game_path: _registryGames[game_type.fsName] = game_path
        del module
    # unload some modules, _supportedGames is meant to run once
    del pkgutil
    _display_fsName.update({v: k for k, v in _fsName_display.iteritems()})
    deprint(u'Detected the following supported games via Windows Registry:')
    for foundName in _registryGames:
        deprint(u' %s:' % foundName, _registryGames[foundName])
    return _registryGames.copy()

def _detectGames(cli_path=u'', bash_ini_=None):
    """Detect which supported games are installed.

    - If Bash supports no games raise.
    - For each game supported by Bash check for a supported game executable
    in the following dirs, in decreasing precedence:
       - the path provided by the -o cli argument if any
       - the sOblivionPath Bash Ini entry if present
       - one directory up from Mopy
    If a game exe is found update the path to this game and return immediately.
    Return (foundGames, name)
      - foundGames: a dict from supported games to their paths (the path will
      default to the windows registry path to the game, if present)
      - name: the game found in the first installDir or None if no game was
      found - a 'suggestion' for a game to use (if no game is specified/found
      via -g argument).
    """
    #--Find all supported games and all games in the windows registry
    foundGames_ = _supportedGames() # sets _allGames if not set
    if not _allGames: # if allGames is empty something goes badly wrong
        raise BoltError(_(u'No game support modules found in Mopy/bash/game.'))
    # check in order of precedence the -o argument, the ini and our parent dir
    installPaths = collections.OrderedDict() #key->(path, found msg, error msg)
    #--First: path specified via the -o command line argument
    if cli_path != u'':
        test_path = GPath(cli_path)
        if not test_path.isabs():
            test_path = Path.getcwd().join(test_path)
        installPaths['cmd'] = (test_path,
            _(u'Set game mode to %(gamename)s specified via -o argument') +
              u': ',
            _(u'No known game in the path specified via -o argument: ' +
              u'%(path)s'))
    #--Second: check if sOblivionPath is specified in the ini
    ini_game_path = get_ini_option(bash_ini_, u'sOblivionPath')
    if ini_game_path and not ini_game_path == u'.':
        test_path = GPath(ini_game_path.strip())
        if not test_path.isabs():
            test_path = Path.getcwd().join(test_path)
        installPaths['ini'] = (test_path,
            _(u'Set game mode to %(gamename)s based on sOblivionPath setting '
              u'in bash.ini') + u': ',
            _(u'No known game in the path specified in sOblivionPath ini '
              u'setting: %(path)s'))
    #--Third: Detect what game is installed one directory up from Mopy
    test_path = Path.getcwd()
    if test_path.cs[-4:] == u'mopy':
        test_path = GPath(test_path.s[:-5])
        if not test_path.isabs():
            test_path = Path.getcwd().join(test_path)
        installPaths['upMopy'] = (test_path,
            _(u'Set game mode to %(gamename)s found in parent directory of'
              u' Mopy') + u': ',
            _(u'No known game in parent directory of Mopy: %(path)s'))
    #--Detect
    deprint(u'Detecting games via the -o argument, bash.ini and relative path:')
    # iterate installPaths in insert order ('cmd', 'ini', 'upMopy')
    for test_path, foundMsg, errorMsg in installPaths.itervalues():
        for name, info in _allGames.items():
            if test_path.join(*info.game_detect_file).exists():
                # Must be this game
                deprint(foundMsg % {'gamename': name}, test_path)
                foundGames_[name] = test_path
                return foundGames_, name
        # no game exe in this install path - print error message
        deprint(errorMsg % {'path': test_path.s})
    # no game found in installPaths - foundGames are the ones from the registry
    return foundGames_, None

def __setGame(name, msg):
    """Set bush game globals - raise if they are already set."""
    global game, game_mod
    if game is not None: raise BoltError(u'Trying to reset the game')
    gamePath = foundGames[name]
    game = _allGames[name](gamePath)
    game_mod = _allModules[name]
    deprint(msg % {'gamename': name}, gamePath)
    # Unload the other modules from the cache
    for i in _allGames.keys():
        if i != name:
            del _allGames[i]
            del _allModules[i]  # the keys should be the same
    game.init()

def detect_and_set_game(cli_game_dir=u'', bash_ini_=None, name=None):
    if name is None: # detect available games
        foundGames_, name = _detectGames(cli_game_dir, bash_ini_)
        foundGames.update(foundGames_) # set the global name -> game path dict
    else:
        name = _display_fsName[name] # we are passed a display name in
    if name is not None: # try the game returned by detectGames() or specified
        __setGame(name, u' Using %(gamename)s game:')
        return None
    elif len(foundGames) == 1:
        __setGame(foundGames.keys()[0], u'Single game found [%(gamename)s]:')
        return None
    # No match found, return the list of possible games (may be empty if
    # nothing is found in registry)
    return [_fsName_display[k] for k in foundGames]

def game_path(display_name): return foundGames[_display_fsName[display_name]]
def get_display_name(fs_name): return _fsName_display[fs_name]

# Id Functions ----------------------------------------------------------------
def getIdFunc(modName):
    return lambda x: (GPath(modName),x)

ob = getIdFunc(u'Oblivion.esm')
cobl = getIdFunc(u'Cobl Main.esm')

# Default Eyes/Hair -----------------------------------------------------------
standardEyes = [ob(x) for x in (0x27306,0x27308,0x27309)] + [cobl(x) for x in (0x000821, 0x000823, 0x000825, 0x000828, 0x000834, 0x000837, 0x000839, 0x00084F, )]

defaultEyes = {
    #--Oblivion.esm
    ob(0x23FE9): #--Argonian
        [ob(0x3E91E)] + [cobl(x) for x in (0x01F407, 0x01F408, 0x01F40B, 0x01F40C, 0x01F410, 0x01F411, 0x01F414, 0x01F416, 0x01F417, 0x01F41A, 0x01F41B, 0x01F41E, 0x01F41F, 0x01F422, 0x01F424, )],
    ob(0x0224FC): #--Breton
        standardEyes,
    ob(0x0191C1): #--Dark Elf
        [ob(0x27307)] + [cobl(x) for x in (0x000861,0x000864,0x000851)],
    ob(0x019204): #--High Elf
        standardEyes,
    ob(0x000907): #--Imperial
        standardEyes,
    ob(0x022C37): #--Khajiit
        [ob(0x375c8)] + [cobl(x) for x in (0x00083B, 0x00083E, 0x000843, 0x000846, 0x000849, 0x00084C, )],
    ob(0x0224FD): #--Nord
        standardEyes,
    ob(0x0191C0): #--Orc
        [ob(0x2730A)]+[cobl(x) for x in (0x000853, 0x000855, 0x000858, 0x00085A, 0x00085C, 0x00085E, )],
    ob(0x000D43): #--Redguard
        standardEyes,
    ob(0x0223C8): #--Wood Elf
        standardEyes,
    #--Cobl
    cobl(0x07948): #--cobRaceAureal
        [ob(0x54BBA)],
    cobl(0x02B60): #--cobRaceHidden
        [cobl(x) for x in (0x01F43A, 0x01F438, 0x01F439, 0x0015A7, 0x01792C, 0x0015AC, 0x0015A8, 0x0015AB, 0x0015AA,)],
    cobl(0x07947): #--cobRaceMazken
        [ob(0x54BB9)],
    cobl(0x1791B): #--cobRaceOhmes
        [cobl(x) for x in (0x017901, 0x017902, 0x017903, 0x017904, 0x017905, 0x017906, 0x017907, 0x017908, 0x017909, 0x01790A, 0x01790B, 0x01790C, 0x01790D, 0x01790E, 0x01790F, 0x017910, 0x017911, 0x017912, 0x017913, 0x017914, 0x017915, 0x017916, 0x017917, 0x017918, 0x017919, 0x01791A, 0x017900,)],
    cobl(0x1F43C): #--cobRaceXivilai
        [cobl(x) for x in (0x01F437, 0x00531B, 0x00531C, 0x00531D, 0x00531E, 0x00531F, 0x005320, 0x005321, 0x01F43B, 0x00DBE1, )],
    }

acbs = {
    u'Armorer': 0,
    u'Athletics': 1,
    u'Blade': 2,
    u'Block': 3,
    u'Blunt': 4,
    u'Hand to Hand': 5,
    u'Heavy Armor': 6,
    u'Alchemy': 7,
    u'Alteration': 8,
    u'Conjuration': 9,
    u'Destruction': 10,
    u'Illusion': 11,
    u'Mysticism': 12,
    u'Restoration': 13,
    u'Acrobatics': 14,
    u'Light Armor': 15,
    u'Marksman': 16,
    u'Mercantile': 17,
    u'Security': 18,
    u'Sneak': 19,
    u'Speechcraft': 20,
    u'Health': 21,
    u'Strength': 25,
    u'Intelligence': 26,
    u'Willpower': 27,
    u'Agility': 28,
    u'Speed': 29,
    u'Endurance': 30,
    u'Personality': 31,
    u'Luck': 32,
    }

# Save File Info --------------------------------------------------------------
saveRecTypes = {
    6 : _(u'Faction'),
    19: _(u'Apparatus'),
    20: _(u'Armor'),
    21: _(u'Book'),
    22: _(u'Clothing'),
    25: _(u'Ingredient'),
    26: _(u'Light'),
    27: _(u'Misc. Item'),
    33: _(u'Weapon'),
    35: _(u'NPC'),
    36: _(u'Creature'),
    39: _(u'Key'),
    40: _(u'Potion'),
    48: _(u'Cell'),
    49: _(u'Object Ref'),
    50: _(u'NPC Ref'),
    51: _(u'Creature Ref'),
    58: _(u'Dialog Entry'),
    59: _(u'Quest'),
    61: _(u'AI Package'),
    }

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
#  Wrye Bash copyright (C) 2005-2009 Wrye, 2010-2015 Wrye Bash Team
#  https://github.com/wrye-bash
#
# =============================================================================

"""This modules defines static data for use by bush, when Fallout 4 is set as
   the active game."""

from .constants import *
from .default_tweaks import default_tweaks
from .. import GameInfo
from ... import brec

class Fallout76GameInfo(GameInfo):
    displayName = u'Fallout 76'
    fsName = u'Fallout76'
    altName = u'Wrye Flash'
    defaultIniFile = u'Fallout76.ini'
    exe = u'Fallout76.exe'
    masterFiles = [u'SeventySix.esm']
    iniFiles = [u'Fallout76.ini', u'Fallout76Prefs.ini', u'Fallout76Custom.ini', ]
    pklfile = ur''
    regInstallKeys = (u'Microsoft\Windows\CurrentVersion\Uninstall\Fallout 76', u'Path')
    nexusUrl = u''
    nexusName = u''
    nexusKey = ''

    bsa_extension = ur'ba2'
    vanilla_string_bsas = {
        u'seventysix.esm': [u'SeventySix - Interface.ba2'],
    }
    resource_archives_keys = (u'sResourceArchiveList', u'sResourceArchiveList2')

    class cs(GameInfo.cs):
        # TODO:  When the Fallout 4 Creation Kit is actually released,
        # double check that the filename is correct, and create an actual icon
        shortName = u'FO76CK'
        longName = u'Creation Kit'
        exe = u'CreationKit.exe'
        seArgs = None
        imageName = u'creationkit%s.png'

    class se(GameInfo.se):
        shortName = u''
        longName = u''
        exe = u''
        steamExe = u''
        url = u''
        urlTip = u''

    class ini(GameInfo.ini):
        allowNewLines = True
        bsaRedirection = (u'',u'')


    # BAIN:
    dataDirs = GameInfo.dataDirs | {
        u'interface',
        u'lodsettings',
        u'materials',
        u'misc',
        u'programs',
        u'scripts',
        u'seq',
        u'shadersfx',
        u'strings',
        u'vis',
    }
    dataDirsPlus = {
        u'f4se',
        u'ini',
        u'mcm',   # FO4 MCM
        u'tools', # bodyslide
    }
    dontSkipDirs = {
        # This rule is to allow mods with string translation enabled.
        'interface\\translations':['.txt']
    }
    SkipBAINRefresh = {u'fo4edit backups'}

    class esp(GameInfo.esp):
        hasEsl = False
        canBash = True
        canEditHeader = True
        validHeaderVersions = (0.95,)

    allTags = {u'Delev', u'Relev'}

    patchers = (u'ListsMerger',)

    # ---------------------------------------------------------------------
    # --Imported - MreGlob is special import, not in records.py
    # ---------------------------------------------------------------------
    @classmethod
    def init(cls):
        # First import from fallout4.records file, so MelModel is set correctly
        from .records import MreHeader, MreLvli, MreLvln
        # ---------------------------------------------------------------------
        # These Are normally not mergable but added to brec.MreRecord.type_class
        #
        #       MreCell,
        # ---------------------------------------------------------------------
        # These have undefined FormIDs Do not merge them
        #
        #       MreNavi, MreNavm,
        # ---------------------------------------------------------------------
        # These need syntax revision but can be merged once that is corrected
        #
        #       MreAchr, MreDial, MreLctn, MreInfo, MreFact, MrePerk,
        # ---------------------------------------------------------------------
        cls.mergeClasses = (
            # -- Imported from Skyrim/SkyrimSE
            # Added to records.py
            MreLvli, MreLvln
        )
        # Setting RecordHeader class variables --------------------------------
        brec.RecordHeader.topTypes = [
            'GMST', 'KYWD', 'LCRT', 'AACT', 'TRNS', 'CMPO', 'TXST', 'GLOB',
            'DMGT', 'CLAS', 'FACT', 'HDPT', 'EYES', 'RACE', 'SOUN', 'SECH',
            'ASPC', 'RESO', 'MGEF', 'LTEX', 'ENCH', 'SPEL', 'ACTI', 'TACT',
            'CURV', 'ARMO', 'BOOK', 'CONT', 'DOOR', 'INGR', 'LIGH', 'MISC',
            'MSCS', 'CNCY', 'STAT', 'SCOL', 'MSTT', 'GRAS', 'TREE', 'FLOR',
            'FURN', 'WEAP', 'AMMO', 'NPC_', 'PLYR', 'LVLN', 'LVLP', 'KEYM',
            'ALCH', 'IDLM', 'NOTE', 'PROJ', 'HAZD', 'BNDS', 'TERM', 'PPAK',
            'PACH', 'LVLI', 'WTHR', 'CLMT', 'SPGD', 'RFCT', 'REGN', 'NAVI',
            'CELL', 'WRLD', 'QUST', 'IDLE', 'PACK', 'CSTY', 'LSCR', 'ANIO',
            'WATR', 'EFSH', 'EXPL', 'DEBR', 'IMGS', 'IMAD', 'FLST', 'PERK',
            'PCRD', 'LVPC', 'BPTD', 'ADDN', 'AVIF', 'CAMS', 'CPTH', 'VTYP',
            'MATT', 'IPCT', 'IPDS', 'ARMA', 'LCTN', 'MESG', 'DOBJ', 'DFOB',
            'LGTM', 'MUSC', 'FSTP', 'FSTS', 'SMBN', 'SMQN', 'SMEN', 'MUST',
            'DLVW', 'EQUP', 'RELA', 'ASTP', 'OTFT', 'ARTO', 'MATO', 'MOVT',
            'SNDR', 'SNCT', 'SOPM', 'COLL', 'CLFM', 'REVB', 'PKIN', 'RFGP',
            'AMDL', 'LAYR', 'COBJ', 'OMOD', 'MSWP', 'ZOOM', 'INNR', 'KSSM',
            'AECH', 'SCCO', 'AORU', 'SCSN', 'STAG', 'NOCM', 'LENS', 'GDRY',
            'OVIS', 'STND', 'STMP', 'GCVR', 'EMOT', 'STHD', 'VOLI', 'ECAT', 
            'WSPR', 'ENTM', 'PCEN', 'COEN', 'CSEN', 'WAVE', 'AAPD', 'PMFT',
            'CHAL', 'AVTR', 'CNDF']
        brec.RecordHeader.recordTypes = (set(brec.RecordHeader.topTypes) |
            {'GRUP', 'TES4', 'REFR', 'ACHR', 'PMIS', 'PARW', 'PGRE', 'PBEA',
             'PFLA', 'PCON', 'PBAR', 'PHZD', 'LAND', 'NAVM', 'DIAL', 'INFO'})
        brec.RecordHeader.plugin_form_version = 184
        brec.MreRecord.type_class = dict((x.classType,x) for x in (
            #--Always present
            MreHeader, MreLvli, MreLvln,
            # Imported from Skyrim or SkyrimSE
            # Added to records.py
            ))
        brec.MreRecord.simpleTypes = (
            set(brec.MreRecord.type_class) - {'TES4',})

GAME_TYPE = Fallout76GameInfo

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
"""This module contains the skyrim SE record classes. The great majority are
imported from skyrim, but only after setting MelModel to the SSE format."""
import itertools

from ... import brec
from ...bass import null1, null2, null3, null4
from ...bolt import Flags, struct_pack, encode
from ...brec import MelBase, MelGroup, MreHeaderBase, MelSet, MelString, \
    MelStruct, MelUnicode, MelNull, MelFidList, MreLeveledListBase, \
    MelGroups, MelFid, FID, MelOptStruct, MelLString, MelStructA, MelRecord, \
    MelCountedFidList, MelStructs, MelObject
from ...exception import ModSizeError
# Set brec.MelModel to the skyrimse one - do not import from skyrim.records yet

class MelMODS(MelBase): # copy pasted from game.skyrim.records.MelMODS
    """MODS/MO2S/etc/DMDS subrecord"""
    def hasFids(self,formElements):
        """Include self if has fids."""
        formElements.add(self)

    def setDefault(self,record):
        """Sets default value for record instance."""
        record.__setattr__(self.attr,None)

    def loadData(self, record, ins, sub_type, size_, readId):
        """Reads data from ins into record attribute."""
        insUnpack = ins.unpack
        count, = insUnpack('I',4,readId)
        data = []
        dataAppend = data.append
        for x in xrange(count):
            string = ins.readString32(readId)
            fid = ins.unpackRef()
            index, = ins.unpack('I',4,readId)
            dataAppend((string,fid,index))
        record.__setattr__(self.attr,data)

    def dumpData(self,record,out):
        """Dumps data from record to outstream."""
        data = record.__getattribute__(self.attr)
        if data is not None:
            data = record.__getattribute__(self.attr)
            outData = struct_pack('I', len(data))
            for (string,fid,index) in data:
                outData += struct_pack('I', len(string))
                outData += encode(string)
                outData += struct_pack('=2I', fid, index)
            out.packSub(self.subType,outData)

    def mapFids(self,record,function,save=False):
        """Applies function to fids.  If save is true, then fid is set
           to result of function."""
        attr = self.attr
        data = record.__getattribute__(attr)
        if data is not None:
            data = [(string,function(fid),index) for (string,fid,index) in record.__getattribute__(attr)]
            if save: record.__setattr__(attr,data)

if brec.MelModel is None:
    class _MelModel(MelGroup):
        """Represents a model record."""
        # MODB and MODD are no longer used by TES5Edit
        typeSets = {'MODL': ('MODL', 'MODT', 'MODC', 'MODS', 'MODF'),
                    'MOD2': ('MOD2', 'MODT', 'MO2C', 'MO2S', 'MO2F'),
                    'MOD3': ('MOD3', 'MODT', 'MO3C', 'MO3S', 'MO3F'),
                    'MOD4': ('MOD4', 'MODT', 'MO4C', 'MO4S', 'MO4F'),
                    'MOD5': ('MOD5', 'MODT', 'MO5C', 'MO5S', 'MO5F'),
                    # Destructible
                    'DMDL': ('DMDL', 'DMDT', 'DMDC', 'DMDS'), }

        class MelModelHash(MelBase):
            """textureHashes are not used for loose files. There is never a
            Bashed Patch, 0.bsa. The record will be read if
            present but no defaults are set and the record will not be written."""
            def loadData(self, record, ins, sub_type, size_, readId):
                MelBase.loadData(self, record, ins, sub_type, size_, readId)
            def getSlotsUsed(self):
                return ()
            def setDefault(self,record): return
            def dumpData(self,record,out): return

        def __init__(self, attr='model', subType='MODL'):
            """Initialize."""
            types = self.__class__.typeSets[subType]
            MelGroup.__init__(
                self, attr, MelString(types[0], 'modPath'),
                self.MelModelHash(types[1], 'textureHashes'),
                MelOptStruct(types[2], 'f', 'colorRemappingIndex'),
                MelOptStruct(types[3], 'I', (FID,'materialSwap')),
                MelBase(types[3], 'modf_p'),
                )

        def debug(self, on=True):
            """Sets debug flag on self."""
            for element in self.elements[:2]: element.debug(on)
            return self
    brec.MelModel = _MelModel
from ...brec import MelModel
# Now we can import from parent game records file
from ..skyrim.records import MelBounds, MelDestructible, MelConditions
# Those are unused here, but need be in this file as are accessed via it
from ..skyrim.records import MreGmst

from_iterable = itertools.chain.from_iterable

#------------------------------------------------------------------------------
# Record Elements    ----------------------------------------------------------
#------------------------------------------------------------------------------
class MelCoed(MelOptStruct):
    """Needs custom unpacker to look at FormID type of owner.  If owner is an
	NPC then it is followed by a FormID.  If owner is a faction then it is
	followed by an signed integer or '=Iif' instead of '=IIf' """ # see #282
    def __init__(self):
        MelOptStruct.__init__(self,'COED','=IIf',(FID,'owner'),(FID,'glob'),
                              'itemCondition')

#------------------------------------------------------------------------------
class MelVmad(MelBase):
    """Virtual Machine data (VMAD)"""
    # Maybe use this later for better access to Fid,Aid pairs?
    ##ObjectRef = collections.namedtuple('ObjectRef',['fid','aid'])

    # DONE with wbScriptFlags
    vmadScriptFlags =  Flags(0L,Flags.getNames(
        (0,'local'), # {0x00}
        (1,'inherited'), # {0x01}
        (2,'removed'), # {0x02}
        (3,'inheritedAndRemoved'), # {0x04}
        ))

    # FOUND with wbScriptFragments
    class scriptFragments(object):
        __slots__ = ('unk','fileName',)
        def __init__(self):
            self.unk = 2
            self.fileName = u''

        def loadData(self,ins,Type,readId):
            if Type == 'PERK': # Not Decoded
                self.unk, = ins.unpack('=b',1,readId)
                self.fileName = ins.readString16(readId)
                count, = ins.unpack('=H',2,readId)
            elif Type == 'TERM':
                # TERM record fragment scripts are by default stored in a SF file,
                # i.e., a file named "SF_<editorID>_<formID>".
                raise Exception(u"Fragment Scripts for 'TERM' records are not implemented.")
            elif Type == 'INFO':
                self.unk,count = ins.unpack('=bB',2,readId)
                self.fileName = ins.readString16(readId)
                count = bin(count).count('1')
            elif Type == 'PACK': # Not Decoded
                self.unk,count = ins.unpack('=bB',2,readId)
                self.fileName = ins.readString16(readId)
                count = bin(count).count('1')
            elif Type == 'QUST':
                self.unk,count = ins.unpack('=bH',3,readId)
                self.fileName = ins.readString16(readId)
            elif Type == 'SCEN': # Not Decoded
                # SCEN record fragment scripts are by default stored in a SF file,
                # i.e., a file named "SF_<editorID>_<formID>".
                raise Exception(u"Fragment Scripts for 'SCEN' records are not implemented.")
            else:
                raise Exception(u"Unexpected Fragment Scripts for record type '%s'." % Type)
            return count

        def dumpData(self,Type,count):
            fileName = encode(self.fileName)
            if Type == 'PERK':
                data = struct_pack('=bH', self.unk, len(fileName)) + fileName
                data += struct_pack('=H', count)
            elif Type == 'TERM':
                data = struct_pack('=bH', self.unk, len(fileName)) + fileName
                data += struct_pack('=H', count)
            elif Type == 'INFO':
                # TODO: check if this is right!
                count = int(count*'1',2)
                data = struct_pack('=bBH', self.unk, count, len(fileName)) + fileName
            elif Type == 'PACK':
                # TODO: check if this is right!
                count = int(count*'1',2)
                data = struct_pack('=bBH', self.unk, count, len(fileName)) + fileName
            elif Type == 'QUST':
                data = struct_pack('=bHH', self.unk, count, len(fileName)) + fileName
            elif Type == 'SCEN':
                raise Exception(u"Fragment Scripts for 'SCEN' records are not implemented.")
            else:
                raise Exception(u"Unexpected Fragment Scripts for record type '%s'." % Type)
            return data

    class PERKFragment(object): # Record Not Decoded
        __slots__ = ('index','unk1','unk2','scriptName','fragmentName',)
        def __init__(self):
            self.index = -1
            self.unk1 = 0
            self.unk2 = 0
            self.scriptName = u''
            self.fragmentName= u''

        def loadData(self,ins,readId):
            self.index,self.unk1,self.unk2 = ins.unpack('=Hhb',4,readId)
            self.scriptName = ins.readString16(readId)
            self.fragmentName = ins.readString16(readId)

        def dumpData(self):
            scriptName = encode(self.scriptName)
            fragmentName = encode(self.fragmentName)
            data = struct_pack('=HhbH', self.index, self.unk1, self.unk2,
                               len(scriptName)) + scriptName
            data += struct_pack('=H', len(fragmentName)) + fragmentName
            return data

    class TERMFragment(object):
        __slots__ = ('index','unk1','unk2','scriptName','fragmentName',)
        def __init__(self):
            self.index = -1
            self.unk1 = 0
            self.unk2 = 0
            self.scriptName = u''
            self.fragmentName= u''

        def loadData(self,ins,readId):
            self.index,self.unk1,self.unk2 = ins.unpack('=Hhb',4,readId)
            self.scriptName = ins.readString16(readId)
            self.fragmentName = ins.readString16(readId)

        def dumpData(self):
            scriptName = encode(self.scriptName)
            fragmentName = encode(self.fragmentName)
            data = struct_pack('=HhbH', self.index, self.unk1, self.unk2,
                               len(scriptName)) + scriptName
            data += struct_pack('=H', len(fragmentName)) + fragmentName
            return data

    class INFOFragment(object):
        __slots__ = ('unk','vmadFlags','scriptName','fragmentName',)
        def __init__(self):
            self.unk = 0
            self.vmadFlags = 0
            self.scriptName = u''
            self.fragmentName = u''

        def loadData(self,ins,readId):
            self.unk, = ins.unpack('=b',1,readId)
            self.vmadFlags, = ins.unpack('=B',1,readId)
            self.scriptName = ins.readString16(readId)
            self.fragmentName = ins.readString16(readId)

        def dumpData(self):
            scriptName = encode(self.scriptName)
            fragmentName = encode(self.fragmentName)
            data = struct_pack('=b', self.unk)
            data += struct_pack('=B', self.vmadFlags)
            data += struct_pack('=H', len(scriptName)) + scriptName
            data += struct_pack('=H', len(fragmentName)) + fragmentName
            return data

    class PACKFragment(object): # Record Not Decoded
        __slots__ = ('unk','scriptName','fragmentName',)
        def __init__(self):
            self.unk = 0
            self.scriptName = u''
            self.fragmentName = u''

        def loadData(self,ins,readId):
            self.unk, = ins.unpack('=b',1,readId)
            self.scriptName = ins.readString16(readId)
            self.fragmentName = ins.readString16(readId)

        def dumpData(self):
            scriptName = encode(self.scriptName)
            fragmentName = encode(self.fragmentName)
            data = struct_pack('=bH', self.unk, len(scriptName)) + scriptName
            data += struct_pack('=H', len(fragmentName)) + fragmentName
            return data

    class QUSTFragment(object):
        __slots__ = ('index','unk1','logentry','unk2','scriptName','fragmentName',)
        def __init__(self):
            self.index = -1 # count of fragments
            self.unk1 = 0 # wbInteger('Unknown', itS8),
            self.logentry = 0 # wbInteger('fragmentCount', itU16, nil, cpBenign),
            self.unk2 = 1
            self.scriptName = u'' # wbLenString('fileName', 2),
            self.fragmentName = u''

        def loadData(self,ins,readId):
            self.index,self.unk1,self.logentry,self.unk2 = ins.unpack('=Hhib',9,readId)
            self.scriptName = ins.readString16(readId)
            self.fragmentName = ins.readString16(readId)

        def dumpData(self):
            scriptName = encode(self.scriptName)
            fragmentName = encode(self.fragmentName)
            data = struct_pack('=HhibH', self.index, self.unk1, self.logentry,
                               self.unk2, len(scriptName)) + scriptName
            data += struct_pack('=H', len(fragmentName)) + fragmentName
            return data

    class SCENFragment(object): # Record Not Decoded
        pass

    FragmentMap = {'PERK': PERKFragment,
                   'TERM': TERMFragment,
                   'INFO': INFOFragment,
                   'PACK': PACKFragment,
                   'QUST': QUSTFragment,
                   'SCEN': SCENFragment,
                   }

    # wbScriptPropertyStruct
    class scriptPropertyStruct(object):
        __slots__ = ('name','status','value',)
        def __init__(self):
            self.name = u''
            self.status = 1
            self.value = None

        def loadData(self,ins,version,objFormat,readId):
            insUnpack = ins.unpack
            # Script Property
            self.name = ins.readString16(readId) # wbLenString('propertyName', 2),
            if version >= 4:
                Type,self.status = insUnpack('=2B',2,readId) # wbInteger('Type', itU8
            else:
                Type, = insUnpack('=B',1,readId) # wbInteger('Type', itU8
                self.status = 1
            # Data
            # DONE with wbScriptPropertyObject
            if Type == 1:
                # Object (8 Bytes)
                if objFormat == 1: # 1th Format
                    fid,aid,nul = insUnpack('=IHH',8,readId)
                else: # 0th Format
                    nul,aid,fid = insUnpack('=HHI',8,readId)
                self.value = (fid,aid)
            elif Type == 2:
                # String
                self.value = ins.readString16(readId)
            elif Type == 3:
                # Int32
                self.value, = insUnpack('=i',4,readId)
            elif Type == 4:
                # Float
                self.value, = insUnpack('=f',4,readId)
            elif Type == 5:
                # Bool (Int8)
                self.value = bool(insUnpack('=b',1,readId)[0])
            elif Type == 6:
                # wbRecursive Struct 3
                self.value = bool(insUnpack('=b', 1, readId)[0])
            elif Type == 7:
                # wbRecursive Struct 3
                self.value = bool(insUnpack('=b', 1, readId)[0])
            elif Type == 11:
                # List of Objects
                count, = insUnpack('=I',4,readId)
                if objFormat == 1: # (fid,aid,nul)
                    value = insUnpack('='+count*'IHH',count*8,readId)
                    self.value = zip(value[::3],value[1::3]) # list of (fid,aid)'s
                else: # (nul,aid,fid)
                    value = insUnpack('='+count*'HHI',count*8,readId)
                    self.value = zip(value[2::3],value[1::3]) # list of (fid,aid)'s
            elif Type == 12:
                # List of Strings
                count, = insUnpack('=I',4,readId)
                self.value = [ins.readString16(readId) for i in xrange(count)]
            elif Type == 13:
                # List of Int32s
                count, = insUnpack('=I',4,readId)
                self.value = list(insUnpack('='+`count`+'i',count*4,readId))
            elif Type == 14:
                # List of Floats
                count, = insUnpack('=I',4,readId)
                self.value = list(insUnpack('='+`count`+'f',count*4,readId))
            elif Type == 15:
                # List of Bools (int8)
                count, = insUnpack('=I',4,readId)
                self.value = map(bool,insUnpack('='+`count`+'b',count,readId))
            elif Type == 17:
                # Array wbRecursive Struct 4
                count, = insUnpack('=I', 4, readId)
                self.value = map(bool, insUnpack('=' + `count` + 'b', count, readId))
            else:
                raise Exception(u'Unrecognized VM Data property type: %i' % Type)

        def dumpData(self):
            ## Property Entry
            # Property Name
            name = encode(self.name)
            data = struct_pack('=H', len(name)) + name
            # Property Type
            value = self.value
            # Type 1 - Object Reference
            if isinstance(value,tuple):
                # Object Format 1 - (Fid, Aid, NULL)
                #data += structPack('=BBIHH',1,self.status,value[0],value[1],0)
                # Object Format 2 - (NULL, Aid, Fid)
                data += struct_pack('=BBHHI', 1, self.status, 0, value[1],
                                    value[0])
            # Type 2 - String
            elif isinstance(value,basestring):
                value = encode(value)
                data += struct_pack('=BBH', 2, self.status, len(value)) + value
            # Type 3 - Int
            elif isinstance(value,(int,long)) and not isinstance(value,bool):
                data += struct_pack('=BBi', 3, self.status, value)
            # Type 4 - Float
            elif isinstance(value,float):
                data += struct_pack('=BBf', 4, self.status, value)
            # Type 5 - Bool
            elif isinstance(value,bool):
                data += struct_pack('=BBb', 5, self.status, value)
            # Type 6 - wbRecursive Struct 3
            elif isinstance(value,bool):
                data += struct_pack('=BBb', 5, self.status, value)
            # Type 7 - wbRecursive Struct 3
            elif isinstance(value,bool):
                data += struct_pack('=BBb', 5, self.status, value)
            # Type 11 -> 15 - lists, Only supported if vmad version >= 5
            elif isinstance(value,list):
                # Empty list, fail to object refereneces?
                count = len(value)
                if not count:
                    data += struct_pack('=BBI', 11, self.status, count)
                else:
                    Type = value[0]
                    # Type 11 - Object References
                    if isinstance(Type,tuple):
                        # Object Format 1 - value = [fid,aid,NULL, fid,aid,NULL, ...]
                        #value = list(from_iterable([x+(0,) for x in value]))
                        #data += structPack('=BBI'+count*'IHH',11,self.status,count,*value)
                        # Object Format 2 - value = [NULL,aid,fid, NULL,aid,fid, ...]
                        value = list(from_iterable([(0,aid,fid) for fid,aid in value]))
                        data += struct_pack('=BBI' + count * 'HHI', 11,
                                            self.status, count, *value)
                    # Type 12 - Strings
                    elif isinstance(Type,basestring):
                        data += struct_pack('=BBI', 12, self.status, count)
                        for string in value:
                            string = encode(string)
                            data += struct_pack('=H', len(string)) + string
                    # Type 13 - Ints
                    elif isinstance(Type,(int,long)) and not isinstance(
                            Type,bool):
                        data += struct_pack('=BBI' + `count` + 'i', 13,
                                            self.status, count, *value)
                    # Type 14 - Floats
                    elif isinstance(Type,float):
                        data += struct_pack('=BBI' + `count` + 'f', 14,
                                            self.status, count, *value)
                    # Type 15 - Bools
                    elif isinstance(Type,bool):
                        data += struct_pack('=BBI' + `count` + 'b', 15,
                                            self.status, count, *value)
                    # Type 17 - Bools
                    elif isinstance(Type, bool):
                        data += struct_pack('=BBI' + `count` + 'b', 15,
                                            self.status, count, *value)
                    else:
                        raise Exception(u'Unrecognized VMAD property type: %s' % type(Type))
            else:
                raise Exception(u'Unrecognized VMAD property type: %s' % type(value))
            return data

    # FOUND wbScriptProperties
    class scriptProperties(object):
        __slots__ = ('name','status','value',)
        def __init__(self):
            self.name = u''
            self.status = 1
            self.value = None

        def loadData(self,ins,version,objFormat,readId):
            insUnpack = ins.unpack
            # Script Property
            self.name = ins.readString16(readId) # wbLenString('propertyName', 2),
            if version >= 4:
                Type,self.status = insUnpack('=2B',2,readId) # wbInteger('Type', itU8
            else:
                Type, = insUnpack('=B',1,readId) # wbInteger('Type', itU8
                self.status = 1
            # Data
            if Type == 1:
                # Object (8 Bytes)
                if objFormat == 1:
                    fid,aid,nul = insUnpack('=IHH',8,readId)
                else:
                    nul,aid,fid = insUnpack('=HHI',8,readId)
                self.value = (fid,aid)
            elif Type == 2:
                # String
                self.value = ins.readString16(readId)
            elif Type == 3:
                # Int32
                self.value, = insUnpack('=i',4,readId)
            elif Type == 4:
                # Float
                self.value, = insUnpack('=f',4,readId)
            elif Type == 5:
                # Bool (Int8)
                self.value = bool(insUnpack('=b',1,readId)[0])
            elif Type == 11:
                # List of Objects
                count, = insUnpack('=I',4,readId)
                if objFormat == 1: # (fid,aid,nul)
                    value = insUnpack('='+count*'IHH',count*8,readId)
                    self.value = zip(value[::3],value[1::3]) # list of (fid,aid)'s
                else: # (nul,aid,fid)
                    value = insUnpack('='+count*'HHI',count*8,readId)
                    self.value = zip(value[2::3],value[1::3]) # list of (fid,aid)'s
            elif Type == 12:
                # List of Strings
                count, = insUnpack('=I',4,readId)
                self.value = [ins.readString16(readId) for i in xrange(count)]
            elif Type == 13:
                # List of Int32s
                count, = insUnpack('=I',4,readId)
                self.value = list(insUnpack('='+`count`+'i',count*4,readId))
            elif Type == 14:
                # List of Floats
                count, = insUnpack('=I',4,readId)
                self.value = list(insUnpack('='+`count`+'f',count*4,readId))
            elif Type == 15:
                # List of Bools (int8)
                count, = insUnpack('=I',4,readId)
                self.value = map(bool,insUnpack('='+`count`+'b',count,readId))
            else:
                raise Exception(u'Unrecognized VM Data property type: %i' % Type)

        def dumpData(self):
            ## Property Entry
            # Property Name
            name = encode(self.name)
            data = struct_pack('=H', len(name)) + name
            # Property Type
            value = self.value
            # Type 1 - Object Reference
            if isinstance(value,tuple):
                # Object Format 1 - (Fid, Aid, NULL)
                #data += structPack('=BBIHH',1,self.status,value[0],value[1],0)
                # Object Format 2 - (NULL, Aid, Fid)
                data += struct_pack('=BBHHI', 1, self.status, 0, value[1],
                                    value[0])
            # Type 2 - String
            elif isinstance(value,basestring):
                value = encode(value)
                data += struct_pack('=BBH', 2, self.status, len(value)) + value
            # Type 3 - Int
            elif isinstance(value,(int,long)) and not isinstance(value,bool):
                data += struct_pack('=BBi', 3, self.status, value)
            # Type 4 - Float
            elif isinstance(value,float):
                data += struct_pack('=BBf', 4, self.status, value)
            # Type 5 - Bool
            elif isinstance(value,bool):
                data += struct_pack('=BBb', 5, self.status, value)
            # Type 11 -> 15 - lists, Only supported if vmad version >= 5
            elif isinstance(value,list):
                # Empty list, fail to object refereneces?
                count = len(value)
                if not count:
                    data += struct_pack('=BBI', 11, self.status, count)
                else:
                    Type = value[0]
                    # Type 11 - Object References
                    if isinstance(Type,tuple):
                        # Object Format 1 - value = [fid,aid,NULL, fid,aid,NULL, ...]
                        #value = list(from_iterable([x+(0,) for x in value]))
                        #data += structPack('=BBI'+count*'IHH',11,self.status,count,*value)
                        # Object Format 2 - value = [NULL,aid,fid, NULL,aid,fid, ...]
                        value = list(from_iterable([(0,aid,fid) for fid,aid in value]))
                        data += struct_pack('=BBI' + count * 'HHI', 11,
                                            self.status, count, *value)
                    # Type 12 - Strings
                    elif isinstance(Type,basestring):
                        data += struct_pack('=BBI', 12, self.status, count)
                        for string in value:
                            string = encode(string)
                            data += struct_pack('=H', len(string)) + string
                    # Type 13 - Ints
                    elif isinstance(Type,(int,long)) and not isinstance(
                            Type,bool):
                        data += struct_pack('=BBI' + `count` + 'i', 13,
                                            self.status, count, *value)
                    # Type 14 - Floats
                    elif isinstance(Type,float):
                        data += struct_pack('=BBI' + `count` + 'f', 14,
                                            self.status, count, *value)
                    # Type 15 - Bools
                    elif isinstance(Type,bool):
                        data += struct_pack('=BBI' + `count` + 'b', 15,
                                            self.status, count, *value)
                    else:
                        raise Exception(u'Unrecognized VMAD property type: %s' % type(Type))
            else:
                raise Exception(u'Unrecognized VMAD property type: %s' % type(value))
            return data

    # DONE with wbScriptEntry
    class scriptEntry(object):
        __slots__ = ('name','status','properties',)
        def __init__(self):
            self.name = u''
            self.status = 0
            self.properties = []

        def loadData(self,ins,version,objFormat,readId):
            script_property = MelVmad.scriptProperties
            self.properties = []
            propAppend = self.properties.append
            # Script Entry
            self.name = ins.readString16(readId)
            if version >= 4:
                self.status,propCount = ins.unpack('=BH',3,readId)
            else:
                self.status = 0
                propCount, = ins.unpack('=H',2,readId)
            # Properties
            for x in xrange(propCount):
                prop = script_property()
                prop.loadData(ins,version,objFormat,readId)
                propAppend(prop)

        def dumpData(self):
            ## Script Entry
            # scriptName
            name = encode(self.name)
            data = struct_pack('=H', len(name)) + name
            # status, property count
            data += struct_pack('=BH', self.status, len(self.properties))
            # properties
            for prop in self.properties:
                data += prop.dumpData()
            return data

        def mapFids(self,record,function,save=False):
            for prop in self.properties:
                value = prop.value
                # Type 1 - Object Reference: (fid,aid)
                if isinstance(value,tuple):
                    value = (function(value[0]),value[1])
                    if save:
                        prop.value = value
                # Type 11 - List of Object References: [(fid,aid), (fid,aid), ...]
                elif isinstance(value,list) and value and isinstance(value[0],tuple):
                    value = [(function(x[0]),x[1]) for x in value]
                    if save:
                        prop.value = value

    class Alias(object):
        __slots__ = ('fid','aid','scripts',)
        def __init__(self):
            self.fid = None
            self.aid = 0
            self.scripts = []

        def loadData(self,ins,version,objFormat,readId):
            insUnpack = ins.unpack
            if objFormat == 1:
                self.fid,self.aid,nul = insUnpack('=IHH',8,readId)
            else:
                nul,self.aid,self.fid = insUnpack('=HHI',8,readId)
            # _version - always the same as the primary script's version.
            # _objFormat - always the same as the primary script's objFormat.
            _version,_objFormat,count = insUnpack('=hhH',6,readId)
            Script = MelVmad.scriptEntry
            self.scripts = []
            scriptAppend = self.scripts.append
            for x in xrange(count):
                script = Script()
                script.loadData(ins,version,objFormat,readId)
                scriptAppend(script)

        def dumpData(self):
            # Object Format 2 - (NULL, Aid, Fid)
            data = struct_pack('=HHI', 0, self.aid, self.fid)
            # vmad version, object format, script count
            data += struct_pack('=3H', 5, 2, len(self.scripts))
            # Primary Scripts
            for script in self.scripts:
                data += script.dumpData()
            return data

        def mapFids(self,record,function,save=False):
            if self.fid:
                fid = function(self.fid)
                if save: self.fid = fid
            for script in self.scripts:
                script.mapFids(record,function,save)

    class Vmad(object):
        __slots__ = ('scripts','fragmentInfo','fragments','aliases',)
        def __init__(self):
            self.scripts = []
            self.fragmentInfo = None
            self.fragments = None
            self.aliases = None

        def loadData(self,record,ins,size,readId):
            insTell = ins.tell
            endOfField = insTell() + size
            self.scripts = []
            scriptsAppend = self.scripts.append
            Script = MelVmad.scriptEntry
            # VMAD Header wbVMAD
            version,objFormat,scriptCount = ins.unpack('=3H',6,readId)
            # Primary Scripts
            for x in xrange(scriptCount):
                script = Script()
                script.loadData(ins,version,objFormat,readId)
                scriptsAppend(script)
            # Script Fragments
            if insTell() < endOfField:
                self.fragmentInfo = MelVmad.scriptFragments()
                Type = record.recType
                fragCount = self.fragmentInfo.loadData(ins,Type,readId)
                self.fragments = []
                fragAppend = self.fragments.append
                Fragment = MelVmad.FragmentMap[Type]
                for x in xrange(fragCount):
                    frag = Fragment()
                    frag.loadData(ins,readId)
                    fragAppend(frag)
                # Alias Scripts
                if Type == 'QUST':
                    aliasCount, = ins.unpack('=H',2,readId)
                    Alias = MelVmad.Alias
                    self.aliases = []
                    aliasAppend = self.aliases.append
                    for x in xrange(aliasCount):
                        alias = Alias()
                        alias.loadData(ins,version,objFormat,readId)
                        aliasAppend(alias)
                else:
                    self.aliases = None
            else:
                self.fragmentInfo = None
                self.fragments = None
                self.aliases = None

        def dumpData(self,record):
            # Header
            #data = structPack('=3H',4,1,len(self.scripts)) # vmad version, object format, script count
            data = struct_pack('=3H', 5, 2, len(self.scripts)) # vmad version, object format, script count
            # Primary Scripts
            for script in self.scripts:
                data += script.dumpData()
            # Script Fragments
            if self.fragments:
                Type = record.recType
                data += self.fragmentInfo.dumpData(Type,len(self.fragments))
                for frag in self.fragments:
                    data += frag.dumpData()
                if Type == 'QUST':
                    # Alias Scripts
                    aliases = self.aliases
                    data += struct_pack('=H', len(aliases))
                    for alias in aliases:
                        data += alias.dumpData()
            return data

        def mapFids(self,record,function,save=False):
            for script in self.scripts:
                script.mapFids(record,function,save)
            if not self.aliases:
                return
            for alias in self.aliases:
                alias.mapFids(record,function,save)

    def __init__(self, subType='VMAD', attr='vmdata'):
        MelBase.__init__(self, subType, attr)

    def hasFids(self,formElements):
        """Include self if has fids."""
        formElements.add(self)

    def setDefault(self,record):
        record.__setattr__(self.attr,None)

    def getDefault(self):
        target = MelObject()
        return self.setDefault(target)

    def loadData(self, record, ins, sub_type, size_, readId):
        vmad = MelVmad.Vmad()
        vmad.loadData(record, ins, size_, readId)
        record.__setattr__(self.attr,vmad)

    def dumpData(self,record,out):
        """Dumps data from record to outstream"""
        vmad = record.__getattribute__(self.attr)
        if vmad is None: return
        # Write
        out.packSub(self.subType,vmad.dumpData(record))

    def mapFids(self,record,function,save=False):
        """Applies function to fids.  If save is true, then fid is set
           to result of function."""
        vmad = record.__getattribute__(self.attr)
        if vmad is None: return
        vmad.mapFids(record,function,save)

#------------------------------------------------------------------------------
# Fallout 4 Records  ----------------------------------------------------------
#------------------------------------------------------------------------------
class MreHeader(MreHeaderBase):
    """TES4 Record.  File header."""
    classType = 'TES4'

    #--Data elements
    melSet = MelSet(
        MelStruct('HEDR','f2I',('version',0.95),'numRecords',('nextObject',0xCE6)),
        MelBase('TNAM', 'tnam_p'),
        MelUnicode('CNAM','author',u'',512),
        MelUnicode('SNAM','description',u'',512),
        MreHeaderBase.MelMasterName('MAST','masters'),
        MelNull('DATA'), # 8 Bytes in Length
        MelFidList('ONAM','overrides',),
        MelBase('SCRN', 'scrn_p'),
        MelBase('INTV','intv_p'),
        MelBase('INCC', 'incc_p'),
        )
    __slots__ = MreHeaderBase.__slots__ + melSet.getSlotsUsed()
#------------------------------------------------------------------------------
class MreActi(MelRecord):
    """Activator."""
    classType = 'ACTI'

    ActivatorFlags = Flags(0L,Flags.getNames(
        (0, 'noDisplacement'),
        (1, 'ignoredBySandbox'),
    ))

    melSet = MelSet(
        MelString('EDID','eid'),
        MelBase('VMAD', 'vmad_p'),
        MelBounds(),
		MelFid('PTRN', 'previewTransform'),
		MelFid('STCP', 'animationSound'),
        MelLString('FULL','full'),
        MelModel(),
        MelDestructible(),
        MelCountedFidList('KWDA', 'keywords', 'KSIZ', '<I'),
		MelStructs('PRPS', 'If', 'properties', (FID,'actorValue'), 'value'),
        MelFid('NTRM', 'nativeTerminal'),
        MelFid('FTYP', 'forcedLocRefType'),
        MelStruct('PNAM','=4B','red','green','blue','unused'),
        MelOptStruct('SNAM','I',(FID,'dropSound')),
        MelOptStruct('VNAM','I',(FID,'pickupSound')),
        MelOptStruct('WNAM','I',(FID,'water')),
        MelLString('ATTX', 'activateTextOverride',),
        MelLString('RNAM','rnam_p'),
        MelOptStruct('FNAM','H',(ActivatorFlags,'flags',0L),),
        MelOptStruct('KNAM','I',(FID,'keyword')),
        MelOptStruct('RADR', 'I2f2b', 'soundModel', 'frequency','volume',
                  'startsActive','noSignalStatic',),
        MelConditions(),
        MelBase('NVNM','navMeshGeometry'),
        )
    __slots__ = melSet.getSlotsUsed()

#------------------------------------------------------------------------------
# Marker for organization please don't remove ---------------------------------
# GLOB ------------------------------------------------------------------------
# Defined in brec.py as class MreGlob(MelRecord) ------------------------------
#------------------------------------------------------------------------------
class MreLeveledList(MreLeveledListBase):
    """Skyrim Leveled item/creature/spell list."""

    class MelLevListLvlo(MelGroups):
        def __init__(self):
            MelGroups.__init__(self,'entries',
                MelStruct('LVLO','=3I','level',(FID,'listId',None),('count',1)),
                MelCoed(),
                )
        def dumpData(self,record,out):
            out.packSub('LLCT','B',len(record.entries))
            MelGroups.dumpData(self,record,out)

    __slots__ = MreLeveledListBase.__slots__


#------------------------------------------------------------------------------
class MreLvli(MreLeveledList):
    classType = 'LVLI'
    copyAttrs = ('chanceNone','maxCount','glob','filterKeywordChances',
                 'epicLootChance','overrideName')

    melSet = MelSet(
        MelString('EDID','eid'),
        MelBounds(),
        MelStruct('LVLD','B','chanceNone'),
        MelStruct('LVLM','B','maxCount'),
        MelStruct('LVLF','B',(MreLeveledListBase._flags,'flags',0L)),
        MelOptStruct('LVLG','I',(FID,'glob')),
        MelNull('LLCT'),
        MreLeveledList.MelLevListLvlo(),
        MelStructA('LLKC','2I','filterKeywordChances',(FID,'keyword',None),
                      ('chance',0)),
        MelFid('LVSG', 'epicLootChance'),
        MelLString('ONAM', 'overrideName')
        )
    __slots__ = MreLeveledList.__slots__ + melSet.getSlotsUsed()

#------------------------------------------------------------------------------
class MreLvln(MreLeveledList):
    classType = 'LVLN'
    copyAttrs = ('chanceNone','maxCount','glob','filterKeywordChances',
                 'model','modt_p')

    melSet = MelSet(
        MelString('EDID','eid'),
        MelBounds(),
        MelStruct('LVLD','B','chanceNone'),
        MelStruct('LVLM','B','maxCount'),
        MelStruct('LVLF','B',(MreLeveledListBase._flags,'flags',0L)),
        MelOptStruct('LVLG','I',(FID,'glob')),
        MelNull('LLCT'),
        MreLeveledList.MelLevListLvlo(),
        MelStructA('LLKC','2I','filterKeywordChances',(FID,'keyword',None),
                      ('chance',0)),
        MelString('MODL','model'),
        MelBase('MODT','modt_p'),
        )
    __slots__ = MreLeveledList.__slots__ + melSet.getSlotsUsed()

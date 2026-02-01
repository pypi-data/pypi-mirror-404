##
# File: PdbxChemCompUtils.py
# Date: 31-May-2010  John Westbrook
#
# Update:
# 06-Aug-2010 - jdw - Generalized construction of methods to apply to any category
#                     Add accessors for lists of dictionaries.
#
# 23-Aug-2010 - jdw - Add internal content categories
#
# 24-Aug-2010 - jdw - Add PdbxChemCompUpdater class
# 14-Aug-2011 - jdw - Add PdbxChemCompWriter class
#  1-Oct-2011 - jdw - Add PdbxChemCompConstants, PdbxChemCompAtom and PdbxChemCompBond classes
# 21-Oct-2012 - jdw - Cleanup and reoranization
# 25-Oct-2018 - jdw - Added this older module to support OneDep ccmodule.
# 15-Jul-2019 - ep  - Added getAtomList() to PdbxChemCompReader
#
##
"""
A collection of classes supporting chemical component dictionary data files.

"""
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "jwest@rcsb.rutgers.edu"
__license__ = "Apache 2.0"

import logging
import os
import sys

from mmcif.api.DataCategory import DataCategory
from mmcif.api.PdbxContainers import *
from mmcif.io.PdbxReader import PdbxReader
from mmcif.io.PdbxWriter import PdbxWriter


logger = logging.getLogger(__name__)


class PdbxChemCompCategoryDefinition(object):
    _categoryInfo = [('chem_comp', 'key-value'),
                     ('chem_comp_atom', 'table'),
                     ('chem_comp_bond', 'table'),
                     ('chem_comp_identifier', 'table'),
                     ('chem_comp_descriptor', 'table'),
                     ('pdbx_chem_comp_audit', 'table'),
                     ('pdbx_chem_comp_import', 'table'),
                     ('pdbx_chem_comp_atom_edit', 'table'),
                     ('pdbx_chem_comp_bond_edit', 'table')
                     ]
    _cDict = {
        'chem_comp': [
            ('_chem_comp.id', '%s', 'str', ''),
            ('_chem_comp.name', '%s', 'str', ''),
            ('_chem_comp.type', '%s', 'str', ''),
            ('_chem_comp.pdbx_type', '%s', 'str', ''),
            ('_chem_comp.formula', '%s', 'str', ''),
            ('_chem_comp.mon_nstd_parent_comp_id', '%s', 'str', ''),
            ('_chem_comp.pdbx_synonyms', '%s', 'str', ''),
            ('_chem_comp.pdbx_formal_charge', '%s', 'str', ''),
            ('_chem_comp.pdbx_initial_date', '%s', 'str', ''),
            ('_chem_comp.pdbx_modified_date', '%s', 'str', ''),
            ('_chem_comp.pdbx_ambiguous_flag', '%s', 'str', ''),
            ('_chem_comp.pdbx_release_status', '%s', 'str', ''),
            ('_chem_comp.pdbx_replaced_by', '%s', 'str', ''),
            ('_chem_comp.pdbx_replaces', '%s', 'str', ''),
            ('_chem_comp.formula_weight', '%s', 'str', ''),
            ('_chem_comp.one_letter_code', '%s', 'str', ''),
            ('_chem_comp.three_letter_code', '%s', 'str', ''),
            ('_chem_comp.pdbx_model_coordinates_details', '%s', 'str', ''),
            ('_chem_comp.pdbx_model_coordinates_missing_flag', '%s', 'str', ''),
            ('_chem_comp.pdbx_ideal_coordinates_details', '%s', 'str', ''),
            ('_chem_comp.pdbx_ideal_coordinates_missing_flag', '%s', 'str', ''),
            ('_chem_comp.pdbx_model_coordinates_db_code', '%s', 'str', ''),
            ('_chem_comp.pdbx_subcomponent_list', '%s', 'str', ''),
            ('_chem_comp.pdbx_processing_site', '%s', 'str', '')
        ],
        'chem_comp_atom': [
            ('_chem_comp_atom.comp_id', '%s', 'str', ''),
            ('_chem_comp_atom.atom_id', '%s', 'str', ''),
            ('_chem_comp_atom.alt_atom_id', '%s', 'str', ''),
            ('_chem_comp_atom.type_symbol', '%s', 'str', ''),
            ('_chem_comp_atom.charge', '%s', 'str', ''),
            ('_chem_comp_atom.pdbx_align', '%s', 'str', ''),
            ('_chem_comp_atom.pdbx_aromatic_flag', '%s', 'str', ''),
            ('_chem_comp_atom.pdbx_leaving_atom_flag', '%s', 'str', ''),
            ('_chem_comp_atom.pdbx_stereo_config', '%s', 'str', ''),
            ('_chem_comp_atom.model_Cartn_x', '%s', 'str', ''),
            ('_chem_comp_atom.model_Cartn_y', '%s', 'str', ''),
            ('_chem_comp_atom.model_Cartn_z', '%s', 'str', ''),
            ('_chem_comp_atom.pdbx_model_Cartn_x_ideal', '%s', 'str', ''),
            ('_chem_comp_atom.pdbx_model_Cartn_y_ideal', '%s', 'str', ''),
            ('_chem_comp_atom.pdbx_model_Cartn_z_ideal', '%s', 'str', ''),
            ('_chem_comp_atom.pdbx_component_atom_id', '%s', 'str', ''),
            ('_chem_comp_atom.pdbx_component_comp_id', '%s', 'str', ''),
            ('_chem_comp_atom.pdbx_ordinal', '%s', 'str', '')
        ],
        'chem_comp_bond': [
            ('_chem_comp_bond.comp_id', '%s', 'str', ''),
            ('_chem_comp_bond.atom_id_1', '%s', 'str', ''),
            ('_chem_comp_bond.atom_id_2', '%s', 'str', ''),
            ('_chem_comp_bond.value_order', '%s', 'str', ''),
            ('_chem_comp_bond.pdbx_aromatic_flag', '%s', 'str', ''),
            ('_chem_comp_bond.pdbx_stereo_config', '%s', 'str', ''),
            ('_chem_comp_bond.pdbx_ordinal', '%s', 'str', '')
        ],
        'chem_comp_descriptor': [
            ('_pdbx_chem_comp_descriptor.comp_id', '%s', 'str', ''),
            ('_pdbx_chem_comp_descriptor.type', '%s', 'str', ''),
            ('_pdbx_chem_comp_descriptor.program', '%s', 'str', ''),
            ('_pdbx_chem_comp_descriptor.program_version', '%s', 'str', ''),
            ('_pdbx_chem_comp_descriptor.descriptor', '%s', 'str', '')
        ],
        'chem_comp_identifier': [
            ('_pdbx_chem_comp_identifier.comp_id', '%s', 'str', ''),
            ('_pdbx_chem_comp_identifier.type', '%s', 'str', ''),
            ('_pdbx_chem_comp_identifier.program', '%s', 'str', ''),
            ('_pdbx_chem_comp_identifier.program_version', '%s', 'str', ''),
            ('_pdbx_chem_comp_identifier.identifier', '%s', 'str', '')
        ],
        'pdbx_chem_comp_import': [
            ('_pdbx_chem_comp_identifier.comp_id', '%s', 'str', ''),
            ('_pdbx_chem_comp_identifier.comp_alias_id', '%s', 'str', ''),
            ('_pdbx_chem_comp_identifier.model_path', '%s', 'str', '')
        ],
        'pdbx_chem_comp_audit': [
            ('_pdbx_chem_comp_identifier.comp_id', '%s', 'str', ''),
            ('_pdbx_chem_comp_identifier.action_type', '%s', 'str', ''),
            ('_pdbx_chem_comp_identifier.date', '%s', 'str', ''),
            ('_pdbx_chem_comp_identifier.processing_site', '%s', 'str', ''),
            ('_pdbx_chem_comp_identifier.annotator', '%s', 'str', ''),
            ('_pdbx_chem_comp_identifier.details', '%s', 'str', '')
        ],
        'pdbx_chem_comp_atom_edit': [
            ('_pdbx_chem_comp_atom_edit.ordinal', '%d', 'int', ''),
            ('_pdbx_chem_comp_atom_edit.comp_id', '%s', 'str', ''),
            ('_pdbx_chem_comp_atom_edit.atom_id', '%s', 'str', ''),
            ('_pdbx_chem_comp_atom_edit.edit_op', '%s', 'str', ''),
            ('_pdbx_chem_comp_atom_edit.edit_atom_id', '%s', 'str', ''),
            ('_pdbx_chem_comp_atom_edit.edit_atom_value', '%s', 'str', '')
        ],
        'pdbx_chem_comp_bond_edit': [
            ('_pdbx_chem_comp_bond_edit.ordinal', '%d', 'int', ''),
            ('_pdbx_chem_comp_bond_edit.comp_id_1', '%s', 'str', ''),
            ('_pdbx_chem_comp_bond_edit.atom_id_1', '%s', 'str', ''),
            ('_pdbx_chem_comp_bond_edit.comp_id_2', '%s', 'str', ''),
            ('_pdbx_chem_comp_bond_edit.atom_id_2', '%s', 'str', ''),
            ('_pdbx_chem_comp_bond_edit.edit_op', '%s', 'str', ''),
            ('_pdbx_chem_comp_bond_edit.edit_bond_value', '%s', 'str', '')
        ]
    }


class PdbxChemCompReader(object):
    ''' Accessor methods chemical component definition data files.

        Currently supporting bond data data for the WWF format converter.
    '''

    def __init__(self, verbose=True, log=sys.stderr):
        self.__verbose = verbose
        self.__debug = False
        self.__lfh = log
        self.__dBlock = None
        self.__topCachePath = None
        self.__ccU = None
        self.__filePath = None
        #

    def getBlockId(self):
        try:
            if self.__dBlock is not None:
                return self.__dBlock.getName()
            else:
                False
        except Exception:
            return False

    def setCachePath(self, topCachePath='/data/components/ligand-dict-v4'):
        self.__topCachePath = topCachePath

    def setCompId(self, compId):
        """ Set the identifier for the target chemical component.   The internal target file path
            is set to the chemmical component definition file stored in the organization of
            CVS repository for chemical components if this exists.
        """
        self.__ccU = compId.upper()
        hashd = self.__getCcdHash(self.__ccU)
        self.__filePath = os.path.join(self.__topCachePath, hashd, self.__ccU, self.__ccU + '.cif')
        if (not os.access(self.__filePath, os.R_OK)):
            if (self.__verbose):
                logger.debug("+ERROR- PdbxChemCompReader.setCompId() Missing file %s\n" % self.__filePath)
            return False
        return True

    def setFilePath(self, filePath, compId=None):
        """ Specify the file path for the target component and optionally provide an identifier
            for component data section within the file.
        """
        try:
            if compId is not None:
                self.__ccU = str(compId).upper()
            self.__filePath = filePath
            if (not os.access(self.__filePath, os.R_OK)):
                if (self.__verbose):
                    logger.debug("+ERROR- PdbxChemCompReader.setFilePath() Missing file %s\n" % filePath)
                return False
            else:
                if (self.__verbose):
                    logger.debug("+PdbxChemCompReader.setFilePath() file path %s comp id %s\n"
                                 % (self.__filePath, self.__ccU))
            return True

        except Exception:
            if (self.__verbose):
                logger.debug("+ERROR- PdbxChemCompReader.setFilePath() Missing file %s\n" % filePath)
            return False

    def getComp(self):
        """ Get the definition data for the target component in the internal filepath.  If the component
            identifer has been set, then the datablock corresponding to this identifier will be returned.

            Otherwise if the component is set to None, the data in the first datablock is returned.

            Returns True for success or False otherwise.
        """
        try:
            block = self.__getDataBlock(self.__filePath, self.__ccU)
            return self.__setDataBlock(block)

        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            return False

    def getChemCompCategory(self, catName='chem_comp'):
        return self.__getDictList(catName=catName)

    def getAtomList(self):
        return self.__getDataList(catName='chem_comp_atom')

    def getBondList(self):
        return self.__getDataList(catName='chem_comp_bond')

    def getAttribDictList(self, catName='chem_comp'):
        return self.__getAttribDictList(catName=catName)

    def getChemCompDict(self):
        return self.__getDictList(catName='chem_comp')

    def __getDataBlock(self, filePath, blockId=None):
        """ Worker method to read chemical component definition file and set the target datablock
            corresponding to the target chemical component.   If no blockId is provided return the
            first data block.
        """
        try:
            ifh = open(filePath, 'r')
            myBlockList = []
            pRd = PdbxReader(ifh)
            pRd.read(myBlockList)
            ifh.close()
            if (blockId is not None):
                for block in myBlockList:
                    if (block.getType() == 'data' and block.getName() == blockId):
                        if (self.__debug):
                            block.printIt(self.__lfh)
                        return block
            else:
                for block in myBlockList:
                    if (block.getType() == 'data'):
                        if (self.__debug):
                            block.printIt(self.__lfh)
                        return block

            return None
        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            return None

    def __setDataBlock(self, dataBlock=None):
        """ Assigns the input data block as the active internal data block containing the
            target chemical component definition.
        """
        ok = False
        try:
            if dataBlock.getType() == 'data':
                self.__dBlock = dataBlock
                ok = True
            else:
                self.__dBlock = None
        except Exception:
            pass

        return ok

    def __getDictList(self, catName='chem_comp'):
        """Return a list of dictionaries of the input category where the dictionaries
           represent the row with full item names as dictionary keys.
        """
        #
        # Get category object - from current data block
        #
        itTupList = PdbxChemCompCategoryDefinition._cDict[catName]

        dList = []
        try:
            catObj = self.__dBlock.getObj(catName)
            # nRows = catObj.getRowCount()
        except Exception:
            return dList
        #
        # Get column name index.
        #
        itDict = {}
        itNameList = catObj.getItemNameList()
        for idxIt, itName in enumerate(itNameList):
            itDict[itName] = idxIt
        #
        # Find the mapping to the local category definition
        #
        colDict = {}
        #
        for ii, itTup in enumerate(itTupList):
            if itTup[0] in itDict:
                colDict[itTup[0]] = itDict[itTup[0]]
        #
        rowList = catObj.getRowList()

        for row in rowList:
            tD = {}
            for k, v in colDict.items():
                tD[k] = row[v]
            dList.append(tD)

        return dList

    def __getAttribDictList(self, catName='chem_comp'):
        """Return the input category as a list of dictionaries where the dictionaries
           represent the row with attribute names as dictionary keys.
        """
        #
        dList = []
        #
        # Get category object - from current data block
        #
        itTupList = PdbxChemCompCategoryDefinition._cDict[catName]

        catObj = self.__dBlock.getObj(catName)
        if catObj is None:
            return dList

        # nRows = catObj.getRowCount()
        #
        # Get column name index.
        #
        itDict = {}
        itNameList = catObj.getItemNameList()
        for idxIt, itName in enumerate(itNameList):
            itDict[itName] = idxIt
        #
        # Find the mapping to the local category definition
        #
        colDict = {}
        #
        for ii, itTup in enumerate(itTupList):
            if itTup[0] in itDict:
                attrib = self.__attributePart(itTup[0])
                colDict[attrib] = itDict[itTup[0]]
        #
        rowList = catObj.getRowList()
        for row in rowList:
            tD = {}
            for k, v in colDict.items():
                tD[k] = row[v]
            dList.append(tD)

        return dList

    def __getDataList(self, catName='chem_comp_bond'):
        """Return  a list of data from the input category including
           data types and default value replacement.

           For list representing each row is column ordered according to the internal
           data structure PdbxChemCompCategoryDefinition._cDict[catName]

        """
        dataList = []
        itTupList = PdbxChemCompCategoryDefinition._cDict[catName]
        catObj = self.__dBlock.getObj(catName)
        if (catObj is None):
            return dataList

        # nRows = catObj.getRowCount()

        itDict = {}
        itNameList = catObj.getItemNameList()
        for idxIt, itName in enumerate(itNameList):
            itDict[itName] = idxIt
        #
        colTupList = []
        # (column index of data or -1, type name, [default value]  )
        for ii, itTup in enumerate(itTupList):
            if itTup[0] in itDict:
                colTupList.append((itDict[itTup[0]], itTup[2], itTup[3]))
            else:
                colTupList.append((-1, itTup[2], itTup[3]))
        #
        rowList = catObj.getRowList()

        for row in rowList:
            uR = []
            for cTup in colTupList:

                if cTup[0] < 0:
                    uR.append(self.__applyType(cTup[1], cTup[2], cTup[2]))
                else:
                    uR.append(self.__applyType(cTup[1], cTup[2], row[cTup[0]]))

            dataList.append(uR)

        return dataList

    def __applyType(self, type, default, val):
        """Apply type conversion to the input value and assign default values to
           missing values.
        """
        tval = val
        if (val is None):
            tval = default
        if (isinstance(tval, str) and (len(tval) < 1 or tval == '.' or tval == '?')):
            tval = default

        if type == "int":
            return int(str(tval))
        elif type == "float":
            return float(str(tval))
        elif type == "str":
            return str(tval)
        else:
            return tval

    def __attributePart(self, name):
        i = name.find(".")
        if i == -1:
            return None
        else:
            return name[i + 1:]

    def __getCcdHash(self, idCode):
        """Returns the hash code for a CCD id.  Currently first letter"""
        if not idCode:
            return None

        if len(idCode) > 3:
            hash_key = idCode.upper()[-2:]
        else:
            hash_key = idCode.upper()[0]

        return hash_key

class PdbxChemCompUpdater(object):
    ''' Utility methods for updating chemical component definition data files.

    '''

    def __init__(self, verbose=True, log=sys.stderr):
        self.__verbose = verbose
        self.__debug = False
        self.__lfh = log
        self.__ccU = None
        self.__filePath = None
        self.__idxBlock = None
        self.__myBlockList = []
        #

    def readComp(self, filePath, compId=None):
        """ Specify the file path for the target component and optionally provide an identifier
            for component data section within the file.
        """
        try:
            if compId is not None:
                self.__ccU = str(compId).upper()
            self.__filePath = filePath
            if (not os.access(self.__filePath, os.R_OK)):
                if (self.__verbose):
                    logger.debug("+ERROR- PdbxChemCompUpdater.readComp() Missing file %s\n" % filePath)
                return False
            else:
                if (self.__verbose):
                    logger.debug("+PdbxChemCompUpdater.readComp() file path %s comp id %s\n"
                                 % (self.__filePath, self.__ccU))
        except Exception:
            if (self.__verbose):
                logger.debug("+ERROR- PdbxChemCompUpdater.readComp() Missing file %s\n" % filePath)
            return False
        #
        return self.__getComp()

    def __getComp(self):
        """ Get the definition data for the target component in the internal filepath.  If the component
            identifer has been set, then the datablock corresponding to this identifier will be returned.

            Otherwise if the component is set to None, the data in the first datablock is returned.

            Returns True for success or False otherwise.
        """
        try:
            self.__idxBlock = self.__getDataBlockIdx(self.__filePath, self.__ccU)
            if self.__idxBlock is not None:
                return True
            else:
                return False

        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            return False

    def __getDataBlockIdx(self, filePath, blockId=None):
        """ Worker method to read chemical component definition file and set the target datablock
            corresponding to the target chemical component.   If no blockId is provided return the
            first data block if this exists.  None is returned otherwise.
        """
        try:
            ifh = open(filePath, 'r')
            self.__myBlockList = []
            pRd = PdbxReader(ifh)
            pRd.read(self.__myBlockList)
            ifh.close()
            idxBlock = 0
            if (blockId is not None):
                for block in self.__myBlockList:
                    if (block.getType() == 'data' and block.getName() == blockId):
                        if (self.__debug):
                            block.printIt(self.__lfh)
                        return idxBlock
                    idxBlock += 1
            else:
                for block in self.__myBlockList:
                    if (block.getType() == 'data'):
                        if (self.__debug):
                            block.printIt(self.__lfh)
                        return idxBlock
                    idxBlock += 1

            return None
        except Exception:
            logger.exception("Failing with %s" % str(e))
            return None

    def update(self, catName, attribName, value, iRow=0):
        #
        #
        try:
            #
            myBlock = self.__myBlockList[self.__idxBlock]

            myCat = myBlock.getObj(catName)
            myCat.setValue(value, attribName, iRow)
            return True

        except Exception:
            logger.exception("Failing with %s" % str(e))
            return False

    def updateItem(self, itemName, value, iRow=0):
        #
        #
        try:
            catName = self.__categoryPart(itemName)
            attribName = self.__attributePart(itemName)
            #
            myBlock = self.__myBlockList[self.__idxBlock]

            myCat = myBlock.getObj(catName)
            myCat.setValue(value, attribName, iRow)
            return True

        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            return False

    def write(self):
        return self.__write(self.__filePath)

    def __write(self, filePath):
        try:
            ofh = open(filePath, "w")
            pdbxW = PdbxWriter(ofh)
            pdbxW.write(self.__myBlockList)
            ofh.close()
        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            return False

        return True

    def __categoryPart(self, name):
        tname = ""
        if name.startswith("_"):
            tname = name[1:]
        else:
            tname = name

        i = tname.find(".")
        if i == -1:
            return tname
        else:
            return tname[:i]

    def __attributePart(self, name):
        i = name.find(".")
        if i == -1:
            return None
        else:
            return name[i + 1:]


class PdbxChemCompWriter(object):
    ''' Utility methods creating new chemical component definition data files.

    '''

    def __init__(self, verbose=True, log=sys.stderr):
        self.__verbose = verbose
        self.__debug = False
        self.__lfh = log
        self.__ccU = None
        self.__filePath = None
        #
        self.__idxBlock = None
        self.__myBlockList = []
        self.__myBlockIdList = []
        self.__curBlock = None
        self.__categoryD = PdbxChemCompCategoryDefinition._cDict
        self.__categoryI = PdbxChemCompCategoryDefinition._categoryInfo
        #

    def setBlock(self, blockId):
        try:
            idxBlock = self.__myBLockIdList.index(blockId)
            self.__curBlock = self.__myBlockList[idxBlock]
            self.__idxBlock = idxBlock
            return True
        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            return False

    def newBlock(self, blockId):
        """  Create an new data block and append this to the block list.

             if blockId exists then no action is taken.

             Returns True for success or False otherwise
        """
        try:
            if blockId in self.__myBlockIdList:
                return True
            self.__curBlock = DataContainer(blockId)
            self.__myBlockList.append(self.__curBlock)
            self.__myBlockIdList.append(blockId)
            self.__idxBlock = self.__myBlockIdList.index(blockId)
            self.__initCategories()
            return True
        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            return False

    def __initCategories(self):
        for category, type in self.__categoryI:
            itemTupList = self.__categoryD[category]
            newCat = DataCategory(category)
            for itemName, format, type, default in itemTupList:
                name = self.__attributePart(itemName)
                newCat.appendAttribute(name)
            self.__curBlock.append(newCat)

    def update(self, catName, attribName, value, iRow=0):

        try:
            #
            myBlock = self.__myBlockList[self.__idxBlock]

            myCat = myBlock.getObj(catName)
            myCat.setValue(value, attribName, iRow)
            return True

        except Exception as e:
            if (self.__verbose):
                logger.debug("PdbxChemCompWriter(update) category %s attribute %s value %s\n" % (catName, attribName, value))
            logger.exception("Failing with %s" % str(e))
            return False

    def updateItem(self, itemName, value, iRow=0):
        try:
            catName = self.__categoryPart(itemName)
            attribName = self.__attributePart(itemName)
            #
            myBlock = self.__myBlockList[self.__idxBlock]

            myCat = myBlock.getObj(catName)
            myCat.setValue(value, attribName, iRow)
            return True

        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            return False

    def write(self, filePath):
        try:
            ofh = open(filePath, "w")
            pdbxW = PdbxWriter(ofh)
            pdbxW.write(self.__myBlockList)
            ofh.close()
        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            return False

        return True

    def __categoryPart(self, name):
        tname = ""
        if name.startswith("_"):
            tname = name[1:]
        else:
            tname = name

        i = tname.find(".")
        if i == -1:
            return tname
        else:
            return tname[:i]

    def __attributePart(self, name):
        i = name.find(".")
        if i == -1:
            return None
        else:
            return name[i + 1:]

##
# File: PdbxAnnFeature.py
# Date: 17-Feb-2012  John Westbrook
#
# Updated:
#  23-Oct-2012 jdw  Update path and reorganize
##
"""
A collection of classes supporting annotation feature data files.

"""
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "john.westbrook@rcsb.org"
__license__ = "Apache 2.0"


import sys
import os

import logging
logger = logging.getLogger(__name__)

from mmcif.io.PdbxReader import PdbxReader
from mmcif.io.PdbxWriter import PdbxWriter


class PdbxAnnFeatureCategoryDefinition(object):

    _categoryInfo = [('pdbx_carbohydrate_features', 'table')]

    _cDict = {
        'pdbx_carbohydrate_features': [
            ('_pdbx_carbohydrate_features.ordinal', '%d', 'int', 1),
            ('_pdbx_carbohydrate_features.entry_id', '%s', 'str', ''),
            ('_pdbx_carbohydrate_features.type', '%s', 'str', ''),
            ('_pdbx_carbohydrate_features.value', '%s', 'str', ''),
            ('_pdbx_carbohydrate_features.assigned_by', '%s', 'str', ''),
            ('_pdbx_carbohydrate_features.support', '%s', 'str', ''),
            ('_pdbx_carbohydrate_features.details', '%s', 'str', ''),
            ('_pdbx_carbohydrate_features.date', '%s', 'str', '')
        ]
    }


class PdbxAnnFeatureReader(object):
    ''' Accessor methods for annotation feature data files.

    '''

    def __init__(self, verbose=True):
        self.__verbose = verbose
        self.__debug = False
        self.__lfh = sys.stdout
        self.__dBlock = None
        self.__topCachePath = None
        self.__blockId = None
        self.__filePath = None
        #

    def getBlock(self):
        return self.__dBlock

    def getBlockId(self):
        try:
            if self.__dBlock is not None:
                return self.__dBlock.getName()
            else:
                False
        except Exception as e:
            return False

    def setFilePath(self, filePath, blockId=None):
        """ Specify the file path for the target data file.
        """
        try:
            if blockId is not None:
                self.__blockId = str(blockId).upper()
            self.__filePath = filePath
            if (not os.access(self.__filePath, os.R_OK)):
                logger.error("+ERROR- PdbxAnnFeatureReader.setFilePath() Missing file %s\n" % filePath)
                return False
            else:
                logger.debug("+PdbxAnnFeatureReader.setFilePath() file path %s prd id %s\n"
                             % (self.__filePath, self.__blockId))
            return True
        except Exception as e:
            logger.error("+ERROR- PdbxAnnFeatureReader.setFilePath() Missing file %s\n" % filePath)
            return False

    def get(self):
        """ Return the current or target datablock.

            Otherwise if the blockId is set to None, the data in the first datablock is returned.

            Returns True for success or False otherwise.
        """
        try:
            block = self.__getDataBlock(self.__filePath, self.__blockId)
            return self.__setDataBlock(block)

        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            return False

    def getCategory(self, catName='pdbx_reference_entity'):
        return self.__getDictList(catName=catName)

    def getCategoryAttribDict(self, catName='pdbx_reference_entity'):
        return self.__getAttribDictList(catName=catName)

    def __getDataBlock(self, filePath, blockId=None):
        """ Worker method to read target file and set the target datablock
            corresponding to blockId.   If no blockId is provided return the
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
        """ Assigns the input data block as the active internal data block.
        """
        ok = False
        try:
            if dataBlock.getType() == 'data':
                self.__dBlock = dataBlock
                ok = True
            else:
                self.__dBlock = None
        except Exception as e:
            pass

        return ok

    def getCategoryList(self):
        if self.__dBlock is not None:
            return self.__dBlock.getObjNameList()
        else:
            return []

    def __getDictList(self, catName='pdbx_reference_entity'):
        """Return the input category as a list of dictionaries where the dictionaries
           represent the row with full item names as dictionary keys.
        """
        #
        dList = []
        #
        # Get category object - from current data block
        #
        itTupList = PdbxAnnFeatureCategoryDefinition._cDict[catName]
        catObj = self.__dBlock.getObj(catName)
        if catObj is None:
            return dList

        nRows = catObj.getRowCount()
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
            for itTup in itTupList:
                tD[itTup[0]] = itTup[3]
            for k, v in colDict.items():
                tD[k] = row[v]
            dList.append(tD)

        return dList

    def __getAttribDictList(self, catName='pdbx_reference_entity'):
        """Return the input category as a list of dictionaries where the dictionaries
           represent the row with attribute names as dictionary keys.
        """
        #
        dList = []
        #
        # Get category object - from current data block
        #
        itTupList = PdbxAnnFeatureCategoryDefinition._cDict[catName]
        catObj = self.__dBlock.getObj(catName)
        if catObj is None:
            return dList

        nRows = catObj.getRowCount()
        #
        # Get column name index.
        #
        itDict = {}
        itNameList = catObj.getItemNameList()
        for idxIt, itName in enumerate(itNameList):
            itDict[itName] = idxIt

        attribList = [self.__attributePart(itTup[0]) for itTup in itTupList]
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
            for itTup in itTupList:
                tD[self.__attributePart(itTup[0])] = itTup[3]
            for k, v in colDict.items():
                tD[k] = row[v]
            dList.append(tD)

        return dList

    def __attributePart(self, name):
        i = name.find(".")
        if i == -1:
            return None
        else:
            return name[i + 1:]

    def __getDataList(self, catName='pdbx_reference_entity'):
        """Return  a list of data from the input category including
           data types and default value replacement.

           For list representing each row is column ordered according to the internal
           data structure PdbxAnnFeatureCategoryDefinition._cDict[catName]

        """
        dataList = []
        itTupList = PdbxAnnFeatureCategoryDefinition._cDict[catName]
        catObj = self.__dBlock.getObj(catName)
        if (catObj is None):
            return dataList

        nRows = catObj.getRowCount()

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


class PdbxAnnFeatureUpdater(object):
    ''' Utility methods for updating peptide reference definition data files.

    '''

    def __init__(self, verbose=True):
        self.__verbose = verbose
        self.__debug = False
        self.__lfh = sys.stdout
        self.__blockId = None
        self.__filePath = None
        self.__idxBlock = None
        self.__myBlockList = []
        #

    def read(self, filePath, blockId=None):
        """ Specify the file path for the target component and optionally provide an identifier
            for prd data section within the file.
        """
        try:
            if blockId is not None:
                self.__blockId = str(blockId).upper()
            self.__filePath = filePath
            if (not os.access(self.__filePath, os.R_OK)):
                if (self.__verbose):
                    logger.warning("+ERROR- PdbxAnnFeatureUpdater.read() Missing file %s\n" % filePath)
                return False
            else:
                logger.debug("+PdbxAnnFeatureUpdater.read() file path %s prd id %s\n"
                             % (self.__filePath, self.__blockId))
        except Exception as e:
            logger.error("+ERROR- PdbxAnnFeatureUpdater.read() Missing file %s\n" % filePath)
            return False
        #
        return self.__get()

    def __get(self):
        """ Get the definition data for the target component in the internal filepath.  If the component
            identifer has been set, then the datablock corresponding to this identifier will be returned.

            Otherwise if the component is set to None, the data in the first datablock is returned.

            Returns True for success or False otherwise.
        """
        try:
            self.__idxBlock = self.__getDataBlockIdx(self.__filePath, self.__blockId)
            if self.__idxBlock is not None:
                return True
            else:
                return False

        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            return False

    def __getDataBlockIdx(self, filePath, blockId=None):
        """ Worker method to read the target datablock.   If no blockId is provided return the
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
        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            return None

    def renameBlock(self, new):
        #
        try:
            myBlock = self.__myBlockList[self.__idxBlock]
            myBlock.setName(new)
            return myBlock.getName()
        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            return None

    def getCategoryList(self):
        #
        #
        try:
            myBlock = self.__myBlockList[self.__idxBlock]
            return myBlock.getObjNameList()

        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            return []

    def getRowCount(self, catName):
        #
        #
        try:
            myBlock = self.__myBlockList[self.__idxBlock]

            myCat = myBlock.getObj(catName)
            return myCat.getRowCount()
        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            return 0

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

    def updateAttribute(self, catName, attribName, value, iRow=0):
        #
        #
        try:
            #
            myBlock = self.__myBlockList[self.__idxBlock]

            myCat = myBlock.getObj(catName)
            myCat.setValue(value, attribName, iRow)
            return True

        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            return False

    def getAttribute(self, catName, attribName, iRow=0):
        #
        #
        try:
            #
            myBlock = self.__myBlockList[self.__idxBlock]

            myCat = myBlock.getObj(catName)
            return myCat.getValue(attribName, iRow)
        except Exception as e:
            #logger.exception("Failing with %s" % str(e))
            return None

    def writeFile(self, filePath):
        return self.__write(filePath)

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

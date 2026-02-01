##
# File: PdbxVersion.py
# Date: 20-May-2011  John Westbrook
#
# Updated:
#  23-Oct-2012 jdw  Update path and reorganize
#
##
"""
A collection of classes supporting pdbx_version data.

"""
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "john.westbrook@rcsb.org"
__license__ = "Apache 2.0"
__version__ = "V0.01"


import sys
import os

import logging
logger = logging.getLogger(__name__)

from mmcif.io.PdbxReader import PdbxReader


class PdbxVersionCategoryDefinition(object):

    _categoryInfo = [('pdbx_version', 'table'),
                     ]

    _cDict = {
        'pdbx_version': [
            ('_pdbx_version.entry_id', '%s', 'str', ''),
            ('_pdbx_version.revision_date', '%s', 'str', ''),
            ('_pdbx_version.major_version', '%s', 'str', ''),
            ('_pdbx_version.minor_version', '%s', 'str', ''),
            ('_pdbx_version.revision_type', '%s', 'str', ''),
            ('_pdbx_version.details', '%s', 'str', '')
        ]
    }


class PdbxVersionReader(object):
    ''' Accessor methods for pdbx version data.

    '''

    def __init__(self, verbose=True):
        self.__verbose = verbose
        self.__debug = False
        self.__lfh = sys.stdout
        self.__dBlock = None
        self.__topCachePath = None
        self.__filePath = None
        self.__defaultBlockName = 'PDBX_VERSION'
        #

    def getBlockId(self):
        try:
            if self.__dBlock is not None:
                return self.__dBlock.getName()
            else:
                False
        except Exception as e:
            return False

    def setFilePath(self, filePath):
        """ Specify the file path for the target file.
        """
        try:
            self.__filePath = filePath
            if (not os.access(self.__filePath, os.R_OK)):
                if (self.__verbose):
                    logger.info("+ERROR- PdbxVersionReader.setFilePath() Missing file %s\n" % self.__filePath)
                return False
            else:
                if (self.__verbose):
                    logger.info("+PdbxVersionReader.setFilePath() file path %s\n" % self.__filePath)
            return True
        except Exception as e:
            if (self.__verbose):
                logger.info("+ERROR- PdbxVersionReader.setFilePath() Missing file %s\n" % self.__filePath)
            return False

    def getVersionData(self):
        """   Get the data -

        """
        try:
            block = self.__getDataBlock(self.__filePath, self.__defaultBlockName)
            return self.__setDataBlock(block)

        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            return False

    def getCategory(self, catName='pdbx_version'):
        return self.__getDictList(catName=catName)

    def __getDataBlock(self, filePath, blockId=None):
        """ Worker method to read the version data file and set the target datablock.
            If no blockId is provided return the first data block.
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
            target version data.
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

    def __getDictList(self, catName='pdbx_version'):
        """Return the input category as a list of dictionaries where the dictionaries
           represent the row with full item names as dictionary keys.
        """
        #
        dList = []
        #
        # Get category object - from current data block
        #
        itTupList = PdbxVersionCategoryDefinition._cDict[catName]
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
            for k, v in colDict.items():
                tD[k] = row[v]
            dList.append(tD)

        return dList

    def __getDataList(self, catName='pdbx_reference_entity'):
        """Return  a list of data from the input category including
           data types and default value replacement.

           For list representing each row is column ordered according to the internal
           data structure PdbxVersionCategoryDefinition._cDict[catName]

        """
        dataList = []
        itTupList = PdbxVersionCategoryDefinition._cDict[catName]
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

##
# File:  InventoryIo.py
# Date:  7-Aug-2015
#
# Updates:
#
##
"""
Methods for building inventories of populated data items and some
limited metrics on these items.

"""
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "john.westbrook@rcsb.org"
__license__ = "Apache 2.0"


import sys
import time
import traceback

import logging
logger = logging.getLogger(__name__)

try:
    from mmcif.io.IoAdapterCore import IoAdapterCore as IoAdapter
except:
    from mmcif.io.IoAdapterPy import IoAdapterPy as IoAdapter
#


class InventoryIo(object):

    """ Methods for building inventories of populated data items and some
        limited metrics on these items.
    """

    def __init__(self, IoAdapter=IoAdapter(), verbose=False, log=sys.stderr):
        """
         :param `verbose`:  boolean flag to activate verbose logging.
         :param `log`:      stream for logging.

        """
        self.__verbose = verbose
        self.__lfh = log
        self.__debug = False
        self.__io = IoAdapter
        #
        self.__inputFilePath = None
        self.__enumItemList = []

    def setEnumItemList(self, itemList):
        """  Assign input data items for enum summary ...
        """
        self.__enumItemList = itemList

    def getIndex(self, inpFilePath):
        """  Create inventory dictioanry the inpFilePath

        """
        #

        logger.debug("+InventoryIo.run() inpFilePath %s\n" % inpFilePath)
        fileIndex = {}
        try:
            containerList = self.__io.readFile(inpFilePath)
            fileIndex = {'FILE_NAME': inpFilePath, 'CONTAINER_COUNT': len(containerList), 'CONTAINER_INFO': {}}
            dbIndex = {}
            for jj, container in enumerate(containerList):
                containerName = container.getName()
                objNameList = container.getObjNameList()
                #
                dbIndex[jj] = {'CONTAINER_NAME': containerName, 'CONTAINER_LENGTH': len(objNameList)}
                #
                objInfo = []
                objDict = {}
                enumD = {}
                for item in self.__enumItemList:
                    enumD[item] = {}
                #
                for objName in objNameList:
                    obj = container.getObj(objName)
                    objLen = obj.getRowCount()
                    itemNameList = obj.getItemNameList()
                    objInfo.append((objName, objLen))
                    rowList = obj.getRowList()
                    colLen = [0 for i in range(0, len(itemNameList))]

                    for row in rowList:
                        for ii, col in enumerate(row):
                            if col is not None and len(col) > 0 and col != '.' and col != '?':
                                colLen[ii] += 1
                                if (itemNameList[ii] in self.__enumItemList):
                                    if (col not in enumD[itemNameList[ii]]):
                                        enumD[itemNameList[ii]][col] = 0
                                    enumD[itemNameList[ii]][col] += 1
                    itemInfo = []
                    for ii, itemName in enumerate(itemNameList):
                        itemInfo.append((itemName, colLen[ii]))
                    #
                    objDict[objName] = {'OBJ_LENGTH': len(rowList), 'ITEM_INFO': itemInfo}

                dbIndex[jj]['OBJ_INFO'] = objDict
                dbIndex[jj]['ITEM_ENUM'] = enumD
                fileIndex['CONTAINER_INFO'] = dbIndex

        except Exception as e:
            logger.exception("Failing for %s with  %s" % (inpFilePath, str(e)))

        return fileIndex

if __name__ == '__main__':
    pass

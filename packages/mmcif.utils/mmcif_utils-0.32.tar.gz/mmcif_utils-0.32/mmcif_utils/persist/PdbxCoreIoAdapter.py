# DEPRECATED## DEPRECATED## DEPRECATED## DEPRECATED## DEPRECATED## DEPRECATED## DEPRECATED## DEPRECATED## DEPRECATED## DEPRECATED## DEPRECATED## DEPRECATED
#
# File: PdbxCoreIoAdapter.py
# Date: 20-Jan-2012  John Westbrook
#
# Updates:
#
# 20-Jan-2012 jdw  Currently using core reader and python writer
#  2-Apr-2014 jdw  Add string() cast on all output data --
#  8-Mar-2018 jdw  DEPRECATED use mmcif.io.IoAdapterCore
##
"""
Adapter between PDBx IO classes (C++ Boost/Python wrappers) and Python persistence classes.

"""
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "john.westbrook@rcsb.org"
__license__ = "Apache 2.0"


import sys
import os

import logging
logger = logging.getLogger(__name__)


from mmcif.core.mmciflib import ParseCifSimple, CifFile
from mmcif.api.PdbxContainers import DataContainer
from mmcif.api.DataCategory import DataCategory


class PdbxCoreIoAdapter(object):
    """ Adapter between PDBx IO classes (C++ Boost/Python wrappers) and Python persistence classes.
    """

    def __init__(self, verbose=True, log=sys.stderr):
        self.__verbose = verbose
        self.__debug = False
        self.__lfh = log
        #
        self.__inputPdbxfilePath = None
        #
        self.__containerList = []
        self.__containerNameList = []
        self.__containerTypeList = []
        #

    def setContainerList(self, containerList=None):
        try:
            self.__containerList = containerList
            self.__containNameList = []
            self.__containTypeList = []
            for container in self.__containerList:
                self.__containerNameList.append(container.getName())
                self.__containerTypeList.append(container.getType())
            return True
        except Exception as e:
            if (self.__verbose):
                logger.info("+ERROR- PdbxCoreIoAdaapter.setContainerList() initialization failed\n")
            logger.exception("Failing with %s" % str(e))
            return False

    def getContainer(self, containerName):
        idx = self.__getContainerIndex(containerName)
        if idx is not None:
            return self.__containerList[idx]
        return None

    def getContainerList(self):
        return self.__containerList

    def getContainerNameList(self):
        return self.__containerNameList

    def read(self, pdbxFilePath):
        """ Import the input Pdbx data file.
        """
        try:
            self.__inputPdbxFilePath = pdbxFilePath
            if (not os.access(pdbxFilePath, os.R_OK)):
                if (self.__verbose):
                    logger.info("+ERROR- PdbxCoreIoAdapter.read() Missing file %s\n" % pdbxFilePath)
                return False
            else:
                if (self.__debug):
                    logger.info("+PdbxCoreIoAdapter.read() reading from file path %s\n" % pdbxFilePath)

            return self.__readData(pdbxFilePath, self.__containerList)

        except Exception as e:
            if (self.__verbose):
                logger.info("+ERROR- PdbxCoreIoAdapter.read() Missing file %s\n" % pdbxFilePath)
            return False

    def __readData(self, pdbxFilePath, containerList=[]):
        """ Read all data/definition containers in the input PDBxfile.
        """
        # read file contents -
        #
        try:
            #myReader = ParseCifSimple(pdbxFilePath)
            myReader = ParseCifSimple(pdbxFilePath, verbose=self.__verbose, intCaseSense=0, maxLineLength=900, nullValue="?", parseLogFileName="")
            containerNameList = []
            containerNameList = list(myReader.GetBlockNames(containerNameList))
            if self.__debug:
                logger.info("+PdbxCoreIoAdapter.__readData() containerNameList %r\n" % repr(containerNameList))
            #
            for containerName in containerNameList:
                #
                aContainer = DataContainer(containerName)
                #
                block = myReader.GetBlock(containerName)
                tableNameList = []
                tableNameList = list(block.GetTableNames(tableNameList))

                for tableName in tableNameList:
                    table = block.GetTable(tableName)
                    attributeNameList = list(table.GetColumnNames())
                    if self.__debug:
                        logger.info("+PdbxCoreIoAdapter.__readData() Attribute name list %r\n" % repr(attributeNameList))
                    numRows = table.GetNumRows()
                    rowList = []
                    for iRow in range(0, numRows):
                        row = table.GetRow(iRow)
                        rowList.append(list(row))
                    aCategory = DataCategory(tableName, attributeNameList, rowList)
                    aContainer.append(aCategory)
                    #
                    if self.__debug:
                        logger.info("+PdbxCoreIoAdapter.__read() read %s length %d %d\n" % (tableName, numRows, len(rowList)))
                        # aCategory.printIt()
                containerList.append(aContainer)
            #
            for container in containerList:
                self.__containerNameList.append(container.getName())
                self.__containerTypeList.append(container.getType())
            #
            return True
        except Exception as e:
            if (self.__verbose):
                logger.info("+ERROR- PdbxCoreIoAdapter.__read() Read failed for file %s\n" % pdbxFilePath)
            logger.exception("Failing with %s" % str(e))
            return False

    def write(self, pdbxFilePath, maxLineLength=2048):
        """ Export the current containerlist to PDBx format file in the path 'pdbxFilePath'.
        """
        try:
            if self.__debug:
                logger.info("+PdbxCoreIoAdapter.write() container length %d\n" % len(self.__containerList))
            #cF = CifFile(maxLineLength=maxLineLength)
            cF = CifFile(True, self.__verbose, 0, maxLineLength, '?')
            for container in self.__containerList:
                containerName = container.getName()
                if self.__debug:
                    logger.info("+PdbxCoreIoAdapter.write() write container %s\n" % containerName)
                cF.AddBlock(containerName)
                block = cF.GetBlock(containerName)
                objNameList = container.getObjNameList()
                if self.__debug:
                    logger.info("+PdbxCoreIoAdapter.write() category length %d\n" % len(objNameList))
                #
                for objName in objNameList:
                    name, attributeNameList, rowList = container.getObj(objName).get()
                    table = block.AddTable(name)
                    for attributeName in attributeNameList:
                        table.AddColumn(attributeName)
                    for ii, row in enumerate(rowList):
                        table.AddRow()
                        table.FillRow(ii, [str(col) if col is not None else '?' for col in row])
                    block.WriteTable(table)
            cF.Write(pdbxFilePath)

        except Exception as e:
            if (self.__verbose):
                logger.info("+ERROR- PdbxCoreIoAdapter.write() write failed for file %s\n" % pdbxFilePath)
            logger.exception("Failing with %s" % str(e))
            return False

    def writeContainerList(self, pdbxFilePath, containerNameList):
        """ Export the input containerlist to PDBx format file in the path 'pdbxFilePath'.
        """
        try:
            #cF = CifFile(maxLineLength=2048)
            cF = CifFile(True, self.__verbose, 0, maxLineLength, '?')
            for containerName in containerNameList:
                idx = self.__getContainerIndex(containerName)
                if idx is not None:
                    cF.AddBlock(containerName)
                    block = cF.GetBlock(containerName)
                    objNameList = container.getObjNameList()
                    #
                    for objName in objNameList:
                        name, attributeNameList, rowList = container.getObj(objName).get()
                        table = block.AddTable(name)
                        for attributeName in attributeNameList:
                            table.AddColumn(attributeName)
                        for ii, row in enumerate(rowList):
                            table.AddRow()
                            table.FillRow(ii, [str(col) if col is not None else '?' for col in row])
                        block.WriteTable(table)
            cF.Write(pdbxFilePath)
        except Exception as e:
            if (self.__verbose):
                logger.info("+ERROR- PdbxCoreIoAdapter.write() write failed for file %s\n" % pdbxFilePath)
            logger.exception("Failing with %s" % str(e))
            return False

    def __getContainerIndex(self, name):
        try:
            return self.__containerNameList.index(name)
        except Exception as e:
            return None
    # -----------------------------------

    def __attributePart(self, name):
        i = name.find(".")
        if i == -1:
            return None
        else:
            return name[i + 1:]

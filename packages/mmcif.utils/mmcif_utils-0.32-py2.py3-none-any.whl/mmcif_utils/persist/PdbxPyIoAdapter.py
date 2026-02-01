# DEPRECATED## DEPRECATED## DEPRECATED## DEPRECATED## DEPRECATED## DEPRECATED## DEPRECATED## DEPRECATED## DEPRECATED## DEPRECATED
# File: PdbxPyIoAdapter.py
# Date: 18-Jan-2012  John Westbrook
#
# Updates:
#
# 20-Jan-2012 jdw refactored from PdbxPersist.
# 22-Feb-2012 jdw reorganized indexing to support appending data from multiple reads.
# 23-Jun-2015 jdw update formatting api call
#  8-Mar-2018 jdw DEPRECATED use mmcif.io.IoAdapterPy
##
"""
Adapter between PDBx IO classes (native Python) and Python persistence classes.

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
# from mmcif.api.PdbxContainers import *


class PdbxPyIoAdapter(object):

    """ Adapter between PDBx IO classes (native Python) and Python persistence classes.
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
        self.__isExpired = True
        #

    def __reIndex(self):
        """ Rebuild name and type lists from container object list.
        """
        #
        self.__containNameList = []
        self.__containTypeList = []
        for container in self.__containerList:
            self.__containerNameList.append(container.getName())
            self.__containerTypeList.append(container.getType())
        #
        self.__isExpired = False

    def setContainerList(self, containerList=None):
        try:
            self.__containerList = containerList
            self.__isExpired = False
            return True
        except Exception as e:
            if (self.__verbose):
                logger.info("+ERROR- PdbxPyIoAdaapter.setContainerList() initialization failed\n")
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
        if (self.__isExpired):
            self.__reIndex()
        return self.__containerNameList

    def read(self, pdbxFilePath):
        """ Import the input Pdbx data file.
        """
        try:
            self.__inputPdbxFilePath = pdbxFilePath
            if (not os.access(pdbxFilePath, os.R_OK)):
                if (self.__verbose):
                    logger.info("+ERROR- PdbxPyIoAdapter.read() Missing file %s\n" % pdbxFilePath)
                return False
            else:
                if (self.__debug):
                    logger.info("+PdbxPyIoAdapter.read() file path %s\n" % pdbxFilePath)

            return self.__readData(pdbxFilePath)

        except Exception as e:
            if (self.__verbose):
                logger.info("+ERROR- PdbxPyIoAdapter.read() Missing file %s\n" % pdbxFilePath)
            return False

    def __readData(self, pdbxFilePath):
        """ Read all data/definition containers in the input PDBxfile.
        """
        # read file contents -
        #
        self.__isExpired = True
        try:
            ifh = open(pdbxFilePath, 'r')
            pRd = PdbxReader(ifh)
            pRd.read(self.__containerList)
            ifh.close()
            return True
        except Exception as e:
            if (self.__verbose):
                logger.info("+ERROR- PdbxPyIoAdapter.__read() Read failed for file %s\n" % pdbxFilePath)
                logger.exception("Failing with %s" % str(e))
            return False

    def write(self, pdbxFilePath, maxLineLength=900, columnAlignFlag=True):
        """ Export the current containerlist to PDBx format file in the path 'pdbxFilePath'.
        """
        try:
            logger.info("Container list length %r" % len(self.__containerList))
            ofh = open(pdbxFilePath, "w")
            pWr = PdbxWriter(ofh)
            pWr.setMaxLineLength(numChars=maxLineLength)
            pWr.setAlignmentFlag(flag=columnAlignFlag)
            pWr.setRowPartition(numParts=5)

            pWr.write(self.__containerList)
            ofh.close()
        except Exception as e:
            if (self.__verbose):
                logger.info("+ERROR- PdbxPyIoAdapter.write() write failed for file %s\n" % pdbxFilePath)
            logger.exception("Failing with %s" % str(e))
            return False

    def writeContainerList(self, pdbxFilePath, containerNameList, maxLineLength=900, columnAlignFlag=True):
        """ Export the input containerlist to PDBx format file in the path 'pdbxFilePath'.
        """
        try:
            ofh = open(pdbxFilePath, "w")
            # pWr=PdbxWriterxy(ofh)

            pWr = PdbxWriter(ofh)
            pWr.setMaxLineLength(numChars=maxLineLength)
            pWr.setAlignmentFlag(flag=columnAlignFlag)
            pWr.setRowPartition(numParts=5)

            for containerName in containerNameList:
                idx = self.__getContainerIndex(containerName)
                if idx is not None:
                    pWr.writeContainer(self.__containerList[idx])
            ofh.close()
        except Exception as e:
            if (self.__verbose):
                logger.info("+ERROR- PdbxPyIoAdapter.write() write failed for file %s\n" % pdbxFilePath)
            logger.exception("Failing with %s" % str(e))
            return False

    def __getContainerIndex(self, name):
        try:
            if (self.__isExpired):
                self.__reIndex()
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

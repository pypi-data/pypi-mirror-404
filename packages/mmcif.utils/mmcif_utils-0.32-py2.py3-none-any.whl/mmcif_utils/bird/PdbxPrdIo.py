##
# File: PdbxPrdIo.py
# Date: 20-Nov-2012  John Westbrook
#
# Update:
#
##
"""
Collected methods for accessing BIRD PRD definitions.

"""
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "john.westbrook@rcsb.org"
__license__ = "Apache 2.0"


import sys
import os
import logging
logger = logging.getLogger(__name__)

from mmcif_utils.style.PdbxStyleIoUtil import PdbxStyleIoUtil
from mmcif_utils.style.PrdCategoryStyle import PrdCategoryStyle


class PdbxPrdIo(PdbxStyleIoUtil):
    ''' Methods for reading BIRD PRD and Family definitions subject to style details.

    '''

    def __init__(self, verbose=True, log=sys.stderr):
        super(PdbxPrdIo, self).__init__(styleObject=PrdCategoryStyle(), verbose=verbose, log=log)

        self.__verbose = verbose
        self.__debug = False
        self.__lfh = log
        #
        # self.__dBlock=None
        #
        self.__topCachePath = None
        self.__prdId = None
        self.__filePath = None

    def makeDefinitionPathList(self):
        """ Return the list of definition file paths in the current repository.

            List is ordered in increasing PRD ID numerical code.
        """
        pathList = []
        sd = {}
        for root, dirs, files in os.walk(self.__topCachePath, topdown=False):
            if "REMOVE" in root:
                continue
            for name in files:
                if name.startswith("PRD_") and name.endswith(".cif") and len(name) <= 14:
                    pth = os.path.join(root, name)
                    sd[int(name[4:-4])] = pth
        #
        for k in sorted(sd.keys()):
            pathList.append(sd[k])
        #
        return pathList

    def makeDefinitionIdList(self):
        """ Return the list of definition identifiers in the current repository.

            List is ordered in increasing PRD ID numerical code.
        """
        idList = []
        sd = {}
        for root, dirs, files in os.walk(self.__topCachePath, topdown=False):
            if "REMOVE" in root:
                continue
            for name in files:
                if name.startswith("PRD_") and name.endswith(".cif") and len(name) <= 14:
                    sd[int(name[4:-4])] = name[4:-4]
        #
        for k in sorted(sd.keys()):
            idList.append(sd[k])
        #
        return idList

    def setCachePath(self, topCachePath='/data/components/prd-v3'):
        self.__topCachePath = topCachePath

    def setPrdId(self, prdId):
        """ Set the identifier for the target definition.   The internal target file path
            is set to the definition file stored in the organization of CVS repository if this exists.

            returns True for success or False otherwise.
        """
        self.__prdId = str(prdId).upper()
        self.__filePath = os.path.join(self.__topCachePath, self.__prdId[-1], self.__prdId + '.cif')
        if self.readFile(self.__filePath):
            return self.setContainer(containerName=self.__prdId)
        else:
            return False

    def setFilePath(self, filePath, prdId=None, appendMode=True):
        """ Specify the file path for the target definition  and optionally provide an identifier
            for the data section within the file.
        """
        self.__filePath = filePath
        self.__prdId = str(prdId).upper()
        if self.readFile(self.__filePath, appendMode=appendMode):
            if self.__prdId is not None:
                return self.setContainer(containerName=self.__prdId)
            else:
                return self.setContainer(containerIndex=0)
        else:
            return False

    def getPrd(self):
        """
            Check for a valid current definition selection.

            Returns True for success or False otherwise.
        """
        return (self.getCurrentContainerId() is not None)

    def getCategory(self, catName='pdbx_reference_entity'):
        return self.getItemDictList(catName)

    def complyStyle(self):
        return self.testStyleComplete(self.__lfh)

    def update(self, catName, attributeName, value, iRow=0):
        #
        return self.updateAttribute(catName, attributeName, value, iRow=iRow)

    def write(self, filePath):
        return self.writeFile(filePath)
        #

    def setBlock(self, blockId):
        return self.setContainer(containerName=blockId)

    def newBlock(self, blockId):
        return self.newContainer(containerName=str(blockId).upper())

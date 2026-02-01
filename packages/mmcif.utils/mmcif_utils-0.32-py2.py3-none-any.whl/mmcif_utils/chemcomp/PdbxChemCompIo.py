##
# File: PdbxChemCompIo.py
# Date: 28-Oct-2012  John Westbrook
#
# Update:
#
# 11-Feb-2013 jdw add missing method getCategory()
# 15-Jun-2016 jdw add method getFilePath()
##
"""
Collected methods for accessing chemical component definitions.

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
from mmcif_utils.style.ChemCompCategoryStyle import ChemCompCategoryStyle


class PdbxChemCompIo(PdbxStyleIoUtil):
    ''' Methods for reading chemical component dictionary definitions including style details.

    '''

    def __init__(self, styleObject=ChemCompCategoryStyle(), verbose=True, log=sys.stderr):
        super(PdbxChemCompIo, self).__init__(styleObject=styleObject, verbose=verbose, log=log)

        self.__verbose = verbose
        self.__debug = False
        self.__lfh = log
        #
        self.__topCachePath = None
        self.__ccU = None
        self.__filePath = None

    def makeComponentPathList(self):
        """ Return the list of chemical component definition file paths in the
            current repository.
        """
        pathList = []
        for root, dirs, files in os.walk(self.__topCachePath, topdown=False):
            if "REMOVE" in root:
                continue
            for name in files:
                if name.endswith(".cif") and len(name) <= 9:
                    pathList.append(os.path.join(root, name))
        return pathList

    def setCachePath(self, topCachePath='/data/components/ligand-dict-v4'):
        self.__topCachePath = topCachePath

    def setCompId(self, compId):
        """ Set the identifier for the target chemical component.   The internal target file path
            is set to the chemmical component definition file stored in the organization of
            CVS repository for chemical components if this exists.

            returns True for success or False otherwise.
        """
        self.__ccU = compId.upper()
        hashd = self.__getCcdHash(self.__ccU)
        self.__filePath = os.path.join(self.__topCachePath, hashd, self.__ccU, self.__ccU + '.cif')
        if self.readFile(self.__filePath):
            return self.setContainer(containerName=self.__ccU)
        else:
            return False

    def getCategory(self, catName='chem_comp'):
        return self.getItemDictList(catName)

    def getChemCompCategory(self, catName='chem_comp'):
        return self.getItemDictList(catName)

    def getChemCompDict(self):
        return self.getItemDictList(catName='chem_comp')

    def getBondList(self):
        return self.getRowDataList(catName='chem_comp_bond')

    def setFilePath(self, filePath, compId=None, appendMode=True):
        """ Specify the file path for the target component and optionally provide an identifier
            for component data section within the file.

            compId: (string) target component Id
            appendMode: (bool) append contents of the file to current container list -

        """
        self.__filePath = filePath
        self.__ccU = compId
        if self.readFile(self.__filePath, appendMode=appendMode):
            if self.__ccU is not None:
                return self.setContainer(containerName=self.__ccU)
            else:
                return self.setContainer(containerIndex=0)
        else:
            return False

    def getFilePath(self):
        return self.__filePath

    def getComp(self):
        """
            Check for a valid current component selection.

            Returns True for success or False otherwise.
        """
        return (self.getCurrentContainerId() is not None)

    def complyStyle(self):
        return self.testStyleComplete(self.__lfh)

    def setBlock(self, blockId):
        return self.setContainer(containerName=blockId)

    def newBlock(self, blockId):
        return self.newContainer(containerName=blockId)

    def update(self, catName, attributeName, value, iRow=0):
        return self.updateAttribute(catName, attributeName, value, iRow=iRow)

    def write(self, filePath):
        return self.writeFile(filePath)

    def __getCcdHash(self, idCode):
        """Returns the hash code for a CCD id.  Currently first letter"""
        if not idCode:
            return None

        if len(idCode) > 3:
            hash_key = idCode.upper()[-2:]
        else:
            hash_key = idCode.upper()[0]

        return hash_key

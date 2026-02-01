##
# File: PdbxChemCompModelIo.py
# Date: 28-Oct-2012  John Westbrook
#
# Update:
#
# 11-Feb-2013 jdw add missing method getCategory()
##
"""
Collected methods for accessing chemical component definitions.

"""
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "john.westbrook@rcsb.org"
__license__ = "Apache 2.0"


import sys

import logging
logger = logging.getLogger(__name__)

from mmcif_utils.style.PdbxStyleIoUtil import PdbxStyleIoUtil
from mmcif_utils.style.ChemCompModelCategoryStyle import ChemCompModelCategoryStyle


class PdbxChemCompModelIo(PdbxStyleIoUtil):
    ''' Methods for reading chemical component model instances including style details.

    '''

    def __init__(self, verbose=True, log=sys.stderr):
        super(PdbxChemCompModelIo, self).__init__(styleObject=ChemCompModelCategoryStyle(), verbose=verbose, log=log)

        self.__verbose = verbose
        self.__debug = False
        self.__lfh = log
        #
        self.__idCode = None
        self.__filePath = None

    def getCategory(self, catName='pdbx_chem_comp_model'):
        return self.getAttribDictList(catName)

    def getChemCompModelCategory(self, catName='pdbx_chem_comp_model'):
        return self.getAttribDictList(catName)

    def getChemCompModelDict(self):
        return self.getItemDictList(catName='pdbx_chem_comp_model')

    def getAtomList(self):
        return self.getAttibDictList(catName='pdbx_chem_comp_model_atom')

    def getBondList(self):
        return self.getAttribDictList(catName='pdbx_chem_comp_model_bond')

    def getDescriptorList(self):
        return self.getAttribDictList(catName='pdbx_chem_comp_model_descriptor')

    def getFeatureList(self):
        return self.getAttribDictList(catName='pdbx_chem_comp_model_feature')

    def getReferenceList(self):
        return self.getAttribDictList(catName='pdbx_chem_comp_model_reference')

    def setFilePath(self, filePath, idCode=None):
        """ Specify the file path for the target component and optionally provide an identifier
            for component data section within the file.
        """
        self.__filePath = filePath
        self.__idCode = idCode
        if self.readFile(self.__filePath):
            if self.__idCode is not None:
                return self.setContainer(containerName=self.__idCode)
            else:
                return self.setContainer(containerIndex=0)
        else:
            return False

    def getModel(self):
        """
            Check for a valid current component model selection.

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

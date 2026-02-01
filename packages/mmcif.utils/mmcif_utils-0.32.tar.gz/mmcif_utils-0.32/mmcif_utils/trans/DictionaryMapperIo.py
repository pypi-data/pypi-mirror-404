##
# File: DictionaryMapperIo.py
# Date: 11-Jun-2015  John Westbrook
#
# Update:
##
"""
Manage IO operations for category/item-level mapping data files.

"""
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "john.westbrook@rcsb.org"
__license__ = "Apache 2.0"


import sys


from mmcif_utils.style.PdbxStyleIoUtil import PdbxStyleIoUtil
from mmcif_utils.style.PdbxItemMappingCategoryStyle import PdbxItemMappingCategoryStyle
from mmcif.io.IoAdapterPy import IoAdapterPy as IoAdapter


class DictionaryMapperIo(PdbxStyleIoUtil):

    ''' Methods for accessing category and item-level mapping information --- .

    '''

    def __init__(self, verbose=True, log=sys.stderr):
        super(DictionaryMapperIo, self).__init__(styleObject=PdbxItemMappingCategoryStyle(), IoAdapter=IoAdapter(), verbose=verbose, log=log)

        self.__verbose = verbose
        self.__debug = False
        self.__lfh = log
        #
        self.__mappingFilePath = None

    def getCategory(self, catName='pdbx_dict_item_mapping'):
        return self.getAttribDictList(catName)

    def setMapFilePath(self, filePath):
        """ Specify the mapping file path.
        """
        self.__mappingFilePath = filePath
        if self.readFile(self.__mappingFilePath):
            return self.setContainer(containerIndex=0)
        else:
            return False

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



##
# File: PdbxMessageIo.py
# Date: 7-Aug-2013  John Westbrook
#
# Update:
#  7-Aug-2013  jdw add 'pdbx_deposition_message_file_reference'
#  16-Aug-2013 rps Updated to accommodate new 'pdbx_deposition_message_status'
#  30-Oct-2013 rps tweak to reflect support for UI feature for classifying messages (e.g. "action required" or "unread")
#  9-Sep-2014  rps add 'pdbx_deposition_message_origcomm_reference'
#  28-Jul-2016 rps read() method updated to accept optional "logtag" parameter
##
"""
Collected methods for accessing message data i/o.

"""
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "john.westbrook@rcsb.org"
__license__ = "Apache 2.0"


import sys

from mmcif_utils.style.PdbxStyleIoUtil import PdbxStyleIoUtil
from mmcif_utils.style.PdbxMessageCategoryStyle import PdbxMessageCategoryStyle


class PdbxMessageIo(PdbxStyleIoUtil):
    ''' Methods for reading chemical component dictionary definitions including style details.

    '''

    def __init__(self, verbose=True, log=sys.stderr):
        super(PdbxMessageIo, self).__init__(styleObject=PdbxMessageCategoryStyle(), verbose=verbose, log=log)

        self.__verbose = verbose
        self.__debug = False
        self.__lfh = log
        self.__filePath = None

    def getCategory(self, catName='pdbx_deposition_message_info'):
        return self.getItemDictList(catName)

    def getMessageInfo(self):
        return self.getAttribDictList(catName='pdbx_deposition_message_info')

    def getFileReferenceInfo(self):
        return self.getAttribDictList(catName='pdbx_deposition_message_file_reference')

    def getOrigCommReferenceInfo(self):
        return self.getAttribDictList(catName='pdbx_deposition_message_origcomm_reference')

    def getMsgStatusInfo(self):
        return self.getAttribDictList(catName='pdbx_deposition_message_status')

    def read(self, filePath, logtag=""):
        """ Specify the file path for the target message data.
        """
        self.__filePath = filePath
        if self.readFile(self.__filePath, logtag=logtag):
            return self.setContainer(containerIndex=0)
        else:
            return False

    def complyStyle(self):
        return self.testStyleComplete(self.__lfh)

    def setBlock(self, blockId):
        return self.setContainer(containerName=blockId)

    def newBlock(self, blockId):
        self.newContainer(containerName=blockId, overWrite=False)
        self.setContainer(containerName=blockId)
        #
        self.newCategory('pdbx_deposition_message_info', container=self.getCurrentContainer())
        self.newCategory('pdbx_deposition_message_file_reference', container=self.getCurrentContainer())
        self.newCategory('pdbx_deposition_message_origcomm_reference', container=self.getCurrentContainer())
        self.newCategory('pdbx_deposition_message_status', container=self.getCurrentContainer())

    def update(self, catName, attributeName, value, iRow=0):
        return self.updateAttribute(catName, attributeName, value, iRow=iRow)

    def appendMessage(self, rowAttribDict):
        return self.appendRowByAttribute(rowAttribDict, catName='pdbx_deposition_message_info')

    def appendFileReference(self, rowAttribDict):
        return self.appendRowByAttribute(rowAttribDict, catName='pdbx_deposition_message_file_reference')

    def appendOrigCommReference(self, rowAttribDict):
        return self.appendRowByAttribute(rowAttribDict, catName='pdbx_deposition_message_origcomm_reference')

    def appendMsgReadStatus(self, rowAttribDict):
        return self.appendRowByAttribute(rowAttribDict, catName='pdbx_deposition_message_status')

    def write(self, filePath):
        return self.writeFile(filePath)

    def nextMessageOrdinal(self):
        nRows = int(self.getRowCount(catName='pdbx_deposition_message_info'))
        return nRows + 1

    def nextFileReferenceOrdinal(self):
        nRows = int(self.getRowCount(catName='pdbx_deposition_message_file_reference'))
        return nRows + 1

    def nextOrigCommReferenceOrdinal(self):
        nRows = int(self.getRowCount(catName='pdbx_deposition_message_origcomm_reference'))
        return nRows + 1

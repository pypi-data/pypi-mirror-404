##
# File: PdbxStyleIoUtil.py
# Date: 4-Nov-2012  John Westbrook
#
# Update:
#  4-Nov-2012  jdw  generalize references to style details through
#                   an input object of class PdbxCategoryStyleBase().
#  8-Nov-2012  jdw  add write/update methods to this base class.
#                   normalize naming or data containers.
# 14-Nov-2012  jdw  Refactor and add diagnostic coverage methods.
#
# 20-Jan-2013  jdw  New method for adding new category -
# 31-Dec-2013  jdw  Use core IO adapter as default -
# 11-Jun-2015  jdw  add some exception handling in getAttribDictList()
# 20-Jul-2015  jdw  add method removeCategory()
#  6-Jun-2016  jdw  use native python IO on Darwin
# 28-Jul-2016 rps readFile(), __appendFile() methods updated to accept optional "logtag" parameter
#  5-Mar-2018  jdw Py2-Py3 and refactor for Python Packaging
#  7-Mar-2018  jdw Make the last container on the list the current container
#
##
"""
IO utility methods for accessing PDBx category data integrated with presentation
and style details.

Either the Python or C++ IoAdapter can be selected in this module.

"""
from __future__ import absolute_import
from six.moves import range
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "john.westbrook@rcsb.org"
__license__ = "Apache 2.0"


import os
import sys
import tarfile
import inspect

import logging
logger = logging.getLogger(__name__)

from mmcif.api.PdbxContainers import DataContainer, CifName
from mmcif.api.DataCategory import DataCategory

try:
    from mmcif.io.IoAdapterCore import IoAdapterCore as IoAdapter
except:
    from mmcif.io.IoAdapterPy import IoAdapterPy as IoAdapter


def tarinfoReset(tarinfo):
    tarinfo.mode = 0o644
    tarinfo.uname = tarinfo.gname = 'nobody'
    return tarinfo


class PdbxStyleIoUtil(object):

    ''' Utility methods for reading and writing PDBx data incorporating
        external presentation style defintions.

    '''

    def __init__(self, styleObject=None, IoAdapter=IoAdapter(), verbose=True, log=sys.stderr):

        self.__stObj = styleObject
        self.__verbose = verbose
        self.__debug = False
        self.__lfh = log

        self.__ioObj = IoAdapter

        # target input and output files -
        #
        self.__inputFilePath = None
        self.__outputFilePath = None
        #
        # current container, identifier, container list and index.
        #
        self.__reset()

    def __reset(self):
        self.__currentContainer = None
        self.__currentContainerId = None
        self.__currentContainerList = []
        self.__currentContainerIndex = {}

    def readFile(self, filePath, logtag="", appendMode=True):
        """ Read the target input file path and append (default) the contents of this file to the
            current container list.
        """
        try:
            self.__inputFilePath = filePath
            if (not os.access(self.__inputFilePath, os.R_OK)):
                if (self.__verbose):
                    logger.error("+ERROR - PdbxStyleIoUtil.readFile() Missing input file %s\n" % filePath)
                return False
            else:
                logger.debug("+INFO - PdbxStyleIoUtil.readFile() file path %s\n" % (self.__inputFilePath))
            if not appendMode:
                self.__reset()

            return self.__appendFile(self.__inputFilePath, logtag=logtag)

        except Exception as e:
            if (self.__verbose):
                logger.error("+ERROR - PdbxStyleIoUtil.readFile() read failed for file %s\n" % filePath)
                logger.exception("Failing with %s" % str(e))
            return False

    def setContainer(self, containerName=None, containerIndex=None):
        """ Set the current container to the input name or index.

            Returns True for success or False otherwise.
        """
        try:
            self.__currentContainer = self.__getContainer(containerName=containerName, containerIndex=containerIndex)
            if self.__currentContainer is not None:
                return True
            else:
                return False
        except Exception as e:
            if (self.__verbose):
                logger.exception("Failing with %s" % str(e))
            return False

    def getCurrentContainerId(self):
        """  Return the name of current container.
        """
        try:
            return self.__currentContainer.getName()
        except Exception as e:
            return None

    def getCurrentContainer(self):
        """  Return the current data container.
        """
        try:
            return self.__currentContainer
        except Exception as e:
            return None

    def getCurrentContainerList(self):
        """  Return the current data container list.
        """
        try:
            return self.__currentContainerList
        except Exception as e:
            return []

    def getCurrentCategoryNameList(self):
        """  Return the list of data category names in the  current container or an empty list.
        """
        try:
            return self.__currentContainer.getObjNameList()
        except Exception as e:
            return []

    def getContainerNameList(self):
        return [container.getName() for container in self.__currentContainerList]

    def __appendFile(self, filePath, logtag=""):
        """ Internal method to read/append data in the input file and append the contents to the current container list.

            On failure None is returned.
        """
        try:
            # if 'logtag' in inspect.getargspec(self.__ioObj.readFile).args:
            #if logtag and len(logtag) > 0:
            #    self.__currentContainerList.extend(self.__ioObj.readFile(filePath, logtag=logtag))
            #else:
            self.__currentContainerList.extend(self.__ioObj.readFile(filePath))
            self.__makeContainerIndex()
            for container in self.__currentContainerList:
                self.__updateContainer(container)
            # JDW Make the last container on the list the default current container -
            if self.__currentContainerList and len(self.__currentContainerList) > 0:
                self.__currentContainer = self.__currentContainerList[-1]
            #
            return True
        except Exception as e:
            if (self.__verbose):
                logger.exception("Failing with %s" % str(e))
            return False

    #
    def __makeContainerIndex(self):
        """ Internal method to create/update index (name to position) of the current data container list.
        """
        self.__currentContainerIndex = {}
        try:
            for ii, container in enumerate(self.__currentContainerList):
                self.__currentContainerIndex[container.getName()] = ii
            return True
        except Exception as e:
            return False

    def __getContainerIndex(self, containerName):
        try:
            return self.__currentContainerIndex[containerName]
        except Exception as e:
            return -1

    def __getContainer(self, containerName=None, containerIndex=None):
        """ Internal method to return a data container from the current container list
            either by name or by index [0 - N-1].

        """
        try:
            if containerName is not None and containerIndex is None:
                return self.__currentContainerList[self.__currentContainerIndex[containerName]]
            elif containerIndex is not None and containerName is None:
                return self.__currentContainerList[containerIndex]
            else:
                return None
        except Exception as e:
            return None
    #

    def newContainer(self, containerName, overWrite=False):
        """  Create an new data container and append this to the current container list.

             Initialize the data container with the category objects defined in the current
             style object.

             It the containerName exists then no action is taken.

             Returns True for success or False otherwise.
        """
        try:
            if self.__getContainerIndex(containerName=containerName) != -1:
                if not overWrite:
                    return True
                else:
                    del self.__currentContainerList[self.__currentContainerIndex[containerName]]

            self.__currentContainerList.append(self.__initContainer(containerName))
            self.__makeContainerIndex()
            return self.setContainer(containerName=containerName)
        except Exception as e:
            if (self.__verbose):
                logger.exception("Failing with %s" % str(e))
            return False

    def __initContainer(self, containerName):
        """ Return a new container initialized with category defintions from the current style object.
        """
        newContainer = DataContainer(containerName)
        #
        for category in self.__stObj.getCategoryList():
            newCat = DataCategory(category)
            for itemName in self.__stObj.getItemNameList(category):
                name = CifName.attributePart(itemName)
                newCat.appendAttribute(name)
            newContainer.append(newCat)
        return newContainer

    def __updateContainer(self, container):
        if container.getType() != 'data':
            return
        for catName in container.getObjNameList():
            catObj = container.getObj(catName)
            self.__updateCategory(catObj)

    def __updateCategory(self, catObj):
        atList = catObj.getAttributeList()
        for itemName in self.__stObj.getItemNameList(catObj.getName()):
            atName = CifName.attributePart(itemName)
            if atName not in atList:
                catObj.appendAttributeExtendRows(atName)

    def newCategory(self, catName, container=None, overWrite=False):
        """ Add a new category to the input container using category defintions from the current style object.
        """
        #
        try:
            if container is not None:
                if container.exists(catName):
                    if overWrite:
                        container.remove(catName)
                    else:
                        return True
            else:
                if self.__currentContainer.exists(catName):
                    if overWrite:
                        self.__currentContainer.remove(catName)
                    else:
                        return True
        except Exception as e:
            logger.error("+ERROR - PdbxStyleIoUtil.newCategory() for category %s\n" % catName)
            if (self.__verbose):
                logger.exception("Failing with %s" % str(e))
            return False

        if catName in self.__stObj.getCategoryList():
            newCat = DataCategory(catName)
            for itemName in self.__stObj.getItemNameList(catName):
                name = CifName.attributePart(itemName)
                newCat.appendAttribute(name)
            if container is not None:
                container.append(newCat)
                return True
            else:
                self.__currentContainer.append(newCat)
                return True
        return False

    def removeCategory(self, catName, container=None):
        """ Remove the category (catName) from input container or current container.
        """
        #
        try:
            if container is not None:
                if container.exists(catName):
                    container.remove(catName)
            else:
                if self.__currentContainer.exists(catName):
                    self.__currentContainer.remove(catName)

            return True
        except Exception as e:
            logger.error("+ERROR - PdbxStyleIoUtil.removeCategory() failed for category %s\n" % catName)
            if (self.__verbose):
                logger.exception("Failing with %s" % str(e))
        return False

    def updateAttribute(self, catName, attribName, value, iRow=0):
        """ Update the value of the input category/attribute in the input row.

            Return True for success or False otherwise
        """
        try:
            myCat = self.__currentContainer.getObj(catName)
            myCat.setValue(value, attribName, iRow)
            return True
        except Exception as e:
            if (self.__verbose):
                logger.error("+ERROR - PdbxStyleIoUtil.updateAttribute() failed for category %s attribute %s value %s\n"
                             % (catName, attribName, value))
                logger.exception("Failing with %s" % str(e))
            return False

    def getAttributeValue(self, catName, attribName, iRow=0):
        """ Get the value of the input category/attribute in the input row.

            Return the value or None
        """
        try:
            myCat = self.__currentContainer.getObj(catName)
            val = myCat.getValueOrDefault(attributeName=attribName, rowIndex=iRow, defaultValue=None)
            return val
        except Exception as e:
            if (self.__verbose):
                logger.error("+ERROR - PdbxStyleIoUtil.getAttributeValue() failed for category %s attribute %s\n"
                             % (catName, attribName))
                logger.exception("Failing with %s" % str(e))
        return None

    def updateRowByAttribute(self, rowAttribDict, catName, iRow=0):
        """ Update category/row using values in the input attribute dictionary.
        """
        try:
            myCat = self.__currentContainer.getObj(catName)
            for attribName, value in rowAttribDict.items():
                myCat.setValue(value, attribName, iRow)
            return True
        except Exception as e:
            if (self.__verbose):
                logger.error("+ERROR - PdbxStyleIoUtil._updateRowByAttribute() failed for category %s attribute %s value %s\n"
                             % (catName, attribName, value))
                logger.exception("Failing with %s" % str(e))
            return False

    def getRowCount(self, catName):
        """ Return the count for the input category or -1.
        """
        try:
            myCat = self.__currentContainer.getObj(catName)
            return myCat.getRowCount()
        except Exception as e:
            if self.__debug:
                logger.error("+ERROR - PdbxStyleIoUtil.getRowCount() for category %s failed\n" % catName)
                logger.exception("Failing with %s" % str(e))
            return -1

    def appendRowByAttribute(self, rowAttribDict, catName):
        """ Append to category using values in the input attribute dictionary.
        """
        try:
            myCat = self.__currentContainer.getObj(catName)
            iRow = myCat.getRowCount()
            for attribName, value in rowAttribDict.items():
                myCat.setValue(value, attribName, iRow)
            return True
        except Exception as e:
            if (self.__verbose):
                logger.error("+ERROR - PdbxStyleIoUtil.appendRowByAttribute() failed for category %s\n" % catName)
                logger.exception("Failing with %s" % str(e))
            return False

    def updateItem(self, itemName, value, iRow=0):
        """ Update the value of the input category/item in the input row.

            Return True for success or False otherwise
        """
        try:
            catName = CifName.categoryPart(itemName)
            attribName = CifName.attributePart(itemName)
            #
            myCat = self.__currentContainer.getObj(catName)
            myCat.setValue(value, attribName, iRow)
            return True

        except Exception as e:
            if (self.__verbose):
                logger.error("+ERROR - PdbxStyleIoUtil._updateItem failed for category %s item %s value %s\n"
                             % (catName, itemName, value))
                logger.exception("Failing with %s" % str(e))
            return False

    #
    def writeFile(self, filePath, applyConstraints=False, tmpPath="./tmpfiles", doubleQuotingFlag=False):
        """  Write the current container list to the specified outputfile.
        """
        self.__outputFilePath = filePath
        if applyConstraints:
            self.__applyOutputConstraints()

        if filePath.endswith(".tar.gz"):
            return self.__writeTarGzFile(self.__outputFilePath, tmpPath=tmpPath, doubleQuotingFlag=doubleQuotingFlag)
        else:
            return self.__write(self.__outputFilePath, doubleQuotingFlag=doubleQuotingFlag)

    def __write(self, filePath, doubleQuotingFlag=False):
        """  Internal method to write the current container list to the specified outputfile -

             Returns True for success or False otherwise.
        """
        try:
            self.__ioObj.writeFile(filePath, self.__currentContainerList, doubleQuotingFlag=doubleQuotingFlag)
        except Exception as e:
            if self.__verbose:
                logger.exception("Failing with %s" % str(e))
            return False

        return True

    def __writeTarGzFile(self, tarGzFilePath, tmpPath="./tmpfiles", doubleQuotingFlag=False):
        """  Internal method to write the current container list to a split gzipped tar file.

             Returns True for success or False otherwise.
        """
        try:
            if not tarGzFilePath.endswith(".tar.gz"):
                return False

            if not os.access(tmpPath, os.W_OK):
                os.mkdir(tmpPath)

            archive = tarfile.open(tarGzFilePath, "w|gz")

            for container in self.__currentContainerList:
                id = container.getName()
                filePath = os.path.join(tmpPath, id + ".cif")
                self.__ioObj.writeFile(filePath, [container], doubleQuotingFlag=doubleQuotingFlag)
                archive.add(filePath, arcname=id + ".cif", filter=tarinfoReset)
                os.remove(filePath)
            archive.close()

        except Exception as e:
            if self.__verbose:
                logger.exception("Failing with %s" % str(e))
            return False

        return True

    #
    def getItemDictList(self, catName):
        """Return a list of dictionaries of the input category where the dictionaries
           represent the row with full item names as dictionary keys.
        """
        #
        #itTupList= PdbxChemCompCategoryDefinition._cDict[catName]
        #
        # List of item names in style order -
        #
        itStList = self.__stObj.getItemNameList(catName)

        #
        # Get category object - from current data container
        dList = []
        try:
            catObj = self.__currentContainer.getObj(catName)
            nRows = catObj.getRowCount()
        except Exception as e:
            return dList
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
        for ii, itSt in enumerate(itStList):
            if itSt in itDict:
                colDict[itSt] = itDict[itSt]
        #
        rowList = catObj.getRowList()

        for row in rowList:
            tD = {}
            for k, v in colDict.items():
                tD[k] = row[v]
            dList.append(tD)

        return dList

    def getAttribDictList(self, catName):
        """Return the input category as a list of dictionaries where the dictionaries
           represent the row with attribute names as dictionary keys.
        """
        #
        dList = []
        #
        #itTupList= PdbxChemCompCategoryDefinition._cDict[catName]
        #
        # List of item names in style order -
        itStList = self.__stObj.getItemNameList(catName)

        # Get category object - from current data container
        #
        catObj = self.__currentContainer.getObj(catName)
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
        for ii, itSt in enumerate(itStList):
            if itSt in itDict:
                attrib = CifName.attributePart(itSt)
                colDict[attrib] = itDict[itSt]
        #
        try:
            rowList = catObj.getRowList()
            for row in rowList:
                tD = {}
                for k, v in colDict.items():
                    tD[k] = row[v]
                dList.append(tD)
        except Exception as e:
            if (self.__verbose):
                logger.error("+ERROR - PdbxStyleIoUtil.getAttribDictList() fails at row %r\n" % row)
                logger.exception("Failing with %s" % str(e))

        return dList

    def getRowDataList(self, catName):
        """Return  a list of data from the input category including
           data types and default value replacement.

           For list representing each row is column ordered according to the internal
           style data structure.

        """
        dataList = []
        #itTupList= PdbxChemCompCategoryDefinition._cDict[catName]
        itTupList = self.__stObj.getItemNameTypeAndDefaultList(catName)

        catObj = self.__currentContainer.getObj(catName)
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
        for ii, (itName, itType, itDefault) in enumerate(itTupList):
            if itName in itDict:
                colTupList.append((itDict[itName], itType, itDefault))
            else:
                colTupList.append((-1, itType, itDefault))
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

    def testStyleComplete(self, ofh):
        """ Diagnostic coverage test of current data content with the style definition.

            Reports categories and items that are not represented in the style definition.
        """
        ok = True
        for dataContainer in self.__currentContainerList:

            catDif = self.__compareCategoryContent(dataContainer)
            if len(catDif) > 0:
                ok = False
                ofh.write("+WARN - PdbxStyleIoUtil._testStyleCompleteness container %s extra category objects %r\n"
                          % (dataContainer.getName(), catDif))
            #
            for catName in dataContainer.getObjNameList():
                itemExtra = self.__extraItemContent(dataContainer, catName)
                if (len(itemExtra) > 0):
                    ok = False
                    ofh.write("+WARN - PdbxStyleIoUtil._testStyleCompleteness EXTRA items in container %s category %s attribute(s) %r\n"
                              % (dataContainer.getName(), catName, [CifName.attributePart(it) for it in itemExtra]))

                itemMissing = self.__missingItemContent(dataContainer, catName)
                if (len(itemMissing) > 0):
                    ok = False
                    ofh.write("+WARN - PdbxStyleIoUtil._testStyleCompleteness MISSING items in container %s category %s attribute(s) %r\n"
                              % (dataContainer.getName(), catName, [CifName.attributePart(it) for it in itemMissing]))

        return ok

    def getStyleCategoryNameList(self):
        return self.__stObj.getCategoryList()

    def __compareCategoryContent(self, dataContainer):
        """  Internal method to compare current category content with the category content of the style definition.

        """
        try:
            categoryNameList = dataContainer.getObjNameList()
            categoryNameListSt = self.__stObj.getCategoryList()
            #
            catDifSet = set(categoryNameList) - set(categoryNameListSt)
            return catDifSet
        except Exception as e:
            if (self.__verbose):
                logger.error("+ERROR - PdbxStyleIoUtil._compareCategoryContent failed for container%s\n"
                             % (dataContainer.getName()))
            return set([])

    def __extraItemContent(self, dataContainer, categoryName):
        """  Internal method to compare the item content of the input category with that of the style definition.
        """
        try:
            containerName = dataContainer.getName()
            catObj = dataContainer.getObj(categoryName)
            itemNameList = catObj.getItemNameList()
            itemNameListSt = self.__stObj.getItemNameList(categoryName)
            itemDifSet = set(itemNameList) - set(itemNameListSt)
            return itemDifSet
        except Exception as e:
            if (self.__verbose):
                logger.error("+ERROR - PdbxStyleIoUtil._compareItemContent failed for %s category %s\n"
                             % (containerName, categoryName))
            return set([])

    def __missingItemContent(self, dataContainer, categoryName):
        """  Internal method to compare the item content of the input category with that of the style definition.
        """
        try:
            containerName = dataContainer.getName()
            catObj = dataContainer.getObj(categoryName)
            itemNameList = catObj.getItemNameList()
            itemNameListSt = self.__stObj.getItemNameList(categoryName)
            itemDifSet = set(itemNameListSt) - set(itemNameList)
            return itemDifSet
        except Exception as e:
            if (self.__verbose):
                logger.error("+ERROR - PdbxStyleIoUtil._compareItemContent failed for %s category %s\n"
                             % (containerName, categoryName))
            return set([])

    def __applyOutputConstraints(self):
        """ Apply exclusion/suppression contraints to the current container list.

        """
        for dataContainer in self.__currentContainerList:
            for catName in dataContainer.getObjNameList():
                if len(self.__stObj.getExcludedList(catName)) > 0:
                    cObj = dataContainer.getObj(catName)
                    for at in self.__stObj.getExcludedList(catName):
                        logger.debug("+INFO- PdbxStyleIoUtil.__applyOutputConstraints exclude category %s attribute %s\n"
                                     % (catName, at))
                        try:
                            cObj.removeAttribute(at)
                        except Exception as e:
                            pass

                if len(self.__stObj.getSuppressList(catName)) > 0:
                    cObj = dataContainer.getObj(catName)
                    for at in self.__stObj.getSuppressList(catName):
                        for idx in range(0, cObj.getRowCount()):
                            logger.debug("+INFO- PdbxStyleIoUtil.__applyOutputConstraints suppress category %s attribute %s\n"
                                         % (catName, at))
                            try:
                                cObj.setValue('?', at, idx)
                            except Exception as e:
                                pass

    def _isEmptyValue(self, val):
        if ((val is None) or (len(val) == 0) or (val in ['.', '?'])):
            return True
        else:
            return False

    def _firstOrDefault(self, valList, default=''):
        if len(valList) > 0 and not self._isEmptyValue(valList[0]):
            return valList[0]
        else:
            return default

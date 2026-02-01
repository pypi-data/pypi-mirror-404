##
# File:  InstanceMapper.py
# Date:  23-Jun-2015
#
# Updates:
#   20-July-2015  jdw add audit processing --
##
"""
Methods for instance mapping applying category and item-level mapping .

"""
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "john.westbrook@rcsb.org"
__license__ = "Apache 2.0"


import sys
import time
import logging
logger = logging.getLogger(__name__)


try:
    from mmcif.io.IoAdapterCore import IoAdapterCore as IoAdapter
except:
    from mmcif.io.IoAdapterPy import IoAdapterPy as IoAdapter
#
from mmcif.api.PdbxContainers import CifName
from mmcif.api.PdbxContainers import DataContainer
from mmcif.api.DataCategory import DataCategory
from mmcif_utils.trans.DictionaryMapperIo import DictionaryMapperIo
from mmcif_utils.trans.DictionaryMapper import DictionaryMapper
from mmcif_utils.trans.FilterCif import FilterCif


class InstanceMapper(object):

    """  Instance mapping and file translation tools -
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
        self.__mappingFilePath = None
        self.__dm = None
        self.__dstIndex = {}
        self.__auditD = {}
        self.__fC = None

    def setMappingFilePath(self, mappingFilePath):
        """  Assign mapping info file path ...
        """
        self.__mappingFilePath = mappingFilePath
        self.__dm = self.__readMappingInfo(mappingFilePath)

    def translate(self, inpFilePath, outFilePath, mode="src-dst"):
        """  Translate content of inpFilePath to outFilePath subject to current mapping information.
             Categories with no mapping details are transfered without attenuation.

              mode = sense of mapping relative to mapping info declarations

             Audit records are added or removed according to directives included in the mapping information file.

        """
        #
        logger.debug("+InstanceMapper.trans() inpFilePath % s outFilePath % s" % (inpFilePath, outFilePath))
        self.__dstIndex = {}
        try:

            #
            #  Handle setting up the pre and post filtering options
            #
            if mode == "src-dst":
                preFilter = "pre_src_to_dst"
                postFilter = "post_src_to_dst"
            elif mode == "dst-src":
                preFilter = "pre_dst_to_src"
                postFilter = "post_dst_to_src"

            inpContainerList = self.__io.readFile(inpFilePath)
            inpContainer = inpContainerList[0]
            inpContainerName = inpContainer.getName()
            preFilterContainer = DataContainer(inpContainerName)
            inpObjNameList = inpContainer.getObjNameList()
            #
            #       Audit tests applied first --
            #
            auditCatObj = None
            if inpContainer.exists("pdbx_audit_conform_extension"):
                auditCatObj = inpContainer.getObj("pdbx_audit_conform_extension")
            status, auditCatObj = self.__applyAuditRules(auditCatObj, mode)
            #
            if status == 'skip':
                #
                #   Pass content unchanged to output file ----
                #
                return self.__io.writeFile(outFilePath, inpContainerList)
            elif status == 'update':
                # status == 'update' -- insert the revised auditCategory object is it exists
                #                       and remove this category from the list of category names for
                #                       further processing -
                if auditCatObj is not None:
                    preFilterContainer.append(auditCatObj)
                try:
                    inpObjNameList.remove("pdbx_audit_conform_extension")
                except Exception as e:
                    pass
            else:
                # status ignore --
                pass

            self.__fC.filter(inpContainer, preFilterContainer, preFilter)

            outContainer = DataContainer(inpContainerName)
            inpContainer = preFilterContainer
            inpObjNameList = inpContainer.getObjNameList()

            #
            #
            #  Copy all the data categories for now -
            #
            if mode == "src-dst":
                mapCatNameList = self.__dm.getSrcCategoryList()
            elif mode == "dst-src":
                mapCatNameList = self.__dm.getDstCategoryList()
            else:
                mapCatNameList = []

            # Apply mapping
            logger.debug("+InstanceMapper.trans() mapCatNameList %r" % mapCatNameList)
            for inpObjName in inpObjNameList:
                catObj = inpContainer.getObj(inpObjName)
                if inpObjName in mapCatNameList:
                    self.__mapCategory(catObj, outContainer, mode=mode)
                    # As mapped do not copy to output
                    continue

                # Copy unmapped categories
                outContainer.append(catObj)

            #
            # Parent correction - must be done after outContainer fully populated
            # with all categories to copy data from
            #
            outObjNameList = outContainer.getObjNameList()
            for outObjName in outObjNameList:
                catObj = outContainer.getObj(outObjName)
                if mode == 'src-dst':
                    parentD = self.__dm.getDstMappedParentItems(dstCatName=outObjName)
                elif mode == 'dst-src':
                    parentD = self.__dm.getSrcMappedParentItems(srcCatName=outObjName)
                else:
                    parentD = {}
                    
                if len(parentD) > 0:
                    self.__mapParentItems(catObj, outContainer, parentD)
            
            #
            # Post filtering
            #
            postFilterContainer = DataContainer(inpContainerName)
            self.__fC.filter(outContainer, postFilterContainer, postFilter)

            #
            # Apply self mapping on the destination -
            #
            outContainerList = []

            outContainerList.append(postFilterContainer)

            return self.__io.writeFile(outFilePath, outContainerList)

        except Exception as e:
            if (self.__verbose):
                logger.debug("+InstanceMapper.trans() failed input file %s output file %s" % (inpFilePath, outFilePath))
                logger.exception("Failing with %s" % str(e))
        return False

    def __mapParentItems(self, catObj, outContainer, parentD):
        """  Apply parent mappings from the current container -
        """
        for curItem, parentItem in parentD.items():
            pCategoryName = CifName.categoryPart(parentItem)
            pAttributeName = CifName.attributePart(parentItem)
            if outContainer.exists(pCategoryName):
                cObj = outContainer.getObj(pCategoryName)
                value = cObj.getValueOrDefault(pAttributeName, rowIndex=0, defaultValue=None)
            else:
                value = None
            if value is not None:
                attributeName = CifName.attributePart(curItem)
                for iRow in range(0, catObj.getRowCount()):
                    catObj.setValue(value, attributeName=attributeName, rowIndex=iRow)

    def __getKeyValues(self, rD, keyItemL):
        tL = []
        ok = True
        for keyItem in keyItemL:
            if keyItem in rD:
                tL.append(rD[keyItem])
            else:
                tL.append(None)
                ok = False
        #
        return ok, tuple(tL)

    def __updateSchema(self, catObj, itemNameList):
        """  Add any missing attributes to the input category object ...
        """
        curNameList = catObj.getItemNameList()
        for itemName in itemNameList:
            if itemName not in curNameList:
                attributeName = CifName.attributePart(itemName)
                catObj.appendAttributeExtendRows(attributeName)

    def __appendRow(self, catObj, srcRowD, mapItemD):
        """  Append new row with mapped data  -

             Return row index appended --
        """
        try:
            idxD = {}
            for ii, item in enumerate(catObj.getItemNameList()):
                idxD[item] = ii
            #
            row = ['?' for ii in range(0, len(idxD))]
            for srcItem, value in srcRowD.items():
                if srcItem in mapItemD:
                    dstItem = mapItemD[srcItem]
                    row[idxD[dstItem]] = value
            catObj.append(row)
            #
            return catObj.getRowCount() - 1
        except Exception as e:
            if (self.__debug):
                for k, v in idxD.items():
                    logger.debug("idxD %r %r" % (k, v))
                for k, v in srcRowD.items():
                    logger.debug("srcRowD %r %r" % (k, v))
                for k, v in mapItemD.items():
                    logger.debug("mapItemD %r %r" % (k, v))
                logger.exception("Failing with %s" % str(e))

    def __updateRow(self, catObj, srcRowD, mapItemD, rowIndex):
        """  Update row with mapped data -
        """
        for srcItem, value in srcRowD.items():
            if srcItem in mapItemD:
                dstAttr = CifName.attributePart(mapItemD[srcItem])
                catObj.setValue(value, dstAttr, rowIndex)

    def __mapCategory(self, srcCatObj, outContainer, mode="src-dst"):
        """  Transfer data in the source category object to the mapped categories in the output container.

             mode = the sense of the transfer -
        """
        if srcCatObj.getRowCount() < 1:
            return
        srcCatName = srcCatObj.getName()
        if mode == "src-dst":
            dstCatNameL = self.__dm.getMappedCategoryListForSrc(srcCatName=srcCatName)
            for dstCatName in dstCatNameL:
                #
                keyItemL = self.__dm.getSrcCategoryKeyItemList(srcCatName=srcCatName, dstCatName=dstCatName)
                mapItemD = self.__dm.getMappedItemsForSrc(srcCatName=srcCatName, dstCatName=dstCatName)
                dstItemL = self.__dm.getDstCategoryItemList(dstCatName=dstCatName)
                #
                if not outContainer.exists(dstCatName):
                    aCat = DataCategory(dstCatName)
                    for dstItem in dstItemL:
                        dstAttr = CifName.attributePart(dstItem)
                        aCat.appendAttribute(dstAttr)
                    outContainer.append(aCat)
                    self.__dstIndex[dstCatName] = {}
                    dstCatObj = outContainer.getObj(dstCatName)
                else:
                    self.__dstIndex[dstCatName] = {}
                    dstCatObj = outContainer.getObj(dstCatName)
                    self.__updateSchema(dstCatObj, dstItemL)
                    #   Create destination index index -
                    dstKeyItemL = self.__dm.getDstCategoryKeyItemList(dstCatName=srcCatName, srcCatName=dstCatName)
                    for iRow in range(0, dstCatObj.getRowCount()):
                        dstRowD = dstCatObj.getRowItemDict(iRow)
                        ok, keyTup = self.__getKeyValues(dstRowD, dstKeyItemL)
                        self.__dstIndex[dstCatName][keyTup] = iRow
                #
                for iRow in range(0, srcCatObj.getRowCount()):
                    srcRowD = srcCatObj.getRowItemDict(iRow)
                    ok, keyTup = self.__getKeyValues(srcRowD, keyItemL)
                    if not ok:
                        logger.warning("Incomplete key in source category %s row %d %r" % (srcCatName, iRow, keyItemL))
                    #
                    #  Test key values against the destination category index
                    if keyTup in self.__dstIndex[dstCatName]:
                        # update -
                        dstRowIndex = self.__dstIndex[dstCatName][keyTup]
                        dstRowIndex = self.__updateRow(dstCatObj, srcRowD, mapItemD, dstRowIndex)
                    else:
                        # append -
                        dstRowIndex = self.__appendRow(dstCatObj, srcRowD, mapItemD)
                        self.__dstIndex[dstCatName][keyTup] = dstRowIndex

        elif mode == "dst-src":
            dstCatNameL = self.__dm.getMappedCategoryListForDst(dstCatName=srcCatName)
            for dstCatName in dstCatNameL:
                #
                keyItemL = self.__dm.getDstCategoryKeyItemList(dstCatName=srcCatName, srcCatName=dstCatName)
                mapItemD = self.__dm.getMappedItemsForDst(dstCatName=srcCatName, srcCatName=dstCatName)
                dstItemL = self.__dm.getSrcCategoryItemList(srcCatName=dstCatName)
                #
                if not outContainer.exists(dstCatName):
                    aCat = DataCategory(dstCatName)
                    for dstItem in dstItemL:
                        dstAttr = CifName.attributePart(dstItem)
                        aCat.appendAttribute(dstAttr)
                    outContainer.append(aCat)
                    self.__dstIndex[dstCatName] = {}
                    dstCatObj = outContainer.getObj(dstCatName)
                else:
                    dstCatObj = outContainer.getObj(dstCatName)
                    self.__dstIndex[dstCatName] = {}
                    self.__updateSchema(dstCatObj, dstItemL)
                    #   Create destination index index -
                    dstKeyItemL = self.__dm.getSrcCategoryKeyItemList(srcCatName=srcCatName, dstCatName=dstCatName)
                    for iRow in range(0, dstCatObj.getRowCount()):
                        dstRowD = dstCatObj.getRowItemDict(iRow)
                        ok, keyTup = self.__getKeyValues(dstRowD, dstKeyItemL)
                        self.__dstIndex[dstCatName][keyTup] = iRow

                #
                for iRow in range(0, srcCatObj.getRowCount()):
                    srcRowD = srcCatObj.getRowItemDict(iRow)
                    ok, keyTup = self.__getKeyValues(srcRowD, keyItemL)
                    if not ok:
                        logger.warning("Incomplete key in source category %s row %d %r" % (srcCatName, iRow, keyItemL))
                    #
                    #  Test key values against the destination category index
                    if keyTup in self.__dstIndex[dstCatName]:
                        # update -
                        dstRowIndex = self.__dstIndex[dstCatName][keyTup]
                        dstRowIndex = self.__updateRow(dstCatObj, srcRowD, mapItemD, dstRowIndex)
                    else:
                        # append -
                        dstRowIndex = self.__appendRow(dstCatObj, srcRowD, mapItemD)
                        self.__dstIndex[dstCatName][keyTup] = dstRowIndex
        else:
            pass

        return True

    def __readMappingInfo(self, pathPdbxMappingInfo):
        """ Read and load info from input mapping file --
        """
        try:
            dmio = DictionaryMapperIo(self.__verbose, self.__lfh)
            self.__fC = FilterCif(self.__verbose, self.__lfh)

            ok = dmio.setMapFilePath(pathPdbxMappingInfo)
            if ok:
                aDL = dmio.getCategory(catName='pdbx_dict_item_mapping_audit')
                self.__assignAuditDetails(aDL)
                rowDL = dmio.getCategory(catName='pdbx_dict_item_mapping')
                self.__dm = DictionaryMapper(verbose=self.__verbose, log=self.__lfh)
                self.__dm.set(attrDictList=rowDL)

                rowDLS = dmio.getCategory('pdbx_dict_item_substitution')
                self.__fC.setFilterSubstitutionDict(rowDLS)

                rowDLE = dmio.getCategory('pdbx_dict_item_exclusion')
                self.__fC.setFilterItemExclusionDict(rowDLE)

                rowDLC = dmio.getCategory('pdbx_dict_category_exclusion')
                self.__fC.setFilterCategoryExclusionDict(rowDLC)

                return self.__dm
        except Exception as e:
            logger.exception("Failing with %s" % str(e))

    def __assignAuditDetails(self, aDL):
        """  Internal method to organize audit information from the mapping data category pdbx_dict_item_mapping
             as an internal dictionary with a 'mode' key.

             Note:  only a single operation per 'mode' is supported --
        """
        self.__auditD = {}
        try:
            for aD in aDL:
                if (('mode' in aD) and ('action' in aD) and ('extension_dict_version' in aD) and ('extension_dict_name' in aD) and ('extension_dict_location' in aD)):
                    d = {}
                    for ky in ['action', 'extension_dict_version', 'extension_dict_name', 'extension_dict_location']:
                        d[ky] = aD[ky]
                    if aD['mode'] in ['src-dst', 'dst-src']:
                        if aD['mode'] not in self.__auditD:
                            self.__auditD[aD['mode']] = []
                        self.__auditD[aD['mode']].append(d)
        except Exception as e:
            logger.exception("Failing with %s" % str(e))

    def __applyAuditRules(self, auditCatObj, mode):
        """
            Evaluate audit rules in the mapping file and update instance mapping category
            as required.   Status is returned to indicate if mapping should be applied to
            the input instance file.

            return:  status = 'skip' | 'update' , auditCatObj (updated)
        """
        if (self.__debug):
            logger.debug("+InstanceMapper.__applyAuditRules() mode %s auditD %r" % (mode, self.__auditD.items()))
        statusL = []
        #
        if mode not in self.__auditD:
            return 'ignore', auditCatObj
        #
        #  Get rules -
        #
        for aD in self.__auditD[mode]:
            #
            if (aD['action'] == 'remove record'):
                #
                # remove the indicated audit record and/or the category --
                if auditCatObj is not None and auditCatObj.getRowCount() > 0:
                    indL = auditCatObj.selectIndicesFromList(attributeValueList=[aD['extension_dict_name'], aD['extension_dict_version']],
                                                             attributeNameList=['extension_dict_name', 'extension_dict_version'])
                    if len(indL) > 0:
                        for ind in indL:
                            auditCatObj.removeRow(ind)
                    if auditCatObj.getRowCount() < 1:
                        auditCatObj = None
                else:
                    auditCatObj = None
                statusL.append('update')
            elif (aD['action'] == 'add record'):
                if auditCatObj is not None and auditCatObj.getRowCount() > 0:
                    indL = auditCatObj.selectIndicesFromList(attributeValueList=[aD['extension_dict_name'], aD['extension_dict_version']],
                                                             attributeNameList=['extension_dict_name', 'extension_dict_version'])
                    if len(indL) > 0:
                        # audit records exist - set the return action to  -- skip  --
                        statusL.append('skip')
                    else:
                        # add audit records to existing category - update -
                        self.__addAuditRecord(auditCatObj, aD)
                        statusL.append('update')
                else:
                    # -- create a new category -- and insert audit records --
                    #
                    auditCatObj = DataCategory('pdbx_audit_conform_extension')
                    auditCatObj.appendAttribute('extension_dict_name')
                    auditCatObj.appendAttribute('extension_dict_version')
                    auditCatObj.appendAttribute('extension_dict_location')
                    self.__addAuditRecord(auditCatObj, aD)
                    statusL.append('update')
            else:
                pass
        #
        if 'update' in statusL:
            status = 'update'
        elif 'skip' in statusL:
            status = 'skip'
        else:
            status = 'update'
        #
        if (self.__debug):
            logger.debug("+InstanceMapper.__applyAuditRules() leaving with status %s" % status)
            if auditCatObj is not None:
                auditCatObj.printIt(fh=self.__lfh)
            else:
                logger.debug("+InstanceMapper.__applyAuditRules() audit category is empty")
        #
        return status, auditCatObj

    def __addAuditRecord(self, auditCatObj, aD):
        numAttribs = auditCatObj.getAttributeCount()
        row = ['?' for ii in range(0, numAttribs)]
        auditCatObj.append(row)
        nRows = auditCatObj.getRowCount()
        auditCatObj.setValue(aD['extension_dict_name'], attributeName='extension_dict_name', rowIndex=nRows - 1)
        auditCatObj.setValue(aD['extension_dict_version'], attributeName='extension_dict_version', rowIndex=nRows - 1)
        auditCatObj.setValue(aD['extension_dict_location'], attributeName='extension_dict_location', rowIndex=nRows - 1)

    def setFilterTagList(self, taglist=[]):
        """Sets tag list for filtering"""
        self.__fC.setFilterTagList(taglist)

if __name__ == '__main__':
    pass

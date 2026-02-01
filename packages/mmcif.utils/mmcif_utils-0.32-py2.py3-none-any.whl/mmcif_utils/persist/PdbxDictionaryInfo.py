##
# File: PdbxDictionaryInfo.py
# Date: 19-Mar-2012  John Westbrook
#
# Updates:
#  20-Mar-2012  jdw add storage class.
#  21-Mar-2012  jdw Add method to support attribute keys in dictionary object
#  28-Jul-2012  jdw Add display view support -
#   1-Aug-2012  jdw Change initialiation in __buildView()
#   1-Aug-2012  rps Updated initialization in __buildView() to also capture displayName when encountering first entry for a category
#   2-Aug-2012  jdw Add category level view details and supporting methods.
#   6-Aug-2012  jdw Add category display name and readonly flag to item level category
#                       Attribute level methods renamed to item level methods -
#                       Make the display category name the unique identifier rather than category name.
#   7-Aug-2012  rps Updated to allow more granular handling of ITEM_LIST and ITEM_DICT relative to a given cif category
#   2-Sep-2012  jdw Add alternate metadata options.
#  21-Sep-2012  jdw Store the unique list of column names in the persisted object.
#   5-Feb-2013  jdw extend view metadata to represent multiple displayable categories within a category group.
#   7-Feb-2013  jdw simplified category organization and changed prototypes of api methods.
#  19-Feb-2017  ep  add setFromViewContainer() to loading container definition
#   8-Mar-2018  jdw using latest mmcif IO modules
#   8-Mar-2018  jdw Py2-Py3 and refactor for Python Packaging
##
"""
Repackage PDBx dictionary and view metadata by category.

"""
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "john.westbrook@rcsb.org"
__license__ = "Apache 2.0"



import sys
import os
import shelve
import shutil
import pickle

import logging
logger = logging.getLogger(__name__)

#from mmcif_utils.persist.PdbxPyIoAdapter import PdbxPyIoAdapter as PdbxIoAdapter
from mmcif.io.IoAdapterPy import IoAdapterPy as IoAdapter
from mmcif.api.DictionaryApi import DictionaryApi
from mmcif_utils.persist.LockFile import LockFile


class PdbxDictionaryViewInfo(object):
    """ Repackages PDBx dictionary view metadata and provide accessors for this information.

    """

    def __init__(self, viewPath="pdbx_display_view_info.cif", verbose=True, log=sys.stderr):
        self.__verbose = verbose
        self.__debug = False
        self.__lfh = log
        #
        self.__pathViewFile = viewPath
        #
        self.__vD = {}
        self.__setup(viewFilePath=self.__pathViewFile)

    def __setup(self, viewFilePath=None):
        """  Create the internal view object data structure from the input view data file.
        """
        if (viewFilePath is not None and os.access(viewFilePath, os.F_OK)):
            myReader = IoAdapter(self.__verbose, self.__lfh)
            containerList = myReader.readFile(inputFilePath=viewFilePath)
            viewContainer = None
            for c in containerList:
                if c.getName() == "display_view":
                    viewContainer = c
                    break
            #
            #viewContainer = myReader.getContainer(containerName="display_view")
            if viewContainer is not None:
                self.__vD = self.__buildView(viewContainer=viewContainer)
                return True
            else:
                return False
        #
        return False

    def __buildView(self, viewContainer=None):
        """  Create the internal view object data structure from the data in the input category container.

             View Data assumptions -

             within category 'pdbx_display_view_category_group_info' the combination of viewId, menu display name and group display name
                                are unique.

             within category 'pdbx_display_view_category_info' the combination of viewId, group display name, and category name
                                are unique.


             within category 'pdbx_display_view_item_info' the combination of viewId, category group display name,
                             and item name must be unique.

        """
        vD = {}
        if viewContainer is None:
            return False
        vCat = viewContainer.getObj("pdbx_display_view_item_info")
        if (vCat is None):
            return False
        if (vCat.hasAttribute("view_id") and vCat.hasAttribute("item_name") and
                vCat.hasAttribute("item_display_name") and vCat.hasAttribute("category_display_name") and
                vCat.hasAttribute("read_only_flag")):
            idView = vCat.getIndex("view_id")
            idItem = vCat.getIndex("item_name")
            idDisplay = vCat.getIndex("item_display_name")
            idCatDisplay = vCat.getIndex("category_display_name")
            idReadOnly = vCat.getIndex("read_only_flag")

            for row in vCat.getRowList():
                viewName = row[idView]
                readOnly = row[idReadOnly]
                catDisplayName = row[idCatDisplay]
                itemName = row[idItem]
                catName = self.__categoryPart(itemName)
                displayName = row[idDisplay]
                if (self.__debug):
                    logger.debug(" %s %s %s\n" % (viewName, itemName, displayName))
                if viewName not in vD:
                    vObj = {}
                    vObj["DISPLAY_CATEGORY_LIST"] = []
                    vObj["DISPLAY_CATEGORY_DICT"] = {}
                    vObj["DISPLAY_MENU_DICT"] = {}
                    vObj["DISPLAY_MENU_LIST"] = []
                    vObj["CATEGORY_GROUP_DICT"] = {}
                    vD[viewName] = vObj
                #
                if catDisplayName not in vD[viewName]["DISPLAY_CATEGORY_DICT"]:
                    vD[viewName]["DISPLAY_CATEGORY_LIST"].append(catDisplayName)
                    vD[viewName]["DISPLAY_CATEGORY_DICT"][catDisplayName] = {}

                if catName not in vD[viewName]["DISPLAY_CATEGORY_DICT"][catDisplayName]:
                    vD[viewName]["DISPLAY_CATEGORY_DICT"][catDisplayName][catName] = {}
                    vD[viewName]["DISPLAY_CATEGORY_DICT"][catDisplayName][catName]['ITEM_LIST'] = []
                    vD[viewName]["DISPLAY_CATEGORY_DICT"][catDisplayName][catName]['ITEM_DICT'] = {}

                vD[viewName]["DISPLAY_CATEGORY_DICT"][catDisplayName][catName]['ITEM_LIST'].append(itemName)

                if itemName not in vD[viewName]["DISPLAY_CATEGORY_DICT"][catDisplayName][catName]['ITEM_DICT']:
                    vD[viewName]["DISPLAY_CATEGORY_DICT"][catDisplayName][catName]['ITEM_DICT'][itemName] = {}

                vD[viewName]["DISPLAY_CATEGORY_DICT"][catDisplayName][catName]['ITEM_DICT'][itemName]['DISPLAY_NAME'] = displayName
                vD[viewName]["DISPLAY_CATEGORY_DICT"][catDisplayName][catName]['ITEM_DICT'][itemName]['READ_ONLY'] = readOnly

        #
        vCat = viewContainer.getObj("pdbx_display_view_category_group_info")
        if ((vCat is not None) and (vCat.hasAttribute("view_id") and
                                    vCat.hasAttribute("category_group_display_name") and
                                    vCat.hasAttribute("category_menu_display_name"))):
            idView = vCat.getIndex("view_id")
            idMenuName = vCat.getIndex("category_menu_display_name")
            idGroupName = vCat.getIndex("category_group_display_name")
            for row in vCat.getRowList():
                viewName = row[idView]
                groupName = row[idGroupName]
                menuName = row[idMenuName]

                if (self.__debug):
                    logger.debug(" %s %s %s\n" % (viewName, menuName, groupName))
                if viewName not in vD:
                    vObj = {}
                    vObj["DISPLAY_CATEGORY_LIST"] = []
                    vObj["DISPLAY_CATEGORY_DICT"] = {}
                    vObj["DISPLAY_MENU_DICT"] = {}
                    vObj["DISPLAY_MENU_LIST"] = []
                    vObj["CATEGORY_GROUP_DICT"] = {}
                    vD[viewName] = vObj
                #
                if menuName not in vD[viewName]["DISPLAY_MENU_DICT"]:
                    vD[viewName]["DISPLAY_MENU_DICT"][menuName] = {}
                    vD[viewName]["DISPLAY_MENU_DICT"][menuName]['DISPLAY_CATEGORY_GROUP_LIST'] = []
                    vD[viewName]["DISPLAY_MENU_DICT"][menuName]['DISPLAY_CATEGORY_GROUP_LIST'].append(groupName)
                    vD[viewName]["DISPLAY_MENU_LIST"].append(menuName)
                else:
                    vD[viewName]["DISPLAY_MENU_DICT"][menuName]['DISPLAY_CATEGORY_GROUP_LIST'].append(groupName)

        vCat = viewContainer.getObj("pdbx_display_view_category_info")
        if ((vCat is not None) and (vCat.hasAttribute("view_id") and
                                    vCat.hasAttribute("category_group_display_name") and
                                    vCat.hasAttribute("category_group_display_name") and
                                    vCat.hasAttribute("category_display_name") and
                                    vCat.hasAttribute("category_name") and
                                    vCat.hasAttribute("category_cardinality"))):
            idView = vCat.getIndex("view_id")
            idMenuName = vCat.getIndex("category_menu_display_name")
            idCategory = vCat.getIndex("category_name")
            idCard = vCat.getIndex("category_cardinality")
            idCatGroupName = vCat.getIndex("category_group_display_name")
            idCatDisplayName = vCat.getIndex("category_display_name")
            for row in vCat.getRowList():
                viewName = row[idView]
                menuName = row[idMenuName]
                groupName = row[idCatGroupName]
                displayName = row[idCatDisplayName]
                catName = row[idCategory]
                cardinality = row[idCard]

                if (self.__debug):
                    logger.debug(" %s %s %s %s %s\n" % (viewName, menuName, groupName, catName, cardinality))

                if viewName not in vD:
                    vObj = {}
                    vObj["DISPLAY_CATEGORY_LIST"] = []
                    vObj["DISPLAY_CATEGORY_DICT"] = {}
                    #
                    vObj["DISPLAY_MENU_LIST"] = []
                    vObj["DISPLAY_MENU_DICT"] = {}
                    vObj["CATEGORY_GROUP_DICT"] = {}
                    vD[viewName] = vObj
                #

                if menuName not in vD[viewName]["DISPLAY_MENU_DICT"]:
                    vD[viewName]["DISPLAY_MENU_DICT"][menuName] = {}
                    vD[viewName]["DISPLAY_MENU_DICT"][menuName]['DISPLAY_CATEGORY_GROUP_DICT'] = {}
                    vD[viewName]["DISPLAY_MENU_DICT"][menuName]['DISPLAY_CATEGORY_GROUP_LIST'] = []
                    vD[viewName]["DISPLAY_MENU_LIST"].append(menuName)

                vD[viewName]["DISPLAY_MENU_DICT"][menuName]['DISPLAY_CATEGORY_GROUP_LIST'].append(groupName)

                if groupName not in vD[viewName]["DISPLAY_MENU_DICT"][menuName]['DISPLAY_CATEGORY_GROUP_DICT']:
                    vD[viewName]["DISPLAY_MENU_DICT"][menuName]['DISPLAY_CATEGORY_GROUP_DICT'][groupName] = []

                vD[viewName]["DISPLAY_MENU_DICT"][menuName]['DISPLAY_CATEGORY_GROUP_DICT'][groupName].append((menuName, displayName, catName, cardinality))

        return vD

    def get(self):
        """  Return the full view object.
        """
        return self.__vD

    def set(self, viewObj=None):
        """  Initialize the internal data structure with the input view object.
        """
        if (viewObj is None):
            self.__vD = {}
        else:
            self.__vD = viewObj

    def setFromViewContainer(self, viewContainer=None):
        """  Initialize the internal data structure with a viewContainer
        """
        if (viewContainer is None):
            self.__vD = {}
        else:
            self.__vD = self.__buildView(viewContainer=viewContainer)

    def getViewList(self):
        """ Return the list of defined views.
        """
        return list(self.__vD.keys())

    def getDisplayCategoryList(self, viewId=None):
        """ Return the category display names list in the input view.
        """
        if (viewId is not None and viewId in self.__vD):
            return self.__vD[viewId]['DISPLAY_CATEGORY_LIST']
        else:
            return []

    def getDisplayMenuList(self, viewId):
        """ Return the list menu display items in the input view.
        """
        if (viewId is not None and viewId in self.__vD):
            return self.__vD[viewId]['DISPLAY_MENU_LIST']
        else:
            return []

    def getCategoryGroupList(self, viewId, menuName):
        """ Return the list of category group names within the input menu of the input view.
        """
        try:
            return self.__vD[viewId]['DISPLAY_MENU_DICT'][menuName]['DISPLAY_CATEGORY_GROUP_LIST']
        except Exception as e:
            return []

    def getDisplayCategoryListInGroup(self, viewId, menuName, groupName):
        """ Return the list of category group names in the input menu in the input view.
        """
        try:
            return [t[1] for t in self.__vD[viewId]["DISPLAY_MENU_DICT"][menuName]['DISPLAY_CATEGORY_GROUP_DICT'][groupName]]
        except Exception as e:
            return []
    #

    def getCategoryGroupListInMenu(self, viewId, menuName):
        """ Return the display category group list in the input display menu view item..
        """
        try:
            return self.__vD[viewId]["DISPLAY_MENU_DICT"][menuName]['DISPLAY_CATEGORY_GROUP_LIST']
        except Exception as e:
            return []

    def getCategoryName(self, viewId, menuName, categoryGroupName, categoryDisplayName):
        """ Return the category name in the input view/menu/category display name.
        """
        try:
            ret = None
            for menuName, displayName, catName, card in self.__vD[viewId]["DISPLAY_MENU_DICT"][menuName]['DISPLAY_CATEGORY_GROUP_DICT'][categoryGroupName]:
                if displayName == categoryDisplayName:
                    ret = catName
            return ret
        except Exception as e:
            return None

    def getCategoryCardinality(self, viewId, menuName, categoryGroupName, categoryDisplayName):
        """ Return the category name in the input view/menu/category display name.
        """
        try:
            ret = None
            for menuName, displayName, catName, card in self.__vD[viewId]["DISPLAY_MENU_DICT"][menuName]['DISPLAY_CATEGORY_GROUP_DICT'][categoryGroupName]:
                if displayName == categoryDisplayName:
                    ret = card
            return ret
        except Exception as e:
            return None

    def getItemList(self, viewId, categoryDisplayName, categoryName):
        """ Return the item list in the input category in the input view.
        """
        if (viewId in self.__vD and categoryDisplayName in self.__vD[viewId]['DISPLAY_CATEGORY_DICT'] and
                categoryName in self.__vD[viewId]['DISPLAY_CATEGORY_DICT'][categoryDisplayName]):
            return self.__vD[viewId]['DISPLAY_CATEGORY_DICT'][categoryDisplayName][categoryName]['ITEM_LIST']
        else:
            return []

    def getItemDisplayName(self, viewId, categoryDisplayName, categoryName, itemName):
        """ Return the item display name for the item in the input display category in the input view.
        """
        if (viewId in self.__vD and categoryDisplayName in self.__vD[viewId]['DISPLAY_CATEGORY_DICT'] and
                categoryName in self.__vD[viewId]['DISPLAY_CATEGORY_DICT'][categoryDisplayName] and
                itemName in self.__vD[viewId]['DISPLAY_CATEGORY_DICT'][categoryDisplayName][categoryName]['ITEM_DICT']):
            return self.__vD[viewId]['DISPLAY_CATEGORY_DICT'][categoryDisplayName][categoryName]['ITEM_DICT'][itemName]['DISPLAY_NAME']
        else:
            return itemName

    def getItemReadOnlyFlag(self, viewId, categoryDisplayName, categoryName, itemName):
        """ Return the read only flag for the item in the input display category in the input view.
        """
        if (viewId in self.__vD and categoryDisplayName in self.__vD[viewId]['DISPLAY_CATEGORY_DICT'] and
                categoryName in self.__vD[viewId]['DISPLAY_CATEGORY_DICT'][categoryDisplayName] and
                itemName in self.__vD[viewId]['DISPLAY_CATEGORY_DICT'][categoryDisplayName][categoryName]['ITEM_DICT']):
            return self.__vD[viewId]['DISPLAY_CATEGORY_DICT'][categoryDisplayName][categoryName]['ITEM_DICT'][itemName]['READ_ONLY']
        else:
            return itemName

    def __attributePart(self, name):
        i = name.find(".")
        if i == -1:
            return None
        else:
            return name[i + 1:]

    def __categoryPart(self, name):
        tname = ""
        if name.startswith("_"):
            tname = name[1:]
        else:
            tname = name

        i = tname.find(".")
        if i == -1:
            return tname
        else:
            return tname[:i]


class PdbxDictionaryInfo(object):
    """ Repackages PDBx dictionary metadata by category.

    """

    def __init__(self, dictPath="mmcif_pdbx_v40.dic", verbose=True, log=sys.stderr):
        self.__verbose = verbose
        self.__debug = False
        self.__lfh = log
        #
        self.__pathPdbxDict = dictPath

        # obsolete
        self.__containerList = []
        self.__containerNameList = []
        #
        self.__categoryNameList = []
        self.__categoryIndexD = {}
        #
        # Parameters to tune lock file management --
        self.__timeoutSeconds = 10
        self.__retrySeconds = 0.2
        # placeholder for LockFile object for open/close methods
        self.__lockObj = None
        self.__isExpired = True
        self.__db = None
        #
        self.__setup()

    def __setup(self):
        """ Read text dictionary and create internal lists of category names and objects.
        """
        self.__viewContainer = None
        myReader = IoAdapter(self.__verbose, self.__lfh)
        #ok = myReader.readFile(inputFilePath=self.__pathPdbxDict)
        #self.__containerNameList = myReader.getContainerNameList()
        #
        self.__containerList = myReader.readFile(inputFilePath=self.__pathPdbxDict)
        self.__containerNameList = [c.getName() for c in self.__containerList]
        self.__dApi = DictionaryApi(self.__containerList)
        self.__categoryNameList = self.__dApi.getCategoryList()
        self.__categoryIndexD = self.__dApi.getCategoryIndex()
        self.__parentD = self.__dApi.getParentDictionary()
        #
        if (self.__debug):
            self.dbg()

    def dbg(self, fName="dict.dump"):
        ofh = open(fName, 'w')
        self.__dApi.dumpFeatures(ofh)
        ofh.close()

    def assembleByIndex(self):
        """ Repackage dictionary data for each category.  Attribute data is stored in
            dictionaries using attribute index keys.
        """
        dInfo = {}
        for categoryName in self.__categoryNameList:
            self.__setCategory(categoryName)
            dI = {}
            dI['DISPLAY_NAME'] = categoryName.lower()
            dI['COLUMN_NAMES'] = self.__currentAttributeNameList
            dI['COLUMN_DISPLAY_NAMES'] = self.__currentAttributeNameList
            dI['PRIMARY_KEYS'] = self.__getKeyIndexList()
            dI['MANDATORY_COLUMNS'] = self.__getMandatoryIndexList()
            dI['MANDATORY_COLUMNS_ALT'] = self.__getAltMandatoryIndexList()
            dI['COLUMN_DISPLAY_ORDER'] = self.__getOrderIndexList(keyList=dI['PRIMARY_KEYS'], mandatoryList=dI['MANDATORY_COLUMNS'])
            dI['COLUMN_TYPES'] = self.__getTypeIndexD()
            dI['COLUMN_TYPES_ALT'] = self.__getAltTypeIndexD()
            dI['COLUMN_ENUMS'] = self.__getEnumIndexD()
            dI['COLUMN_ENUMS_ALT'] = self.__getAltEnumIndexD()
            dI['COLUMN_DESCRIPTIONS'] = self.__getDescriptionIndexD()
            dI['COLUMN_DESCRIPTIONS_ALT'] = self.__getAltDescriptionIndexD()
            dI['COLUMN_EXAMPLES'] = self.__getExampleIndexD()
            dI['COLUMN_EXAMPLES_ALT'] = self.__getAltExampleIndexD()
            dI['COLUMN_REGEX'] = self.__getRegexIndexD()
            dI['COLUMN_REGEX_ALT'] = self.__getAltRegexIndexD()
            dI['COLUMN_BOUNDARY_VALUES'] = self.__getBoundaryIndexD()
            dI['COLUMN_BOUNDARY_VALUES_ALT'] = self.__getAltBoundaryIndexD()
            dI['COLUMN_DEFAULT_VALUES'] = self.__getDefaultIndexD()
            #
            if (self.__debug):
                logger.debug("PdbxDictionaryInfo(assemble): category %s attributes %r\n" % (categoryName, self.__currentAttributeNameList))
                logger.debug("PdbxDictionaryInfo(assemble): category %s key index list %r\n" % (categoryName, dI['PRIMARY_KEYS']))
                logger.debug("PdbxDictionaryInfo(assemble): category %s mandatory index list %r\n" % (categoryName, dI['MANDATORY_COLUMNS']))
                logger.debug("PdbxDictionaryInfo(assemble): category %s mandatory index list (alt) %r\n" % (categoryName, dI['MANDATORY_COLUMNS_ALT']))
                logger.debug("PdbxDictionaryInfo(assemble): category %s order index list %r\n" % (categoryName, dI['COLUMN_DISPLAY_ORDER']))
                logger.debug("PdbxDictionaryInfo(assemble): category %s type index dictionary %r\n" % (categoryName, dI['COLUMN_TYPES'].items()))
                logger.debug("PdbxDictionaryInfo(assemble): category %s type index dictionary (alt) %r\n" % (categoryName, dI['COLUMN_TYPES_ALT'].items()))
                logger.debug("PdbxDictionaryInfo(assemble): category %s type enum dictionary %r\n" % (categoryName, dI['COLUMN_ENUMS'].items()))
                logger.debug("PdbxDictionaryInfo(assemble): category %s type enum dictionary (alt)  %r\n" % (categoryName, dI['COLUMN_ENUMS_ALT'].items()))
                logger.debug("PdbxDictionaryInfo(assemble): category %s type description dictionary %r\n" % (categoryName, dI['COLUMN_DESCRIPTIONS'].items()))
                logger.debug("PdbxDictionaryInfo(assemble): category %s type description dictionary (alt) %r\n" % (categoryName, dI['COLUMN_DESCRIPTIONS_ALT'].items()))
                logger.debug("PdbxDictionaryInfo(assemble): category %s type example dictionary %r\n" % (categoryName, dI['COLUMN_DESCRIPTIONS'].items()))
                logger.debug("PdbxDictionaryInfo(assemble): category %s type example dictionary (alt) %r\n" % (categoryName, dI['COLUMN_DESCRIPTIONS_ALT'].items()))
                logger.debug("PdbxDictionaryInfo(assemble): category %s type regex dictionary %r\n" % (categoryName, dI['COLUMN_REGEX'].items()))
                logger.debug("PdbxDictionaryInfo(assemble): category %s type regex dictionary (alt) %r\n" % (categoryName, dI['COLUMN_REGEX_ALT'].items()))
                logger.debug("PdbxDictionaryInfo(assemble): category %s boundary dictionary %r\n" % (categoryName, dI['COLUMN_BOUNDARY_VALUES'].items()))
                logger.debug("PdbxDictionaryInfo(assemble): category %s boundary dictionary (alt)  %r\n" % (categoryName, dI['COLUMN_BOUNDARY_VALUES_ALT'].items()))
                logger.debug("PdbxDictionaryInfo(assemble): category %s default value dictionary %r\n" % (categoryName, dI['COLUMN_BOUNDARY_VALUES'].items()))
            dInfo[categoryName] = dI
        #
        return dInfo

    def assembleByAttribute(self):
        """ Repackage dictionary data for each category.  Attribute data is stored in dictionaries
            using attribute name keys.
        """
        dInfo = {}
        for categoryName in self.__categoryNameList:
            self.__setCategory(categoryName)
            dI = {}
            dI['DISPLAY_NAME'] = categoryName.lower()
            dI['COLUMN_NAMES'] = self.__currentAttributeNameList
            dI['COLUMN_DISPLAY_NAMES'] = self.__currentAttributeNameList
            dI['PRIMARY_KEYS'] = self.__getKeyAttributeList()
            dI['MANDATORY_COLUMNS'] = self.__getMandatoryAttributeList()
            dI['MANDATORY_COLUMNS_ALT'] = self.__getAltMandatoryAttributeList()
            dI['COLUMN_DISPLAY_ORDER'] = self.__getOrderAttributeList(keyList=dI['PRIMARY_KEYS'], mandatoryList=dI['MANDATORY_COLUMNS'])
            dI['COLUMN_TYPES'] = self.__getTypeD()
            dI['COLUMN_TYPES_ALT'] = self.__getAltTypeD()
            dI['COLUMN_ENUMS'] = self.__getEnumD()
            dI['COLUMN_ENUMS_ALT'] = self.__getAltEnumD()
            dI['COLUMN_DESCRIPTIONS'] = self.__getDescriptionD()
            dI['COLUMN_DESCRIPTIONS_ALT'] = self.__getAltDescriptionD()
            dI['COLUMN_EXAMPLES'] = self.__getExampleD()
            dI['COLUMN_EXAMPLES_ALT'] = self.__getAltExampleD()
            dI['COLUMN_REGEX'] = self.__getRegexD()
            dI['COLUMN_REGEX_ALT'] = self.__getAltRegexD()
            dI['COLUMN_BOUNDARY_VALUES'] = self.__getBoundaryD()
            dI['COLUMN_BOUNDARY_VALUES_ALT'] = self.__getAltBoundaryD()
            dI['COLUMN_DEFAULT_VALUES'] = self.__getDefaultD()
            #
            if (self.__debug):
                logger.debug("PdbxDictionaryInfo(assemble): category %s attributes %r\n" % (categoryName, self.__currentAttributeNameList))
                logger.debug("PdbxDictionaryInfo(assemble): category %s key index list %r\n" % (categoryName, dI['PRIMARY_KEYS']))
                logger.debug("PdbxDictionaryInfo(assemble): category %s mandatory index list %r\n" % (categoryName, dI['MANDATORY_COLUMNS']))
                logger.debug("PdbxDictionaryInfo(assemble): category %s mandatory index list (alt) %r\n" % (categoryName, dI['MANDATORY_COLUMNS_ALT']))
                logger.debug("PdbxDictionaryInfo(assemble): category %s order index list %r\n" % (categoryName, dI['COLUMN_DISPLAY_ORDER']))
                logger.debug("PdbxDictionaryInfo(assemble): category %s type index dictionary %r\n" % (categoryName, dI['COLUMN_TYPES'].items()))
                logger.debug("PdbxDictionaryInfo(assemble): category %s type index dictionary (alt) %r\n" % (categoryName, dI['COLUMN_TYPES_ALT'].items()))
                logger.debug("PdbxDictionaryInfo(assemble): category %s type enum dictionary %r\n" % (categoryName, dI['COLUMN_ENUMS'].items()))
                logger.debug("PdbxDictionaryInfo(assemble): category %s type enum dictionary (alt)  %r\n" % (categoryName, dI['COLUMN_ENUMS_ALT'].items()))
                logger.debug("PdbxDictionaryInfo(assemble): category %s type description dictionary %r\n" % (categoryName, dI['COLUMN_DESCRIPTIONS'].items()))
                logger.debug("PdbxDictionaryInfo(assemble): category %s type description dictionary (alt) %r\n" % (categoryName, dI['COLUMN_DESCRIPTIONS_ALT'].items()))
                logger.debug("PdbxDictionaryInfo(assemble): category %s type example dictionary %r\n" % (categoryName, dI['COLUMN_DESCRIPTIONS'].items()))
                logger.debug("PdbxDictionaryInfo(assemble): category %s type example dictionary (alt) %r\n" % (categoryName, dI['COLUMN_DESCRIPTIONS_ALT'].items()))
                logger.debug("PdbxDictionaryInfo(assemble): category %s type regex dictionary %r\n" % (categoryName, dI['COLUMN_REGEX'].items()))
                logger.debug("PdbxDictionaryInfo(assemble): category %s type regex dictionary (alt) %r\n" % (categoryName, dI['COLUMN_REGEX_ALT'].items()))
                logger.debug("PdbxDictionaryInfo(assemble): category %s boundary dictionary %r\n" % (categoryName, dI['COLUMN_BOUNDARY_VALUES'].items()))
                logger.debug("PdbxDictionaryInfo(assemble): category %s boundary dictionary (alt)  %r\n" % (categoryName, dI['COLUMN_BOUNDARY_VALUES_ALT'].items()))
                logger.debug("PdbxDictionaryInfo(assemble): category %s default value dictionary %r\n" % (categoryName, dI['COLUMN_BOUNDARY_VALUES'].items()))

            dInfo[categoryName] = dI
        #
        return dInfo

    def __getEnumIndexD(self):
        rD = {}
        for attributeName in self.__currentAttributeNameList:
            eList = self.__dApi.getEnumList(self.__currentCategoryName, attributeName)
            if len(eList) > 0:
                rD[self.__getAttributeIndex(attributeName)] = eList
        return rD

    def __getAltEnumIndexD(self):
        rD = {}
        for attributeName in self.__currentAttributeNameList:
            eList = self.__dApi.getEnumListAlt(self.__currentCategoryName, attributeName)
            if len(eList) > 0:
                rD[self.__getAttributeIndex(attributeName)] = eList
        return rD

    def __getDescriptionIndexD(self):
        rD = {}
        for attributeName in self.__currentAttributeNameList:
            txt = self.__dApi.getDescription(self.__currentCategoryName, attributeName)
            if txt is not None and len(txt) > 0:
                rD[self.__getAttributeIndex(attributeName)] = txt
        return rD

    def __getAltDescriptionIndexD(self):
        rD = {}
        for attributeName in self.__currentAttributeNameList:
            txt = self.__dApi.getDescriptionAlt(self.__currentCategoryName, attributeName)
            if txt is not None and len(txt) > 0:
                rD[self.__getAttributeIndex(attributeName)] = txt
        return rD

    def __getExampleIndexD(self):
        rD = {}
        for attributeName in self.__currentAttributeNameList:
            eList = self.__dApi.getExampleList(self.__currentCategoryName, attributeName)
            if len(eList) > 0:
                rD[self.__getAttributeIndex(attributeName)] = eList
        return rD

    def __getAltExampleIndexD(self):
        rD = {}
        for attributeName in self.__currentAttributeNameList:
            eList = self.__dApi.getExampleListAlt(self.__currentCategoryName, attributeName)
            if len(eList) > 0:
                rD[self.__getAttributeIndex(attributeName)] = eList
        return rD

    def __getRegexIndexD(self):
        rD = {}
        for attributeName in self.__currentAttributeNameList:
            typ = self.__dApi.getTypeRegex(self.__currentCategoryName, attributeName)
            if typ is not None and len(typ) > 0:
                rD[self.__getAttributeIndex(attributeName)] = typ
        return rD

    def __getAltRegexIndexD(self):
        rD = {}
        for attributeName in self.__currentAttributeNameList:
            typ = self.__dApi.getTypeRegexAlt(self.__currentCategoryName, attributeName)
            if typ is not None and len(typ) > 0:
                rD[self.__getAttributeIndex(attributeName)] = typ
        return rD

    def __getDefaultIndexD(self):
        rD = {}
        for attributeName in self.__currentAttributeNameList:
            typ = self.__dApi.getDefaultValue(self.__currentCategoryName, attributeName)
            if typ is not None and len(typ) > 0:
                rD[self.__getAttributeIndex(attributeName)] = typ
        return rD

    def __getBoundaryIndexD(self):
        rD = {}
        for attributeName in self.__currentAttributeNameList:
            bList = self.__dApi.getBoundaryList(self.__currentCategoryName, attributeName)
            if len(bList) > 0:
                rD[self.__getAttributeIndex(attributeName)] = bList
        return rD

    def __getAltBoundaryIndexD(self):
        rD = {}
        for attributeName in self.__currentAttributeNameList:
            bList = self.__dApi.getBoundaryListAlt(self.__currentCategoryName, attributeName)
            if len(bList) > 0:
                rD[self.__getAttributeIndex(attributeName)] = bList
        return rD

    def __getTypeIndexD(self):
        rD = {}
        for attributeName in self.__currentAttributeNameList:
            dType = self.__dApi.getTypeCode(self.__currentCategoryName, attributeName)
            pType = self.__dApi.getTypePrimitive(self.__currentCategoryName, attributeName)
            isEnum = self.__dApi.isEnumerated(self.__currentCategoryName, attributeName)
            #
            pL = self.__dApi.getParentList(self.__currentCategoryName, attributeName)
            if (self.__debug):
                logger.debug("PdbxDictionaryInfo(assemble): category %s attribute %s parent list %r\n" % (self.__currentCategoryName, attributeName, pL))
            #
            if dType is None:
                (iG, tC, tA) = self.__getUltimateParent(self.__currentCategoryName, attributeName)
                if iG > 0:
                    dType = self.__dApi.getTypeCode(tC, tA)

            if dType is None:
                logger.info("PdbxDictionaryInfo(assemble): category %s attribute %s missing data type\n" % (self.__currentCategoryName, attributeName))
                dType = 'code'

            if isEnum:
                typ = 'select'
            elif dType in ['float', 'float-range']:
                typ = 'float'
            elif dType in ['int', 'int-range', 'positive_int', 'non_negative_int']:
                typ = 'int'
            elif dType in ['text']:
                typ = 'text'
            elif dType in ['line', 'uline']:
                typ = 'line'
            elif dType in ['code', 'ucode', 'name', 'idname', 'atcode']:
                typ = 'word'
            elif dType.startswith('yyyy-mm'):
                typ = 'date-time'
            elif dType in ['fax', 'phone']:
                typ = 'phone-number'
            elif dType in ['email']:
                typ = 'email'
            elif pType in ['char', 'uchar']:
                typ = 'word'
            else:
                logger.info("PdbxDictionaryInfo(assemble): category %s attribute %s odd type %s\n" % (self.__currentCategoryName, attributeName, dType))

            rD[self.__getAttributeIndex(attributeName)] = typ

        return rD

    #
    def __getAltTypeIndexD(self):
        rD = {}
        for attributeName in self.__currentAttributeNameList:
            dType = self.__dApi.getTypeCodeAlt(self.__currentCategoryName, attributeName)
            pType = self.__dApi.getTypePrimitive(self.__currentCategoryName, attributeName)
            isEnum = self.__dApi.isEnumerated(self.__currentCategoryName, attributeName)
            #
            pL = self.__dApi.getParentList(self.__currentCategoryName, attributeName)
            if (self.__debug):
                logger.debug("PdbxDictionaryInfo(assemble): category %s attribute %s parent list %r\n" % (self.__currentCategoryName, attributeName, pL))
            #
            if dType is None:
                (iG, tC, tA) = self.__getUltimateParent(self.__currentCategoryName, attributeName)
                if iG > 0:
                    dType = self.__dApi.getTypeCodeAlt(tC, tA)

            if dType is None:
                logger.info("PdbxDictionaryInfo(assemble): category %s attribute %s missing data type\n" % (self.__currentCategoryName, attributeName))
                dType = 'code'

            if isEnum:
                typ = 'select'
            elif dType in ['float', 'float-range']:
                typ = 'float'
            elif dType in ['int', 'int-range']:
                typ = 'int'
            elif dType in ['text']:
                typ = 'text'
            elif dType in ['line', 'uline']:
                typ = 'line'
            elif dType in ['code', 'ucode', 'name', 'idname', 'atcode']:
                typ = 'word'
            elif dType.startswith('yyyy-mm'):
                typ = 'date-time'
            elif dType in ['fax', 'phone']:
                typ = 'phone-number'
            elif dType in ['email']:
                typ = 'email'
            elif pType in ['char', 'uchar']:
                typ = 'word'
            else:
                logger.info("PdbxDictionaryInfo(assemble): category %s attribute %s odd type %s\n" % (self.__currentCategoryName, attributeName, dType))

            rD[self.__getAttributeIndex(attributeName)] = typ

        return rD

    # -----------------------------------
    #
    def __getEnumD(self):
        rD = {}
        for attributeName in self.__currentAttributeNameList:
            eList = self.__dApi.getEnumList(self.__currentCategoryName, attributeName)
            if len(eList) > 0:
                rD[attributeName] = eList
        return rD

    def __getAltEnumD(self):
        rD = {}
        for attributeName in self.__currentAttributeNameList:
            eList = self.__dApi.getEnumListAlt(self.__currentCategoryName, attributeName)
            if len(eList) > 0:
                rD[attributeName] = eList
        return rD

    def __getDescriptionD(self):
        rD = {}
        for attributeName in self.__currentAttributeNameList:
            txt = self.__dApi.getDescription(self.__currentCategoryName, attributeName)
            if txt is not None and len(txt) > 0:
                rD[attributeName] = txt
        return rD

    def __getAltDescriptionD(self):
        rD = {}
        for attributeName in self.__currentAttributeNameList:
            txt = self.__dApi.getDescriptionAlt(self.__currentCategoryName, attributeName)
            if txt is not None and len(txt) > 0:
                rD[attributeName] = txt
        return rD

    def __getExampleD(self):
        rD = {}
        for attributeName in self.__currentAttributeNameList:
            eList = self.__dApi.getExampleList(self.__currentCategoryName, attributeName)
            if len(eList) > 0:
                rD[attributeName] = eList
        return rD

    def __getAltExampleD(self):
        rD = {}
        for attributeName in self.__currentAttributeNameList:
            eList = self.__dApi.getExampleListAlt(self.__currentCategoryName, attributeName)
            if len(eList) > 0:
                rD[attributeName] = eList
        return rD

    def __getRegexD(self):
        rD = {}
        for attributeName in self.__currentAttributeNameList:
            typ = self.__dApi.getTypeRegex(self.__currentCategoryName, attributeName)
            if typ is not None and len(typ) > 0:
                rD[attributeName] = typ
        return rD

    def __getAltRegexD(self):
        rD = {}
        for attributeName in self.__currentAttributeNameList:
            typ = self.__dApi.getTypeRegexAlt(self.__currentCategoryName, attributeName)
            if typ is not None and len(typ) > 0:
                rD[attributeName] = typ
        return rD

    def __getDefaultD(self):
        rD = {}
        for attributeName in self.__currentAttributeNameList:
            typ = self.__dApi.getDefaultValue(self.__currentCategoryName, attributeName)
            if typ is not None and len(typ) > 0:
                rD[attributeName] = typ
        return rD

    def __getBoundaryD(self):
        rD = {}
        for attributeName in self.__currentAttributeNameList:
            bList = self.__dApi.getBoundaryList(self.__currentCategoryName, attributeName)
            if len(bList) > 0:
                rD[attributeName] = bList
        return rD

    def __getAltBoundaryD(self):
        rD = {}
        for attributeName in self.__currentAttributeNameList:
            bList = self.__dApi.getBoundaryListAlt(self.__currentCategoryName, attributeName)
            if len(bList) > 0:
                rD[attributeName] = bList
        return rD

    def __getTypeD(self):
        rD = {}
        for attributeName in self.__currentAttributeNameList:
            dType = self.__dApi.getTypeCode(self.__currentCategoryName, attributeName)
            pType = self.__dApi.getTypePrimitive(self.__currentCategoryName, attributeName)
            isEnum = self.__dApi.isEnumerated(self.__currentCategoryName, attributeName)
            #
            pL = self.__dApi.getParentList(self.__currentCategoryName, attributeName)
            if (self.__debug):
                logger.debug("PdbxDictionaryInfo(assemble): category %s attribute %s parent list %r\n" % (self.__currentCategoryName, attributeName, pL))
            #
            if dType is None:
                (iG, tC, tA) = self.__getUltimateParent(self.__currentCategoryName, attributeName)
                if iG > 0:
                    dType = self.__dApi.getTypeCode(tC, tA)

            if dType is None:
                logger.info("PdbxDictionaryInfo(assemble): category %s attribute %s missing data type\n" % (self.__currentCategoryName, attributeName))
                dType = 'code'

            if isEnum:
                typ = 'select'
            elif dType in ['float', 'float-range']:
                typ = 'float'
            elif dType in ['int', 'int-range', 'positive_int', 'non_negative_int']:
                typ = 'int'
            elif dType in ['text']:
                typ = 'text'
            elif dType in ['line', 'uline']:
                typ = 'line'
            elif dType in ['code', 'ucode', 'name', 'idname', 'atcode', 'emd_id', 'pdb_id']:
                typ = 'word'
            elif dType.startswith('yyyy-mm'):
                typ = 'date-time'
            elif dType in ['fax', 'phone']:
                typ = 'phone-number'
            elif dType in ['email']:
                typ = 'email'
            elif pType in ['char', 'uchar']:
                typ = 'word'
            else:
                typ = 'text'
                logger.info("PdbxDictionaryInfo(assemble): category %s attribute %s odd type %s\n" % (self.__currentCategoryName, attributeName, dType))

            rD[attributeName] = typ

        return rD

    def __getAltTypeD(self):
        rD = {}
        for attributeName in self.__currentAttributeNameList:
            dType = self.__dApi.getTypeCodeAlt(self.__currentCategoryName, attributeName)
            pType = self.__dApi.getTypePrimitive(self.__currentCategoryName, attributeName)
            isEnum = self.__dApi.isEnumerated(self.__currentCategoryName, attributeName)
            #
            pL = self.__dApi.getParentList(self.__currentCategoryName, attributeName)
            if (self.__debug):
                logger.debug("PdbxDictionaryInfo(assemble): category %s attribute %s parent list %r\n" % (self.__currentCategoryName, attributeName, pL))
            #
            if dType is None:
                (iG, tC, tA) = self.__getUltimateParent(self.__currentCategoryName, attributeName)
                if iG > 0:
                    dType = self.__dApi.getTypeCodeAlt(tC, tA)

            if dType is None:
                logger.info("PdbxDictionaryInfo(assemble): category %s attribute %s missing data type\n" % (self.__currentCategoryName, attributeName))
                dType = 'code'

            if isEnum:
                typ = 'select'
            elif dType in ['float', 'float-range']:
                typ = 'float'
            elif dType in ['int', 'int-range', 'positive_int', 'non_negative_int']:
                typ = 'int'
            elif dType in ['text']:
                typ = 'text'
            elif dType in ['line', 'uline']:
                typ = 'line'
            elif dType in ['code', 'ucode', 'name', 'idname', 'atcode']:
                typ = 'word'
            elif dType.startswith('yyyy-mm'):
                typ = 'date-time'
            elif dType in ['fax', 'phone']:
                typ = 'phone-number'
            elif dType in ['email']:
                typ = 'email'
            elif pType in ['char', 'uchar']:
                typ = 'word'
            else:
                typ = 'text'
                logger.info("PdbxDictionaryInfo(assemble): category %s attribute %s odd type %s\n" % (self.__currentCategoryName, attributeName, dType))

            rD[attributeName] = typ

        return rD

    def __getOrderIndexList(self, keyList=None, mandatoryList=None):
        iL = []
        if keyList is not None:
            for ii in keyList:
                if not ii in iL:
                    iL.append(ii)
        #
        if mandatoryList is not None:
            for ii in mandatoryList:
                if ii not in iL:
                    iL.append(ii)
        #
        for attrib, ii in self.__currentAttributeD.items():
            if not ii in iL:
                iL.append(ii)
        #
        return iL

    def __getOrderAttributeList(self, keyList=None, mandatoryList=None):
        iL = []
        if keyList is not None:
            for att in keyList:
                if not att in iL:
                    iL.append(att)
        #
        if mandatoryList is not None:
            for att in mandatoryList:
                if att not in iL:
                    iL.append(att)
        #
        for att in self.__currentAttributeNameList:
            if not att in iL:
                iL.append(att)
        #
        return iL

    def __getKeyIndexList(self):
        rL = []
        kyL = self.__dApi.getCategoryKeyList(self.__currentCategoryName)
        for ky in kyL:
            rL.append(self.__getItemIndex(ky))
        return rL

    def __getMandatoryIndexList(self):
        rL = []
        for attributeName in self.__currentAttributeNameList:
            val = self.__dApi.getMandatoryCode(self.__currentCategoryName, attributeName)
            if val is not None and val.upper() in ['Y', 'YES']:
                rL.append(self.__getAttributeIndex(attributeName))
        return rL

    def __getAltMandatoryIndexList(self):
        rL = []
        for attributeName in self.__currentAttributeNameList:
            val = self.__dApi.getMandatoryCodeAlt(self.__currentCategoryName, attributeName)
            if val is not None and val.upper() in ['Y', 'YES']:
                rL.append(self.__getAttributeIndex(attributeName))
        return rL

    def __getKeyAttributeList(self):
        rL = []
        kyL = self.__dApi.getCategoryKeyList(self.__currentCategoryName)
        for ky in kyL:
            rL.append(self.__attributePart(ky))
        return rL

    def __getMandatoryAttributeList(self):
        rL = []
        for attributeName in self.__currentAttributeNameList:
            val = self.__dApi.getMandatoryCode(self.__currentCategoryName, attributeName)
            if val is not None and val.upper() in ['Y', 'YES']:
                rL.append(attributeName)
        return rL

    def __getAltMandatoryAttributeList(self):
        rL = []
        for attributeName in self.__currentAttributeNameList:
            val = self.__dApi.getMandatoryCodeAlt(self.__currentCategoryName, attributeName)
            if val is not None and val.upper() in ['Y', 'YES']:
                rL.append(attributeName)
        return rL

    def __setCategory(self, categoryName):
        """  Set the current category.
        """
        self.__currentCategoryName = categoryName
        self.__currentAttributeNameList = []
        self.__currentAttributeD = {}
        try:
            self.__currentAttributeNameList = sorted(list(set(self.__categoryIndexD[categoryName])))
            for idx, attributeName in enumerate(self.__currentAttributeNameList):
                if attributeName not in self.__currentAttributeD:
                    self.__currentAttributeD[attributeName] = idx
        except Exception as e:
            pass

    def __getParentList(self, itemName):
        try:
            return self.__parentD[itemName]
        except Exception as e:
            return []

    def __getUltimateParent(self, category, attribute):
        """  Return the item(s) at the root of the parent-child tree.
        """
        ok = True
        itemName = "_" + category + "." + attribute
        iGen = 0
        while ok:
            pL = self.__getParentList(itemName)
            #logger.debug("PdbxDictionaryInfo(getUltimateParent): item %s  parent list %r\n" % (itemName,pL))
            if (len(pL) > 0):
                iGen += 1
                itemName = pL[0]
            else:
                ok = False

        return (iGen, self.__categoryPart(itemName), self.__attributePart(itemName))

    def __getAttributeIndex(self, attributeName):
        try:
            return self.__currentAttributeD[attributeName]
        except Exception as e:
            return -1

    def __getItemIndex(self, itemName):
        try:
            return self.__currentAttributeD[self.__attributePart(itemName)]
        except Exception as e:
            return -1

    def __attributePart(self, name):
        i = name.find(".")
        if i == -1:
            return None
        else:
            return name[i + 1:]

    def __categoryPart(self, name):
        tname = ""
        if name.startswith("_"):
            tname = name[1:]
        else:
            tname = name

        i = tname.find(".")
        if i == -1:
            return tname
        else:
            return tname[:i]


class PdbxDictionaryInfoStore(object):
    """ Manage the persistent store of repackaged dictionary and view metadata.

    """

    def __init__(self, verbose=True, log=sys.stderr):
        self.__verbose = verbose
        self.__debug = True
        self.__lfh = log
        #
        # Parameters to tune lock file management --
        self.__timeoutSeconds = 10
        self.__retrySeconds = 0.2
        # placeholder for LockFile object for open/close methods
        self.__lockObj = None
        self.__isExpired = True
        #
        self.__db = None
        #

    def open(self, dbFileName="my.db", flag='r'):
        """ Open the persistent store with the input database file name and access mode.

            flag = 'r read-only'
                   'c/n new/create'
                   'w read/write'
        """
        try:
            self.__lockObj = LockFile(dbFileName, timeoutSeconds=self.__timeoutSeconds, retrySeconds=self.__retrySeconds,
                                      verbose=self.__verbose, log=self.__lfh)
            self.__lockObj.acquire()
            self.__db = shelve.open(dbFileName, flag=flag, protocol=pickle.HIGHEST_PROTOCOL)
            return True
        except Exception as e:
            if self.__lockObj is not None:
                self.__lockObj.release()
            if (self.__verbose):
                logger.debug("+ERROR- PdbxDictInfoStore.open() write failed for file %s\n" % dbFileName)
            if (self.__debug):
                logger.exception("Failing with %s" % str(e))
            return False

    def close(self):
        """ Close the persistent store
        """
        try:
            self.__db.shelve.close()
            if self.__lockObj is not None:
                self.__lockObj.release()
            return True
        except Exception as e:
            if self.__lockObj is not None:
                self.__lockObj.release()
            return False

    def moveStore(self, srcDbFilePath, dstDbFilePath):
        """ Move source store to destination store with destination locking.

            No locking is performed on the source file.
        """
        with LockFile(dstDbFilePath, timeoutSeconds=self.__timeoutSeconds, retrySeconds=self.__retrySeconds, verbose=self.__verbose, log=self.__lfh) as lf:
            retVal = self.__moveStore(srcDbFilePath, dstDbFilePath)
        return retVal

    def store(self, dbFileName="my.db", od=None, ov=None):
        """ Store the input object dictionary and optional view object in persistent database
        """
        with LockFile(dbFileName, timeoutSeconds=self.__timeoutSeconds, retrySeconds=self.__retrySeconds, verbose=self.__verbose, log=self.__lfh) as lf:
            retVal = self.__storeShelve(dbFileName, od=od, ov=ov)
        return retVal

    def getIndex(self, dbFileName="my.db"):
        """ Recover the index of the persistent store.
        """
        with LockFile(dbFileName, timeoutSeconds=self.__timeoutSeconds, retrySeconds=self.__retrySeconds, verbose=self.__verbose, log=self.__lfh) as lf:
            retVal = self.__indexShelve(dbFileName)
        return retVal

    def fetchOneObject(self, dbFileName="my.db", objectName=None):
        """  Fetch a single object from a named container.  This is atomic operation with respect to the store.
        """
        with LockFile(dbFileName, timeoutSeconds=self.__timeoutSeconds, retrySeconds=self.__retrySeconds, verbose=self.__verbose, log=self.__lfh) as lf:
            retVal = self.__fetchOneObjectShelve(dbFileName, objectName)
        return retVal

    def fetchViewObject(self, dbFileName="my.db"):
        """  Fetch a single object from a named container.  This is atomic operation with respect to the store.
        """
        with LockFile(dbFileName, timeoutSeconds=self.__timeoutSeconds, retrySeconds=self.__retrySeconds, verbose=self.__verbose, log=self.__lfh) as lf:
            retVal = self.__fetchOneObjectShelve(dbFileName, objectName="__view__")
        return retVal

    def fetchObject(self, objectName=None):
        """ Fetch object from container from an open store.

            Use this method to extract multiple objects from a store.
        """
        return self.__fetchObjectShelve(objectName)

    def __moveStore(self, src, dst):
        """  Internal method to perform file move.
        """
        try:
            shutil.move(src, dst)
            return True
        except Exception as e:
            if (self.__verbose):
                logger.error("+ERROR- PdbxDictInfoStore.__moveStore() move failed for file %s\n" % src)
            if (self.__debug):
                logger.exception("Failing with %s" % str(e))
            return False

    def __storeShelve(self, dbFileName="my.db", od=None, ov=None):
        """  Create a new persistent store using the internal object dictionary and optional view object dictionary.
        """
        if od is None:
            return False

        try:
            db = shelve.open(dbFileName, flag='c', protocol=pickle.HIGHEST_PROTOCOL)
            for k, v in od.items():
                db[k] = od[k]
            db['__index__'] = list(od.keys())
            db['__view__'] = ov
            db.close()
            return True
        except Exception as e:
            if (self.__verbose):
                logger.error("+ERROR- PdbxDictInfoStore.__storeShelve() shelve store failed for file %s\n" % dbFileName)
            if (self.__debug):
                logger.exception("Failing with %s" % str(e))
            return False

    def __indexShelve(self, dbFileName="my.db"):
        """  Recover the index/list of objects in the persistent store.
        """
        try:
            indexL = []
            db = shelve.open(dbFileName, flag='r', protocol=pickle.HIGHEST_PROTOCOL)
            indexL = db['__index__']
            db.close()
            return indexL
        except Exception as e:
            if (self.__verbose):
                logger.error("+ERROR- PdbxDictInfoStore.__indexShelve() shelve index failed for file %s\n" % dbFileName)
            if (self.__debug):
                logger.exception("Failing with %s" % str(e))
            return {}

    def __fetchOneObjectShelve(self, dbFileName="my.db", objectName=None):
        """ Recover the object from from persistent store corresponding to the
            object name.
        """
        try:
            #
            db = shelve.open(dbFileName, flag='r', protocol=pickle.HIGHEST_PROTOCOL)
            d = db[objectName]
            db.close()
            return d
        except Exception as e:
            if (self.__verbose):
                logger.error("+ERROR- PdbxDictInfoStore.__fetchOneObjectShelve() shelve fetch failed for file %s %s\n"
                             % (dbFileName, objectName))
            if (self.__debug):
                logger.exception("Failing with %s" % str(e))
            return None

    def __fetchObjectShelve(self, objectName=None):
        """ Recover the object from from persistent store corresponding to the
            input object name.

            shelve store must be opened from prior call.
        """
        try:
            d = self.__db[objectName]
            return d
        except Exception as e:
            if (self.__debug):
                logger.error("+ERROR- PdbxDictInfoStore.__fetchObjectShelve() shelve fetch failed %s\n"
                             % (objectName))
            if (self.__debug):
                logger.exception("Failing with %s" % str(e))
            #
            return None

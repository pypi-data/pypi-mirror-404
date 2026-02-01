##
# File: FilterCif.py
# Date: 2016-05-05
#
# Updates:
##
"""Methods for filtering an mmCIF to remove individual items and
categories based on a parsed file already in memory from an IoAdapter
"""

import sys
import copy
import logging
logger = logging.getLogger(__name__)


from mmcif.api.PdbxContainers import CifName
from mmcif.api.DataCategory import DataCategory


class FilterCif(object):
    """ Cif filtering tool"""

    def __init__(self, verbose=False,
                 log=sys.stderr):
        """
        :param 'verbose': boolean flag to activate verbose logging
        :param 'log': open stream for logging
        :param 'IoAdapter' : Adapater for I/O of dictionary
        """
        self.__verbose = verbose
        self.__debug = True
        self.__lfh = log
        # Dictionaries indexed by mode
        self.__allCategories = {}
        self.__substituteItems = {}
        self.__excludeItems = {}
        self.__excludeCategories = {}
        self.__filterTags = []

    def setFilterSubstitutionDict(self, substDL):
        """Given a dictionary category describing the substitution, internalises it"""

        try:
            for sF in substDL:
                if (('item_name' in sF) and ('value' in sF) and ('mode' in sF) and ('tag' in sF)):
                    mode = sF['mode']
                    itemName = sF['item_name']
                    tag = sF['tag']
                    value = sF['value']
                    cat = CifName.categoryPart(itemName)
                    attr = CifName.attributePart(itemName)

                    self.__substituteItems.setdefault(mode, {})
                    self.__substituteItems[mode].setdefault(cat, {})
                    self.__substituteItems[mode][cat][attr] = [tag, value]

                    # Update list of categories to operate on
                    self.__allCategories.setdefault(mode, set())
                    self.__allCategories[mode].add(cat)
            return True
        except Exception as e:
            logger.exception("Failing with %s" % str(e))

        return False

    def setFilterItemExclusionDict(self, excludeDL):
        """Given a dictionary category describing the substitution, internalises it"""

        try:
            for eI in excludeDL:
                if (('item_id' in eI) and ('mode' in eI) and ('tag' in eI)):
                    mode = eI['mode']
                    itemId = eI['item_id']
                    tag = eI['tag']
                    cat = CifName.categoryPart(itemId)
                    attr = CifName.attributePart(itemId)

                    self.__excludeItems.setdefault(mode, {})
                    self.__excludeItems[mode].setdefault(cat, {})
                    self.__excludeItems[mode][cat][attr] = tag

                    # Update list of categories to operate on
                    self.__allCategories.setdefault(mode, set())
                    self.__allCategories[mode].add(cat)
            return True
        except Exception as e:
            logger.exception("Failing with %s" % str(e))

    def setFilterCategoryExclusionDict(self, excludeDL):
        """Given a dictionary category describing the substitution, internalises it"""

        try:
            for eI in excludeDL:
                if (('category_id' in eI) and ('mode' in eI) and ('tag' in eI)):
                    mode = eI['mode']
                    catId = eI['category_id']
                    tag = eI['tag']

                    # Removes the underscore
                    cat = CifName.categoryPart(catId)
                    self.__excludeCategories.setdefault(mode, {})
                    self.__excludeCategories[mode].setdefault(cat, {})
                    self.__excludeCategories[mode][cat] = tag

                    # Update list of categories to operate on
                    self.__allCategories.setdefault(mode, set())
                    self.__allCategories[mode].add(cat)
            return True
        except Exception as e:
            logger.exception("Failing with %s" % str(e))

    def setFilterTagList(self, tagList=[]):
        """Sets the filter context for filtering"""
        if not tagList or None in tagList:
            tagList = []
        self.__filterTags = tagList

    def filter(self, inpContainer, outContainer, mode):
        """Filters the object in memory and returns a new one.   Note - in memory objects may be updated due to data structure sharing"""

        allCats = self.__allCategories.get(mode, [])
        substItems = self.__substituteItems.get(mode, {})
        excludeItems = self.__excludeItems.get(mode, {})
        excludeCats = self.__excludeCategories.get(mode, {})

        for inpObjName in inpContainer.getObjNameList():
            srcCatObj = inpContainer.getObj(inpObjName)

            if inpObjName not in allCats:
                # Shortcut - not in an effected category
                outContainer.append(srcCatObj)
                continue

            # Check filtering of category
            catName = srcCatObj.getName()

            if excludeCats.get(catName, None) in self.__filterTags:
                # Exclude category from output - skip
                continue

            copyCategory = False

            # Check if removing an attribute
            if catName in excludeItems:
                filterAttrs = []
                for item, tag in excludeItems[catName].items():
                    if tag in self.__filterTags:
                        filterAttrs.append(item)

                # Are there attributes to filter?
                if len(filterAttrs) != 0:
                    if len(filterAttrs) == len(srcCatObj.getAttributeList()):
                        # Category will be empty - skip copy
                        continue

                    if not copyCategory:
                        dstCatObj = self.__copyCatObj(srcCatObj)
                        copyCategory = True

                    for attr in filterAttrs:
                        dstCatObj.removeAttribute(attr)

            # Check if substitutions needed
            if catName in substItems:
                for item, tagTup in substItems[catName].items():
                    tag = tagTup[0]
                    value = tagTup[1]
                    if tag in self.__filterTags and srcCatObj.hasAttribute(item):
                        if not copyCategory:
                            dstCatObj = self.__copyCatObj(srcCatObj)
                            copyCategory = True

                        # Check again - as we may have tossed the attribute in
                        # item filtering
                        if dstCatObj.hasAttribute(item):
                            for row in range(dstCatObj.getRowCount()):
                                dstCatObj.setValue(value, item, row)

            # Copy data to output
            if copyCategory:
                outContainer.append(dstCatObj)
            else:
                outContainer.append(srcCatObj)

        return True

    def __copyCatObj(self, srcCatObj):
        """Copyies the data contents so original left intact"""
        outCatObj = DataCategory(srcCatObj.getName(),
                                 list(srcCatObj.getAttributeList()),
                                 copy.deepcopy(srcCatObj.getRowList()))

        return outCatObj

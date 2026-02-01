##
# File: DictionaryMapper.py
# Date: 22-Jun-2015  John Westbrook
#
# Updates:
#  24-Jun-2015  jdw add parent self mapping
##
"""
Accessors for item-level mapping information between dictionary versions.

"""
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "john.westbrook@rcsb.org"
__license__ = "Apache 2.0"


import sys
import logging
logger = logging.getLogger(__name__)

from mmcif.api.PdbxContainers import CifName


class DictionaryMapper(object):

    """ Methods for accessing category and item-level mapping information --- .
    """

    def __init__(self, verbose=True, log=sys.stderr):
        self.__verbose = verbose
        self.__debug = False
        self.__lfh = log
        # for each source and destination category the list of corresponding/mapped categories
        self.__srcCatMap = {}
        self.__dstCatMap = {}
        # for each source and destination category the list of items declared
        self.__srcCatItems = {}
        self.__dstCatItems = {}
        #
        # for each source and destination category the list of key items in a mapped key relation
        self.__srcCatMappedKeyItems = {}
        self.__dstCatMappedKeyItems = {}
        #
        # Item correspondences - for each source category as a dictionary of d[srcItem] = dstItem
        #
        self.__srcCatMappedItems = {}
        #
        # Item correspondences - for each destination category as a dictionary of d[dstItem] = srcItem
        #
        self.__dstCatMappedItems = {}
        #
        #  Source self mapping:   target = src_to_src and type = as_parent
        #
        self.__srcCatParentMappedItems = {}

        #  Destination self mapping:   target = dst_to_dst and type = as_parent
        #
        self.__dstCatParentMappedItems = {}

    def set(self, attrDictList):
        """  Input mapping category (pdbx_dict_item_mapping) data as an attribute dictionary list.
        """
        self.__itemMapCatObj = attrDictList
        self.__build()

    def __build(self):
        """  Create internal data structures supporting the methods in this class -

             Supported map_target/type  -- SRC_TO_DST (AS_KEY,AS_ITEM)
                                           SRC_TO_SRC (FROM_PARENT)
                                           DST_TO_DST (FROM_PARENT)

        """
        for row in self.__itemMapCatObj:
            srcItem = row['item_name_src']
            dstItem = row['item_name_dst']
            if srcItem is None or len(srcItem) == 0 or srcItem in ['.', '?'] or dstItem is None or len(dstItem) == 0 or dstItem in ['.', '?']:
                logger.debug("+DictionaryMapper.__build() - incomplete mapping for %s %s" % (srcItem, dstItem))
                continue
            srcCat = CifName.categoryPart(srcItem)
            dstCat = CifName.categoryPart(dstItem)
            mapType = str(row['map_type']).upper()
            mapTarget = str(row['map_target']).upper()

            #
            #  Special cases for limited self mapping -
            #
            if (mapType == 'FROM_PARENT' and mapTarget == 'DST_TO_DST'):
                if dstCat not in self.__dstCatItems:
                    self.__dstCatItems[dstCat] = []
                if dstItem not in self.__dstCatItems[dstCat]:
                    self.__dstCatItems[dstCat].append(dstItem)

                if dstCat not in self.__dstCatParentMappedItems:
                    self.__dstCatParentMappedItems[dstCat] = {}
                self.__dstCatParentMappedItems[dstCat][dstItem] = srcItem
                continue

            if (mapType == 'FROM_PARENT' and mapTarget == 'SRC_TO_SRC'):

                if srcCat not in self.__srcCatItems:
                    self.__srcCatItems[srcCat] = []
                if srcItem not in self.__srcCatItems[srcCat]:
                    self.__srcCatItems[srcCat].append(srcItem)
                if srcCat not in self.__srcCatParentMappedItems:
                    self.__srcCatParentMappedItems[srcCat] = {}
                self.__srcCatParentMappedItems[srcCat][srcItem] = dstItem
                continue
            #
            if mapTarget not in ['SRC_TO_DST'] and mapType not in ['AS_ITEM', 'AS_KEY']:
                logger.warning("Unsupported mapping for %s %s %s %s" % (srcItem, dstItem, mapType, mapTarget))
                continue
            #
            # For other supported mapping types --
            #
            if srcCat not in self.__srcCatMap:
                self.__srcCatMap[srcCat] = []
            if dstCat not in self.__srcCatMap[srcCat]:
                self.__srcCatMap[srcCat].append(dstCat)

            if srcCat not in self.__srcCatItems:
                self.__srcCatItems[srcCat] = []
            if srcItem not in self.__srcCatItems[srcCat]:
                self.__srcCatItems[srcCat].append(srcItem)

            if dstCat not in self.__dstCatMap:
                self.__dstCatMap[dstCat] = []
            if srcCat not in self.__dstCatMap[dstCat]:
                self.__dstCatMap[dstCat].append(srcCat)
            #
            if dstCat not in self.__dstCatItems:
                self.__dstCatItems[dstCat] = []
            if dstItem not in self.__dstCatItems[dstCat]:
                self.__dstCatItems[dstCat].append(dstItem)
            #
            #
            if mapType == 'AS_KEY':
                if (srcCat, dstCat) not in self.__srcCatMappedKeyItems:
                    self.__srcCatMappedKeyItems[(srcCat, dstCat)] = []
                self.__srcCatMappedKeyItems[(srcCat, dstCat)].append(srcItem)

                if (dstCat, srcCat) not in self.__dstCatMappedKeyItems:
                    self.__dstCatMappedKeyItems[(dstCat, srcCat)] = []
                self.__dstCatMappedKeyItems[(dstCat, srcCat)].append(dstItem)

            if (srcCat, dstCat) not in self.__srcCatMappedItems:
                self.__srcCatMappedItems[(srcCat, dstCat)] = {}
            self.__srcCatMappedItems[(srcCat, dstCat)][srcItem] = dstItem

            if (dstCat, srcCat) not in self.__dstCatMappedItems:
                self.__dstCatMappedItems[(dstCat, srcCat)] = {}
            self.__dstCatMappedItems[(dstCat, srcCat)][dstItem] = srcItem
            #

    def getSrcMappedParentItems(self, srcCatName):
        if srcCatName in self.__srcCatParentMappedItems:
            return self.__srcCatParentMappedItems[srcCatName]
        else:
            return {}

    def getDstMappedParentItems(self, dstCatName):
        if dstCatName in self.__dstCatParentMappedItems:
            return self.__dstCatParentMappedItems[dstCatName]
        else:
            return {}

    def getSrcCategoryList(self):
        """ Return the list of declared source categories.
        """
        return sorted(self.__srcCatMap.keys())

    def getSrcCategoryItemList(self, srcCatName):
        """ Return the list of declared items in the input source category.
        """
        if srcCatName in self.__srcCatItems:
            return self.__srcCatItems[srcCatName]
        else:
            return []

    def getSrcCategoryKeyItemList(self, srcCatName, dstCatName):
        """ Return the list of mapped key items in the input source category.
        """
        if (srcCatName, dstCatName) in self.__srcCatMappedKeyItems:
            return self.__srcCatMappedKeyItems[(srcCatName, dstCatName)]
        else:
            return []

    def getDstCategoryList(self):
        """ Return the list of declared destination categories.
        """
        return sorted(self.__dstCatMap.keys())

    def getDstCategoryItemList(self, dstCatName):
        """ Return the list of declared items in the input destination category.
        """
        if dstCatName in self.__dstCatItems:
            return self.__dstCatItems[dstCatName]
        else:
            return []

    def getDstCategoryKeyItemList(self, dstCatName, srcCatName):
        """ Return the list of mapped key items in the input destination category.
        """
        if (dstCatName, srcCatName) in self.__dstCatMappedKeyItems:
            return self.__dstCatMappedKeyItems[(dstCatName, srcCatName)]
        else:
            return []

    def getMappedCategoryListForSrc(self, srcCatName):
        """  Return the list of destination categories mapped to the input source category.
        """
        if srcCatName in self.__srcCatMap:
            return self.__srcCatMap[srcCatName]
        else:
            return []

    def getMappedItemsForSrc(self, srcCatName, dstCatName):
        """  Return the dictionary of mapped items in the input source category (d[srcItem]=dstItem)
        """
        if (srcCatName, dstCatName) in self.__srcCatMappedItems:
            return self.__srcCatMappedItems[(srcCatName, dstCatName)]
        else:
            return {}

    def getMappedCategoryListForDst(self, dstCatName):
        """  Return the list of source categories mapped to the input destination category.
        """
        if dstCatName in self.__dstCatMap:
            return self.__dstCatMap[dstCatName]
        else:
            return []

    def getMappedItemsForDst(self, dstCatName, srcCatName):
        """  Return the dictionary of mapped items in the input destination category (d[dstItem]=srcItem)
        """
        if (dstCatName, srcCatName) in self.__dstCatMappedItems:
            return self.__dstCatMappedItems[(dstCatName, srcCatName)]
        else:
            return {}

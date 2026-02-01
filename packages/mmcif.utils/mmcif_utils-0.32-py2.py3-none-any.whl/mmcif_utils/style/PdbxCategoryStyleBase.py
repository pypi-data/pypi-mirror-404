##
# File: PdbxCategoryStyleBase.py
# Date: 28-Oct-2012  John Westbrook
#
# Update:
#  4-Nov-2012  jdw  Convert data structure to Functional api for style information.
#                   Provide methods for excluded and suppressed items.
# 11-Feb-2013  jdw  Add style identifier method.
#  5-Mar-2018  jdw Py2-Py3 and refactor for Python Packaging
##
"""
Base functions for accessing presentation style details for PDBx categories.

"""
from __future__ import absolute_import
from __future__ import print_function
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "john.westbrook@rcsb.org"
__license__ = "Apache 2.0"



from mmcif.api.PdbxContainers import CifName


class PdbxCategoryStyleBase(object):

    ''' Base class for essential details for standardizing the presentation style of
        PDBx category data.

        styleId:

        __styleId

        catFormaL:

        __cL=[('<categoryName_1', 'style{table|key-value}', ('<categoryName_2>', 'style'),... ]

        catItemD:

        __cD={ <categoryName_1> : [ (itemName_1,feature1, feature2, ... ),(itemName_2,feature1, feature2, ... ), ... ],
              <categoryName_2> : [ (itemName_1,feature1, feature2, ... ),(itemName_2,feature1, feature2, ... ), ... ]
            }

         excludeList:
                      items separately flagged as candidates for exclusion -
         __excludeList-[itemName_1,itemName_2,... ]

         suppressList:
                              items separately flagged as candidates for value suppression-
         __suppressList=[itemname_1, itemName_2, ...]

    '''

    def __init__(self, styleId=None, catFormatL=None, catItemD=None, excludeList=None, suppressList=None):

        self.__styleId = styleId
        self.__cD = catItemD if catItemD is not None else {}
        self.__cL = catFormatL if catFormatL is not None else []
        self.__excludeList = excludeList if excludeList is not None else []
        self.__suppressList = suppressList if suppressList is not None else []
        #
        self.__indexExclude = {}
        for item in self.__excludeList:
            categoryName = CifName.categoryPart(item)
            if categoryName not in self.__indexExclude:
                self.__indexExclude[categoryName] = []
            self.__indexExclude[categoryName].append(CifName.attributePart(item))
        #
        self.__indexSuppress = {}
        for item in self.__suppressList:
            categoryName = CifName.categoryPart(item)
            if categoryName not in self.__indexSuppress:
                self.__indexSuppress[categoryName] = []
            self.__indexSuppress[categoryName].append(CifName.attributePart(item))
        #

    def getStyleId(self):
        """  Return an identifier for this style definition -
        """
        return self.__styleId

    def getExcludedList(self, categoryName):
        """ Return the list of excluded attributes or an empty list
        """
        try:
            return self.__indexExclude[categoryName]
        except Exception as e:
            return []

    def getSuppressList(self, categoryName):
        """ Return the list of suppress attributes or an empty list
        """
        try:
            return self.__indexSuppress[categoryName]
        except Exception as e:
            return []

    def checkStyleDefinition(self, ofh):
        """ Report internal consistency issues with the current style definition.

            Return True if ok or False otherwise

        """
        # category consistency.
        #
        missing = 0
        cDefList = list(self.__cD.keys())
        cFormatList = []
        for (categoryName, st) in self.__cL:
            cFormatList.append(categoryName)
            if categoryName not in cDefList:
                ofh.write("+WARN PdbxCategoryStyleBase.checkStyleDefinition - missing category in dictionary %s\n" % categoryName)
                missing += 1
        for categoryName in cDefList:
            if categoryName not in cFormatList:
                ofh.write("+WARN PdbxCategoryStyleBase.checkStyleDefinition - missing category in format list %s\n" % categoryName)
                missing += 1
        #
        for itemName in self.__excludeList:
            categoryName = CifName.categoryPart(itemName)
            if ((categoryName not in cFormatList) or (categoryName not in cDefList)):
                ofh.write("+WARN PdbxCategoryStyleBase.checkStyleDefinition - missing excluded category %s\n" % categoryName)
                missing += 1

            if itemName not in [itTup[0] for itTup in self.__cD[categoryName]]:
                ofh.write("+WARN PdbxCategoryStyleBase.checkStyleDefinition - missing excluded item %s\n" % itemName)
                missing += 1

        for itemName in self.__suppressList:
            categoryName = CifName.categoryPart(itemName)
            if ((categoryName not in cFormatList) or (categoryName not in cDefList)):
                ofh.write("+WARN PdbxCategoryStyleBase.checkStyleDefinition - missing suppressed category %s\n" % categoryName)
                missing += 1

            if itemName not in [itTup[0] for itTup in self.__cD[categoryName]]:
                ofh.write("+WARN PdbxCategoryStyleBase.checkStyleDefinition - missing suppressed item %s\n" % itemName)
                missing += 1

        return (missing == 0)

    def getCategoryList(self):
        """  Return an ordered list of categories.
        """
        try:
            return [tp[0] for tp in self.__cL]
        except Exception as e:
            print(self.__cL)
            return []

    def getItemNameList(self, categoryName):
        """
        """
        try:
            return [tp[0] for tp in self.__cD[categoryName]]
        except Exception as e:
            return []

    def getAttributeNameList(self, categoryName):
        """
        """
        try:
            return [CifName.attributePart(tp[0]) for tp in self.__cD[categoryName]]
        except Exception as e:
            return []

    def isItemExcluded(self, itemName):
        return (itemName in self.__excludeList)

    def isItemSuppressed(self, itemName):
        return (itemName in self.__suppressList)

    def isAttributeExcluded(self, categoryName, attributeName):
        return (CifName.itemName(categoryName, attribute) in self.__excludeList)

    def isAttributeSuppressed(self, categoryName, attributeName):
        return (CifName.itemName(categoryName, attribute) in self.__suppressList)

    def getItemNameAndDefaultList(self, categoryName):
        """  Return an ordered list of (itemName,defaultValue) tuples for the input category.
        """
        try:
            return [(tp[0], tp[3]) for tp in self.__cD[categoryName]]
        except Exception as e:
            return []

    def getItemNameTypeAndDefaultList(self, categoryName):
        """  Return an ordered list of (itemName,defaultValue) tuples for the input category.
        """
        try:
            return [(tp[0], tp[2], tp[3]) for tp in self.__cD[categoryName]]
        except Exception as e:
            return []

##
# File:  make-style-from-item-list.py
# Date:  Mar 5, 2018 jdw
#
# Create a template style definition from a list of mmCIF data items-
#
from __future__ import absolute_import
import sys
from mmcif.api.PdbxContainers import CifName

itemFileName = 'ITEMS'
with open(itemFileName, 'r') as ifh:
    #
    itList = []
    for line in ifh:
        itList.append(str(line[:-1]))

cList = []
iD = {}
for it in itList:
    catName = CifName.categoryPart(it)
    #
    if catName not in iD:
        cList.append(catName)
        iD[catName] = []
    iD[catName].append(it)

#
r = '''
##
# File: PdbxPLACEHOLDERCategoryStyle.py
# Date: 00-Mon-2015  J. Westbrook
#
# Updates:
#
##
"""
Abbreviated PDBx style defining data categories containing ....  details.

"""
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "john.westbrook@rcsb.org"
__license__ = "Apache 2.0"



from mmcif_utils.style.PdbxCategoryStyleBase import PdbxCategoryStyleBase

class PdbxPLACEHOLDERCategoryStyle(PdbxCategoryStyleBase):
'''

sys.stdout.write("%s\n" % r)
sys.stdout.write("_styleId = 'PDBX_STYLE_PLACEHOLDER_V1'\n")
sys.stdout.write("_categoryInfo = [\n")
for catName in cList:
    sys.stdout.write("    ('%s', 'table'),\n" % catName)
sys.stdout.write("    ]\n")


sys.stdout.write("_cDict = {\n")
for catName in cList:
    sys.stdout.write("'%s': [\n" % catName)
    for it in iD[catName]:
        sys.stdout.write("    ('%s', '%%s', 'str', ''),\n" % (it))
    sys.stdout.write("     ],\n")
sys.stdout.write("    }\n")
#
sys.stdout.write("  _excludeList = []\n")
sys.stdout.write("  _suppressList = []\n")
r = '''
    #

    def __init__(self):
        super(PdbxPLACEHOLDERCategoryStyle, self).__init__(styleId=PdbxPLACEHOLDERCategoryStyle._styleId,
                                                         catFormatL=PdbxPLACEHOLDERCategoryStyle._categoryInfo,
                                                         catItemD=PdbxPLACEHOLDERCategoryStyle._cDict,
                                                         excludeList=PdbxPLACEHOLDERCategoryStyle._excludeList,
                                                         suppressList=PdbxPLACEHOLDERCategoryStyle._suppressList)
'''

sys.stdout.write("%s\n" % r)

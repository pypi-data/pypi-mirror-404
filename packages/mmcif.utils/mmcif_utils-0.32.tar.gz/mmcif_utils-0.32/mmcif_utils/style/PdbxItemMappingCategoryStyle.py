##
# File: PdbxItemMappingCategoryStyle.py
# Date: 11-July-2015  J. Westbrook
#
# Updates:
#  20-July-2015   jdw  add category pdbx_dict_item_mapping_audit
#    5-Mar-2018   jdw Py2-Py3 and refactor for Python Packaging
##
"""
Abbreviated PDBx style defining data categories related to mapping data between dictionary versions.

"""
from __future__ import absolute_import
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "john.westbrook@rcsb.org"
__license__ = "Apache 2.0"



from mmcif_utils.style.PdbxCategoryStyleBase import PdbxCategoryStyleBase


class PdbxItemMappingCategoryStyle(PdbxCategoryStyleBase):
    _styleId = "PDBX_DICT_ITEM_MAPPING_V1"
    _categoryInfo = [
        ('pdbx_dict_item_mapping', 'table'),
        ('pdbx_dict_item_mapping_audit', 'table'),
        ('pdbx_dict_item_substitution', 'table'),
        ('pdbx_dict_item_exclusion', 'table'),
        ('pdbx_dict_category_exclusion', 'table'),
    ]
    _cDict = {
        'pdbx_dict_item_mapping': [
            ('_pdbx_dict_item_mapping.item_name_src', '%s', 'str', ''),
            ('_pdbx_dict_item_mapping.item_name_dst', '%s', 'str', ''),
            ('_pdbx_dict_item_mapping.map_target', '%s', 'str', ''),
            ('_pdbx_dict_item_mapping.map_type', '%s', 'str', '')
        ],
        'pdbx_dict_item_mapping_audit': [
            ('_pdbx_dict_item_mapping_audit.mode', '%s', 'str', ''),
            ('_pdbx_dict_item_mapping_audit.action', '%s', 'str', ''),
            ('_pdbx_dict_item_mapping_audit.extension_dict_name', '%s', 'str', ''),
            ('_pdbx_dict_item_mapping_audit.extension_dict_version', '%s', 'str', ''),
            ('_pdbx_dict_item_mapping_audit.extension_dict_location', '%s', 'str', '')
        ],
        'pdbx_dict_item_substitution': [
            ('_pdbx_dict_item_substitution.item_name', '%s', 'str', ''),
            ('_pdbx_dict_item_substitution.value', '%s', 'str', ''),
            ('_pdbx_dict_item_substitution.mode', '%s', 'str', ''),
            ('_pdbx_dict_item_substitution.tag', '%s', 'str', '')
        ],
        'pdbx_dict_item_exclusion': [
            ('_pdbx_dict_item_exclusion.item_id', '%s', 'str', ''),
            ('_pdbx_dict_item_exclusion.mode', '%s', 'str', ''),
            ('_pdbx_dict_item_exclusion.tag', '%s', 'str', '')
        ],
        'pdbx_dict_category_exclusion': [
            ('_pdbx_dict_category_exclusion.category_id', '%s', 'str', ''),
            ('_pdbx_dict_category_exclusion.mode', '%s', 'str', ''),
            ('_pdbx_dict_category_exclusion.tag', '%s', 'str', '')
        ],
    }
    _excludeList = []
    _suppressList = []
    #

    def __init__(self):
        super(PdbxItemMappingCategoryStyle, self).__init__(styleId=PdbxItemMappingCategoryStyle._styleId,
                                                           catFormatL=PdbxItemMappingCategoryStyle._categoryInfo,
                                                           catItemD=PdbxItemMappingCategoryStyle._cDict,
                                                           excludeList=PdbxItemMappingCategoryStyle._excludeList,
                                                           suppressList=PdbxItemMappingCategoryStyle._suppressList)

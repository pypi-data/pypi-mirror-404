##
# File: PdbxStatusHistoryCategoryStyle.py
# Date: 7-July-2014  J. Westbrook
#
# Updates:
#     11-Dec-2014  jdw  make status --> status_begin/status_end
#      6-Jan-2015  jdw  add pdb_id
#      5-Mar-2018  jdw Py2-Py3 and refactor for Python Packaging
##
"""
Abbreviated PDBx style defining data categories containing status history  details.

"""
from __future__ import absolute_import
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "john.westbrook@rcsb.org"
__license__ = "Apache 2.0"



from mmcif_utils.style.PdbxCategoryStyleBase import PdbxCategoryStyleBase


class PdbxStatusHistoryCategoryStyle(PdbxCategoryStyleBase):
    _styleId = "PDBX_STATUS_HISTORY_V1"
    _categoryInfo = [
        ('pdbx_database_status_history', 'table'),
    ]
    _cDict = {
        'pdbx_database_status_history': [
            ('_pdbx_database_status_history.entry_id', '%s', 'str', ''),
            ('_pdbx_database_status_history.pdb_id', '%s', 'str', ''),
            ('_pdbx_database_status_history.ordinal', '%s', 'str', ''),
            ('_pdbx_database_status_history.date_begin', '%s', 'str', ''),
            ('_pdbx_database_status_history.date_end', '%s', 'str', ''),
            ('_pdbx_database_status_history.status_code_begin', '%s', 'str', ''),
            ('_pdbx_database_status_history.status_code_end', '%s', 'str', ''),
            ('_pdbx_database_status_history.annotator', '%s', 'str', ''),
            ('_pdbx_database_status_history.details', '%s', 'str', ''),
            ('_pdbx_database_status_history.delta_days', '%.4f', 'str', '')
        ]
    }

    _excludeList = []
    _suppressList = []
    #

    def __init__(self):
        super(PdbxStatusHistoryCategoryStyle, self).__init__(styleId=PdbxStatusHistoryCategoryStyle._styleId,
                                                             catFormatL=PdbxStatusHistoryCategoryStyle._categoryInfo,
                                                             catItemD=PdbxStatusHistoryCategoryStyle._cDict,
                                                             excludeList=PdbxStatusHistoryCategoryStyle._excludeList,
                                                             suppressList=PdbxStatusHistoryCategoryStyle._suppressList)

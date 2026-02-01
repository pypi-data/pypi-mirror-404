##
# File: PdbxLocalMapIndexCategoryStyle.py
# Date:17-July-2014  J. Westbrook
#
# Updates:
#   5-Mar-2018  jdw Py2-Py3 and refactor for Python Packaging
#
##
"""
Abbreviated PDBx style defining data categories in the local map index.

"""
from __future__ import absolute_import
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "john.westbrook@rcsb.org"
__license__ = "Apache 2.0"



from mmcif_utils.style.PdbxCategoryStyleBase import PdbxCategoryStyleBase


class PdbxLocalMapIndexCategoryStyle(PdbxCategoryStyleBase):
    _styleId = "PDBX_LOCAL_MAP_INDEX_V1"
    _categoryInfo = [
        ('dcc_ligand', 'table'),
    ]
    _cDict = {
        'dcc_ligand': [
            ('_dcc_ligand.id', '%s', 'str', ''),
            ('_dcc_ligand.residue_name', '%s', 'str', ''),
            ('_dcc_ligand.chain_id', '%s', 'str', ''),
            ('_dcc_ligand.dcc_correlation', '%s', 'str', ''),
            ('_dcc_ligand.real_space_R', '%s', 'str', ''),
            ('_dcc_ligand.Biso_mean', '%s', 'str', ''),
            ('_dcc_ligand.occupancy_mean', '%s', 'str', ''),
            ('_dcc_ligand.warning', '%s', 'str', ''),
            ('_dcc_ligand.file_name_map_html', '%s', 'str', ''),
            ('_dcc_ligand.file_name_pdb', '%s', 'str', ''),
            ('_dcc_ligand.file_name_map', '%s', 'str', ''),
            ('_dcc_ligand.file_name_jmol', '%s', 'str', '')
        ]
    }

    _excludeList = []
    _suppressList = []
    #

    def __init__(self):
        super(PdbxLocalMapIndexCategoryStyle, self).__init__(styleId=PdbxLocalMapIndexCategoryStyle._styleId,
                                                             catFormatL=PdbxLocalMapIndexCategoryStyle._categoryInfo,
                                                             catItemD=PdbxLocalMapIndexCategoryStyle._cDict,
                                                             excludeList=PdbxLocalMapIndexCategoryStyle._excludeList,
                                                             suppressList=PdbxLocalMapIndexCategoryStyle._suppressList)

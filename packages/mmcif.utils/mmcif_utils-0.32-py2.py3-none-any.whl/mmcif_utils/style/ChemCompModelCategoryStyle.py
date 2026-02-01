##
# File: ChemCompCategoryModelStyle.py
# Date: 2-Nov-2014  John Westbrook
#
# Updates:
#   5-Mar-2018  jdw Py2-Py3 and refactor for Python Packaging
##
"""
Standard style details for chemical component model data categories describing
 additional coordinate models for chemical components.
"""

from __future__ import absolute_import
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "john.westbrook@rcsb.org"
__license__ = "Apache 2.0"



from mmcif_utils.style.PdbxCategoryStyleBase import PdbxCategoryStyleBase


class ChemCompModelCategoryStyle(PdbxCategoryStyleBase):
    #
    _styleId = "CHEM_COMP_MODEL_V1"

    _categoryInfo = [('pdbx_chem_comp_model', 'key-value'),
                     ('pdbx_chem_comp_model_reference', 'table'),
                     ('pdbx_chem_comp_model_feature', 'table'),
                     ('pdbx_chem_comp_model_atom', 'table'),
                     ('pdbx_chem_comp_model_bond', 'table'),
                     #('pdbx_chem_comp_model_identifier',    'table'),
                     ('pdbx_chem_comp_model_descriptor', 'table'),
                     ('pdbx_chem_comp_model_audit', 'table'),
                     ]
    _cDict = {
        'pdbx_chem_comp_model': [
            ('_pdbx_chem_comp_model.id', '%s', 'str', ''),
            ('_pdbx_chem_comp_model.comp_id', '%s', 'str', ''),
        ],
        'pdbx_chem_comp_model_atom': [
            ('_pdbx_chem_comp_model_atom.model_id', '%s', 'str', ''),
            ('_pdbx_chem_comp_model_atom.atom_id', '%s', 'str', ''),
            ('_pdbx_chem_comp_model_atom.type_symbol', '%s', 'str', ''),
            ('_pdbx_chem_comp_model_atom.charge', '%s', 'str', ''),
            ('_pdbx_chem_comp_model_atom.model_Cartn_x', '%s', 'str', ''),
            ('_pdbx_chem_comp_model_atom.model_Cartn_y', '%s', 'str', ''),
            ('_pdbx_chem_comp_model_atom.model_Cartn_z', '%s', 'str', ''),
            ('_pdbx_chem_comp_model_atom.ordinal_id', '%s', 'str', '')
        ],
        'pdbx_chem_comp_model_bond': [
            ('_pdbx_chem_comp_model_bond.model_id', '%s', 'str', ''),
            ('_pdbx_chem_comp_model_bond.atom_id_1', '%s', 'str', ''),
            ('_pdbx_chem_comp_model_bond.atom_id_2', '%s', 'str', ''),
            ('_pdbx_chem_comp_model_bond.value_order', '%s', 'str', ''),
            ('_pdbx_chem_comp_model_bond.ordinal_id', '%s', 'str', '')
        ],
        'pdbx_chem_comp_model_descriptor': [
            ('_pdbx_chem_comp_model_descriptor.model_id', '%s', 'str', ''),
            ('_pdbx_chem_comp_model_descriptor.type', '%s', 'str', ''),
            #('_pdbx_chem_comp_model_descriptor.program','%s','str',''),
            #('_pdbx_chem_comp_model_descriptor.program_version','%s','str',''),
            ('_pdbx_chem_comp_model_descriptor.descriptor', '%s', 'str', '')
        ],
        'pdbx_chem_comp_model_identifier': [
            ('_pdbx_chem_comp_model_identifier.model_id', '%s', 'str', ''),
            ('_pdbx_chem_comp_model_identifier.type', '%s', 'str', ''),
            #('_pdbx_chem_comp_model_identifier.program',        '%s','str',''),
            #('_pdbx_chem_comp_model_identifier.program_version','%s','str',''),
            ('_pdbx_chem_comp_model_identifier.identifier', '%s', 'str', '')
        ],
        'pdbx_chem_comp_model_audit': [
            ('_pdbx_chem_comp_model_audit.model_id', '%s', 'str', ''),
            ('_pdbx_chem_comp_model_audit.action_type', '%s', 'str', ''),
            ('_pdbx_chem_comp_model_audit.date', '%s', 'str', '')
            # ('_pdbx_chem_comp_model_audit.processing_site', '%s', 'str', ''),
            # ('_pdbx_chem_comp_model_audit.annotator', '%s', 'str', ''),
            # ('_pdbx_chem_comp_model_audit.details', '%s', 'str', '')
        ],
        'pdbx_chem_comp_model_reference': [
            ('_pdbx_chem_comp_model_reference.model_id', '%s', 'str', ''),
            ('_pdbx_chem_comp_model_reference.db_name', '%s', 'str', ''),
            ('_pdbx_chem_comp_model_reference.db_code', '%s', 'str', ''),
        ],

        'pdbx_chem_comp_model_feature': [
            ('_pdbx_chem_comp_model_reference.model_id', '%s', 'str', ''),
            ('_pdbx_chem_comp_model_reference.feature_name', '%s', 'str', ''),
            ('_pdbx_chem_comp_model_reference.feature_value', '%s', 'str', ''),
        ],

    }

    _suppressList = ['_pdbx_chem_comp_model_audit.annotator', '_pdbx_chem_comp_model_audit.details']
    _excludeList = ['_pdbx_chem_comp_model_audit.annotator', '_pdbx_chem_comp_model_audit.details']
    #

    def __init__(self):
        super(ChemCompModelCategoryStyle, self).__init__(styleId=ChemCompModelCategoryStyle._styleId,
                                                         catFormatL=ChemCompModelCategoryStyle._categoryInfo,
                                                         catItemD=ChemCompModelCategoryStyle._cDict,
                                                         excludeList=ChemCompModelCategoryStyle._excludeList,
                                                         suppressList=ChemCompModelCategoryStyle._suppressList)

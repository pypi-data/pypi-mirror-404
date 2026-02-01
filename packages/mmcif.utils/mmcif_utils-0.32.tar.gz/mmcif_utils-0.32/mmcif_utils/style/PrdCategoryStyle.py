##
# File: PrdCategoryStyle.py
# Date: 4-Nov-2012  John Westbrook
#
# Updates:
#  11-Feb-2013 jdw   add style identifier
#   5-Mar-2018  jdw Py2-Py3 and refactor for Python Packaging
##
"""
Standard style details for PRD and Family data categories in the
BIRD dictionary.

"""
from __future__ import absolute_import
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "john.westbrook@rcsb.org"
__license__ = "Apache 2.0"



from mmcif_utils.style.PdbxCategoryStyleBase import PdbxCategoryStyleBase


class PrdCategoryStyle(PdbxCategoryStyleBase):
    _styleId = "BIRD_V1"

    _categoryInfo = [('citation', 'table'),
                     ('citation_author', 'table'),
                     ('pdbx_reference_molecule_family', 'table'),
                     ('pdbx_reference_molecule_list', 'table'),
                     ('pdbx_reference_molecule', 'table'),
                     ('pdbx_reference_entity_list', 'table'),
                     ('pdbx_reference_entity_nonpoly', 'table'),
                     ('pdbx_reference_entity_link', 'table'),
                     ('pdbx_reference_entity_poly_link', 'table'),
                     ('pdbx_reference_entity_poly', 'table'),
                     ('pdbx_reference_entity_poly_seq', 'table'),
                     ('pdbx_reference_entity_sequence', 'table'),
                     ('pdbx_reference_entity_src_nat', 'table'),
                     ('pdbx_reference_molecule_details', 'table'),
                     ('pdbx_reference_molecule_synonyms', 'table'),
                     ('pdbx_reference_entity_subcomponents', 'table'),
                     ('pdbx_reference_molecule_annotation', 'table'),
                     ('pdbx_reference_molecule_features', 'table'),
                     ('pdbx_reference_molecule_related_structures', 'table'),
                     ('pdbx_prd_audit', 'table'),
                     ('pdbx_family_prd_audit', 'table'),
                     ('pdbx_reference_entity_sequence_list', 'table')
                     ]
    _cDict = {
        'citation': [
            ('_citation.id', '%s', 'str', ''),
            ('_citation.title', '%s', 'str', ''),
            ('_citation.journal_abbrev', '%s', 'str', ''),
            ('_citation.journal_volume', '%s', 'str', ''),
            ('_citation.page_first', '%s', 'str', ''),
            ('_citation.page_last', '%s', 'str', ''),
            ('_citation.pdbx_database_id_DOI', '%s', 'str', ''),
            ('_citation.pdbx_database_id_PubMed', '%s', 'str', ''),
            ('_citation.year', '%s', 'str', '')
        ],
        'citation_author': [
            ('_citation_author.citation_id', '%s', 'str', ''),
            ('_citation_author.ordinal', '%s', 'str', ''),
            ('_citation_author.name', '%s', 'str', '')
        ],

        'pdbx_reference_molecule_family': [
            ('_pdbx_reference_molecule_family.family_prd_id', '%s', 'str', ''),
            ('_pdbx_reference_molecule_family.name', '%s', 'str', ''),
            ('_pdbx_reference_molecule_family.release_status', '%s', 'str', ''),
            ('_pdbx_reference_molecule_family.replaces', '%s', 'str', ''),
            ('_pdbx_reference_molecule_family.replaced_by', '%s', 'str', '')
        ],
        'pdbx_reference_molecule_list': [
            ('_pdbx_reference_molecule_list.family_prd_id', '%s', 'str', ''),
            ('_pdbx_reference_molecule_list.prd_id', '%s', 'str', '')
        ],
        'pdbx_reference_molecule': [
            ('_pdbx_reference_molecule.prd_id', '%s', 'str', ''),
            ('_pdbx_reference_molecule.formula_weight', '%s', 'str', ''),
            ('_pdbx_reference_molecule.formula', '%s', 'str', ''),
            ('_pdbx_reference_molecule.type', '%s', 'str', ''),
            ('_pdbx_reference_molecule.type_evidence_code', '%s', 'str', ''),
            ('_pdbx_reference_molecule.class', '%s', 'str', ''),
            ('_pdbx_reference_molecule.class_evidence_code', '%s', 'str', ''),
            ('_pdbx_reference_molecule.name', '%s', 'str', ''),
            ('_pdbx_reference_molecule.represent_as', '%s', 'str', ''),
            ('_pdbx_reference_molecule.chem_comp_id', '%s', 'str', ''),
            ('_pdbx_reference_molecule.compound_details', '%s', 'str', ''),
            ('_pdbx_reference_molecule.description', '%s', 'str', ''),
            ('_pdbx_reference_molecule.representative_PDB_id_code', '%s', 'str', ''),
            ('_pdbx_reference_molecule.release_status', '%s', 'str', ''),
            ('_pdbx_reference_molecule.replaces', '%s', 'str', ''),
            ('_pdbx_reference_molecule.replaced_by', '%s', 'str', '')
        ],
        'pdbx_reference_entity_list': [
            ('_pdbx_reference_entity_list.prd_id', '%s', 'str', ''),
            ('_pdbx_reference_entity_list.ref_entity_id', '%s', 'str', ''),
            ('_pdbx_reference_entity_list.type', '%s', 'str', ''),
            ('_pdbx_reference_entity_list.details', '%s', 'str', ''),
            ('_pdbx_reference_entity_list.component_id', '%s', 'str', '')
        ],
        'pdbx_reference_entity_nonpoly': [
            ('_pdbx_reference_entity_nonpoly.prd_id', '%s', 'str', ''),
            ('_pdbx_reference_entity_nonpoly.ref_entity_id', '%s', 'str', ''),
            ('_pdbx_reference_entity_nonpoly.details', '%s', 'str', ''),
            ('_pdbx_reference_entity_nonpoly.name', '%s', 'str', ''),
            ('_pdbx_reference_entity_nonpoly.chem_comp_id', '%s', 'str', '')
        ],
        'pdbx_reference_entity_link': [
            ('_pdbx_reference_entity_link.prd_id', '%s', 'str', ''),
            ('_pdbx_reference_entity_link.link_id', '%s', 'str', ''),
            ('_pdbx_reference_entity_link.details', '%s', 'str', ''),
            ('_pdbx_reference_entity_link.ref_entity_id_1', '%s', 'str', ''),
            ('_pdbx_reference_entity_link.ref_entity_id_2', '%s', 'str', ''),
            ('_pdbx_reference_entity_link.entity_seq_num_1', '%s', 'str', ''),
            ('_pdbx_reference_entity_link.entity_seq_num_2', '%s', 'str', ''),
            ('_pdbx_reference_entity_link.comp_id_1', '%s', 'str', ''),
            ('_pdbx_reference_entity_link.comp_id_2', '%s', 'str', ''),
            ('_pdbx_reference_entity_link.atom_id_1', '%s', 'str', ''),
            ('_pdbx_reference_entity_link.atom_id_2', '%s', 'str', ''),
            ('_pdbx_reference_entity_link.value_order', '%s', 'str', ''),
            ('_pdbx_reference_entity_link.component_1', '%s', 'str', ''),
            ('_pdbx_reference_entity_link.component_2', '%s', 'str', ''),
            ('_pdbx_reference_entity_link.nonpoly_res_num_1', '%s', 'str', ''),
            ('_pdbx_reference_entity_link.nonpoly_res_num_2', '%s', 'str', ''),
            ('_pdbx_reference_entity_link.link_class', '%s', 'str', '')
        ],
        'pdbx_reference_entity_poly_link': [
            ('_pdbx_reference_entity_poly_link.prd_id', '%s', 'str', ''),
            ('_pdbx_reference_entity_poly_link.link_id', '%s', 'str', ''),
            ('_pdbx_reference_entity_poly_link.details', '%s', 'str', ''),
            ('_pdbx_reference_entity_poly_link.ref_entity_id', '%s', 'str', ''),
            ('_pdbx_reference_entity_poly_link.component_id', '%s', 'str', ''),
            ('_pdbx_reference_entity_poly_link.entity_seq_num_1', '%s', 'str', ''),
            ('_pdbx_reference_entity_poly_link.entity_seq_num_2', '%s', 'str', ''),
            ('_pdbx_reference_entity_poly_link.comp_id_1', '%s', 'str', ''),
            ('_pdbx_reference_entity_poly_link.comp_id_2', '%s', 'str', ''),
            ('_pdbx_reference_entity_poly_link.atom_id_1', '%s', 'str', ''),
            ('_pdbx_reference_entity_poly_link.atom_id_2', '%s', 'str', ''),
            ('_pdbx_reference_entity_poly_link.insert_code_1', '%s', 'str', ''),
            ('_pdbx_reference_entity_poly_link.insert_code_2', '%s', 'str', ''),
            ('_pdbx_reference_entity_poly_link.value_order', '%s', 'str', '')
        ],
        'pdbx_reference_entity_poly': [
            ('_pdbx_reference_entity_poly.prd_id', '%s', 'str', ''),
            ('_pdbx_reference_entity_poly.ref_entity_id', '%s', 'str', ''),
            ('_pdbx_reference_entity_poly.type', '%s', 'str', ''),
            ('_pdbx_reference_entity_poly.db_code', '%s', 'str', ''),
            ('_pdbx_reference_entity_poly.db_name', '%s', 'str', '')
        ],
        'pdbx_reference_entity_poly_seq': [
            ('_pdbx_reference_entity_poly_seq.prd_id', '%s', 'str', ''),
            ('_pdbx_reference_entity_poly_seq.ref_entity_id', '%s', 'str', ''),
            ('_pdbx_reference_entity_poly_seq.mon_id', '%s', 'str', ''),
            ('_pdbx_reference_entity_poly_seq.parent_mon_id', '%s', 'str', ''),
            ('_pdbx_reference_entity_poly_seq.num', '%s', 'str', ''),
            ('_pdbx_reference_entity_poly_seq.observed', '%s', 'str', ''),
            ('_pdbx_reference_entity_poly_seq.hetero', '%s', 'str', '')
        ],
        'pdbx_reference_entity_sequence': [
            ('_pdbx_reference_entity_sequence.prd_id', '%s', 'str', ''),
            ('_pdbx_reference_entity_sequence.ref_entity_id', '%s', 'str', ''),
            ('_pdbx_reference_entity_sequence.type', '%s', 'str', ''),
            ('_pdbx_reference_entity_sequence.NRP_flag', '%s', 'str', ''),
            ('_pdbx_reference_entity_sequence.one_letter_codes', '%s', 'str', '')
        ],
        'pdbx_reference_entity_src_nat': [
            ('_pdbx_reference_entity_src_nat.prd_id', '%s', 'str', ''),
            ('_pdbx_reference_entity_src_nat.ref_entity_id', '%s', 'str', ''),
            ('_pdbx_reference_entity_src_nat.ordinal', '%s', 'str', ''),
            ('_pdbx_reference_entity_src_nat.organism_scientific', '%s', 'str', ''),
            ('_pdbx_reference_entity_src_nat.strain', '%s', 'str', ''),
            ('_pdbx_reference_entity_src_nat.taxid', '%s', 'str', ''),
            ('_pdbx_reference_entity_src_nat.atcc', '%s', 'str', ''),
            ('_pdbx_reference_entity_src_nat.db_code', '%s', 'str', ''),
            ('_pdbx_reference_entity_src_nat.db_name', '%s', 'str', ''),
            ('_pdbx_reference_entity_src_nat.source', '%s', 'str', ''),
            ('_pdbx_reference_entity_src_nat.source_id', '%s', 'str', '')
        ],
        'pdbx_reference_molecule_details': [
            ('_pdbx_reference_molecule_details.family_prd_id', '%s', 'str', ''),
            ('_pdbx_reference_molecule_details.prd_id', '%s', 'str', ''),
            ('_pdbx_reference_molecule_details.ordinal', '%s', 'str', ''),
            ('_pdbx_reference_molecule_details.source', '%s', 'str', ''),
            ('_pdbx_reference_molecule_details.source_id', '%s', 'str', ''),
            ('_pdbx_reference_molecule_details.text', '%s', 'str', '')
        ],
        'pdbx_reference_molecule_synonyms': [
            ('_pdbx_reference_molecule_synonyms.family_prd_id', '%s', 'str', ''),
            ('_pdbx_reference_molecule_synonyms.prd_id', '%s', 'str', ''),
            ('_pdbx_reference_molecule_synonyms.ordinal', '%s', 'str', ''),
            ('_pdbx_reference_molecule_synonyms.name', '%s', 'str', ''),
            ('_pdbx_reference_molecule_synonyms.source', '%s', 'str', ''),
            ('_pdbx_reference_molecule_synonyms.chem_comp_id', '%s', 'str', '')
        ],
        'pdbx_reference_entity_subcomponents': [
            ('_pdbx_reference_entity_subcomponents.prd_id', '%s', 'str', ''),
            ('_pdbx_reference_entity_subcomponents.seq', '%s', 'str', ''),
            ('_pdbx_reference_entity_subcomponents.chem_comp_id', '%s', 'str', '')
        ],
        'pdbx_reference_molecule_annotation': [
            ('_pdbx_reference_molecule_annotation.family_prd_id', '%s', 'str', ''),
            ('_pdbx_reference_molecule_annotation.prd_id', '%s', 'str', ''),
            ('_pdbx_reference_molecule_annotation.ordinal', '%s', 'str', ''),
            ('_pdbx_reference_molecule_annotation.text', '%s', 'str', ''),
            ('_pdbx_reference_molecule_annotation.type', '%s', 'str', ''),
            ('_pdbx_reference_molecule_annotation.support', '%s', 'str', ''),
            ('_pdbx_reference_molecule_annotation.source', '%s', 'str', ''),
            ('_pdbx_reference_molecule_annotation.chem_comp_id', '%s', 'str', '')
        ],
        'pdbx_reference_molecule_features': [
            ('_pdbx_reference_molecule_features.family_prd_id', '%s', 'str', ''),
            ('_pdbx_reference_molecule_features.prd_id', '%s', 'str', ''),
            ('_pdbx_reference_molecule_features.ordinal', '%s', 'str', ''),
            ('_pdbx_reference_molecule_features.source_ordinal', '%s', 'str', ''),
            ('_pdbx_reference_molecule_features.type', '%s', 'str', ''),
            ('_pdbx_reference_molecule_features.value', '%s', 'str', ''),
            ('_pdbx_reference_molecule_features.source', '%s', 'str', ''),
            ('_pdbx_reference_molecule_features.chem_comp_id', '%s', 'str', '')
        ],
        'pdbx_reference_molecule_related_structures': [
            ('_pdbx_reference_molecule_related_structures.family_prd_id', '%s', 'str', ''),
            ('_pdbx_reference_molecule_related_structures.ordinal', '%s', 'str', ''),
            ('_pdbx_reference_molecule_related_structures.db_name', '%s', 'str', ''),
            ('_pdbx_reference_molecule_related_structures.db_code', '%s', 'str', ''),
            ('_pdbx_reference_molecule_related_structures.db_accession', '%s', 'str', ''),
            ('_pdbx_reference_molecule_related_structures.name', '%s', 'str', ''),
            ('_pdbx_reference_molecule_related_structures.formula', '%s', 'str', ''),
            ('_pdbx_reference_molecule_related_structures.citation_id', '%s', 'str', '')
        ],
        'pdbx_prd_audit': [
            ('_pdbx_prd_audit.prd_id', '%s', 'str', ''),
            ('_pdbx_prd_audit.date', '%s', 'str', ''),
            ('_pdbx_prd_audit.annotator', '%s', 'str', ''),
            ('_pdbx_prd_audit.processing_site', '%s', 'str', ''),
            ('_pdbx_prd_audit.details', '%s', 'str', ''),
            ('_pdbx_prd_audit.action_type', '%s', 'str', '')
        ],
        'pdbx_family_prd_audit': [
            ('_pdbx_family_prd_audit.family_prd_id', '%s', 'str', ''),
            ('_pdbx_family_prd_audit.date', '%s', 'str', ''),
            ('_pdbx_family_prd_audit.annotator', '%s', 'str', ''),
            ('_pdbx_family_prd_audit.processing_site', '%s', 'str', ''),
            ('_pdbx_family_prd_audit.details', '%s', 'str', ''),
            ('_pdbx_family_prd_audit.action_type', '%s', 'str', '')
        ],
        'pdbx_reference_entity_sequence_list': [
            ('_pdbx_reference_entity_sequence_list.prd_id', '%s', 'str', ''),
            ('_pdbx_reference_entity_sequence_list.ref_entity_id', '%s', 'str', ''),
            ('_pdbx_reference_entity_sequence_list.v_id', '%s', 'str', ''),
            ('_pdbx_reference_entity_sequence_list.three_letter_codes', '%s', 'str', '')
        ]

    }

    _excludeList = []
    #_excludeList=['_pdbx_family_prd_audit.annotator', '_pdbx_family_prd_audit.details']
    _excludeList = ['_pdbx_prd_audit.annotator', '_pdbx_prd_audit.details', '_pdbx_reference_entity_src_nat.atcc',
                    '_pdbx_reference_entity_src_nat.source_id', '_pdbx_reference_entity_sequence.one_letter_codes']
    _suppressList = []
    #

    def __init__(self):
        super(PrdCategoryStyle, self).__init__(styleId=PrdCategoryStyle._styleId,
                                               catFormatL=PrdCategoryStyle._categoryInfo,
                                               catItemD=PrdCategoryStyle._cDict,
                                               excludeList=PrdCategoryStyle._excludeList,
                                               suppressList=PrdCategoryStyle._suppressList)

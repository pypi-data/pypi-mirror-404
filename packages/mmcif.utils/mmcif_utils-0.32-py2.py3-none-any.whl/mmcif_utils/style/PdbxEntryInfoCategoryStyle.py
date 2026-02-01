##
# File: PdbxEntryInfoCategoryStyle.py
# Date: 12-June-2014  J. Westbrook
#
# Updates:
#
# 09-July-2014  jdw add category 'exptl'
# 14-Apr-2015   jdw add category 'pdbx_depui_entry_details'
# 27-Aug-2015   jdw add category em_admin
#  5-Mar-2018   jdw Py2-Py3 and refactor for Python Packaging

##
"""
Abbreviated PDBx style defining data categories containing essential entry and status details.

"""
from __future__ import absolute_import
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "john.westbrook@rcsb.org"
__license__ = "Apache 2.0"



from mmcif_utils.style.PdbxCategoryStyleBase import PdbxCategoryStyleBase


class PdbxEntryInfoCategoryStyle(PdbxCategoryStyleBase):
    _styleId = "PDBX_ENTRY_INFO_V1"
    _categoryInfo = [
        ('em_admin', 'table'),
        ('audit_contact_author', 'table'),
        ('pdbx_contact_author', 'table'),
        ('pdbx_SG_project', 'table'),
        ('audit_author', 'table'),
        ('pdbx_database_status', 'table'),
        ('pdbx_database_proc', 'table'),
        ('entry', 'table'),
        ('pdbx_entry_details', 'table'),
        ('citation', 'table'),
        ('citation_author', 'table'),
        ('database_2', 'table'),
        ('exptl', 'table'),
        ('struct', 'table'),
        ('pdbx_depui_entry_details', 'table'),
        ('em_depui', 'table')
    ]
    _cDict = {
        'em_admin': [
            ('_em_admin.current_status', '%s', 'str', ''),
            ('_em_admin.deposition_date', '%s', 'str', ''),
            ('_em_admin.deposition_site', '%s', 'str', ''),
            ('_em_admin.details', '%s', 'str', ''),
            ('_em_admin.entry_id', '%s', 'str', ''),
            ('_em_admin.last_update', '%s', 'str', ''),
            ('_em_admin.map_hold_date', '%s', 'str', ''),
            ('_em_admin.map_release_date', '%s', 'str', ''),
            ('_em_admin.header_release_date', '%s', 'str', ''),
            ('_em_admin.obsoleted_date', '%s', 'str', ''),
            ('_em_admin.replace_existing_entry_flag', '%s', 'str', ''),
            ('_em_admin.title', '%s', 'str', ''),
        ],
        'audit_contact_author': [
            ('_audit_contact_author.name', '%s', 'str', ''),
            ('_audit_contact_author.address', '%s', 'str', ''),
            ('_audit_contact_author.phone', '%s', 'str', ''),
            ('_audit_contact_author.fax', '%s', 'str', ''),
            ('_audit_contact_author.email', '%s', 'str', '')
        ],
        'pdbx_contact_author': [
            ('_pdbx_contact_author.id', '%s', 'str', ''),
            ('_pdbx_contact_author.name_salutation', '%s', 'str', ''),
            ('_pdbx_contact_author.name_first', '%s', 'str', ''),
            ('_pdbx_contact_author.name_last', '%s', 'str', ''),
            ('_pdbx_contact_author.name_mi', '%s', 'str', ''),
            ('_pdbx_contact_author.role', '%s', 'str', ''),
            ('_pdbx_contact_author.email', '%s', 'str', ''),
            ('_pdbx_contact_author.phone', '%s', 'str', ''),
            ('_pdbx_contact_author.fax', '%s', 'str', ''),
            ('_pdbx_contact_author.address_1', '%s', 'str', ''),
            ('_pdbx_contact_author.address_2', '%s', 'str', ''),
            ('_pdbx_contact_author.address_3', '%s', 'str', ''),
            ('_pdbx_contact_author.city', '%s', 'str', ''),
            ('_pdbx_contact_author.state_province', '%s', 'str', ''),
            ('_pdbx_contact_author.postal_code', '%s', 'str', ''),
            ('_pdbx_contact_author.country', '%s', 'str', ''),
            ('_pdbx_contact_author.organization_type', '%s', 'str', ''),
            ('_pdbx_contact_author.continent', '%s', 'str', '')
        ],
        'pdbx_SG_project': [
            ('_pdbx_SG_project.id', '%s', 'str', ''),
            ('_pdbx_SG_project.project_name', '%s', 'str', ''),
            ('_pdbx_SG_project.full_name_of_center', '%s', 'str', ''),
            ('_pdbx_SG_project.initial_of_center', '%s', 'str', '')
        ],
        'audit_author': [
            ('_audit_author.name', '%s', 'str', ''),
            ('_audit_author.pdbx_ordinal', '%s', 'str', '')
        ],

        'pdbx_database_status': [
            ('_pdbx_database_status.status_code', '%s', 'str', ''),
            ('_pdbx_database_status.entry_id', '%s', 'str', ''),
            ('_pdbx_database_status.pdbx_tid', '%s', 'str', ''),
            ('_pdbx_database_status.status_coordinates_in_NDB', '%s', 'str', ''),
            ('_pdbx_database_status.recvd_deposit_form', '%s', 'str', ''),
            ('_pdbx_database_status.date_deposition_form', '%s', 'str', ''),
            ('_pdbx_database_status.recvd_coordinates', '%s', 'str', ''),
            ('_pdbx_database_status.date_coordinates', '%s', 'str', ''),
            ('_pdbx_database_status.recvd_struct_fact', '%s', 'str', ''),
            ('_pdbx_database_status.date_struct_fact', '%s', 'str', ''),
            ('_pdbx_database_status.recvd_internal_approval', '%s', 'str', ''),
            ('_pdbx_database_status.recvd_manuscript', '%s', 'str', ''),
            ('_pdbx_database_status.date_manuscript', '%s', 'str', ''),
            ('_pdbx_database_status.name_depositor', '%s', 'str', ''),
            ('_pdbx_database_status.pdbx_annotator', '%s', 'str', ''),
            ('_pdbx_database_status.recvd_author_approval', '%s', 'str', ''),
            ('_pdbx_database_status.date_author_approval', '%s', 'str', ''),
            ('_pdbx_database_status.recvd_initial_deposition_date', '%s', 'str', ''),
            ('_pdbx_database_status.date_submitted', '%s', 'str', ''),
            ('_pdbx_database_status.author_release_status_code', '%s', 'str', ''),
            ('_pdbx_database_status.date_revised', '%s', 'str', ''),
            ('_pdbx_database_status.revision_id', '%s', 'str', ''),
            ('_pdbx_database_status.replaced_entry_id', '%s', 'str', ''),
            ('_pdbx_database_status.revision_description', '%s', 'str', ''),
            ('_pdbx_database_status.date_of_NDB_release', '%s', 'str', ''),
            ('_pdbx_database_status.date_released_to_PDB', '%s', 'str', ''),
            ('_pdbx_database_status.date_of_PDB_release', '%s', 'str', ''),
            ('_pdbx_database_status.date_hold_coordinates', '%s', 'str', ''),
            ('_pdbx_database_status.date_hold_struct_fact', '%s', 'str', ''),
            ('_pdbx_database_status.hold_for_publication', '%s', 'str', ''),
            ('_pdbx_database_status.date_hold_nmr_constraints', '%s', 'str', ''),
            ('_pdbx_database_status.dep_release_code_coordinates', '%s', 'str', ''),
            ('_pdbx_database_status.dep_release_code_struct_fact', '%s', 'str', ''),
            ('_pdbx_database_status.dep_release_code_nmr_constraints', '%s', 'str', ''),
            ('_pdbx_database_status.dep_release_code_sequence', '%s', 'str', ''),
            ('_pdbx_database_status.pdb_date_of_author_approval', '%s', 'str', ''),
            ('_pdbx_database_status.deposit_site', '%s', 'str', ''),
            ('_pdbx_database_status.process_site', '%s', 'str', ''),
            ('_pdbx_database_status.date_of_sf_release', '%s', 'str', ''),
            ('_pdbx_database_status.date_of_mr_release', '%s', 'str', ''),
            ('_pdbx_database_status.status_code_sf', '%s', 'str', ''),
            ('_pdbx_database_status.status_code_mr', '%s', 'str', ''),
            ('_pdbx_database_status.SG_entry', '%s', 'str', ''),
            ('_pdbx_database_status.date_hold_chemical_shifts', '%s', 'str', ''),
            ('_pdbx_database_status.date_chemical_shifts', '%s', 'str', ''),
            ('_pdbx_database_status.recvd_chemical_shifts', '%s', 'str', ''),
            ('_pdbx_database_status.dep_release_code_chemical_shifts', '%s', 'str', ''),
            ('_pdbx_database_status.date_of_cs_release', '%s', 'str', ''),
            ('_pdbx_database_status.status_code_cs', '%s', 'str', ''),
            ('_pdbx_database_status.author_approval_type', '%s', 'str', ''),
            ('_pdbx_database_status.date_nmr_constraints', '%s', 'str', ''),
            ('_pdbx_database_status.recvd_nmr_constraints', '%s', 'str', ''),
            ('_pdbx_database_status.skip_PDB_REMARK_500', '%s', 'str', ''),
            ('_pdbx_database_status.skip_PDB_REMARK', '%s', 'str', ''),
            ('_pdbx_database_status.title_suppression', '%s', 'str', ''),
            ('_pdbx_database_status.methods_development_category', '%s', 'str', '')
        ],

        'pdbx_database_proc': [
            ('_pdbx_database_proc.entry_id', '%s', 'str', ''),
            ('_pdbx_database_proc.cycle_id', '%s', 'str', ''),
            ('_pdbx_database_proc.date_begin_cycle', '%s', 'str', ''),
            ('_pdbx_database_proc.date_end_cycle', '%s', 'str', ''),
            ('_pdbx_database_proc.details', '%s', 'str', '')
        ],

        'entry': [
            ('_entry.id', '%s', 'str', '')
        ],
        'pdbx_entry_details': [
            ('_pdbx_entry_details.entry_id', '%s', 'str', ''),
            ('_pdbx_entry_details.nonpolymer_details', '%s', 'str', ''),
            ('_pdbx_entry_details.sequence_details', '%s', 'str', ''),
            ('_pdbx_entry_details.compound_details', '%s', 'str', ''),
            ('_pdbx_entry_details.source_details', '%s', 'str', '')
        ],
        'pdbx_version': [
            ('_pdbx_version.entry_id', '%s', 'str', ''),
            ('_pdbx_version.revision_date', '%s', 'str', ''),
            ('_pdbx_version.major_version', '%s', 'str', ''),
            ('_pdbx_version.minor_version', '%s', 'str', ''),
            ('_pdbx_version.revision_type', '%s', 'str', ''),
            ('_pdbx_version.details', '%s', 'str', '')
        ],
        'citation': [
            ('_citation.id', '%s', 'str', ''),
            ('_citation.title', '%s', 'str', ''),
            ('_citation.journal_abbrev', '%s', 'str', ''),
            ('_citation.journal_volume', '%s', 'str', ''),
            ('_citation.page_first', '%s', 'str', ''),
            ('_citation.page_last', '%s', 'str', ''),
            ('_citation.year', '%s', 'str', ''),
            ('_citation.journal_id_ASTM', '%s', 'str', ''),
            ('_citation.country', '%s', 'str', ''),
            ('_citation.journal_id_ISSN', '%s', 'str', ''),
            ('_citation.journal_id_CSD', '%s', 'str', ''),
            ('_citation.book_publisher', '%s', 'str', ''),
            ('_citation.pdbx_database_id_PubMed', '%s', 'str', ''),
            ('_citation.pdbx_database_id_DOI', '%s', 'str', '')
        ],

        'citation_author': [
            ('_citation_author.citation_id', '%s', 'str', ''),
            ('_citation_author.name', '%s', 'str', ''),
            ('_citation_author.ordinal', '%s', 'str', '')
        ],
        'database_2': [
            ('_database_2.database_id', '%s', 'str', ''),
            ('_database_2.database_code', '%s', 'str', '')
        ],
        'exptl': [
            ('_exptl.entry_id', '%s', 'str', ''),
            ('_exptl.method', '%s', 'str', ''),
            ('_exptl.crystals_number', '%s', 'str', '')
        ],

        'struct': [
            ('_struct.entry_id', '%s', 'str', ''),
            ('_struct.title', '%s', 'str', ''),
            ('_struct.pdbx_descriptor', '%s', 'str', ''),
            ('_struct.pdbx_model_details', '%s', 'str', ''),
            ('_struct.pdbx_details', '%s', 'str', ''),
            ('_struct.pdbx_CASP_flag', '%s', 'str', ''),
            ('_struct.pdbx_model_type_details', '%s', 'str', '')
        ],
        'pdbx_depui_entry_details': [
            ('_pdbx_depui_entry_details.dep_dataset_id', '%s', 'str', ''),
            ('_pdbx_depui_entry_details.experimental_methods', '%s', 'str', ''),
            ('_pdbx_depui_entry_details.requested_accession_types', '%s', 'str', ''),
            ('_pdbx_depui_entry_details.validated_contact_email', '%s', 'str', ''),
            ('_pdbx_depui_entry_details.country', '%s', 'str', ''),
            ('_pdbx_depui_entry_details.structural_genomics_flag', '%s', 'str', ''),
            ('_pdbx_depui_entry_details.related_database_name', '%s', 'str', ''),
            ('_pdbx_depui_entry_details.related_database_code', '%s', 'str', '')
        ],
        'em_depui': [
            ('_em_depui.depositor_hold_instructions', '%s', 'str', ''),
            ('_em_depui.entry_id', '%s', 'str', ''),
            ('_em_depui.macromolecule_description', '%s', 'str', ''),
            ('_em_depui.obsolete_instructions', '%s', 'str', ''),
            ('_em_depui.same_authors_as_pdb', '%s', 'str', ''),
            ('_em_depui.same_title_as_pdb', '%s', 'str', ''),
        ]
    }

    _excludeList = []
    _suppressList = []
    #

    def __init__(self):
        super(PdbxEntryInfoCategoryStyle, self).__init__(styleId=PdbxEntryInfoCategoryStyle._styleId,
                                                         catFormatL=PdbxEntryInfoCategoryStyle._categoryInfo,
                                                         catItemD=PdbxEntryInfoCategoryStyle._cDict,
                                                         excludeList=PdbxEntryInfoCategoryStyle._excludeList,
                                                         suppressList=PdbxEntryInfoCategoryStyle._suppressList)

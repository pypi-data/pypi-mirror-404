##
# File: PdbxGeometryReportCategoryStyle.py
# Date: 1-Jan-2014
#
# Updates:
#   5-Mar-2018  jdw Py2-Py3 and refactor for Python Packaging
#
##
"""
Report style details for PDBx geometry validation data categories.

"""
from __future__ import absolute_import
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "john.westbrook@rcsb.org"
__license__ = "Apache 2.0"



from mmcif_utils.style.PdbxCategoryStyleBase import PdbxCategoryStyleBase


class PdbxGeometryReportCategoryStyle(PdbxCategoryStyleBase):
    _styleId = "PDBX_GEOMETRY_REPORT_V1"
    _categoryInfo = [
        ('pdbx_validate_close_contact', 'table'),
        ('pdbx_validate_symm_contact', 'table'),
        ('pdbx_validate_rmsd_bond', 'table'),
        ('pdbx_validate_rmsd_angle', 'table'),
        ('pdbx_validate_torsion', 'table'),
        ('pdbx_validate_peptide_omega', 'table'),
        ('pdbx_validate_main_chain_plane', 'table'),
        ('pdbx_validate_polymer_linkage', 'table'),
        ('pdbx_validate_chiral', 'table'),
    ]
    _cDict = {
        'pdbx_validate_close_contact': [
            ('_pdbx_validate_close_contact.id', '%s', 'str', ''),
            ('_pdbx_validate_close_contact.PDB_model_num', '%s', 'str', ''),
            ('_pdbx_validate_close_contact.auth_atom_id_1', '%s', 'str', ''),
            ('_pdbx_validate_close_contact.auth_asym_id_1', '%s', 'str', ''),
            ('_pdbx_validate_close_contact.auth_comp_id_1', '%s', 'str', ''),
            ('_pdbx_validate_close_contact.auth_seq_id_1', '%s', 'str', ''),
            ('_pdbx_validate_close_contact.PDB_ins_code_1', '%s', 'str', ''),
            ('_pdbx_validate_close_contact.label_alt_id_1', '%s', 'str', ''),
            ('_pdbx_validate_close_contact.auth_atom_id_2', '%s', 'str', ''),
            ('_pdbx_validate_close_contact.auth_asym_id_2', '%s', 'str', ''),
            ('_pdbx_validate_close_contact.auth_comp_id_2', '%s', 'str', ''),
            ('_pdbx_validate_close_contact.auth_seq_id_2', '%s', 'str', ''),
            ('_pdbx_validate_close_contact.PDB_ins_code_2', '%s', 'str', ''),
            ('_pdbx_validate_close_contact.label_alt_id_2', '%s', 'str', ''),
            ('_pdbx_validate_close_contact.dist', '%s', 'str', '')
        ],
        'pdbx_validate_symm_contact': [
            ('_pdbx_validate_symm_contact.id', '%s', 'str', ''),
            ('_pdbx_validate_symm_contact.PDB_model_num', '%s', 'str', ''),
            ('_pdbx_validate_symm_contact.auth_atom_id_1', '%s', 'str', ''),
            ('_pdbx_validate_symm_contact.auth_asym_id_1', '%s', 'str', ''),
            ('_pdbx_validate_symm_contact.auth_comp_id_1', '%s', 'str', ''),
            ('_pdbx_validate_symm_contact.auth_seq_id_1', '%s', 'str', ''),
            ('_pdbx_validate_symm_contact.PDB_ins_code_1', '%s', 'str', ''),
            ('_pdbx_validate_symm_contact.label_alt_id_1', '%s', 'str', ''),
            ('_pdbx_validate_symm_contact.site_symmetry_1', '%s', 'str', ''),
            ('_pdbx_validate_symm_contact.auth_atom_id_2', '%s', 'str', ''),
            ('_pdbx_validate_symm_contact.auth_asym_id_2', '%s', 'str', ''),
            ('_pdbx_validate_symm_contact.auth_comp_id_2', '%s', 'str', ''),
            ('_pdbx_validate_symm_contact.auth_seq_id_2', '%s', 'str', ''),
            ('_pdbx_validate_symm_contact.PDB_ins_code_2', '%s', 'str', ''),
            ('_pdbx_validate_symm_contact.label_alt_id_2', '%s', 'str', ''),
            ('_pdbx_validate_symm_contact.site_symmetry_2', '%s', 'str', ''),
            ('_pdbx_validate_symm_contact.dist', '%s', 'str', '')
        ],
        'pdbx_validate_rmsd_bond': [
            ('_pdbx_validate_rmsd_bond.id', '%s', 'str', ''),
            ('_pdbx_validate_rmsd_bond.PDB_model_num', '%s', 'str', ''),
            ('_pdbx_validate_rmsd_bond.auth_atom_id_1', '%s', 'str', ''),
            ('_pdbx_validate_rmsd_bond.auth_asym_id_1', '%s', 'str', ''),
            ('_pdbx_validate_rmsd_bond.auth_comp_id_1', '%s', 'str', ''),
            ('_pdbx_validate_rmsd_bond.auth_seq_id_1', '%s', 'str', ''),
            ('_pdbx_validate_rmsd_bond.PDB_ins_code_1', '%s', 'str', ''),
            ('_pdbx_validate_rmsd_bond.label_alt_id_1', '%s', 'str', ''),
            ('_pdbx_validate_rmsd_bond.auth_atom_id_2', '%s', 'str', ''),
            ('_pdbx_validate_rmsd_bond.auth_asym_id_2', '%s', 'str', ''),
            ('_pdbx_validate_rmsd_bond.auth_comp_id_2', '%s', 'str', ''),
            ('_pdbx_validate_rmsd_bond.auth_seq_id_2', '%s', 'str', ''),
            ('_pdbx_validate_rmsd_bond.PDB_ins_code_2', '%s', 'str', ''),
            ('_pdbx_validate_rmsd_bond.label_alt_id_2', '%s', 'str', ''),
            ('_pdbx_validate_rmsd_bond.bond_value', '%s', 'str', ''),
            ('_pdbx_validate_rmsd_bond.bond_target_value', '%s', 'str', ''),
            ('_pdbx_validate_rmsd_bond.bond_deviation', '%s', 'str', ''),
            ('_pdbx_validate_rmsd_bond.bond_standard_deviation', '%s', 'str', ''),
            ('_pdbx_validate_rmsd_bond.linker_flag', '%s', 'str', '')
        ],
        'pdbx_validate_rmsd_angle': [
            ('_pdbx_validate_rmsd_angle.id', '%s', 'str', ''),
            ('_pdbx_validate_rmsd_angle.PDB_model_num', '%s', 'str', ''),
            ('_pdbx_validate_rmsd_angle.auth_atom_id_1', '%s', 'str', ''),
            ('_pdbx_validate_rmsd_angle.auth_asym_id_1', '%s', 'str', ''),
            ('_pdbx_validate_rmsd_angle.auth_comp_id_1', '%s', 'str', ''),
            ('_pdbx_validate_rmsd_angle.auth_seq_id_1', '%s', 'str', ''),
            ('_pdbx_validate_rmsd_angle.PDB_ins_code_1', '%s', 'str', ''),
            ('_pdbx_validate_rmsd_angle.label_alt_id_1', '%s', 'str', ''),
            ('_pdbx_validate_rmsd_angle.auth_atom_id_2', '%s', 'str', ''),
            ('_pdbx_validate_rmsd_angle.auth_asym_id_2', '%s', 'str', ''),
            ('_pdbx_validate_rmsd_angle.auth_comp_id_2', '%s', 'str', ''),
            ('_pdbx_validate_rmsd_angle.auth_seq_id_2', '%s', 'str', ''),
            ('_pdbx_validate_rmsd_angle.PDB_ins_code_2', '%s', 'str', ''),
            ('_pdbx_validate_rmsd_angle.label_alt_id_2', '%s', 'str', ''),
            ('_pdbx_validate_rmsd_angle.auth_atom_id_3', '%s', 'str', ''),
            ('_pdbx_validate_rmsd_angle.auth_asym_id_3', '%s', 'str', ''),
            ('_pdbx_validate_rmsd_angle.auth_comp_id_3', '%s', 'str', ''),
            ('_pdbx_validate_rmsd_angle.auth_seq_id_3', '%s', 'str', ''),
            ('_pdbx_validate_rmsd_angle.PDB_ins_code_3', '%s', 'str', ''),
            ('_pdbx_validate_rmsd_angle.label_alt_id_3', '%s', 'str', ''),
            ('_pdbx_validate_rmsd_angle.angle_value', '%s', 'str', ''),
            ('_pdbx_validate_rmsd_angle.angle_target_value', '%s', 'str', ''),
            ('_pdbx_validate_rmsd_angle.angle_deviation', '%s', 'str', ''),
            ('_pdbx_validate_rmsd_angle.angle_standard_deviation', '%s', 'str', ''),
            ('_pdbx_validate_rmsd_angle.linker_flag', '%s', 'str', '')
        ],
        'pdbx_validate_torsion': [
            ('_pdbx_validate_torsion.id', '%s', 'str', ''),
            ('_pdbx_validate_torsion.PDB_model_num', '%s', 'str', ''),
            ('_pdbx_validate_torsion.auth_comp_id', '%s', 'str', ''),
            ('_pdbx_validate_torsion.auth_asym_id', '%s', 'str', ''),
            ('_pdbx_validate_torsion.auth_seq_id', '%s', 'str', ''),
            ('_pdbx_validate_torsion.PDB_ins_code', '%s', 'str', ''),
            ('_pdbx_validate_torsion.label_alt_id', '%s', 'str', ''),
            ('_pdbx_validate_torsion.phi', '%s', 'str', ''),
            ('_pdbx_validate_torsion.psi', '%s', 'str', '')
        ],
        'pdbx_validate_peptide_omega': [
            ('_pdbx_validate_peptide_omega.id', '%s', 'str', ''),
            ('_pdbx_validate_peptide_omega.PDB_model_num', '%s', 'str', ''),
            ('_pdbx_validate_peptide_omega.auth_comp_id_1', '%s', 'str', ''),
            ('_pdbx_validate_peptide_omega.auth_asym_id_1', '%s', 'str', ''),
            ('_pdbx_validate_peptide_omega.auth_seq_id_1', '%s', 'str', ''),
            ('_pdbx_validate_peptide_omega.PDB_ins_code_1', '%s', 'str', ''),
            ('_pdbx_validate_peptide_omega.label_alt_id_1', '%s', 'str', ''),
            ('_pdbx_validate_peptide_omega.auth_comp_id_2', '%s', 'str', ''),
            ('_pdbx_validate_peptide_omega.auth_asym_id_2', '%s', 'str', ''),
            ('_pdbx_validate_peptide_omega.auth_seq_id_2', '%s', 'str', ''),
            ('_pdbx_validate_peptide_omega.PDB_ins_code_2', '%s', 'str', ''),
            ('_pdbx_validate_peptide_omega.label_alt_id_2', '%s', 'str', ''),
            ('_pdbx_validate_peptide_omega.omega', '%s', 'str', '')
        ],
        'pdbx_validate_main_chain_plane': [
            ('_pdbx_validate_main_chain_plane.id', '%s', 'str', ''),
            ('_pdbx_validate_main_chain_plane.PDB_model_num', '%s', 'str', ''),
            ('_pdbx_validate_main_chain_plane.auth_comp_id', '%s', 'str', ''),
            ('_pdbx_validate_main_chain_plane.auth_asym_id', '%s', 'str', ''),
            ('_pdbx_validate_main_chain_plane.auth_seq_id', '%s', 'str', ''),
            ('_pdbx_validate_main_chain_plane.PDB_ins_code', '%s', 'str', ''),
            ('_pdbx_validate_main_chain_plane.label_alt_id', '%s', 'str', ''),
            ('_pdbx_validate_main_chain_plane.improper_torsion_angle', '%s', 'str', '')
        ],
        'pdbx_validate_polymer_linkage': [
            ('_pdbx_validate_polymer_linkage.id', '%s', 'str', ''),
            ('_pdbx_validate_polymer_linkage.PDB_model_num', '%s', 'str', ''),
            ('_pdbx_validate_polymer_linkage.auth_atom_id_1', '%s', 'str', ''),
            ('_pdbx_validate_polymer_linkage.auth_asym_id_1', '%s', 'str', ''),
            ('_pdbx_validate_polymer_linkage.auth_comp_id_1', '%s', 'str', ''),
            ('_pdbx_validate_polymer_linkage.auth_seq_id_1', '%s', 'str', ''),
            ('_pdbx_validate_polymer_linkage.PDB_ins_code_1', '%s', 'str', ''),
            ('_pdbx_validate_polymer_linkage.label_alt_id_1', '%s', 'str', ''),
            ('_pdbx_validate_polymer_linkage.auth_atom_id_2', '%s', 'str', ''),
            ('_pdbx_validate_polymer_linkage.auth_asym_id_2', '%s', 'str', ''),
            ('_pdbx_validate_polymer_linkage.auth_comp_id_2', '%s', 'str', ''),
            ('_pdbx_validate_polymer_linkage.auth_seq_id_2', '%s', 'str', ''),
            ('_pdbx_validate_polymer_linkage.PDB_ins_code_2', '%s', 'str', ''),
            ('_pdbx_validate_polymer_linkage.label_alt_id_2', '%s', 'str', ''),
            ('_pdbx_validate_polymer_linkage.dist', '%s', 'str', '')
        ],
        'pdbx_validate_chiral': [
            ('_pdbx_validate_chiral.id', '%s', 'str', ''),
            ('_pdbx_validate_chiral.PDB_model_num', '%s', 'str', ''),
            ('_pdbx_validate_chiral.auth_atom_id', '%s', 'str', ''),
            ('_pdbx_validate_chiral.label_alt_id', '%s', 'str', ''),
            ('_pdbx_validate_chiral.auth_asym_id', '%s', 'str', ''),
            ('_pdbx_validate_chiral.auth_comp_id', '%s', 'str', ''),
            ('_pdbx_validate_chiral.auth_seq_id', '%s', 'str', ''),
            ('_pdbx_validate_chiral.PDB_ins_code', '%s', 'str', ''),
            ('_pdbx_validate_chiral.details', '%s', 'str', '')
        ]
    }
    _excludeList = []
    _suppressList = []
    #

    def __init__(self):
        super(PdbxGeometryReportCategoryStyle, self).__init__(styleId=PdbxGeometryReportCategoryStyle._styleId,
                                                              catFormatL=PdbxGeometryReportCategoryStyle._categoryInfo,
                                                              catItemD=PdbxGeometryReportCategoryStyle._cDict,
                                                              excludeList=PdbxGeometryReportCategoryStyle._excludeList,
                                                              suppressList=PdbxGeometryReportCategoryStyle._suppressList)

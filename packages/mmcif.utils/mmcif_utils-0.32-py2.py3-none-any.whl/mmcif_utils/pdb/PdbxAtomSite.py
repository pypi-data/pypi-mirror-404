##
# File: PdbxAtomSite.py
# Date: 21-Mar-2011  Jdw
#
# Updated:
#  23-Oct-2012 jdw  Update path and reorganize
###
"""
A collection of classes to assemble/merge atom site records.

Methods are provided to integrated separately stored anisotropic temperature
factor tensor components into atom site records.

"""
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "john.westbrook@rcsb.org"
__license__ = "Apache 2.0"

import logging
logger = logging.getLogger(__name__)

# from mmcif.api.PdbxContainers import *
from mmcif.api.DataCategory import DataCategory


class PdbxAtomSite(object):
    """
    """

    def __init__(self, verbose=True):
        self.__verbose = verbose
        self.__debug = False
        #
        self.__dBlock = None

        self.__atomSiteTags = ['PDB_RECORD', 'ATOM_ID', 'AUTH_ATOM_ID', 'TYPE_SYMBOL', 'AUTH_COMP_ID', 'AUTH_ASYM_ID', 'AUTH_SEQ_ID', 'PDB_INS_CODE',
                               'CARTN_X', 'CARTN_Y', 'CARTN_Z', 'FORMAL_CHARGE', 'MODEL_NUMBER', 'GROUP_ID', 'OCCUPANCY', 'B_ISO', 'ALT_ID',
                               'U11', 'U22', 'U33', 'U12', 'U13', 'U23']

        self.__atomSiteMap = {
            'PDB_RECORD': '_atom_site.pdbx_group_PDB',
            'ATOM_ID': '_atom_site.id',
            'AUTH_ATOM_ID': '_atom_site.auth_atom_id',
            'TYPE_SYMBOL': '_atom_site.type_symbol',
            'AUTH_COMP_ID': '_atom_site.auth_comp_id',
            'AUTH_ASYM_ID': '_atom_site.auth_asym_id',
            'AUTH_SEQ_ID': '_atom_site.auth_seq_id',
            'PDB_INS_CODE': '_atom_site.pdbx_PDB_ins_code',
            'CARTN_X': '_atom_site.Cartn_x',
            'CARTN_Y': '_atom_site.Cartn_y',
            'CARTN_Z': '_atom_site.Cartn_z',
            'FORMAL_CHARGE': '_atom_site.pdbx_formal_charge',
            'MODEL_NUMBER': '_atom_site.pdbx_PDB_model_num',
            'GROUP_ID': '_atom_site.pdbx_group_id',
            'OCCUPANCY': '_atom_site.occupancy',
            'B_ISO': '_atom_site.B_iso_or_equiv',
            'ALT_ID': '_atom_site.label_alt_id',
            'U11': '_atom_site.aniso_U[1][1]',
            'U22': '_atom_site.aniso_U[2][2]',
            'U33': '_atom_site.aniso_U[3][3]',
            'U12': '_atom_site.aniso_U[1][2]',
            'U13': '_atom_site.aniso_U[1][3]',
            'U23': '_atom_site.aniso_U[2][3]'
        }

        self.__atomSiteAnisoTags = ['PDB_RECORD', 'ATOM_ID', 'U11', 'U22', 'U33', 'U12', 'U13', 'U23']
        self.__atomSiteAnisoMap = {
            'PDB_RECORD': '_atom_site_anisotrop.group_PDB',
            'ATOM_ID': '_atom_site_anisotrop.id',
            'U11': '_atom_site_anisotrop.U[1][1]',
            'U22': '_atom_site_anisotrop.U[2][2]',
            'U33': '_atom_site_anisotrop.U[3][3]',
            'U12': '_atom_site_anisotrop.U[1][2]',
            'U13': '_atom_site_anisotrop.U[1][3]',
            'U23': '_atom_site_anisotrop.U[2][3]'}

        """
        Example PDBx atom_site and atom_site_aniso data sections from pdb 1g2r

loop_
_atom_site.group_PDB
_atom_site.id
_atom_site.type_symbol
_atom_site.label_atom_id
_atom_site.label_alt_id
_atom_site.label_comp_id
_atom_site.label_asym_id
_atom_site.label_entity_id
_atom_site.label_seq_id
_atom_site.pdbx_PDB_ins_code
_atom_site.Cartn_x
_atom_site.Cartn_y
_atom_site.Cartn_z
_atom_site.occupancy
_atom_site.B_iso_or_equiv
_atom_site.Cartn_x_esd
_atom_site.Cartn_y_esd
_atom_site.Cartn_z_esd
_atom_site.occupancy_esd
_atom_site.B_iso_or_equiv_esd
_atom_site.pdbx_formal_charge
_atom_site.auth_seq_id
_atom_site.auth_comp_id
_atom_site.auth_asym_id
_atom_site.auth_atom_id
_atom_site.pdbx_PDB_model_num
ATOM   1   N N   . ARG A 1 7   ? 16.757  8.703   13.450  0.62 21.74 ? ? ? ? ? ? 4   ARG A N   1
ATOM   2   C CA  . ARG A 1 7   ? 17.014  7.699   12.351  0.62 18.89 ? ? ? ? ? ? 4   ARG A CA  1
ATOM   3   C C   . ARG A 1 7   ? 16.929  8.224   10.937  0.62 18.59 ? ? ? ? ? ? 4   ARG A C   1
# ...

#
loop_
_atom_site_anisotrop.id
_atom_site_anisotrop.type_symbol
_atom_site_anisotrop.pdbx_label_atom_id
_atom_site_anisotrop.pdbx_label_alt_id
_atom_site_anisotrop.pdbx_label_comp_id
_atom_site_anisotrop.pdbx_label_asym_id
_atom_site_anisotrop.pdbx_label_seq_id
_atom_site_anisotrop.U[1][1]
_atom_site_anisotrop.U[2][2]
_atom_site_anisotrop.U[3][3]
_atom_site_anisotrop.U[1][2]
_atom_site_anisotrop.U[1][3]
_atom_site_anisotrop.U[2][3]
_atom_site_anisotrop.U[1][1]_esd
_atom_site_anisotrop.U[2][2]_esd
_atom_site_anisotrop.U[3][3]_esd
_atom_site_anisotrop.U[1][2]_esd
_atom_site_anisotrop.U[1][3]_esd
_atom_site_anisotrop.U[2][3]_esd
_atom_site_anisotrop.pdbx_auth_seq_id
_atom_site_anisotrop.pdbx_auth_comp_id
_atom_site_anisotrop.pdbx_auth_asym_id
_atom_site_anisotrop.pdbx_auth_atom_id
1   N N   . ARG A 7   0.3083 0.2627 0.2550 0.0385  0.0117  -0.0184 ? ? ? ? ? ? 4   ARG A N
2   C CA  . ARG A 7   0.2277 0.2454 0.2447 0.0416  0.0180  -0.0114 ? ? ? ? ? ? 4   ARG A CA
3   C C   . ARG A 7   0.2320 0.2201 0.2544 0.0298  0.0127  -0.0050 ? ? ? ? ? ? 4   ARG A C
4   O O   . ARG A 7   0.1796 0.1693 0.2865 0.0514  0.0604   0.0124  ? ? ? ? ? ? 4   ARG A O
5   C CB  . ARG A 7   0.2434 0.2587 0.2580 0.0271  0.0224  -0.0195  ? ? ? ? ? ? 4   ARG A CB
6   C CG  . ARG A 7   0.2760 0.3058 0.2823 0.0220  0.0253   0.0067  ? ? ? ? ? ? 4   ARG A CG
7   C CD  . ARG A 7   0.2900 0.2967 0.3303 0.0019  0.0299  -0.0281  ? ? ? ? ? ? 4   ARG A CD
8   N NE  . ARG A 7   0.2469 0.2965 0.3095 0.0233  0.0535  -0.0339  ? ? ? ? ? ? 4   ARG A NE
# ....
        """

        self.__clear()

    def __clear(self):
        self.__uD = {}

    def __categoryPart(self, name):
        tname = ""
        if name.startswith("_"):
            tname = name[1:]
        else:
            tname = name

        i = tname.find(".")
        if i == -1:
            return tname
        else:
            return tname[:i]

    def __attributePart(self, name):
        i = name.find(".")
        if i == -1:
            return None
        else:
            return name[i + 1:]

    def setAtomSiteBlock(self, block=None):
        self.__clear()
        return self.__setDataBlock(block)

    def __setDataBlock(self, dataBlock=None):
        """
        """
        ok = False
        try:
            if (dataBlock.getType() == 'data'):
                self.__dBlock = dataBlock
                ok = True
            else:
                self.__dBlock = None
        except Exception as e:
            logger.exception("Failing with %s" % str(e))

        return ok

    def getAnisoTensorData(self, catName='atom_site_anisotrop'):
        """ Return a dictionary of lists of anisotropic tensor elements stored in the
            in the input category (i.e. atom_site_anisotrop') in a dictionary with
            an atom serial number key (i.e. ATOM_ID).

        """
        catObj = self.__dBlock.getObj(catName)
        nRows = catObj.getRowCount()

        itDict = {}
        itNameList = catObj.getItemNameList()
        for idxIt, itName in enumerate(itNameList):
            itDict[itName] = idxIt
        #
        # column name to row index map -
        cM = {}
        for k, v in self.__atomSiteAnisoMap.items():
            if v in itDict:
                cM[k] = itDict[v]
            else:
                cM[k] = -1
        #
        self.__clear()
        #
        self.__uD = {}
        rowList = catObj.getRowList()
        for row in rowList:
            if ((row[cM['ATOM_ID']] is not None) and (row[cM['U11']] is not None)):
                self.__uD[row[cM['ATOM_ID']]] = (row[cM['U11']], row[cM['U22']], row[cM['U33']], row[cM['U12']], row[cM['U13']], row[cM['U23']])

        return self.__uD

    def mergeAnisoTensorData(self, inCatName='atom_site', outCatName='atom_site_xray_aniso'):
        """ Read the atom records in input category (i.e. default atom_site) and integrate the
            anisotropic tensor elements in the internal dictionary (self.__uD) into each record.

            The integrated records are written to a new category (i.e. outCatName='atom_site_xray_aniso')
            in the current datablock
        """
        catObjIn = self.__dBlock.getObj(inCatName)
        nRows = catObjIn.getRowCount()

        # make out category container --
        catObjOut = DataCategory(outCatName)
        for tag in self.__atomSiteTags:
            att = self.__attributePart(self.__atomSiteMap[tag])
            catObjOut.appendAttribute(att)

        itDict = {}
        itNameList = catObjIn.getItemNameList()
        for idxIt, itName in enumerate(itNameList):
            itDict[itName] = idxIt
        #
        # column name to row index map  or -1
        cM = {}
        for k, v in self.__atomSiteMap.items():
            if v in itDict:
                cM[k] = itDict[v]
            else:
                cM[k] = -1
        #
        # self.__clear()
        #

        rowListIn = catObjIn.getRowList()
        for row in rowListIn:
            # copy corresponding data items --
            #
            rD = {}
            for k in cM.keys():
                rD[k] = row[cM[k]]
            #
            #logger.info("KEYS %r\n\n" % self.__uD.keys())
            #logger.info("ATOM_ID %r\n" % rD['ATOM_ID'])

            if rD['ATOM_ID'] in self.__uD:
                tup = self.__uD[rD['ATOM_ID']]
                for i, k in enumerate(self.__atomSiteAnisoTags[2:]):
                    rD[k] = tup[i]
            #
            newR = []
            for k in self.__atomSiteTags:
                if k in rD:
                    newR.append(rD[k])
                else:
                    newR.append('?')

            catObjOut.append(newR)
        #
        self.__dBlock.append(catObjOut)
        return catObjOut

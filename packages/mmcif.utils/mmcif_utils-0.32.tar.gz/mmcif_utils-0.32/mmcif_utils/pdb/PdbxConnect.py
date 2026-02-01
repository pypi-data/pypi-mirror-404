##
# File: PdbxConnect.py
# Date: 05-June-2010
#
#
# Updated:
#  23-Oct-2012 jdw  Update path and reorganize
##
"""

A collection of classes to determine connectivity based on atom serial numbers.


"""

__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "john.westbrook@rcsb.org"
__license__ = "Apache 2.0"

import sys
import time
import os

from operator import itemgetter
from mmcif.api.PdbxContainers import *
from mmcif.api.DataCategory import DataCategory
from mmcif_utils.chemcomp.PdbxChemCompIo import PdbxChemCompIo


def numeric_compare(x, y):
    return int(x) - int(y)


class PdbxConnect(object):
    """
    """

    def __init__(self, topCachePath='/data/components/ligand-dict-v3', verbose=True):
        self.__verbose = verbose
        self.__debug = False
        self.__lfh = log
        self.__topCachePath = topCachePath
        self.__dBlock = None
        self.__sC = ':'
        self.__atomSiteMap = {'ID': '_atom_site.id',
                              'ATOM_NAME': '_atom_site.auth_atom_id',
                              'ALT_LOC': '_atom_site.label_alt_id',
                              'COMP_ID': '_atom_site.auth_comp_id',
                              'ASYM_ID': '_atom_site.auth_asym_id',
                              'SEQ_NUM': '_atom_site.auth_seq_id',
                              'INS_CODE': '_atom_site.pdbx_PDB_ins_code',
                              'MODEL_NUM': '_atom_site.pdbx_PDB_model_num'
                              }
        self.__stdCcList = ["ALA", "ARG", "ASN", "ASP", "ASX", "CYS", "GLN", "GLU", "GLX",
                            "GLY", "HIS", "ILE", "LEU", "LYS", "MET", "PHE", "PRO", "SER",
                            "THR", "TRP", "TYR", "VAL", "DA", "DC", "DG", "DT", "DU",
                            "DI", "A", "C", "G", "I", "T", "U", "HOH", "UNK", "UNL"]

        self.__structConnMap = {
            'ID_CONN': '_struct_conn.id',
            'CONN_TYPE': '_struct_conn.conn_type_id',
            'ATOM_NAME_1': '_struct_conn.ptnr1_label_atom_id',
            'ALT_LOC_1': '_struct_conn.pdbx_ptnr1_label_alt_id',
            'COMP_ID_1': '_struct_conn.ptnr1_auth_comp_id',
            'ASYM_ID_1': '_struct_conn.ptnr1_auth_asym_id',
            'SEQ_NUM_1': '_struct_conn.ptnr1_auth_seq_id',
            'INS_CODE_1': '_struct_conn.pdbx_ptnr1_PDB_ins_code',
            'SYM_OP_1': '_struct_conn.ptnr1_symmetry',
            'ATOM_NAME_2': '_struct_conn.ptnr2_label_atom_id',
            'ALT_LOC_2': '_struct_conn.pdbx_ptnr2_label_alt_id',
            'COMP_ID_2': '_struct_conn.ptnr2_auth_comp_id',
            'ASYM_ID_2': '_struct_conn.ptnr2_auth_asym_id',
            'SEQ_NUM_2': '_struct_conn.ptnr2_auth_seq_id',
            'INS_CODE_2': '_struct_conn.pdbx_ptnr2_PDB_ins_code',
            'SYM_OP_2': '_struct_conn.ptnr2_symmetry',
            'MODEL_NUM': '_struct_conn.pdbx_PDB_model_num',
            'VALUE_DIST': '_struct_conn.pdbx_dist_value'
        }
        """
        Example intermolecular contact.
loop_
_struct_conn.id
_struct_conn.conn_type_id
_struct_conn.pdbx_PDB_id
_struct_conn.ptnr1_label_asym_id
_struct_conn.ptnr1_label_comp_id
_struct_conn.ptnr1_label_seq_id
_struct_conn.ptnr1_label_atom_id
_struct_conn.pdbx_ptnr1_label_alt_id
_struct_conn.pdbx_ptnr1_PDB_ins_code
_struct_conn.pdbx_ptnr1_standard_comp_id
_struct_conn.ptnr1_symmetry
_struct_conn.ptnr2_label_asym_id
_struct_conn.ptnr2_label_comp_id
_struct_conn.ptnr2_label_seq_id
_struct_conn.ptnr2_label_atom_id
_struct_conn.pdbx_ptnr2_label_alt_id
_struct_conn.pdbx_ptnr2_PDB_ins_code
_struct_conn.ptnr1_auth_asym_id
_struct_conn.ptnr1_auth_comp_id
_struct_conn.ptnr1_auth_seq_id
_struct_conn.ptnr2_auth_asym_id
_struct_conn.ptnr2_auth_comp_id
_struct_conn.ptnr2_auth_seq_id
_struct_conn.ptnr2_symmetry
_struct_conn.pdbx_ptnr3_label_atom_id
_struct_conn.pdbx_ptnr3_label_seq_id
_struct_conn.pdbx_ptnr3_label_comp_id
_struct_conn.pdbx_ptnr3_label_asym_id
_struct_conn.pdbx_ptnr3_label_alt_id
_struct_conn.pdbx_ptnr3_PDB_ins_code
_struct_conn.details
_struct_conn.pdbx_dist_value
disulf1 disulf ? A CYS 23 SG ? ? ? 1_555 A CYS 88  SG ? ? A CYS 23 A CYS 88  1_555 ? ? ? ? ? ? ? 2.011
disulf2 disulf ? B CYS 22 SG ? ? ? 1_555 B CYS 95  SG ? ? B CYS 22 B CYS 95  1_555 ? ? ? ? ? ? ? 2.012
disulf3 disulf ? C CYS 6  SG ? ? ? 1_555 C CYS 127 SG ? ? C CYS 6  C CYS 127 1_555 ? ? ? ? ? ? ? 2.046
disulf4 disulf ? C CYS 30 SG ? ? ? 1_555 C CYS 115 SG ? ? C CYS 30 C CYS 115 1_555 ? ? ? ? ? ? ? 2.022
disulf5 disulf ? C CYS 64 SG ? ? ? 1_555 C CYS 80  SG ? ? C CYS 64 C CYS 80  1_555 ? ? ? ? ? ? ? 2.026
disulf6 disulf ? C CYS 76 SG ? ? ? 1_555 C CYS 94  SG ? ? C CYS 76 C CYS 94  1_555 ? ? ? ? ? ? ? 2.023

        """

        self.__clear()

    def __clear(self):
        self.__uniqCcList = []
        self.__nsCcDict = {}
        self.__nsCcList = []
        self.__nsCcAltDict = {}
        self.__bondTemplates = {}
        self.__linkCcList = []
        self.__linkCcSig = []
        self.__linkCcDict = {}
        self.__modelList = []

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
            pass

        return ok

    def getNonStandardData(self, catName='atom_site'):
        """Return a list of bonds and types.
        """

        catObj = self.__dBlock.getObj(catName)
        nRows = catObj.getRowCount()

        itDict = {}
        itNameList = catObj.getItemNameList()
        for idxIt, itName in enumerate(itNameList):
            itDict[itName] = idxIt
        #
        cM = {}
        for k, v in self.__atomSiteMap.items():
            if v in itDict:
                cM[k] = itDict[v]
            else:
                cM[k] = -1
        #
        self.__clear()
        #
        rowList = catObj.getRowList()
        for row in rowList:
            if (row[cM['COMP_ID']] not in self.__stdCcList):
                rSig = self.__getCompSignatureAtomSite(row, cM)
                if rSig not in self.__nsCcDict:
                    self.__nsCcDict[rSig] = {}
                    self.__nsCcList.append(rSig)
                    self.__nsCcAltDict[rSig] = []
                    if row[cM['COMP_ID']] not in self.__uniqCcList:
                        self.__uniqCcList.append(row[cM['COMP_ID']])

                aSig = row[cM['ATOM_NAME']] + self.__sC + row[cM['ALT_LOC']]
                self.__nsCcDict[rSig][aSig] = row[cM['ID']]
                if row[cM['ALT_LOC']] not in self.__nsCcAltDict[rSig]:
                    self.__nsCcAltDict[rSig].append(row[cM['ALT_LOC']])

        if (self.__debug):
            logger.debug("\n+DEBUG - __nsCcList %r\n" % self.__nsCcList)
            logger.debug("\n+DEBUG - __nsCcDict %r\n" % self.__nsCcDict.items())

        self.__getBondTemplates()

    def getNonStandardDataAndLinks(self, catName='atom_site'):
        """Return a list of bonds and types.
        """

        catObj = self.__dBlock.getObj(catName)
        nRows = catObj.getRowCount()

        itDict = {}
        itNameList = catObj.getItemNameList()
        for idxIt, itName in enumerate(itNameList):
            itDict[itName] = idxIt
        #
        cM = {}
        for k, v in self.__atomSiteMap.items():
            if v in itDict:
                cM[k] = itDict[v]
            else:
                cM[k] = -1
        #
        self.__clear()
        #
        rowList = catObj.getRowList()
        for row in rowList:
            rSigNM = self.__getCompSignatureNoModel(row, cM)
            if (rSigNM in self.__linkCcSigList):
                rSig = self.__getCompSignatureAtomSite(row, cM)
                if rSig not in self.__linkCcDict:
                    self.__linkCcDict[rSig] = {}
                aSig = row[cM['ATOM_NAME']] + self.__sC + row[cM['ALT_LOC']]
                self.__linkCcDict[rSig][aSig] = row[cM['ID']]

            if (row[cM['COMP_ID']] not in self.__stdCcList):
                rSig = self.__getCompSignatureAtomSite(row, cM)
                if (self.__debug):
                    logger.info("\n+DEBUG -rSig %r model %r\n" % (rSig, row[cM['MODEL_NUM']]))
                if rSig not in self.__nsCcDict:
                    self.__nsCcDict[rSig] = {}
                    self.__nsCcList.append(rSig)
                    self.__nsCcAltDict[rSig] = []
                    if row[cM['COMP_ID']] not in self.__uniqCcList:
                        self.__uniqCcList.append(row[cM['COMP_ID']])

                aSig = row[cM['ATOM_NAME']] + self.__sC + row[cM['ALT_LOC']]
                self.__nsCcDict[rSig][aSig] = row[cM['ID']]

                if row[cM['ALT_LOC']] not in self.__nsCcAltDict[rSig]:
                    self.__nsCcAltDict[rSig].append(row[cM['ALT_LOC']])

            modNum = self.__getModelNum(row[cM['MODEL_NUM']])
            if (modNum not in self.__modelList):
                self.__modelList.append(modNum)

        if (self.__debug):
            logger.debug("\n+DEBUG - __nsCcList %r\n" % self.__nsCcList)
            logger.debug("\n+DEBUG - __nsCcDict %r\n" % self.__nsCcDict.items())

        self.__getBondTemplates()

    def __getBondTemplates(self):
        for ccId in self.__uniqCcList:
            bL = []
            try:
                cc = PdbxChemCompIo(verbose=self.__verbose, log=self.__lfh)
                cc.setCachePath(self.__topCachePath)
                cc.setCompId(compId=ccId)
                cc.getComp()
                bL = cc.getBondList()
            except Exception as e:
                logger.error("+ERROR - No component definition for %s\n" % ccId)
                logger.exception("Failing with %s" % str(e))
                continue

            if len(bL) > 0:
                self.__bondTemplates[ccId] = bL

    def __getModelNum(self, tString):
        """ Regularize the model number to 1 it is missing or null.
        """
        try:
            modNum = int(str(tString))
        except Exception as e:
            modNum = 1

        return str(modNum)

    def __getCompSignatureAtomSite(self, row, cM):
        """ Create a unique signature for this component -
        """
        modNum = self.__getModelNum(row[cM['MODEL_NUM']])

        rSig = row[cM['COMP_ID']] + self.__sC + row[cM['ASYM_ID']] + self.__sC + row[cM['SEQ_NUM']] + self.__sC + row[cM['INS_CODE']] + self.__sC + str(modNum)
        return rSig

    def __getCompSignatureNoModel(self, row, cM):
        """ Create a unique signature for this component -
        """
        rSig = row[cM['COMP_ID']] + self.__sC + row[cM['ASYM_ID']] + self.__sC + row[cM['SEQ_NUM']] + self.__sC + row[cM['INS_CODE']]
        return rSig

    def __getCompSignatureStructConn(self, row, cM):
        """ Create a unique signatures for the the components in this linkage.
        """

        rSig1 = row[cM['COMP_ID_1']] + self.__sC + row[cM['ASYM_ID_1']] + self.__sC + row[cM['SEQ_NUM_1']] + self.__sC + row[cM['INS_CODE_1']]
        rSig2 = row[cM['COMP_ID_2']] + self.__sC + row[cM['ASYM_ID_2']] + self.__sC + row[cM['SEQ_NUM_2']] + self.__sC + row[cM['INS_CODE_2']]
        return (rSig1, rSig2)

    def getConnect(self):
        cCat = DataCategory("pdbx_geom_bond")
        cCat.appendAttribute("atom_site_id_1")
        cCat.appendAttribute("atom_signature_1")
        cCat.appendAttribute("atom_site_id_2")
        cCat.appendAttribute("atom_signature_2")
        cCat.appendAttribute("symmetry_2")
        cCat.appendAttribute("value_order")
        # cCat.appendAttribute("model_number")
        #
        rowList = []
        #
        # Non-standard components internal connectivities --
        #
        for nsCC in self.__nsCcList:
            atD = self.__nsCcDict[nsCC]
            altL = self.__nsCcAltDict[nsCC]
            fields = nsCC.split(self.__sC)
            nsCompId = str(fields[0]).strip()
            #
            if nsCompId in self.__bondTemplates:
                bT = self.__bondTemplates[nsCompId]
                for b in bT:
                    tAtI = b[1]
                    tAtJ = b[2]
                    tOrder = b[3]
                    tArom = b[4]
                    if tArom.upper() == 'Y':
                        bType = 'AROM'
                    else:
                        bType = tOrder.upper()
                    for alt in altL:
                        atI = tAtI + self.__sC + alt
                        atJ = tAtJ + self.__sC + alt
                        tsigI = atI + self.__sC + nsCC
                        tsigJ = atJ + self.__sC + nsCC
                        sigI = tsigI.replace('?', '_').replace('.', '_')
                        sigJ = tsigJ.replace('?', '_').replace('.', '_')
                        if atI in atD and atJ in atD:
                            rowList.append((atD[atI], sigI, atD[atJ], sigJ, '1_555', bType))
        #
        # Now do the links
        #
        if (self.__debug):
            logger.info("+DEBUG - __linkCcDict residue keys %r\n" % self.__linkCcDict.keys())

        for link in self.__linkList:
            for mNum in self.__modelList:
                rSig1 = link[0] + self.__sC + str(mNum)
                aSig1 = link[1]
                symOp1 = link[2]
                tsig1 = aSig1 + self.__sC + rSig1
                sig1 = tsig1.replace('?', '_').replace('.', '_')
                #
                rSig2 = link[3] + self.__sC + str(mNum)
                aSig2 = link[4]
                symOp2 = link[5]
                tsig2 = aSig2 + self.__sC + rSig2
                sig2 = tsig2.replace('?', '_').replace('.', '_')
                #
                try:
                    idx1 = self.__linkCcDict[rSig1][aSig1]
                    idx2 = self.__linkCcDict[rSig2][aSig2]
                    if symOp1 == '1_555':
                        rowList.append((idx1, sig1, idx2, sig2, symOp2, 'SING'))
                    elif symOp2 == '1_555':
                        rowList.append((idx2, sig2, idx1, sig1, symOp1, 'SING'))
                    else:
                        logger.info("No link members in asymmetric unit %s %s %s %s\n" % (rSig1, aSig1, rSig2, aSig2))
                except Exception as e:
                    logger.error("Failing link lookup - %r model %r numModels %d\n" % (link, mNum, len(self.__modelList)))
                    logger.exception("Failing with %s" % str(e))
                    continue

        #
        # sorted(rowList,key=itemgetter(0,2))
        #
        # Fill in the data for the return category
        #
        #        for row in sorted(rowList,key=itemgetter(0,2),cmp=numeric_compare):
        for row in sorted(rowList, key=itemgetter(0), cmp=numeric_compare):
            cCat.append(row)
        #
        self.__dBlock.append(cCat)
        return cCat
        #

    def getConnectIndexOnly(self):
        cCat = DataCategory("pdbx_geom_bond")
        cCat.appendAttribute("atom_site_id_1")
        cCat.appendAttribute("atom_site_id_2")
        cCat.appendAttribute("symmetry_2")
        cCat.appendAttribute("value_order")
        # cCat.appendAttribute("model_number")
        #
        rowList = []
        #
        # Non-standard components internal connectivities --
        #
        for nsCC in self.__nsCcList:
            atD = self.__nsCcDict[nsCC]
            altL = self.__nsCcAltDict[nsCC]
            fields = nsCC.split(self.__sC)
            nsCompId = str(fields[0]).strip()
            #
            if nsCompId in self.__bondTemplates:
                bT = self.__bondTemplates[nsCompId]
                for b in bT:
                    tAtI = b[1]
                    tAtJ = b[2]
                    tOrder = b[3]
                    tArom = b[4]
                    if tArom.upper() == 'Y':
                        bType = 'AROM'
                    else:
                        bType = tOrder.upper()
                    for alt in altL:
                        atI = tAtI + self.__sC + alt
                        atJ = tAtJ + self.__sC + alt
                        if atI in atD and atJ in atD:
                            rowList.append((atD[atI], atD[atJ], '1_555', bType))
        #
        # Now do the links
        #
        if (self.__debug):
            logger.info("+DEBUG - __linkCcDict residue keys %r\n" % self.__linkCcDict.keys())

        for link in self.__linkList:
            for mNum in self.__modelList:
                rSig1 = link[0] + self.__sC + str(mNum)
                aSig1 = link[1]
                symOp1 = link[2]

                rSig2 = link[3] + self.__sC + str(mNum)
                aSig2 = link[4]
                symOp2 = link[5]
                try:
                    idx1 = self.__linkCcDict[rSig1][aSig1]
                    idx2 = self.__linkCcDict[rSig2][aSig2]
                    if symOp1 == '1_555':
                        rowList.append((idx1, idx2, symOp2, 'SING'))
                    elif symOp2 == '1_555':
                        rowList.append((idx2, idx1, symOp1, 'SING'))
                    else:
                        logger.info("No link members in asymmetric unit %s %s %s %s\n" % (rSig1, aSig1, rSig2, aSig2))
                except Exception as e:
                    logger.error("Failing link lookup - %r model %r numModels %d\n" % (link, mNum, len(self.__modelList)))
                    logger.exception("Failing with %s" % str(e))
                    continue

        #
        sorted(rowList, key=itemgetter(0, 1))
        #
        # Fill in the data for the return category
        #
        for row in rowList:
            cCat.append(row)
        #
        self.__dBlock.append(cCat)
        return cCat
        #

    def getLinkData(self, catName='struct_conn'):
        """Return a list linkages from the struct_conn category.
        """
        self.__linkCcList = []
        self.__linkCcSigList = []
        self.__linkList = []

        catObj = self.__dBlock.getObj(catName)
        if catObj is None:
            return

        nRows = catObj.getRowCount()

        itDict = {}
        itNameList = catObj.getItemNameList()
        for idxIt, itName in enumerate(itNameList):
            itDict[itName] = idxIt
        #
        cM = {}
        for k, v in self.__structConnMap.items():
            if v in itDict:
                cM[k] = itDict[v]
            else:
                cM[k] = -1
        #

        rowList = catObj.getRowList()
        for row in rowList:
            #
            if (not (row[cM['CONN_TYPE']].startswith('covale') or row[cM['CONN_TYPE']].startswith('disulf') or row[cM['CONN_TYPE']].startswith('metal'))):
                continue
            (rSig1, rSig2) = self.__getCompSignatureStructConn(row, cM)
            if rSig1 not in self.__linkCcSigList:
                self.__linkCcSigList.append(rSig1)

            if rSig2 not in self.__linkCcSigList:
                self.__linkCcSigList.append(rSig2)

            if (row[cM['COMP_ID_1']] not in self.__linkCcList):
                self.__linkCcList.append(row[cM['COMP_ID_1']])

            if (row[cM['COMP_ID_2']] not in self.__linkCcList):
                self.__linkCcList.append(row[cM['COMP_ID_2']])

            if (row[cM['ALT_LOC_1']] == '?'):
                altLoc1 = '.'
            else:
                altLoc1 = row[cM['ALT_LOC_1']]

            if (row[cM['ALT_LOC_2']] == '?'):
                altLoc2 = '.'
            else:
                altLoc2 = row[cM['ALT_LOC_2']]

            aSig1 = row[cM['ATOM_NAME_1']] + self.__sC + altLoc1
            aSig2 = row[cM['ATOM_NAME_2']] + self.__sC + altLoc2

            symOp1 = row[cM['SYM_OP_1']]
            symOp2 = row[cM['SYM_OP_2']]

            self.__linkList.append((rSig1, aSig1, symOp1, rSig2, aSig2, symOp2))

        #
        if (self.__debug):
            logger.debug("\n+DEBUG - __linkCcSigList %r\n" % self.__linkCcSigList)
            logger.debug("\n+DEBUG - __linkCcList %r\n" % self.__linkList)

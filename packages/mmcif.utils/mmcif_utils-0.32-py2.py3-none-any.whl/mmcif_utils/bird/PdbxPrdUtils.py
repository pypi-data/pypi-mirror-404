##
# File: PdbxPrdUtils.py
# Date: 28-Nov-2012
#
# Update:
#
# 21-Jan-2013 jdw add options to update schema table with materialized 3-letter-code sequences.
#  1-May-2013 jdw add method for general status and audit update.
#
##
"""
A collection of utilities methods for BIRD PRD and family definitions.

"""
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "john.westbrook@rcsb.org"
__license__ = "Apache 2.0"


import sys
import time
import os
import traceback

import logging
logger = logging.getLogger(__name__)

import itertools

from mmcif_utils.bird.PdbxPrd import *


class PdbxPrdUtils(object):
    """ Utilities methods for BIRD PRD and family definitions.

    """

    def __init__(self, PdbxPrdIoObj=None, verbose=True, log=sys.stderr):
        self.__verbose = verbose
        self.__debug = False
        self.__lfh = log
        self.__pObj = PdbxPrdIoObj

    def getFamilyMembers(self):
        """ Return of a dictionary of PRD family members for each family defintion within the
            current PRD container collection.

            Return dictionary contains a list of member Prd Id codes for each family -
                s[familyId] = [prdId1,prdId2,...]
        """
        _mId = "(" + self.__class__.__name__ + "." + sys._getframe().f_code.co_name + ")"
        fD = {}
        for prdIdC in self.__pObj.getContainerNameList():
            self.__pObj.setContainer(prdIdC)
            id = self.__pObj.getCurrentContainerId()
            if id == prdIdC:
                dL = self.__pObj.getAttribDictList(catName='pdbx_reference_molecule_list')
                for d in dL:
                    rOb = PdbxReferenceMoleculeList(d, self.__verbose, self.__lfh)
                    prdId = rOb.getPrdId()
                    familyId = rOb.getFamilyPrdId()
                    if familyId not in fD:
                        fD[familyId] = []
                    if familyId == id:
                        fD[familyId].append(prdId)
                    else:
                        logger.info("+ERROR 0 - %s container %s id mismatch %s\n" % (_mId, id, familyId))
        return fD

    def getChemCompIds(self):
        """ Return of a dictionary of corresponding chemical component identifiers

            Return dictionary contains the status codes organized by prdId -
                s[prdId] = CCID or PRDCC_ID
        """
        _mId = "(" + self.__class__.__name__ + "." + sys._getframe().f_code.co_name + ")"
        pD = {}
        for prdIdC in self.__pObj.getContainerNameList():
            self.__pObj.setContainer(prdIdC)
            id = self.__pObj.getCurrentContainerId()
            if id == prdIdC:
                dL = self.__pObj.getAttribDictList(catName='pdbx_reference_molecule')
                for d in dL:
                    rOb = PdbxReferenceMolecule(d, self.__verbose, self.__lfh)
                    repType = rOb.getRepresentAs()
                    ccId = rOb.getChemCompId()
                    if ccId is not None and ccId not in ['.', '?']:
                        pD[id] = ccId
                    elif repType is not None and repType == 'polymer':
                        pD[id] = "PRDCC_" + id[4:]
                    else:
                        logger.info("+ERROR 0 - %s container %s id representation error\n" % (_mId, id))
            else:
                logger.info("+ERROR 0 - %s container %s id mismatch %s\n" % (_mId, id, pId))
        return pD

    def getStatus(self):
        """ Return of a dictionary of defintion status for the current PRD container collection.

            Return dictionary contains the status codes organized by prdId -
                s[prdId] = REL, HOLD, ...
        """
        _mId = "(" + self.__class__.__name__ + "." + sys._getframe().f_code.co_name + ")"
        sD = {}
        for prdIdC in self.__pObj.getContainerNameList():
            self.__pObj.setContainer(prdIdC)
            id = self.__pObj.getCurrentContainerId()
            if id == prdIdC:
                dL = self.__pObj.getAttribDictList(catName='pdbx_reference_molecule')
                for d in dL:
                    rOb = PdbxReferenceMolecule(d, self.__verbose, self.__lfh)
                    status = rOb.getReleaseStatus()
                    pId = rOb.getId()
                    if pId == id:
                        sD[pId] = status
                    else:
                        logger.info("+ERROR 0 - %s container %s id mismatch %s\n" % (_mId, id, pId))
        return sD

    def suppressComponentsFromFile(self, filePath=None):
        """ Suppress values of _pdbx_reference_molecule.chem_comp_id that are listed in the
            input file.

        """
        _mId = "(" + self.__class__.__name__ + "." + sys._getframe().f_code.co_name + ")"
        #
        if not os.access(filePath, os.R_OK):
            logger.info("+ERROR 0 - %s cannot open reference id list %s\n" % (_mId, filePath))
        refD = {}
        ifh = open(filePath, 'r')
        for line in ifh.readlines():
            id = str(line[:-1])
            refD[id] = id
        ifh.close()
        #
        self.__suppressComponents(refD=refD)

    def suppressComponentsFromList(self, idList=None):
        """ Suppress values of _pdbx_reference_molecule.chem_comp_id that are in the input id list.
        """
        #
        sL = idList if idList is not None else []
        refD = {}
        for id in sL:
            refD[id] = id
        self.__suppressComponents(refD=refD)

    def __suppressComponents(self, refD={}):
        """ Suppress values of _pdbx_reference_molecule.chem_comp_id that are keys in the
            input dictionary.
        """
        #
        _mId = "(" + self.__class__.__name__ + "." + sys._getframe().f_code.co_name + ")"
        for prdIdC in self.__pObj.getContainerNameList():
            self.__pObj.setContainer(prdIdC)
            id = self.__pObj.getCurrentContainerId()
            if id == prdIdC:
                myCatName = 'pdbx_reference_molecule'
                dL = self.__pObj.getAttribDictList(catName=myCatName)
                for iRow, rowD in enumerate(dL):
                    rOb = PdbxReferenceMolecule(rowD, self.__verbose, self.__lfh)
                    ccId = rOb.getChemCompId()
                    if ccId in refD:
                        rOb.setChemCompId(None)
                        self.__pObj.updateRowByAttribute(rowD, myCatName, iRow=iRow)
                        if (self.__verbose):
                            logger.info("+INFO - %s suppressing component id %s in %s\n" % (_mId, ccId, id))

    def setReleaseAndAudit(self, relDate="YYYY-MM-DD"):
        """
        """
        _mId = "(" + self.__class__.__name__ + "." + sys._getframe().f_code.co_name + ")"
        for prdIdC in self.__pObj.getContainerNameList():
            self.__pObj.setContainer(prdIdC)
            id = self.__pObj.getCurrentContainerId()
            if id == prdIdC:
                myCatName = 'pdbx_reference_molecule'
                dL = self.__pObj.getAttribDictList(catName=myCatName)
                for iRow, rowD in enumerate(dL):
                    rOb = PdbxReferenceMolecule(rowD, self.__verbose, self.__lfh)
                    ok = rOb.setReleaseStatus('REL')
                    self.__pObj.updateRowByAttribute(rowD, myCatName, iRow=iRow)

                aFlag = False
                # first check for an existing record
                myCatName = 'pdbx_prd_audit'
                dL = self.__pObj.getAttribDictList(catName=myCatName)
                for iRow, rowD in enumerate(dL):
                    rOb = PdbxPrdAudit(rowD, self.__verbose, self.__lfh)
                    actionType = rOb.getActionType()
                    if actionType == "Initial release":
                        aFlag = True
                        ok1 = rOb.setDate(relDate)
                        ok2 = self.__pObj.updateRowByAttribute(rowD, myCatName, iRow=iRow)
                        if (self.__verbose):
                            logger.info("+INFO - %s id %s setting date %s in %r %r\n" % (_mId, id, relDate, ok1, ok2))

                if not aFlag:
                    rowD = {}
                    rOb = PdbxPrdAudit(rowD, self.__verbose, self.__lfh)
                    ok = rOb.setActionType("Initial release")
                    ok = rOb.setId(id)
                    ok = rOb.setDate(relDate)
                    ok = rOb.setProcessingSite("RCSB")
                    #
                    self.__pObj.appendRowByAttribute(rowD, myCatName)

    def setStatusAndAudit(self, statusCode='HOLD', updateDate="YYYY-MM-DD", site="RCSB", annotator=None, details=None):
        """
        """
        _mId = "(" + self.__class__.__name__ + "." + sys._getframe().f_code.co_name + ")"
        for prdIdC in self.__pObj.getContainerNameList():
            self.__pObj.setContainer(prdIdC)
            id = self.__pObj.getCurrentContainerId()
            if id == prdIdC:
                myCatName = 'pdbx_reference_molecule'
                dL = self.__pObj.getAttribDictList(catName=myCatName)
                for iRow, rowD in enumerate(dL):
                    rOb = PdbxReferenceMolecule(rowD, self.__verbose, self.__lfh)
                    ok = rOb.setReleaseStatus(statusCode)
                    self.__pObj.updateRowByAttribute(rowD, myCatName, iRow=iRow)

                myCatName = 'pdbx_prd_audit'
                dL = self.__pObj.getAttribDictList(catName=myCatName)

                rowD = {}
                rOb = PdbxPrdAudit(rowD, self.__verbose, self.__lfh)
                ok = rOb.setActionType("Modify audit")
                ok = rOb.setId(id)
                ok = rOb.setDate(updateDate)
                ok = rOb.setProcessingSite(site)
                if annotator is not None:
                    ok = rOb.setAnnotator(annotator)
                if details is not None:
                    ok = rOb.setDetails(details)
                #
                self.__pObj.appendRowByAttribute(rowD, myCatName)

    def getReferencedComponents(self):
        """ Get referenced chemical components within the current PRD container collection.

            Return a dictionary or components containing the list -
                d[prdId] = [
        """
        _mId = "(" + self.__class__.__name__ + "." + sys._getframe().f_code.co_name + ")"
        compD = {}
        for prdIdC in self.__pObj.getContainerNameList():
            self.__pObj.setContainer(prdIdC)
            id = self.__pObj.getCurrentContainerId()
            if id == prdIdC:
                dL = self.__pObj.getAttribDictList(catName='pdbx_reference_entity_poly_seq')
                for d in dL:
                    rOb = PdbxReferenceEntityPolySeq(d, self.__verbose, self.__lfh)
                    pId = rOb.getId()
                    cc = rOb.getComponentId()
                    if pId == id:
                        if pId not in compD:
                            compD[pId] = []
                        compD[pId].append(cc)
                    else:
                        logger.info("+ERROR 1 - %s container %s id mismatch %s\n" % (_mId, id, pId))

                dL = self.__pObj.getAttribDictList(catName='pdbx_reference_entity_nonpoly')
                for d in dL:
                    rOb = PdbxReferenceEntityNonPoly(d, self.__verbose, self.__lfh)
                    pId = rOb.getId()
                    cc = rOb.getComponentId()
                    if pId == id:
                        if pId not in compD:
                            compD[pId] = []
                        compD[pId].append(cc)
                    else:
                        logger.info("+ERROR 2 - %s container %r id mismatch %r\n" % (_mId, id, pId))

                dL = self.__pObj.getAttribDictList(catName='pdbx_reference_entity_link')
                for d in dL:
                    rOb = PdbxReferenceEntityLink(d, self.__verbose, self.__lfh)
                    pId = rOb.getId()
                    cc1 = rOb.getComponentId1()
                    cc2 = rOb.getComponentId1()
                    if pId == id:
                        if pId not in compD:
                            compD[pId] = []
                        compD[pId].append(cc1)
                        compD[pId].append(cc2)
                    else:
                        logger.info("+ERROR 3 - %s container %s id mismatch %s\n" % (_mId, id, pId))

                dL = self.__pObj.getAttribDictList(catName='pdbx_reference_entity_poly_link')
                for d in dL:
                    rOb = PdbxReferenceEntityPolyLink(d, self.__verbose, self.__lfh)
                    pId = rOb.getId()
                    cc1 = rOb.getComponentId1()
                    cc2 = rOb.getComponentId1()
                    if pId == id:
                        if pId not in compD:
                            compD[pId] = []
                        compD[pId].append(cc1)
                        compD[pId].append(cc2)
                    else:
                        logger.info("+ERROR 4 - %s container %s id mismatch %s\n" % (_mId, id, pId))

                dL = self.__pObj.getAttribDictList(catName='pdbx_reference_entity_nonpoly_link')
                for d in dL:
                    rOb = PdbxReferenceEntityNonPolyLink(d, self.__verbose, self.__lfh)
                    pId = rOb.getId()
                    cc1 = rOb.getComponentId1()
                    cc2 = rOb.getComponentId1()
                    if pId == id:
                        if pId not in compD:
                            compD[pId] = []
                        compD[pId].append(cc1)
                        compD[pId].append(cc2)
                    else:
                        logger.info("+ERROR 5 - %s container %s id mismatch %s\n" % (_mId, id, pId))

        rD = {}
        for id in sorted(compD.keys()):
            t = set([cc for cc in compD[id] if cc not in [None, '.', '?']])
            if len(t) > 0:
                rD[id] = list(t)

        return rD

    def getComponentSequences(self, addCategory=False):
        """ Get component sequences (3-letter-codes) as a list for each polymer reference entity in
            in the current definition container list.

            Return a dictionary of components containing the list -
                d[prdId][refEntityId]=[res1,res2,...]
        """

        seqD = {}
        for prdIdC in self.__pObj.getContainerNameList():
            self.__pObj.setContainer(prdIdC)
            id = self.__pObj.getCurrentContainerId()
            if id == prdIdC:
                dL = self.__pObj.getAttribDictList(catName='pdbx_reference_entity_poly_seq')
                refD = {}
                for d in dL:
                    rOb = PdbxReferenceEntityPolySeq(d, self.__verbose, self.__lfh)
                    pid = rOb.getId()
                    refId = rOb.getReferenceEntityId()
                    compId = rOb.getComponentId()
                    num = int(rOb.getSequenceNumber())
                    het = rOb.getHeterogeneityFlag()
                    #
                    if refId not in refD:
                        refD[refId] = {}

                    if num not in refD[refId]:
                        refD[refId][num] = []

                    refD[refId][num].append((num, compId))

                seqD[prdIdC] = refD
            else:
                logger.info("+ERROR - container %s id mismatch %s\n" % (id, prdIdC))
        #
        rD = {}
        for id in sorted(seqD.keys()):
            if id not in rD:
                rD[id] = {}
            for refId, sD in seqD[id].items():

                vL = self.__makeVariantCombinations(seqVarD=sD)
                if (len(vL) > 0):
                    if (self.__debug):
                        logger.info("%s %s variants %d list: %s\n" % (id, refId, len(vL), vL))
                    tmpLoL = []
                    for ii, vtup in enumerate(vL):
                        tmpL = []
                        for ii in sorted(sD.keys()):
                            if len(sD[ii]) > 1:
                                choice = list(set(sD[ii]) & set(vtup))
                            else:
                                choice = sD[ii]
                            tmpL.append(choice[0][1])
                        tmpLoL.append(tmpL)
                    rD[id][refId] = tmpLoL
                else:
                    tmpL = []
                    for ii in sorted(sD.keys()):
                        choice = sD[ii]
                        tmpL.append(choice[0][1])
                    rD[id][refId] = [tmpL]

        # Create a new category to hold the sequence data --
        #
        if (addCategory):
            for id in sorted(rD.keys()):
                ok = self.__pObj.setContainer(containerName=id)
                if not ok:
                    logger.info("+PrdUtility(getComponentSequences) container lookup failed %s\n" % id)
                self.__pObj.newCategory(catName='pdbx_reference_entity_sequence_list')
                iRow = 0
                for refId, seq3L in rD[id].items():
                    for ii, seq3 in enumerate(seq3L, start=1):
                        tD = {}
                        tD['prd_id'] = id
                        tD['ref_entity_id'] = refId
                        tD['v_id'] = str(ii)
                        tD['three_letter_codes'] = ' '.join(seq3)
                        self.__pObj.updateRowByAttribute(rowAttribDict=tD, catName='pdbx_reference_entity_sequence_list', iRow=iRow)
                        iRow += 1
                        if self.__debug:
                            logger.info("+PrdUtility(getComponentSequences) row dict: %r\n" % tD.items())
                        #
        return rD

    def __makeVariantCombinations(self, seqVarD={}):
        #
        varLofL = []
        #
        for k, vL in seqVarD.items():
            if len(vL) > 1:
                varLofL.append(vL)
        #
        vL = []
        if (len(varLofL) > 0):
            if (self.__debug):
                logger.info("+PrdUtility(__makeVariantCombinations) List - %r\n" % varLofL)
            vL = list(itertools.product(*varLofL))
            if (self.__debug):
                logger.info("+PrdUtility(__makeVariantCombinations) Product list: %r\n" % vL)

        return vL

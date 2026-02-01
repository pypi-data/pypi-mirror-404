##
# File: PdbxPrd.py
# Date: 28-Nov-2012
#
# Update:
#  05-May-2013  jdw Add class PdbxReferenceMoleculeList()
##
"""
A collection of accessor classes supporting PRD & Family dictionary data categories.

"""
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "john.westbrook@rcsb.org"
__license__ = "Apache 2.0"


import sys
import os

import logging
logger = logging.getLogger(__name__)


class PdbxReferenceMolecule(object):
    ''' Accessor methods for PRD reference molecule top-level attributes.

    '''

    def __init__(self, rowD=None, verbose=True, log=sys.stderr):
        self.__verbose = verbose
        self.__debug = False
        self.__lfh = log
        self.__atD = rowD if rowD is not None else {}

    def get(self):
        return self.__atD

    def __getAttribute(self, name):
        try:
            return self.__atD[name]
        except Exception as e:
            return None

    def __setAttribute(self, name, value):
        try:
            self.__atD[name] = value
            return True
        except Exception as e:
            return False

    def getId(self):
        return self.__getAttribute('prd_id')

    def setId(self, value):
        return self.__setAttribute('prd_id', value)

    def getChemCompId(self):
        return self.__getAttribute('chem_comp_id')

    def setChemCompId(self, value):
        return self.__setAttribute('chem_comp_id', value)

    def getName(self):
        return self.__getAttribute('name')

    def setName(self, value):
        return self.__setAttribute('name', value)

    def getRepresentAs(self):
        return self.__getAttribute('represent_as')

    def setRepresentAs(self, value):
        return self.__setAttribute('represent_as', value)

    def getFormula(self):
        return self.__getAttribute('formula')

    def setFormula(self, value):
        return self.__setAttribute('formula', value)

    def getFormulaWeight(self):
        return self.__getAttribute('formula_weight')

    def setFormulaWeight(self, value):
        return self.__setAttribute('formula_weight', value)

    def getType(self):
        return self.__getAttribute('type')

    def setType(self, value):
        return self.__setAttribute('type', value)

    def getTypeEvidence(self):
        return self.__getAttribute('type_evidence_code')

    def setTypeEvidence(self, value):
        return self.__setAttribute('type_evidence_code', value)

    def getClass(self):
        return self.__getAttribute('class')

    def setClass(self, value):
        return self.__setAttribute('class', value)

    def getClassEvidence(self):
        return self.__getAttribute('class_evidence_code')

    def setClassEvidence(self, value):
        return self.__setAttribute('class_evidence_code', value)

    def getReleaseStatus(self):
        return self.__getAttribute('release_status')

    def setReleaseStatus(self, value):
        return self.__setAttribute('release_status', value)

    def getReplacedBy(self):
        return self.__getAttribute('replaced_by')

    def setReplacedBy(self, value):
        return self.__setAttribute('replaced_by', value)

    def getReplaces(self):
        return self.__getAttribute('replaces')

    def setReplaces(self, value):
        return self.__setAttribute('replaces', value)

    def getDescription(self):
        return self.__getAttribute('description')

    def setDescription(self, value):
        return self.__setAttribute('description', value)

    def getCompoundDetails(self):
        return self.__getAttribute('compound_details')

    def setCompoundDetails(self, value):
        return self.__setAttribute('compound_details', value)

    def getRepresentativePdbIdCode(self):
        return self.__getAttribute('representative_PDB_id_code')

    def setRepresentativePdbIdCode(self, value):
        return self.__setAttribute('representative_PDB_id_code', value)


class PdbxReferenceMoleculeList(object):
    ''' Accessor methods for Family PRD membership records

    '''

    def __init__(self, rowD=None, verbose=True, log=sys.stderr):
        self.__verbose = verbose
        self.__debug = False
        self.__lfh = log
        self.__atD = rowD if rowD is not None else {}

    def get(self):
        return self.__atD

    def __getAttribute(self, name):
        try:
            return self.__atD[name]
        except Exception as e:
            return None

    def __setAttribute(self, name, value):
        try:
            self.__atD[name] = value
            return True
        except Exception as e:
            return False

    def getPrdId(self):
        return self.__getAttribute('prd_id')

    def setPrdId(self, value):
        return self.__setAttribute('prd_id', value)

    def getFamilyPrdId(self):
        return self.__getAttribute('family_prd_id')

    def setFamilyPrdId(self, value):
        return self.__setAttribute('family_prd_id', value)

    def new(self):
        self.setPrdId(None)
        self.setFamilyPrdId(None)
        return self.__atD


class PdbxPrdAudit(object):
    ''' Accessor methods for PRD definition audit records.

    '''

    def __init__(self, rowD, verbose=True, log=sys.stderr):
        self.__verbose = verbose
        self.__debug = False
        self.__lfh = log
        self.__atD = rowD if rowD is not None else {}

    def __getAttribute(self, name):
        try:
            return self.__atD[name]
        except Exception as e:
            return None

    def __setAttribute(self, name, value):
        try:
            self.__atD[name] = value
            return True
        except Exception as e:
            return False

    def new(self):
        self.setId(None)
        self.setActionType(None)
        self.setDate(None)
        self.setAnnotator(None)
        self.setProcessingSite(None)
        self.setDetails(None)
        return self.__atD

    def getId(self):
        return self.__getAttribute('prd_id')

    def setId(self, value):
        return self.__setAttribute('prd_id', value)

    def getActionType(self):
        return self.__getAttribute('action_type')

    def setActionType(self, value):
        return self.__setAttribute('action_type', value)

    def getProcessingSite(self):
        return self.__getAttribute('processing_site')

    def setProcessingSite(self, value):
        return self.__setAttribute('processing_site', value)

    def getDate(self):
        return self.__getAttribute('date')

    def setDate(self, value):
        return self.__setAttribute('date', value)

    def getAnnotator(self):
        return self.__getAttribute('annotator')

    def setAnnotator(self, value):
        return self.__setAttribute('annotator', value)

    def getDetails(self):
        return self.__getAttribute('details')

    def setDetails(self, value):
        return self.__setAttribute('details', value)


class PdbxReferenceEntityPolySeq(object):
    ''' Accessor methods PRD reference polymer sequences

    '''

    def __init__(self, rowD, verbose=True, log=sys.stderr):
        self.__verbose = verbose
        self.__debug = False
        self.__lfh = log
        self.__atD = rowD if rowD is not None else {}

    def __getAttribute(self, name):
        try:
            return self.__atD[name]
        except Exception as e:
            return None

    def __setAttribute(self, name, value):
        try:
            self.__atD[name] = value
            return True
        except Exception as e:
            return False

    def getId(self):
        return self.__getAttribute('prd_id')

    def setId(self, value):
        return self.__setAttribute('prd_id', value)

    def getReferenceEntityId(self):
        return self.__getAttribute('ref_entity_id')

    def setReferenceEntityId(self, value):
        return self.__setAttribute('ref_entity_id', value)

    def getSequenceNumber(self):
        return self.__getAttribute('num')

    def setSequenceNumber(self, value):
        return self.__setAttribute('num', value)

    def getComponentId(self):
        return self.__getAttribute('mon_id')

    def setComponentId(self, value):
        return self.__setAttribute('mon_id', value)

    def getParentComponentId(self):
        return self.__getAttribute('parent_mon_id')

    def setParentComponentId(self, value):
        return self.__setAttribute('parent_mon_id', value)

    def getHeterogeneityFlag(self):
        return self.__getAttribute('hetero')

    def setHeterogeneityFlag(self, value):
        return self.__setAttribute('hetero', value)

    def getObservedFlag(self):
        return self.__getAttribute('observed')

    def setObservedFlag(self, value):
        return self.__setAttribute('observed', value)


class PdbxReferenceEntityPolyLink(object):
    ''' Accessor methods PRD reference polymer linkages

    '''

    def __init__(self, rowD, verbose=True, log=sys.stderr):
        self.__verbose = verbose
        self.__debug = False
        self.__lfh = log
        self.__atD = rowD if rowD is not None else {}

    def __getAttribute(self, name):
        try:
            return self.__atD[name]
        except Exception as e:
            return None

    def __setAttribute(self, name, value):
        try:
            self.__atD[name] = value
            return True
        except Exception as e:
            return False

    def getId(self):
        return self.__getAttribute('prd_id')

    def setId(self, value):
        return self.__setAttribute('prd_id', value)

    def getReferenceEntityId(self):
        return self.__getAttribute('ref_entity_id')

    def setReferenceEntityId(self, value):
        return self.__setAttribute('ref_entity_id', value)

    def getSequenceNumber1(self):
        return self.__getAttribute('entity_seq_num_1')

    def setSequenceNumber1(self, value):
        return self.__setAttribute('entity_seq_num_1', value)

    def getSequenceNumber2(self):
        return self.__getAttribute('entity_seq_num_2')

    def setSequenceNumber1(self, value):
        return self.__setAttribute('entity_seq_num_2', value)

    def getComponentId1(self):
        return self.__getAttribute('comp_id_1')

    def setComponentId1(self, value):
        return self.__setAttribute('comp_id_1', value)

    def getComponentId2(self):
        return self.__getAttribute('comp_id_2')

    def setComponentId2(self, value):
        return self.__setAttribute('comp_id_2', value)

    def getAtomId1(self):
        return self.__getAttribute('atom_id_1')

    def setAtomId1(self, value):
        return self.__setAttribute('atom_id_1', value)

    def getAtomId2(self):
        return self.__getAttribute('atom_id_2')

    def setAtomId2(self, value):
        return self.__setAttribute('atom_id_2', value)

    def getValueOrder(self):
        return self.__getAttribute('value_order')

    def setValueOrder(self, value):
        return self.__setAttribute('value_order', value)

    def getComponentId(self):
        return self.__getAttribute('component_id')

    def setComponentId(self, value):
        return self.__setAttribute('component_id', value)


class PdbxReferenceEntityNonPoly(object):
    ''' Accessor methods PRD reference non-polymer entities

    '''

    def __init__(self, rowD, verbose=True, log=sys.stderr):
        self.__verbose = verbose
        self.__debug = False
        self.__lfh = log
        self.__atD = rowD if rowD is not None else {}

    def __getAttribute(self, name):
        try:
            return self.__atD[name]
        except Exception as e:
            return None

    def __setAttribute(self, name, value):
        try:
            self.__atD[name] = value
            return True
        except Exception as e:
            return False

    def getId(self):
        return self.__getAttribute('prd_id')

    def setId(self, value):
        return self.__setAttribute('prd_id', value)

    def getReferenceEntityId(self):
        return self.__getAttribute('ref_entity_id')

    def setReferenceEntityId(self, value):
        return self.__setAttribute('ref_entity_id', value)

    def getComponentId(self):
        return self.__getAttribute('comp_id')

    def setComponentId(self, value):
        return self.__setAttribute('comp_id', value)

    def getType(self):
        return self.__getAttribute('type')

    def setType(self, value):
        return self.__setAttribute('type', value)

    def getDetails(self):
        return self.__getAttribute('details')

    def setDetails(self, value):
        return self.__setAttribute('details', value)


class PdbxReferenceEntityLink(object):
    ''' Accessor methods PRD reference entity linkages

    '''

    def __init__(self, rowD, verbose=True, log=sys.stderr):
        self.__verbose = verbose
        self.__debug = False
        self.__lfh = log
        self.__atD = rowD if rowD is not None else {}

    def __getAttribute(self, name):
        try:
            return self.__atD[name]
        except Exception as e:
            return None

    def __setAttribute(self, name, value):
        try:
            self.__atD[name] = value
            return True
        except Exception as e:
            return False

    def getId(self):
        return self.__getAttribute('prd_id')

    def setId(self, value):
        return self.__setAttribute('prd_id', value)

    def getLinkId(self):
        return self.__getAttribute('link_id')

    def setLinkId(self, value):
        return self.__setAttribute('link_id', value)

    def getLinkClass(self):
        return self.__getAttribute('link_class')

    def setLinkClass(self, value):
        return self.__setAttribute('link_class', value)

    def getReferenceEntityId1(self):
        return self.__getAttribute('ref_entity_id_1')

    def setReferenceEntityId1(self, value):
        return self.__setAttribute('ref_entity_id_1', value)

    def getReferenceEntityId2(self):
        return self.__getAttribute('ref_entity_id_2')

    def setReferenceEntityId2(self, value):
        return self.__setAttribute('ref_entity_id_2', value)

    def getSequenceNumber1(self):
        return self.__getAttribute('entity_seq_num_1')

    def setSequenceNumber1(self, value):
        return self.__setAttribute('entity_seq_num_1', value)

    def getSequenceNumber2(self):
        return self.__getAttribute('entity_seq_num_2')

    def setSequenceNumber1(self, value):
        return self.__setAttribute('entity_seq_num_2', value)

    def getComponentId1(self):
        return self.__getAttribute('comp_id_1')

    def setComponentId1(self, value):
        return self.__setAttribute('comp_id_1', value)

    def getComponentId2(self):
        return self.__getAttribute('comp_id_2')

    def setComponentId2(self, value):
        return self.__setAttribute('comp_id_2', value)

    def getAtomId1(self):
        return self.__getAttribute('atom_id_1')

    def setAtomId1(self, value):
        return self.__setAttribute('atom_id_1', value)

    def getAtomId2(self):
        return self.__getAttribute('atom_id_2')

    def setAtomId2(self, value):
        return self.__setAttribute('atom_id_2', value)

    def getValueOrder(self):
        return self.__getAttribute('value_order')

    def setValueOrder(self, value):
        return self.__setAttribute('value_order', value)

    def getComponentId1(self):
        return self.__getAttribute('component_id_1')

    def setComponentId1(self, value):
        return self.__setAttribute('component_id_1', value)

    def getComponentId2(self):
        return self.__getAttribute('component_id_2')

    def setComponentId2(self, value):
        return self.__setAttribute('component_id_2', value)


class PdbxReferenceEntityList(object):
    ''' Accessor methods PRD reference entities

    '''

    def __init__(self, rowD, verbose=True, log=sys.stderr):
        self.__verbose = verbose
        self.__debug = False
        self.__lfh = log
        self.__atD = rowD if rowD is not None else {}

    def __getAttribute(self, name):
        try:
            return self.__atD[name]
        except Exception as e:
            return None

    def __setAttribute(self, name, value):
        try:
            self.__atD[name] = value
            return True
        except Exception as e:
            return False

    def getId(self):
        return self.__getAttribute('prd_id')

    def setId(self, value):
        return self.__setAttribute('prd_id', value)

    def getReferenceEntityId(self):
        return self.__getAttribute('ref_entity_id')

    def setReferenceEntityId(self, value):
        return self.__setAttribute('ref_entity_id', value)

    def getComponentId(self):
        return self.__getAttribute('component_id')

    def setComponentId(self, value):
        return self.__setAttribute('component_id', value)

    def getType(self):
        return self.__getAttribute('type')

    def setType(self, value):
        return self.__setAttribute('type', value)

    def getDetails(self):
        return self.__getAttribute('details')

    def setDetails(self, value):
        return self.__setAttribute('details', value)


class PdbxReferenceEntityPoly(object):
    ''' Accessor methods PRD reference polymer entities

    '''

    def __init__(self, rowD, verbose=True, log=sys.stderr):
        self.__verbose = verbose
        self.__debug = False
        self.__lfh = log
        self.__atD = rowD if rowD is not None else {}

    def __getAttribute(self, name):
        try:
            return self.__atD[name]
        except Exception as e:
            return None

    def __setAttribute(self, name, value):
        try:
            self.__atD[name] = value
            return True
        except Exception as e:
            return False

    def getId(self):
        return self.__getAttribute('prd_id')

    def setId(self, value):
        return self.__setAttribute('prd_id', value)

    def getReferenceEntityId(self):
        return self.__getAttribute('ref_entity_id')

    def setReferenceEntityId(self, value):
        return self.__setAttribute('ref_entity_id', value)

    def getType(self):
        return self.__getAttribute('type')

    def setType(self, value):
        return self.__setAttribute('type', value)

    def getDatabaseCode(self):
        return self.__getAttribute('db_code')

    def setDatabaseName(self, value):
        return self.__setAttribute('db_name', value)

##
# File: PdbxChemComp.py
# Date: 7-Nov-2012
#
# Update:
#  20-Nov-2012 jdw add accessor methods for
#
##
"""
A collection of accessor classes supporting chemical component dictionary data categories.

"""
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "john.westbrook@rcsb.org"
__license__ = "Apache 2.0"



import sys
import logging
logger = logging.getLogger(__name__)


class PdbxChemCompConstants(object):
    _periodicTable = [
        "H", "HE",
        "LI", "BE", "B", "C", "N", "O", "F", "NE",
        "NA", "MG", "AL", "SI", "P", "S", "CL", "AR",
        "K", "CA", "SC", "TI", "V", "CR", "MN", "FE", "CO", "NI",
        "CU", "ZN", "GA", "GE", "AS", "SE", "BR", "KR",
        "RB", "SR", "Y", "ZR", "NB", "MO", "TC", "RU", "RH", "PD",
        "AG", "CD", "IN", "SN", "SB", "TE", "I", "XE",
        "CS", "BA", "LA", "CE", "PR", "ND", "PM", "SM", "EU", "GD", "TB",
        "DY", "HO", "ER", "TM", "YB", "LU", "HF", "TA", "W",
        "RE", "OS", "IR", "PT", "AU", "HG", "TL", "PB", "BI",
        "PO", "AT", "RN",
        "FR", "RA", "AC", "TH", "PA", "U", "NP", "PU", "AM", "CM", "BK",
        "CF", "ES", "FM", "MD", "NO", "LR", "UNQ", "UNP", "UNH",
        "UNS", "UNO", "UNE"]


class PdbxChemComp(object):
    ''' Accessor methods chemical component attributes.

    '''

    def __init__(self, compD, verbose=True, log=sys.stderr):
        self.__verbose = verbose
        self.__debug = False
        self.__lfh = log
        # Attribute mapping of chem_comp data category to dictionary structure (e.g. _category.attribute)
        self.__atD = compD

    def __getAttribute(self, name):
        try:
            return self.__atD[name]
        except Exception as e:
            return None

    def getId(self):
        return self.__getAttribute('id')

    def getName(self):
        return self.__getAttribute('name')

    def getFormula(self):
        return self.__getAttribute('formula')

    def getType(self):
        return self.__getAttribute('type')

    def getTypePdbx(self):
        return self.__getAttribute('pdbx_type')

    def getSynonyms(self):
        return self.__getAttribute('pdbx_synonyms')

    def getFormulaWeight(self):
        return self.__getAttribute('formula_weight')

    def getFormalCharge(self):
        return self.__getAttribute('pdbx_formal_charge')

    def getNonStandardParent(self):
        return self.__getAttribute('mon_nstd_parent_comp_id')

    def getAmbiguousFlag(self):
        return self.__getAttribute('pdbx_ambiguous_flag')

    def getOneLetterCode(self):
        return self.__getAttribute('one_letter_code')

    def getThreeLetterCode(self):
        return self.__getAttribute('three_letter_code')

    def getSubComponentList(self):
        return self.__getAttribute('pdbx_subcomponent_list')

    def getType(self):
        return self.__getAttribute('type')

    def getReleaseStatus(self):
        return self.__getAttribute('pdbx_release_status')

    def getProcessingSite(self):
        return self.__getAttribute('pdbx_processing_site')

    def getInitialDate(self):
        return self.__getAttribute('pdbx_initial_date')

    def getModifiedDate(self):
        return self.__getAttribute('pdbx_modified_date')

    def getReplacedBy(self):
        return self.__getAttribute('pdbx_replaced_by')

    def getReplaces(self):
        return self.__getAttribute('pdbx_replaces')

    def getModelCoordinatesDatabaseCode(self):
        return self.__getAttribute('pdbx_model_coordinates_db_code')

    def getModelCoordinatesMissingFlag(self):
        return self.__getAttribute('pdbx_model_coordinates_missing_flag')

    def getIdealCoordinatesMissingFlag(self):
        return self.__getAttribute('pdbx_ideal_coordinates_missing_flag')

    def getIdealCoordinatesDetails(self):
        return self.__getAttribute('pdbx_ideal_coordinates_details')

    def getModelCoordinatesDetails(self):
        return self.__getAttribute('pdbx_model_coordinates_details')

    # others to be implemented


class PdbxChemCompAtom(object):
    ''' Accessor methods chemical component atom attributes.

    '''

    def __init__(self, atomD, verbose=True, log=sys.stderr):
        self.__verbose = verbose
        self.__debug = False
        self.__lfh = log
        # Attribute mapping of chem_comp_atom data category to dictionary structure (e.g. _category.attribute)
        self.__atD = atomD

    def __getAttribute(self, name):
        try:
            return self.__atD[name]
        except Exception as e:
            return None

    def getName(self):
        return self.__getAttribute('atom_id')

    def isChiral(self):
        return (self.__getAttribute('pdbx_stereo_config') != 'N')

    def getType(self):
        return self.__getAttribute('type_symbol')

    def getAtNo(self):
        try:
            tyU = str(self.getType()).upper()
            if ((tyU == 'D') or (tyU == 'T')):
                tyU = 'H'
            return PdbxChemCompConstants._periodicTable.index(tyU) + 1
        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            return 0

    def getIsotope(self):
        ty = self.getType()
        if ty == 'D':
            return 2
        elif ty == 'T':
            return 3
        else:
            return 0

    def isAromatic(self):
        return (self.__getAttribute('pdbx_aromatic_flag') != 'N')

    def getCIPStereo(self):
        return self.__getAttribute('pdbx_stereo_config')

    def getFormalCharge(self):
        try:
            return int(self.__getAttribute('charge'))
        except Exception as e:
            return 0

    def hasModelCoordinates(self):
        x = self.__getAttribute('model_Cartn_x')
        y = self.__getAttribute('model_Cartn_y')
        z = self.__getAttribute('model_Cartn_z')
        #
        return ((x is not None) and (y is not None) and (z is not None))

    def hasIdealCoordinates(self):
        x = self.__getAttribute('pdbx_model_Cartn_x_ideal')
        y = self.__getAttribute('pdbx_model_Cartn_y_ideal')
        z = self.__getAttribute('pdbx_model_Cartn_z_ideal')
        #
        return ((x is not None) and (y is not None) and (z is not None))

    def getModelCoordinates(self):
        """ Returns (x,y,z)
        """
        try:
            x = float(self.__getAttribute('model_Cartn_x'))
            y = float(self.__getAttribute('model_Cartn_y'))
            z = float(self.__getAttribute('model_Cartn_z'))
            return (x, y, z)
        except Exception as e:
            return (None, None, None)

    def getIdealCoordinates(self):
        """ Returns (x,y,z)
        """
        try:
            x = float(self.__getAttribute('pdbx_model_Cartn_x_ideal'))
            y = float(self.__getAttribute('pdbx_model_Cartn_y_ideal'))
            z = float(self.__getAttribute('pdbx_model_Cartn_z_ideal'))
            return (x, y, z)
        except Exception as e:
            return (None, None, None)


class PdbxChemCompBond(object):
    ''' Accessor methods chemical component bond attributes.

    '''

    def __init__(self, bondD, verbose=True, log=sys.stderr):
        self.__verbose = verbose
        self.__debug = False
        self.__lfh = log
        # Attribute mapping of chem_comp_bond data category to dictionary structure (e.g. _category.attribute)
        self.__atD = bondD

    def __getAttribute(self, name):
        try:
            return self.__atD[name]
        except Exception as e:
            return None

    def getBond(self):
        """ Returns (atomI,atomJ) atom ids from the atom list.
        """
        return (self.__getAttribute('atom_id_1'), self.__getAttribute('atom_id_2'))

    def getType(self):
        return self.__getAttribute('value_order')

    def getIntegerType(self):
        bT = self.__getAttribute('value_order')
        if bT == 'SING':
            return 1
        elif bT == 'DOUB':
            return 2
        elif bT == 'TRIP':
            return 3
        elif bT == 'QUAD':
            return 4
        else:
            return 0

    def isAromatic(self):
        return (self.__getAttribute('pdbx_aromatic_flag') == 'Y')

    def getStereo(self):
        return self.__getAttribute('pdbx_stereo_config')

    def hasStereo(self):
        return (self.__getAttribute('pdbx_stereo_config') != 'N')

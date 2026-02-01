##
# File: PdbxChemCompModel.py
# Date: 29-Nov-2014
#
# Update:
#
##
"""
A collection of accessor classes supporting chemical component model data categories.

"""
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "john.westbrook@rcsb.org"
__license__ = "Apache 2.0"



import sys

import logging
logger = logging.getLogger(__name__)

from mmcif_utils.chemcomp.PdbxChemComp import PdbxChemCompConstants


class PdbxChemCompModel(object):
    ''' Accessor methods chemical component model attributes.

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

    def getCompId(self):
        return self.__getAttribute('comp_id')


class PdbxChemCompModelAtom(object):
    ''' Accessor methods chemical component model atom attributes.

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


class PdbxChemCompModelBond(object):
    ''' Accessor methods chemical component model bond attributes.

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


class PdbxChemCompModelDescriptor(object):
    ''' Accessor methods chemical component model descriptor.

    '''

    def __init__(self, dD, verbose=True, log=sys.stderr):
        self.__verbose = verbose
        self.__debug = False
        self.__lfh = log
        # Attribute mapping of chem_comp_bond data category to dictionary structure (e.g. _category.attribute)
        self.__atD = dD

    def __getAttribute(self, name):
        try:
            return self.__atD[name]
        except Exception as e:
            return None

    def getType(self):
        return self.__getAttribute('type')

    def getDescriptor(self):
        return self.__getAttribute('descriptor')


class PdbxChemCompModelFeature(object):
    ''' Accessor methods chemical component model features.

    '''

    def __init__(self, fD, verbose=True, log=sys.stderr):
        self.__verbose = verbose
        self.__debug = False
        self.__lfh = log
        # Attribute mapping of chem_comp_bond data category to dictionary structure (e.g. _category.attribute)
        self.__atD = fD

    def __getAttribute(self, name):
        try:
            return self.__atD[name]
        except Exception as e:
            return None

    def getFeatureName(self):
        return self.__getAttribute('feature_name')

    def getFeatureValue(self):
        return self.__getAttribute('feature_value')


class PdbxChemCompModelReference(object):
    ''' Accessor methods chemical component model reference.

    '''

    def __init__(self, rD, verbose=True, log=sys.stderr):
        self.__verbose = verbose
        self.__debug = False
        self.__lfh = log
        # Attribute mapping of chem_comp_bond data category to dictionary structure (e.g. _category.attribute)
        self.__atD = rD

    def __getAttribute(self, name):
        try:
            return self.__atD[name]
        except Exception as e:
            return None

    def getDatabaseName(self):
        return self.__getAttribute('database_name')

    def getDatabaseCode(self):
        return self.__getAttribute('database_code')


class PdbxChemCompModelAudit(object):
    ''' Accessor methods chemical component model audit records.

    '''

    def __init__(self, aD, verbose=True, log=sys.stderr):
        self.__verbose = verbose
        self.__debug = False
        self.__lfh = log
        # Attribute mapping of chem_comp_bond data category to dictionary structure (e.g. _category.attribute)
        self.__atD = aD

    def __getAttribute(self, name):
        try:
            return self.__atD[name]
        except Exception as e:
            return None

    def getActionType(self):
        return self.__getAttribute('action_type')

    def getDate(self):
        return self.__getAttribute('date')

    def getProcessingSite(self):
        return self.__getAttribute('processing_site')

    def getAnnotator(self):
        return self.__getAttribute('annotator')

    def getDetails(self):
        return self.__getAttribute('details')

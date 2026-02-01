##
# File: PdbxBirdIndex.py
# Date: 05-May-2013
#
# Update:
#    6-Jun-2016  jdw general cleanup
##
"""
A collection of indexing utilities for FAMILY and PRD molecule definitions.

"""
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "john.westbrook@rcsb.org"
__license__ = "Apache 2.0"


import sys
import os
import copy

try:
    import pickle
except Exception as e:
    import _pickle as pickle

import logging
logger = logging.getLogger(__name__)

from mmcif_utils.bird.PdbxPrdIo import PdbxPrdIo
from mmcif_utils.bird.PdbxFamilyIo import PdbxFamilyIo
from mmcif_utils.bird.PdbxPrdUtils import PdbxPrdUtils


class PdbxBirdIndex(object):
    """ Utilities methods for BIRD PRD and family definitions.

    """

    def __init__(self, indexPath='family_prd_index.pic',
                 topPrdCache='/data/components/prd-v3',
                 topPrdCCCache='/data/components/prdcc-v3',
                 topFamilyCache='/data/components/family-v3',
                 topChemCompCache='/data/components/ligand-dict-v3',
                 rebuildFlag=False, verbose=True, log=sys.stderr):
        self.__verbose = verbose
        self.__debug = True
        self.__lfh = log
        #
        self.__indexPath = indexPath
        #
        self.__topPrdCachePath = topPrdCache
        self.__topPrdCCCachePath = topPrdCCCache
        self.__topFamilyCachePath = topFamilyCache
        self.__topChemCompCachePath = topChemCompCache
        #
        self.__pickleProtocol = pickle.HIGHEST_PROTOCOL
        #
        self.__fD = {}
        self.__cD = {}
        self.__setup(rebuildFlag)

    def getFamilyList(self):
        logger.debug("fD %r" % self.__fD)
        return sorted(list(self.__fD.keys()))

    def getPrdIdList(self, familyId):
        try:
            return self.__fD[familyId]
        except Exception as e:
            return []

    def getPrdPathList(self, familyId):
        try:
            pathList = []
            for prdId in self.__fD[familyId]:
                prdIdU = str(prdId).upper()
                pth = os.path.join(self.__topPrdCachePath, prdIdU[-1], prdIdU + '.cif')
                if os.access(pth, os.R_OK):
                    pathList.append(pth)
                else:
                    logger.warning("+PdbxBirdIndex.getPrdPathList() family %s missing PRD member %s" % (familyId, prdId))
            return pathList
        except Exception as e:
            if self.__verbose:
                logger.info("+PdbxBirdIndex.getPrdPathList() family %s PRD member list construction failed" % familyId)
            return []

    def getChemCompId(self, prdId):
        try:
            return self.__cD[prdId]
        except Exception as e:
            return None

    def getChemCompPath(self, prdId):
        try:
            tId = str(self.__cD[prdId]).upper()
            if tId.startswith("PRDCC_"):
                pth = os.path.join(self.__topPrdCCCachePath, tId[-1], tId + '.cif')
            else:
                pth = os.path.join(self.__topChemCompCachePath, tId[0], tId, tId + '.cif')
            if os.access(pth, os.R_OK):
                return pth
            else:
                logger.warning("+PdbxBirdIndex.getChemCompPath() PRD id %s missing chemical component definition %s" % (prdId, tId))
                return None
        except Exception as e:
            if self.__verbose:
                logger.warning("+PdbxBirdIndex.getChemCompPath() PRD id %s missing chemical component definition" % prdId)
            return None

    def __setup(self, rebuildFlag=False):
        if not os.access(self.__indexPath, os.R_OK) or rebuildFlag:
            self.__buildFamilyIndex()
            self.__buildPrdIndex()
            self.__serialize(indexPath=self.__indexPath)
        else:
            self.__deserialize(indexPath=self.__indexPath)

    def __buildFamilyIndex(self):
        """ Build and serialize index of family identifier correspondences -
        """
        try:
            prd = PdbxFamilyIo(verbose=self.__verbose, log=self.__lfh)
            prd.setCachePath(self.__topFamilyCachePath)
            self.__pathList = prd.makeDefinitionPathList()
            for pth in self.__pathList:
                logger.debug("Family path %r" % pth)
            logger.info("Length of path list %d" % len(self.__pathList))
            #
            for pth in self.__pathList:
                prd.setFilePath(pth)
            logger.debug("Repository read completed")
            #
            prdU = PdbxPrdUtils(prd, verbose=self.__verbose, log=self.__lfh)
            self.__fD = prdU.getFamilyMembers()
            #
            if (self.__debug):
                for familyId, prdIdList in self.__fD.items():
                    logger.debug("Family %s  members: %s" % (familyId, prdIdList))

            return True
        except Exception as e:
            if (self.__verbose):
                logger.exception("Failing with %s" % str(e))
        return False

    def __buildPrdIndex(self):
        """Test case - build index of PRD chemical component identifier correspondences -
        """
        try:
            prd = PdbxPrdIo(verbose=self.__verbose, log=self.__lfh)
            prd.setCachePath(self.__topPrdCachePath)
            self.__pathList = prd.makeDefinitionPathList()
            #
            for pth in self.__pathList:
                prd.setFilePath(pth)
            logger.debug("Repository read completed")
            #
            prdU = PdbxPrdUtils(prd, verbose=self.__verbose, log=self.__lfh)
            self.__cD = prdU.getChemCompIds()
            #
            if (self.__debug):
                for prdId, ccId in self.__cD.items():
                    logger.debug("PRD Id %s  ccId: %s" % (prdId, ccId))
            #
            return True
        except Exception as e:
            logger.exception("Failing with %s" % str(e))
        return False

    def __serialize(self, indexPath='family_prd_index.pic'):
        try:
            ofh = open(indexPath, 'wb')
            pickle.dump(self.__fD, ofh, self.__pickleProtocol)
            pickle.dump(self.__cD, ofh, self.__pickleProtocol)
            ofh.close()
            return True
        except Exception as e:
            if (self.__verbose):
                logger.exception("Failing with %s" % str(e))
        return False

    def __deserialize(self, indexPath='family_prd_index.pic'):
        try:
            ifh = open(indexPath, 'rb')
            self.__fD = pickle.load(ifh)
            self.__cD = pickle.load(ifh)
            ifh.close()
            return True
        except Exception as e:
            if (self.__verbose):
                logger.exception("Failing with %s" % str(e))
        return False

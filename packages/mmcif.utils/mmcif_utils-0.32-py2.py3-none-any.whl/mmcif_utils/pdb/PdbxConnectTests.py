##
# File:    PdbxConnectTests.py
# Author:  jdw
# Date:    5-June-2010
# Version: 0.001
#
# Updated:
#  23-Oct-2012 jdw  Update path and reorganize
##


__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "john.westbrook@rcsb.org"
__license__ = "Apache 2.0"
__version__ = "V0.01"


import sys
import unittest
import time
import os

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s]-%(module)s.%(funcName)s: %(message)s')
logger = logging.getLogger()

HERE = os.path.abspath(os.path.dirname(__file__))
TOPDIR = os.path.dirname(os.path.dirname(HERE))

try:
    from mmcif_utils import __version__
except Exception as e:
    sys.path.insert(0, TOPDIR)
    from mmcif_utils import __version__

from mmcif_utils.pdb.PdbxConnect import PdbxConnect
from mmcif.io.PdbxReader import PdbxReader


class PdbxConnectTests(unittest.TestCase):

    def setUp(self):
        self.__lfh = sys.stdout
        self.__verbose = True
        self.__pathOutputFile = os.path.join(HERE, "test-output", "testOutputDataFile.cif")
        self.__topCachePath = '/data/components/ligand-dict-v3'
        self.__pathPdbxDataFile = os.path.join(HERE, "data", "1kip.cif")
        self.__startTime = time.time()
        logger.debug("Running tests on version %s" % __version__)
        logger.debug("Starting %s at %s" % (self.id(),
                                            time.strftime("%Y %m %d %H:%M:%S", time.localtime())))

    def tearDown(self):
        endTime = time.time()
        logger.debug("Completed %s at %s (%.4f seconds)\n" % (self.id(),
                                                              time.strftime("%Y %m %d %H:%M:%S", time.localtime()),
                                                              endTime - self.__startTime))

    def testConnect1(self):
        """Test case -  process atom site records
        """
        try:
            myBlockList = []
            with open(self.__pathPdbxDataFile, "r") as ifh:
                pRd = PdbxReader(ifh)
                pRd.read(myBlockList)

            cCon = PdbxConnect(topCachePath=self.__topCachePath, verbose=self.__verbose, log=self.__lfh)
            for block in myBlockList:
                ok = cCon.setAtomSiteBlock(block)
                if ok:
                    cCon.getLinkData()
                    cCon.getNonStandardDataAndLinks()
                    cCat = cCon.getConnect()
                    # block.printIt(self.__lfh)
                else:
                    self.__lfh("No datablock in file %s\n" % self.__pathPdbxDataFile)
        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            self.fail()


def suite():
    return unittest.makeSuite(PdbxConnectTests, 'test')

if __name__ == '__main__':
    unittest.main()

##
# File:    InventoryIoBatchRunner.py
# Author:  jdw
# Date:    15-Aug-2015
# Version: 0.001
#
# Updates:
#   8-Mar-2018 jdw   Use with caution -
##
"""
Batch runner tests for InventoryIo operations ---- Preliminary version --

"""
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "john.westbrook@rcsb.org"
__license__ = "Apache 2.0"


import sys
import unittest
import time
import os
import shutil
import pickle

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s]-%(module)s.%(funcName)s: %(message)s')
logger = logging.getLogger()


from mmcif_utils.inventory.InventoryIo import InventoryIo
from wwpdb.utils.rcsb.MultiProcUtil import MultiProcUtil


class InventoryIoBatchTests(unittest.TestCase):

    def setUp(self):
        self.__lfh = sys.stderr
        self.__verbose = True
        # example files --
        self.__pathIdListFile = "PDBID.LIST"
        self.__overWrite = False

    def tearDown(self):
        pass

    def __getIdList(self, idFilePath):
        idList = []
        ifh = open(idFilePath, 'r')
        for line in ifh:
            if not line.startswith('#'):
                idList.append(line[:-1])
        return idList

    def __getPathList(self, pdbIdList):
        """ return the path list using the input ID list and 2-letter hash path -
        """
        pthL = []
        for pdbId in pdbIdList:
            p = self.__getInputPath(pdbId)
            pthL.append(p)
        return pthL

    def __getInputFilePath(self, pdbId, topPath="/net/to_ftp_arch/ftp-v4.0/pdb/data/structures/divided/structure_factors/"):
        return os.path.join(topPath, pdbId[1:3], 'r' + pdbId + 'sf.ent.gz')

    def __makeOutputFilePath(self, pdbId, topPath="/net/analysis_1/sf-data"):
        pth = os.path.join(topPath, pdbId[1:3], pdbId)
        if not os.access(pth, os.W_OK):
            os.makedirs(pth, 0o775)
        return os.path.join(topPath, pdbId[1:3], pdbId, pdbId + '_sf.cif')

    def __getOutputSummaryFilePath(self, pdbId, topPath="/net/analysis_1/sf-data"):
        return os.path.join(topPath, pdbId[1:3], pdbId, pdbId + '_sf.pic')

    def __exportSummary(self, summaryD, picPath):
        return pickle.dump(summaryD, open(picPath, "wb"))

    def __importSummary(self, picPath):
        if os.access(picPath, os.R_OK):
            return pickle.load(open(picPath, "rb"))
        else:
            return {}

    def __fetch(self, inpPath, outPath):
        try:
            shutil.copyfile(inpPath, outPath)
            return True
        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            return False

    def __copyUnGzip(self, inpFilePath, outFilePath, overWrite=False):
        """
        """
        try:
            if os.access(outFilePath, os.R_OK) and not overWrite:
                return True
            if not os.access(inpFilePath, os.R_OK):
                return False
            cmd = " zcat  %s > %s " % (inpFilePath, outFilePath)
            os.system(cmd)
            return True
        except Exception as e:
            if self.__verbose:
                logger.exception("Failing with %s" % str(e))
            return False

    def getInventoryWorkerMulti(self, dataList, procName, optionsD, workingDir):
        """ Return a list of summary dictionaries --
        """
        retList = []
        oList = []
        try:
            for pdbId in dataList:
                startTime = time.time()
                logger.info("\nStarting %s %s at %s\n" % (self.__class__.__name__,
                                                          sys._getframe().f_code.co_name,
                                                          time.strftime("%Y %m %d %H:%M:%S", time.localtime())))

                iPth = self.__getInputFilePath(pdbId)
                oPth = self.__makeOutputFilePath(pdbId)
                if self.__copyUnGzip(iPth, oPth, overWrite=self.__overWrite):
                    rD = {'pdb_id': pdbId.lower(), 'summary': {}}
                    #
                    inv = InventoryIo(verbose=self.__verbose, log=self.__lfh)
                    inv.setEnumItemList(['_refln.status', '_refln.pdbx_r_free_flag'])
                    d = inv.getIndex(oPth)
                    sPth = self.__getOutputSummaryFilePath(pdbId)
                    ok = self.__exportSummary(d, sPth)
                    if ok:
                        rD['summary'] = d
                        retList.append(rD)
                        oList.append(pdbId)
                        logger.info("+%s %s return length %d\n" % (self.__class__.__name__, sys._getframe().f_code.co_name, len(d)))
                        if self.__verbose:
                            for k, v in d.items():
                                logger.info("+  %s  %r\n" % (k, v))
                    else:
                        pass
                else:
                    od, of = os.path.split(oPth)
                    shutil.rmtree(od)

                endTime = time.time()
                logger.info("\nCompleted %s %s at %s (%.2f seconds)\n" % (self.__class__.__name__,
                                                                          sys._getframe().f_code.co_name,
                                                                          time.strftime("%Y %m %d %H:%M:%S", time.localtime()),
                                                                          endTime - startTime))

        except Exception as e:
            logger.exception("Failing with %s" % str(e))

        endTime = time.time()
        logger.info("\nCompleted %s %s at %s (%.2f seconds)\n" % (self.__class__.__name__,
                                                                  sys._getframe().f_code.co_name,
                                                                  time.strftime("%Y %m %d %H:%M:%S", time.localtime()),
                                                                  endTime - startTime))

        return oList, retList, []

    def testLoadSummaryMulti(self):
        """Test case - create batch load of sf summary files -
        """
        logger.info("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        startTime = time.time()
        numProc = 8
        try:
            dataList = self.__getIdList(self.__pathIdListFile)
            mpu = MultiProcUtil(verbose=True, log=self.__lfh)
            mpu.set(workerObj=self, workerMethod="getInventoryWorkerMulti")
            ok, failList, retLists, diagList = mpu.runMulti(dataList=dataList, numProc=numProc, numResults=1)
            summaryList = retLists[0]
            endTime0 = time.time()
            logger.info("\nPath list length %d  in %.2f seconds\n" % (len(summaryList), endTime0 - startTime))

        except Exception as e:
            logger.exception("Failing with %s" % str(e))

    def processSummaryTest1(self):
        """ Return a list of summary dictionaries --
        """
        startTime = time.time()
        logger.info("\nStarting %s %s at %s\n" % (self.__class__.__name__,
                                                  sys._getframe().f_code.co_name,
                                                  time.strftime("%Y %m %d %H:%M:%S", time.localtime())))
        retList = []
        oList = []
        dataList = self.__getIdList(self.__pathIdListFile)
        #
        itemD = {}
        numDataSetD = {}
        numSummaryFiles = 0
        try:
            for pdbId in dataList:
                sPth = self.__getOutputSummaryFilePath(pdbId)
                sD = self.__importSummary(sPth)

                if len(sD) == 0:
                    continue

                if False:
                    logger.info("+%s %s return length %d\n" % (self.__class__.__name__, sys._getframe().f_code.co_name, len(sD)))
                    for k, v in sD.items():
                        logger.info("+  %s  %r\n" % (k, v))
                numSummaryFiles += 1
                #
                # number of data sets -
                #
                numDataSets = sD['CONTAINER_COUNT']
                if numDataSets not in numDataSetD:
                    numDataSetD[numDataSets] = 0
                numDataSetD[numDataSets] += 1
                #
                # Count items -  CONTAINER_INFO  {0: {'OBJ_INFO': {'audit': {'OBJ_LENGTH': 1, 'ITEM_INFO': [('_audit.revision_id', 1), ('_audit.creat
                d = sD['CONTAINER_INFO']
                for iSet, tD in d.items():
                    if iSet != 0:
                        continue
                    objD = tD['OBJ_INFO']
                    for catName, catD in objD.items():
                        for itTup in catD['ITEM_INFO']:
                            if itTup[0] not in itemD:
                                itemD[itTup[0]] = []
                            itemD[itTup[0]].append(pdbId)
            #
            logger.info("Total entries = %d\n" % len(dataList))
            logger.info("Total summary files = %d  %.4f\n" % (numSummaryFiles, float(numSummaryFiles) / len(dataList)))
            #
            totalDataSets = 0
            n = 0
            for k in sorted(numDataSetD.keys()):
                v = numDataSetD[k]
                logger.info(" set count %2d    number %6d   pc %.4f\n" % (k, v, float(v) / float(numSummaryFiles)))
                totalDataSets += (k * v)
                n += v
            #
            logger.info(" Total data set count %7d\n" % totalDataSets)
            logger.info(" Check of the number of summary files %7d\n" % n)

            #
            #  number of sets containing item
            #
            for k in sorted(itemD.keys()):
                vL = itemD[k]
                numSets = len(vL)
                numEntries = len(set(vL))
                logger.info("%-55s   in data sets %6d  (%8.4f) in entries %6d (%8.4f)\n" %
                            (k, numSets, float(numSets) / float(totalDataSets), numEntries, float(numEntries) / float(numSummaryFiles)))

            ok = True
        except Exception as e:
            ok = False
            logger.exception("Failing with %s" % str(e))

        endTime = time.time()
        logger.info("\nCompleted %s %s at %s (%.2f seconds)\n" % (self.__class__.__name__,
                                                                  sys._getframe().f_code.co_name,
                                                                  time.strftime("%Y %m %d %H:%M:%S", time.localtime()),
                                                                  endTime - startTime))

        return ok


def suiteInventoryTests():
    suiteSelect = unittest.TestSuite()
    suiteSelect.addTest(InventoryIoBatchTests("testLoadSummaryMulti"))


def suiteProcessSummaryTests():
    suiteSelect = unittest.TestSuite()
    suiteSelect.addTest(InventoryIoBatchTests("processSummaryTest1"))
    return suiteSelect

if __name__ == '__main__':
    if (False):
        mySuite = suiteInventoryTests()
        unittest.TextTestRunner(verbosity=2).run(mySuite)

        mySuite = suiteProcessSummaryTests()
        unittest.TextTestRunner(verbosity=2).run(mySuite)

    mySuite = suiteProcessSummaryTests()
    unittest.TextTestRunner(verbosity=2).run(mySuite)

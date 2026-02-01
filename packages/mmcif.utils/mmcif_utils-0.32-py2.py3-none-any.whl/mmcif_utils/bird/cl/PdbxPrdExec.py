##
# File: PdbxPrdExec.py
# Date: 1-Dec-2012
#
# Updates:
# 22-Jan-2013 jdw add option to export analog PRDCC definitions.
# 28-Jan-2013 jdw updated for change in return types for CvsSandboxAdmin() methods.
# 15-Oct-2013 jdw changed prdcc export to use prdcc_ in data_ section name.
##
"""
Execution environment for administrative operation on  BIRD PRD/FAMILY dictionary definitions.

"""
import sys
import os
import time
import traceback
import multiprocessing
from optparse import OptionParser

from mmcif_utils.bird.PdbxPrdIo import PdbxPrdIo
from mmcif_utils.bird.PdbxPrdCcIo import PdbxPrdCcIo
from mmcif_utils.bird.PdbxPrd import *
from mmcif_utils.bird.PdbxPrdUtils import PdbxPrdUtils
from wwpdb.utils.rcsb.CvsAdmin import CvsAdmin, CvsSandBoxAdmin


def readList(fn):
    try:
        idList = []
        ifh = open(fn, 'r')
        for line in ifh.readlines():
            tt = str(line[:-1]).strip()
            if len(tt) < 1 or tt.startswith("#"):
                continue
            idList.append(tt)
        return idList
    except Exception as e:
        return []


def exportList(dataList, fn=None):
    try:
        if fn is None:
            ofh = sys.stdout
            for datum in dataList:
                ofh.write("%s\n" % datum)
        else:
            ofh = open(fn, 'w')
            for datum in dataList:
                ofh.write("%s\n" % datum)
            ofh.close()
        #
        return True
    except Exception as e:
        return False


class PdbxPrdWorker(multiprocessing.Process):

    def __init__(self, taskQueue, resultQueue, pIndex=1, verbose=False, log=sys.stderr):
        multiprocessing.Process.__init__(self)
        self.__taskQueue = taskQueue
        self.__resultQueue = resultQueue

        self.__pIndex = pIndex
        #
        self.__verbose = verbose
        self.__lfh = log

    def run(self):
        processName = self.name
        while True:
            nextList = self.__taskQueue.get()
            if nextList is None:
                # end of queue condition
                if self.__verbose:
                    lt = time.strftime("%Y %m %d %H:%M:%S", time.localtime())
                    logger.info("+PdbLoaderExecWorker(run)  %s exiting at %s \n" % (processName, lt))
                break
            #

#            retList=pdbL.loadList(idList=nextList)
#            self.__resultQueue.put(retList)
        return


class PdbxPrdExec(object):
    """ Execution class for BIRD PRD/FAMILY dictionary definition administrative operations.

    """

    def __init__(self, topCachePath=None, topPrdCcCachePath=None, verbose=False, log=sys.stderr):
        self.__verbose = verbose
        self.__debug = True
        self.__lfh = log
        self.__topCachePath = topCachePath
        self.__topPrdCcCachePath = topPrdCcCachePath
        self.__pathList = []
        self.__setup()
        #

    def __setup(self):
        self.__cvsRepositoryPath = os.getenv("CVS_REPOSITORY_PATH")
        self.__cvsRepositoryHost = os.getenv("CVS_REPOSITORY_HOST")
        self.__cvsUser = os.getenv("CVS_REPOSITORY_USER")
        self.__cvsPassword = os.getenv("CVS_REPOSITORY_PASSWORD")

    def runSequential(self):
        """Run load  operations sequentially
        """
        if self.__verbose:
            lt = time.strftime("%Y %m %d %H:%M:%S", time.localtime())
            logger.info("+PdbxPrdExec(runSequential) beginning tasks at %s\n" % lt)
        #

        if self.__verbose:
            lt = time.strftime("%Y %m %d %H:%M:%S", time.localtime())
            logger.info("+PdbxPrdExec(runSequential) task completed at %s\n" % lt)
        #

    def run(self, numProc=0):
        """Run all load operations in mulitprocessing mode.
        """
        #
        if self.__verbose:
            lt = time.strftime("%Y %m %d %H:%M:%S", time.localtime())
            logger.info("+PdbxPrdExec(run) beginning tasks at %s\n" % lt)

    def getIdsByStatus(self, selectList=['ALL']):
        """Read all repository files and return id codes corresponding to input status options
        """
        logger.info("\nStarting %s %s\n" % (self.__class__.__name__,
                                            sys._getframe().f_code.co_name))
        rL = []
        try:
            if selectList is None or len(selectList) < 1:
                return rL
            #
            prd = PdbxPrdIo(verbose=self.__verbose, log=self.__lfh)
            prd.setCachePath(self.__topCachePath)
            self.__pathList = prd.makeDefinitionPathList()
            for pth in self.__pathList:
                prd.setFilePath(pth)
            if (self.__verbose):
                logger.info("Repository %s read completed\n" % self.__topCachePath)
            #
            prdU = PdbxPrdUtils(prd, verbose=self.__verbose, log=self.__lfh)
            statusD = prdU.getStatus()
            if 'ALL' in selectList:
                rL = sorted(statusD.keys())
            else:
                for id in sorted(statusD.keys()):
                    if statusD[id] in selectList:
                        rL.append(id)
            return rL
        except Exception as e:
            if self.__verbose:
                logger.exception("Failing with %s" % str(e))
            return []

    def getStatus(self):
        pass

    def exportList(self, idList=None, outPath=None, stripFlag=False, suppressCompFile=None, releaseDate=None):
        """Export concatenated/split file of PRD definitions corresponding to input PRD id code list.

           Return True for success or False otherwise.
        """
        _mId = "(" + self.__class__.__name__ + "." + sys._getframe().f_code.co_name + ")"
        if self.__verbose:
            logger.info("\n%s Starting\n" % _mId)
        try:
            if idList is None or outPath is None:
                return False

            prd = PdbxPrdIo(verbose=self.__verbose, log=self.__lfh)
            prd.setCachePath(self.__topCachePath)
            for id in idList:
                prd.setPrdId(prdId=id)
            if self.__verbose:
                logger.info("%s Repository read completed\n" % _mId)
            #
            prdU = PdbxPrdUtils(prd, verbose=self.__verbose, log=self.__lfh)
            if suppressCompFile is not None:
                if self.__verbose:
                    logger.info("%s Suppressing chemical component id codes from file %s \n" % (_mId, suppressCompFile))
                ccList = readList(suppressCompFile)
                prdU.suppressComponentsFromList(idList=ccList)

            if releaseDate is not None:
                if self.__verbose:
                    logger.info("%s Assigning release release status and audit date %s\n" % (_mId, releaseDate))
                cD = prdU.setReleaseAndAudit(relDate=releaseDate)
            #
            prd.writeFile(outPath, applyConstraints=stripFlag)

        except Exception as e:
            if self.__verbose:
                logger.exception("Failing with %s" % str(e))
            return []

    def exportPrdCcList(self, idList=None, stripFlag=False, outPath=None):
        """Export concatenated/split file or PRDCC analog definitions corresponding to input id PRD ID code list.

           Return True for success or False otherwise.
        """
        _mId = "(" + self.__class__.__name__ + "." + sys._getframe().f_code.co_name + ")"
        if self.__verbose:
            logger.info("\n%s Starting\n" % _mId)
        try:
            if idList is None or outPath is None:
                return False
            prd = PdbxPrdCcIo(verbose=self.__verbose, log=self.__lfh)
            prd.setCachePath(self.__topPrdCcCachePath)
            for id in idList:
                # convert PRD_ to PRDCC_ id code
                myId = "PRDCC_" + id[4:]
                filePath = os.path.join(self.__topPrdCcCachePath, myId[-1], myId + '.cif')
                if os.access(filePath, os.R_OK):
                    prd.setFilePath(filePath=filePath, prdCcId=myId)
                else:
                    pass
            if self.__verbose:
                logger.info("%s Repository read completed\n" % _mId)
            #
            # Change the name of the data_ section to the PRDCC_ prefix.
            cList = prd.getCurrentContainerList()
            for c in cList:
                id = c.getName()
                newId = 'PRDCC_' + id[4:]
                c.setName(newId)
            #
            prd.writeFile(outPath, applyConstraints=stripFlag)

        except Exception as e:
            if self.__verbose:
                logger.exception("Failing with %s" % str(e))
            return []

    def getChemCompIdList(self, idList=None):
        """Get the list of referenced chemical component id codes in the input list of PRD defnitions.

           Return a list of chemical component 3-letter codes.
        """
        _mId = "(" + self.__class__.__name__ + "." + sys._getframe().f_code.co_name + ")"
        if self.__verbose:
            logger.info("\n%s Starting\n" % _mId)
        try:
            if idList is None:
                return False

            prd = PdbxPrdIo(verbose=self.__verbose, log=self.__lfh)
            prd.setCachePath(self.__topCachePath)
            for id in idList:
                prd.setPrdId(prdId=id)
            if self.__verbose:
                logger.info("%s Repository read completed\n" % _mId)
            #
            prdU = PdbxPrdUtils(prd, verbose=self.__verbose, log=self.__lfh)
            ccD = prdU.getReferencedComponents()
            #
            rD = {}
            for prdId, ccL in ccD.items():
                for cc in ccL:
                    rD[cc] = cc

            return sorted(rD.keys())

        except Exception as e:
            if self.__verbose:
                logger.exception("Failing with %s" % str(e))
            return []

    def releaseList(self, idList=None, releaseDate=None):
        """Set the release/audit records for selected definitions in the working copy of the repository.
           The working copy is first updated, the status/audit records changed, and changed definitions
           are committed to the repository.

           Return True for success or False otherwise.
        """
        _mId = "(" + self.__class__.__name__ + "." + sys._getframe().f_code.co_name + ")"
        if self.__verbose:
            logger.info("\n%s Starting using releaseDate %s\n" % (_mId, releaseDate))
        try:
            if idList is None or releaseDate is None:
                return False

            (wrkPath, projDir) = os.path.split(self.__topCachePath)

            vc = CvsSandBoxAdmin(tmpPath="./")
            vc.setRepositoryPath(host=self.__cvsRepositoryHost, path=self.__cvsRepositoryPath)
            vc.setAuthInfo(user=self.__cvsUser, password=self.__cvsPassword)
            vc.setSandBoxTopPath(wrkPath)

            # first update the working directory with the latest files from the repository
            #
            for id in idList:
                hash = id[-1]
                relFilePath = os.path.join(hash, id + '.cif')
                #
                vc.update(projDir, relFilePath)

                # update the status items --
                #
                prd = PdbxPrdIo(verbose=self.__verbose, log=self.__lfh)
                prd.setCachePath(self.__topCachePath)
                prd.setPrdId(prdId=id)
                #
                prdU = PdbxPrdUtils(prd, verbose=self.__verbose, log=self.__lfh)
                if releaseDate is not None:
                    if self.__verbose:
                        logger.info("%s  %s assigning release release status and audit date %s\n" % (_mId, id, releaseDate))
                    cD = prdU.setReleaseAndAudit(relDate=releaseDate)
                #
                outPath = os.path.join(wrkPath, projDir, relFilePath)
                prd.writeFile(outPath, applyConstraints=False)
                #
                vc.commit(projDir, relFilePath)
            #
            if (not self.__debug):
                vc.cleanup()
            return True
        except Exception as e:
            if self.__verbose:
                logger.info("%s  error in release list processing\n" % _mId)
                logger.exception("Failing with %s" % str(e))
            return False

    def checkOut(self):
        """Checkout a working copy of the project within the repository.

           Return True for success or False otherwise.
        """
        _mId = "(" + self.__class__.__name__ + "." + sys._getframe().f_code.co_name + ")"
        if self.__verbose:
            logger.info("\n%s Starting\n" % _mId)
        try:
            (wrkPath, projDir) = os.path.split(self.__topCachePath)

            vc = CvsSandBoxAdmin(tmpPath="./", verbose=self.__verbose, log=self.__lfh)
            vc.setRepositoryPath(host=self.__cvsRepositoryHost, path=self.__cvsRepositoryPath)
            vc.setAuthInfo(user=self.__cvsUser, password=self.__cvsPassword)
            vc.setSandBoxTopPath(wrkPath)

            ok, text = vc.checkOut(projectPath=projDir)
            if self.__verbose:
                logger.info("\n%s CVS checkout output:\n%s\n" % (_mId, text))

            vc.cleanup()
            return True
        except Exception as e:
            if self.__verbose:
                logger.exception("Failing with %s" % str(e))
            return False


def main():
    _mId = "(" + sys._getframe().f_code.co_name + ")"
    usage = "usage: %prog [options]"
    #
    parser = OptionParser(usage)
    # parser.add_option("--numproc", default=10, type="int", dest="numProc", help="Number of concurent processes to run")

    parser.add_option("-v", "--verbose", default=False,
                      action="store_true", dest="verbose", help="Enable verbose output")

    parser.add_option("--prd_id", default=None, type="string", dest="prdId", help="Target PRD ID Code")

    parser.add_option("--set_cvs_release_status", dest="setReleaseStatusCvsOp", action='store_true', default=False,
                      help="Set release status and audit records in cvs repository")

    parser.add_option("--cvs_checkout", dest="cvsCheckOutOp", action='store_true', default=False,
                      help="Checkout a working copy of the current repository and project")

    parser.add_option("--strip_internal_items", dest="stripInternalOp", action='store_true', default=False,
                      help="Exclude internal data items in exported files")

    parser.add_option("--export_release_date", dest="exportReleaseDate", default=None, type="string",
                      help="Assign release status and audit records with YYYY-MM-DD in exported definitions")

    parser.add_option("--export_public_targzfile", dest="exportPubTgzOp", action='store_true', default=False,
                      help="Export split gzipped tarfile of PRDpublic definitions")

    parser.add_option("--export_public_file", dest="exportPubOp", action='store_true', default=False,
                      help="Export concatenated file of PRD public definitions")

    parser.add_option("--export_public_prdcc_targzfile", dest="exportPubPrdCcTgzOp", action='store_true', default=False,
                      help="Export split gzipped tarfile of PRDCC public definitions")

    parser.add_option("--export_public_prdcc_file", dest="exportPubPrdCcOp", action='store_true', default=False,
                      help="Export concatenated file of PRDCC public definitions")

    parser.add_option("--export_from_list", dest="exportListOp", action='store_true', default=False,
                      help="Export concatenated/split file from input id list")

    parser.add_option("--list_id_codes", dest="listIdCodesOp", default=None, type="string", help="List Id codes by status (ALL,REL,HOLD,..)")

    parser.add_option("--list_chem_comp_id_codes", dest="listChemCompIdCodesOp", action='store_true', default=False,
                      help="List id codes for referenced chemical components")

    parser.add_option("--suppress_chem_comp_file", dest="suppressCompFile", default=None, type="string",
                      help="File containing chemical component identifiers to be suppressed")

    parser.add_option("-o", "--outfile", dest="outputFilePath", default=None, type="string", help="Output file path")

    parser.add_option("-i", "--inpfile", dest="inputFilePath", default=None, type="string", help="Input file path")

    parser.add_option("--cvs_path", dest="topCachePath", default="/data/components/prd-v3", type="string", help="PRD CVS working directory path")

    parser.add_option("--cvs_prdcc_path", dest="topPrdCcCachePath", default="/data/components/prdcc-v3", type="string", help="PRDCC CVS working directory path")

    (options, args) = parser.parse_args()

    if (options.verbose):
        lt = time.strftime("%Y %m %d %H:%M:%S", time.localtime())
        sys.stdout.write("%s begin tasks at %s\n" % (_mId, lt))

    if options.cvsCheckOutOp:
        pX = PdbxPrdExec(topCachePath=options.topCachePath, verbose=options.verbose, log=sys.stdout)
        ok = pX.checkOut()

    elif options.setReleaseStatusCvsOp and (options.prdId is not None or options.inputFilePath is not None):

        if options.prdId is not None:
            if options.verbose:
                sys.stdout.write("%s set release status and audit records for %s\n" % (_mId, options.prdId))
            idList = [options.prdId]
        elif options.inputFilePath is not None:
            if options.verbose:
                sys.stdout.write("%s set release status and audit records for id code list file  %s\n" % (_mId, options.inputFilePath))
            idList = readList(inputFilePath)
        else:
            pass
        #
        if options.exportReleaseDate is not None:
            dt = options.exportReleaseDate
        else:
            dt = time.strftime("%Y-%m-%d", time.localtime())
        pX = PdbxPrdExec(topCachePath=options.topCachePath, verbose=options.verbose, log=sys.stdout)
        ok = pX.releaseList(idList=idList, releaseDate=dt)

    elif (options.exportPubOp or options.exportPubTgzOp) and options.outputFilePath is not None:
        if options.exportPubTgzOp and options.outputFilePath.endswith(".tar.gz"):
            sys.stdout.write("%s export split gzipped tarfile of public definitions in %s\n" % (_mId, options.outputFilePath))
        elif options.exportPubOp and options.outputFilePath is not None:
            sys.stdout.write("%s export concatenated file of public definitions in %s\n" % (_mId, options.outputFilePath))
        else:
            sys.stdout.write("%s bad input for export %s\n" % (_mId, options.outputFilePath))
            exit(2)

        pX = PdbxPrdExec(topCachePath=options.topCachePath, verbose=options.verbose, log=sys.stdout)
        idList = pX.getIdsByStatus(selectList=['REL', 'OBS'])

        ok = pX.exportList(idList=idList,
                           outPath=options.outputFilePath,
                           stripFlag=True,
                           suppressCompFile=options.suppressCompFile,
                           releaseDate=options.exportReleaseDate)

    elif (options.exportPubPrdCcOp or options.exportPubPrdCcTgzOp) and options.outputFilePath is not None:
        if options.exportPubPrdCcTgzOp and options.outputFilePath.endswith(".tar.gz"):
            sys.stdout.write("%s export split gzipped tarfile of public PRDCC analog definitions in %s\n" % (_mId, options.outputFilePath))
        elif options.exportPubPrdCcOp and options.outputFilePath is not None:
            sys.stdout.write("%s export concatenated file of public PRDCC analog definitions in %s\n" % (_mId, options.outputFilePath))
        else:
            sys.stdout.write("%s bad input for export %s\n" % (_mId, options.outputFilePath))
            exit(2)

        pX = PdbxPrdExec(topCachePath=options.topCachePath, topPrdCcCachePath=options.topPrdCcCachePath, verbose=options.verbose, log=sys.stdout)
        idList = pX.getIdsByStatus(selectList=['REL', 'OBS'])

        ok = pX.exportPrdCcList(idList=idList, outPath=options.outputFilePath, stripFlag=False)

    elif options.exportListOp and options.inputFilePath is not None:
        if options.verbose:
            sys.stdout.write("%s export concatenated file of definitions from input id file %s\n" % (_mId, options.inputFilePath))

        idList = readList(options.inputFilePath)

        pX = PdbxPrdExec(topCachePath=options.topCachePath, verbose=options.verbose, log=sys.stdout)
        ok = pX.exportList(idList=idList,
                           outPath=options.outputFilePath,
                           stripFlag=options.stripInternalOp,
                           suppressCompFile=options.suppressCompFile,
                           releaseDate=options.exportReleaseDate)

    elif options.listIdCodesOp is not None:
        if options.verbose:
            sys.stdout.write("%s list codes with status %s\n" % (_mId, options.listIdCodesOp))

        pX = PdbxPrdExec(topCachePath=options.topCachePath, verbose=options.verbose, log=sys.stdout)
        sL = pX.getIdsByStatus(selectList=[options.listIdCodesOp])

        if options.outputFilePath is not None:
            exportList(sL, fn=options.outputFilePath)
        else:
            exportList(sL)

    elif options.listChemCompIdCodesOp is not None:
        if options.verbose:
            sys.stdout.write("%s list id codes for referenced chemical components\n" % (_mId))

        pX = PdbxPrdExec(topCachePath=options.topCachePath, verbose=options.verbose, log=sys.stdout)
        prdIdList = pX.getIdsByStatus(selectList=['REL', 'OBS'])
        ccL = pX.getChemCompIdList(idList=prdIdList)
        if options.outputFilePath is not None:
            exportList(ccL, fn=options.outputFilePath)
        else:
            exportList(ccL)
    else:
        pass

    if (options.verbose):
        lt = time.strftime("%Y %m %d %H:%M:%S", time.localtime())
        sys.stdout.write("%s completed tasks at %s\n" % (_mId, lt))


if __name__ == "__main__":
    main()

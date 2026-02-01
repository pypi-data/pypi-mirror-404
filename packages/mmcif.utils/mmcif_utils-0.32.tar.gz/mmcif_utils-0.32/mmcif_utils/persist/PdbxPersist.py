##
# File: PdbxPersist.py
# Date: 9-Jan-2012  John Westbrook
#
# Updates:
# 20-Jan-2012  jdw refactor and simplify persisted data - using only primitive data types.
# 24-Jan-2012  jdw added code but did not implement some methods for locking if needed in future.
#
# 17-Feb-2012  jdw added convenience methods updating individual objects in stores -
#                 updateOneObject() -
#
# 20-Feb-2012  jdw adjustments to nomenclature in fetch methods.
# 21-Feb-2012  jdw Introduce lock file support within atomic store/fetch/update/... methods.
#                  This is also implemented more coarsely for open/close methods.
# 22-Feb-2012  jdw add move method with destination locking and reindexing.
# 24-Feb-2012  jdw add method to recover index store
#  8-Nov-2018  jdw/ep restore timeout and retry constructor arguments
#  9-Nov-2018  jdw add encoding of keys and indices.
#
##
"""
Class supporting Python dictionary level (by Pdbx category) persistence.

"""
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "john.westbrook@rcsb.org"
__license__ = "Apache 2.0"

import sys
import shelve
import shutil
import pickle
import logging
logger = logging.getLogger(__name__)

from mmcif.api.PdbxContainers import DefinitionContainer, DataContainer
from mmcif.api.DataCategory import DataCategory
from mmcif_utils.persist.LockFile import LockFile


class PdbxPersist(object):
    """ Persistent storage for instances of PDBx/mmCIF category objects.

    """

    def __init__(self, verbose=True, log=sys.stderr, **kwargs):
        self.__verbose = verbose
        self.__debug = True
        self.__lfh = log
        #
        self.__inputPdbxfilePath = None
        self.__containerList = []

        self.__containerNameList = []
        self.__containerTypeList = []
        self.__storeObjectIndex = False
        #
        # Parameters to tune lock file management --
        self.__timeoutSeconds = kwargs.get('timeoutSeconds', 10)
        self.__retrySeconds = kwargs.get('retrySeconds', 0.2)
        # placeholder for LockFile object for open/close methods
        self.__lockObj = None
        self.__isExpired = True
        self.__keyEncoding = kwargs.get('keyEncoding', 'ascii')
        self.__encodingErrors = kwargs.get('keyEncoding', 'xmlcharrefreplace')

        #
    def __encode(self, istring):
        if sys.version_info[0] < 3:
            # tS = istring.encode(self.__keyEncoding, errors=self.__encodingErrors)
            # logger.info("String: %r (%r) type %r (%r)" % (istring, tS, type(istring), type(tS)))
            return istring.encode(self.__keyEncoding, errors=self.__encodingErrors)
        else:
            # tS = istring.encode(self.__keyEncoding, errors=self.__encodingErrors).decode(self.__keyEncoding)
            # logger.info("String: %r (%r) type %r (%r)" % (istring, tS, type(istring), type(tS)))
            return istring.encode(self.__keyEncoding, errors=self.__encodingErrors).decode(self.__keyEncoding)

    def __reIndex(self):
        """ Rebuild name and type lists from container object list.
        """
        #
        self.__containerNameList = []
        self.__containerTypeList = []
        for container in self.__containerList:
            self.__containerNameList.append(self.__encode(container.getName()))
            self.__containerTypeList.append(self.__encode(container.getType()))
        #
        self.__isExpired = False

    def __getContainerIndex(self, name):
        try:
            if (self.__isExpired):
                self.__reIndex()
            return self.__containerNameList.index(self.__encode(name))
        except Exception as e:
            return None

    def setContainerList(self, containerList=None):
        """ Initialize container data in the internal containlist to be persisted to the data store.
        """
        try:
            self.__containerList = containerList
            self.__isExpired = True
            if (self.__debug):
                logger.info("+PdbxPersist.setContainerList() - Container list length %d\n" % len(self.__containerList))
            return True
        except Exception as e:
            if (self.__verbose):
                logger.info("+ERROR- PdbxPersist.setContainerList() initialization failed\n")
            if (self.__debug):
                logger.exception("Failing with %s" % str(e))
            return False

    def appendContainerList(self, containerList=None):
        """ Append container data to the internal containerlist to be persisted to the data store.
        """
        try:
            self.__containerList.extend(containerList)
            self.__isExpired = True
            if (self.__debug):
                logger.info("+PdbxPersist.appendContainerList() - Container list length %d\n" % len(self.__containerList))
            return True
        except Exception as e:
            if (self.__verbose):
                logger.info("+ERROR- PdbxPersist.appendContainerList() initialization failed\n")
            if (self.__debug):
                logger.exception("Failing with %s" % str(e))
            return False

    def getContainer(self, containerName):
        """ Return the container from internal containerlist corresponding to the input container name.

            **Note that this method is NOT directly fetching data from the internal store.  First recover the
            the store to internal storage before calling this method.
        """
        idx = self.__getContainerIndex(self.__encode(containerName))
        if idx is not None:
            return self.__containerList[idx]
        else:
            return None

    def getContainerList(self):
        """ Return the current container list.
        """
        return self.__containerList

    def getContainerNameList(self):
        """ Return the current list of container names.
        """
        if (self.__isExpired):
            self.__reIndex()
        return self.__containerNameList

    #
    def open(self, dbFileName="my.db", flag='r'):
        """ Open the persistent store with the input database file name and access mode.

            flag = 'r read-only'
                   'c/n new/create'
                   'w read/write'
        """
        try:
            self.__lockObj = LockFile(dbFileName, timeoutSeconds=self.__timeoutSeconds, retrySeconds=self.__retrySeconds,
                                      verbose=self.__verbose, log=self.__lfh)
            self.__lockObj.acquire()
            self.__db = shelve.open(dbFileName, flag=flag, protocol=pickle.HIGHEST_PROTOCOL)
            return True
        except Exception as e:
            if self.__lockObj is not None:
                self.__lockObj.release()
            if (self.__verbose):
                logger.info("+ERROR- PdbxPersist.open() write failed for file %s\n" % dbFileName)
            if (self.__debug):
                logger.exception("Failing with %s" % str(e))
            return False

    def getStoreContainerIndex(self):
        try:
            return self.__db['__index__']
        except Exception as e:
            return []

    def close(self):
        """ Close the persistent store
        """
        try:
            self.__db.shelve.close()
            if self.__lockObj is not None:
                self.__lockObj.release()
            return True
        except Exception as e:
            if self.__lockObj is not None:
                self.__lockObj.release()
            return False

    def moveStore(self, srcDbFilePath, dstDbFilePath):
        """ Move source store to destination store with destination locking.

            No locking is performed on the source file.
        """
        with LockFile(dstDbFilePath, timeoutSeconds=self.__timeoutSeconds, retrySeconds=self.__retrySeconds, verbose=self.__verbose, log=self.__lfh) as lf:
            retVal = self.__moveStore(srcDbFilePath, dstDbFilePath)
        return retVal

    def store(self, dbFileName="my.db"):
        """ Store the current container list in persistent database.
        """
        with LockFile(dbFileName, timeoutSeconds=self.__timeoutSeconds, retrySeconds=self.__retrySeconds, verbose=self.__verbose, log=self.__lfh) as lf:
            retVal = self.__storeShelve(dbFileName)
        return retVal

    def recover(self, dbFileName="my.db"):
        """ Recover the stored state to the current in-memory container representation.
        """
        with LockFile(dbFileName, timeoutSeconds=self.__timeoutSeconds, retrySeconds=self.__retrySeconds, verbose=self.__verbose, log=self.__lfh) as lf:
            retVal = self.__recoverShelve(dbFileName)
        return retVal

    def getIndex(self, dbFileName="my.db"):
        """ Recover the index of the persistent store.
        """
        with LockFile(dbFileName, timeoutSeconds=self.__timeoutSeconds, retrySeconds=self.__retrySeconds, verbose=self.__verbose, log=self.__lfh) as lf:
            retVal = self.__indexShelve(dbFileName)
        return retVal

    def updateOneObject(self, inputObject, dbFileName="my.db", containerName=None, containerType='data'):
        """ Update or append an object to a container in an existing store.
        """
        with LockFile(dbFileName, timeoutSeconds=self.__timeoutSeconds, retrySeconds=self.__retrySeconds, verbose=self.__verbose, log=self.__lfh) as lf:
            retVal = self.__updateObjectShelve(dbFileName=dbFileName, containerName=containerName, inputObject=inputObject, containerType=containerType)
        return retVal

    def updateContainerList(self, dbFileName="my.db", containerList=None):
        """ Update or append the contents of the input container list to an existing store.
        """
        with LockFile(dbFileName, timeoutSeconds=self.__timeoutSeconds, retrySeconds=self.__retrySeconds, verbose=self.__verbose, log=self.__lfh) as lf:
            retVal = self.__updateContainerListShelve(dbFileName=dbFileName, updateContainerList=containerList)
        return retVal

    def fetchOneObject(self, dbFileName="my.db", containerName=None, objectName=None):
        """  Fetch a single object from a named container.  This is atomic operation with respect to the store.
        """
        with LockFile(dbFileName, timeoutSeconds=self.__timeoutSeconds, retrySeconds=self.__retrySeconds, verbose=self.__verbose, log=self.__lfh) as lf:
            retVal = self.__fetchOneObjectShelve(dbFileName, containerName, objectName)
        return retVal

    def fetchObject(self, containerName=None, objectName=None):
        """ Fetch object from container from an open store.

            Use this method to extract multiple objects from a store.
        """
        return self.__fetchObjectShelve(containerName, objectName)

    def __moveStore(self, src, dst):
        """  Internal method to perform file move.
        """
        try:
            shutil.move(src, dst)
            return True
        except Exception as e:
            if (self.__verbose):
                logger.info("+ERROR- PdbxPersist.__moveStore() move failed for file %s\n" % src)
            if (self.__debug):
                logger.exception("Failing with %s" % str(e))
            return False

    def __storeShelve(self, dbFileName="my.db"):
        """  Create a new persistent store using the internal object list within the current container list.
        """
        try:
            if (self.__isExpired):
                self.__reIndex()
            db = shelve.open(dbFileName, flag='c', protocol=pickle.HIGHEST_PROTOCOL)
            db['__index__'] = self.__containerNameList
            db['__types__'] = self.__containerTypeList
            if (self.__debug):
                logger.info("+PdbxPersist.__storeShelve() - Container list length  %d\n" % len(self.__containerList))
            for ii, container in enumerate(self.__containerList):
                objNameList = container.getObjNameList()
                #
                # store the object name index for this container.
                #
                containerName = container.getName()
                ky = containerName + "||__index__"
                db[self.__encode(ky)] = objNameList
                #
                for objName in objNameList:
                    d = {}
                    d['name'], d['aL'], d['rL'] = container.getObj(objName).get()
                    ky = containerName + "||" + objName
                    db[self.__encode(ky)] = d
            db.close()
            return True
        except Exception as e:
            if (self.__verbose):
                logger.info("+ERROR- PdbxPersist.__storeShelve() shelve store failed for file %s\n" % dbFileName)
            if (self.__debug):
                logger.exception("Failing with %s" % str(e))
            return False

    def __indexShelve(self, dbFileName="my.db"):
        """  Recover the index of containers and objects in the persistent store.
        """
        try:
            indexD = {}
            db = shelve.open(dbFileName, flag='r', protocol=pickle.HIGHEST_PROTOCOL)
            containerNameList = db['__index__']
            containerTypeList = db['__types__']
            indexD['__containers__'] = []
            for ii, containerName in enumerate(containerNameList):
                #
                indexD['__containers__'].append((containerName, containerTypeList[ii]))
                #
                ky = containerName + "||__index__"
                objNameList = db[self.__encode(ky)]
                #
                indexD[containerName] = []
                for objName in objNameList:
                    indexD[containerName].append(objName)

            db.close()
            return indexD
        except Exception as e:
            if (self.__verbose):
                logger.info("+ERROR- PdbxPersist.__indexShelve() shelve index failed for file %s\n" % dbFileName)
            if (self.__debug):
                logger.exception("Failing with %s" % str(e))
            return {}

    def __recoverShelve(self, dbFileName="my.db"):
        """  Recover the list of containers and their object contents from the persistent store.
        """
        try:
            self.__containerList = []
            db = shelve.open(dbFileName, flag='r', protocol=pickle.HIGHEST_PROTOCOL)
            self.__containerNameList = db['__index__']
            self.__containerTypeList = db['__types__']
            if (self.__debug):
                logger.info("+PdbxPersist.__recoverShelve() - Container name list %r\n" % self.__containerNameList)
                logger.info("+PdbxPersist.__recoverShelve() - Container type list %r\n" % self.__containerTypeList)

            for ii, containerName in enumerate(self.__containerNameList):
                if self.__containerTypeList[ii] == 'data':
                    dC = DataContainer(containerName)
                else:
                    dC = DefinitionContainer(containerName)
                #
                ky = containerName + "||__index__"
                objNameList = db[self.__encode(ky)]

                for objName in objNameList:
                    ky = containerName + "||" + objName
                    d = db[self.__encode(ky)]
                    dObj = DataCategory(name=d['name'], attributeNameList=d['aL'], rowList=d['rL'])
                    dC.append(dObj)
                self.__containerList.append(dC)

            db.close()
            return True
        except Exception as e:
            if (self.__verbose):
                logger.info("+ERROR- PdbxPersist.__recoverShelve() shelve recover failed for file %s\n" % dbFileName)
            if (self.__debug):
                logger.exception("Failing with %s" % str(e))
            return False

    def __fetchOneObjectShelve(self, dbFileName="my.db", containerName=None, objectName=None):
        """ Recover the object from from persistent store corresponding to the
            input container and object name.
        """
        try:
            #
            db = shelve.open(dbFileName, flag='r', protocol=pickle.HIGHEST_PROTOCOL)
            ky = containerName + '||' + objectName
            d = db[self.__encode(ky)]
            outObject = DataCategory(name=d['name'], attributeNameList=d['aL'], rowList=d['rL'])
            db.close()
            return outObject
        except Exception as e:
            if (self.__verbose):
                logger.info("+ERROR- PdbxPersist.__fetchOneObjectShelve() shelve fetch failed for file %s %s %s \n"
                            % (dbFileName, containerName, objectName))
            if (self.__debug):
                logger.exception("Failing with %s" % str(e))
            return None

    def __fetchObjectShelve(self, containerName=None, objectName=None):
        """ Recover the object from from persistent store corresponding to the
            input container and object name.

            shelve store must be opened from prior call.
        """
        try:
            #
            ky = containerName + '||' + objectName
            d = self.__db[self.__encode(ky)]
            outObject = DataCategory(name=d['name'], attributeNameList=d['aL'], rowList=d['rL'])
            return outObject
        except Exception as e:
            if (self.__debug):
                logger.info("+ERROR- PdbxPersist.__fetchObjectShelve() shelve fetch failed %s %s \n"
                            % (containerName, objectName))
            if (self.__debug):
                logger.exception("Failing with %s" % str(e))
            #
            return None

    def __updateObjectShelve(self, dbFileName="my.db", containerName=None, inputObject=None, containerType='data'):
        """ Update/append the single input object into the named container in the persistent store.
        """
        try:
            objectName = self.__encode(inputObject.getName())
            containerName = self.__encode(containerName)
            #
            db = shelve.open(dbFileName, flag='w', protocol=pickle.HIGHEST_PROTOCOL)
            #
            # get container index -
            #
            containerNameList = db['__index__']
            containerTypeList = db['__types__']
            #
            # Modify or append input container --
            #
            cExists = True
            if containerName in containerNameList:
                idx = containerNameList.index(containerName)
                containerTypeList[idx] = containerType
            else:
                cExists = False
                containerNameList.append(containerName)
                containerTypeList.append(containerType)
            #
            # store updated container index lists -
            #
            db['__index__'] = containerNameList
            db['__types__'] = containerTypeList
            #
            # ------------------------------------------
            # Get object index for the target container
            #   store updates if needed --
            #
            ky = containerName + "||__index__"
            if (cExists):
                objectNameList = db[ky]
            else:
                objectNameList = []

            oExists = True
            if objectName in objectNameList:
                idx = objectNameList.index(objectName)
            else:
                oExists = False
                objectNameList.append(objectName)
                db[ky] = objectNameList

            # ---------------------------------
            #    Update the object contents --
            #
            ky = containerName + "||" + objectName

            d = {}
            d['name'], d['aL'], d['rL'] = inputObject.get()
            db[ky] = d
            db.close()
            return True
        except Exception as e:
            if (self.__verbose):
                logger.info("+ERROR- PdbxPersist.__updateObjectShelve() update failed for file %s %s \n" % (dbFileName, containerName))
            if (self.__debug):
                logger.exception("Failing with %s" % str(e))
            return False

    def __updateContainerListShelve(self, dbFileName="my.db", updateContainerList=None):
        """ Update/append the contents of the input container list into an existing persistent store.
        """
        try:
            db = shelve.open(dbFileName, flag='w', protocol=pickle.HIGHEST_PROTOCOL)
            #
            # get container index -
            #
            containerNameList = db['__index__']
            containerTypeList = db['__types__']

            for updateContainer in updateContainerList:
                #
                updateContainerName = self.__encode(updateContainer.getName())
                updateContainerType = self.__encode(updateContainer.getType())
                #
                # Modify or append input container --
                #
                cExists = True
                if updateContainerName in containerNameList:
                    idx = containerNameList.index(updateContainerName)
                    containerTypeList[idx] = updateContainerType
                else:
                    cExists = False
                    containerNameList.append(updateContainerName)
                    containerTypeList.append(updateContainerType)
                #
                # Store updated container index lists -
                #
                db['__index__'] = containerNameList
                db['__types__'] = containerTypeList

                #
                # ------------------------------------------
                # Get object index for the target container
                #   and store updates if needed --
                #
                idxKy = updateContainerName + "||__index__"
                if (cExists):
                    objectNameList = db[idxKy]
                else:
                    objectNameList = []

                #
                updateObjectNameList = updateContainer.getObjNameList()
                #
                for updateObjectName in updateObjectNameList:
                    updateObject = updateContainer.getObj(updateObjectName)
                    oExists = True
                    if updateObjectName not in objectNameList:
                        oExists = False
                        objectNameList.append(updateObjectName)
                        db[idxKy] = objectNameList

                    # ---------------------------------
                    #   Now update the object contents --
                    #
                    ky = updateContainerName + "||" + updateObjectName
                    d = {}
                    d['name'], d['aL'], d['rL'] = updateObject.get()
                    db[ky] = d
            #
            db.close()
            return True
        except Exception as e:
            if (self.__verbose):
                logger.info("+ERROR- PdbxPersist.__updateContainerListShelve() update failed for store %s\n" % dbFileName)
            if (self.__debug):
                logger.exception("Failing with %s" % str(e))
            return False

    def __attributePart(self, name):
        i = name.find(".")
        if i == -1:
            return None
        else:
            return name[i + 1:]

    ##
    # Obsolete methods -- which serial objects as well as data -- found to be less efficient.
    ##
    def __fetchOneObjectShelve2(self, dbFileName="my.db", containerName=None, objectName=None):
        """ Recover the object from from persistent store corresponding to the
            input container and object name.
        """
        try:
            #
            db = shelve.open(dbFileName, flag='r', protocol=pickle.HIGHEST_PROTOCOL)
            ky = containerName + '||' + objectName
            outContainer = db[self.__encode(ky)]
            db.close()
            return outContainer
        except Exception as e:
            if (self.__verbose):
                logger.info("+ERROR- PdbxPersist.__fetchOneObjectShelve() shelve fetch failed for file %s %s %s \n"
                            % (dbFileName, containerName, objectName))
            if (self.__debug):
                logger.exception("Failing with %s" % str(e))
            return None

    def __storeShelve2(self, dbFileName="my.db"):
        """  Create a new store the object list in the current container list into the persistent store.
        """

        try:
            db = shelve.open(dbFileName, flag='c', protocol=pickle.HIGHEST_PROTOCOL)
            # print self.__containerNameList
            db['__index__'] = self.__containerNameList
            db['__types__'] = self.__containerTypeList
            for ii, container in enumerate(self.__containerList):
                objNameList = container.getObjNameList()
                #
                # store the object name index for this container.
                #
                containerName = container.getName()
                ky = containerName + "||__index__"
                db[self.__encode(ky)] = objNameList
                #
                for objName in objNameList:
                    dObj = container.getObj(objName)
                    ky = containerName + "||" + objName
                    db[self.__encode(ky)] = dObj
            db.close()
            return True
        except Exception as e:
            if (self.__verbose):
                logger.info("+ERROR- PdbxPersist.__storeShelve() shelve store failed for file %s\n" % dbFileName)
            if (self.__debug):
                logger.exception("Failing with %s" % str(e))
            return False

    def __recoverShelve2(self, dbFileName="my.db"):
        """  Recover the list of containers and their object contents from the persistent store.
        """
        try:
            self.__containerList = []
            db = shelve.open(dbFileName, flag='r', protocol=pickle.HIGHEST_PROTOCOL)
            self.__containerNameList = db['__index__']
            self.__containerTypeList = db['__types__']
            for ii, containerName in enumerate(self.__containerNameList):
                if self.__containerTypeList[ii] == 'data':
                    dC = DataContainer(containerName)
                else:
                    dC = DefinitionContainer(containerName)
                #
                ky = containerName + "||__index__"
                objNameList = db[self.__encode(ky)]

                for objName in objNameList:
                    ky = containerName + "||" + objName
                    dObj = db[self.__encode(ky)]
                    dC.append(dObj)
                self.__containerList.append(dC)

            db.close()
            return True
        except Exception as e:
            if (self.__verbose):
                logger.info("+ERROR- PdbxPersist.__recoverShelve() shelve recover failed for file %s\n" % dbFileName)
            if (self.__debug):
                logger.exception("Failing with %s" % str(e))
            return False

    def __updateObjectShelve2(self, dbFileName="my.db", containerName=None, inputObject=None, containerType='data'):
        """ Update/append the input object into the named container in the persistent store.
        """
        try:
            objectName = self.__encode(inputObject.getName())
            containerName = self.__encode(containerName)
            #
            db = shelve.open(dbFileName, flag='w', protocol=pickle.HIGHEST_PROTOCOL)
            #
            # get container index -
            #
            containerNameList = db['__index__']
            containerTypeList = db['__types__']
            #
            # Modifying or appending containers --
            #
            cExists = True
            if containerName in containerNameList:
                idx = containerNameList.index(containerName)
                containerTypeList[idx] = containerType
            else:
                cExists = False
                containerNameList.append(containerName)
                containerTypeList.append(containerType)
            #
            # store updated container index lists -
            #
            db['__index__'] = containerNameList
            db['__types__'] = containerTypeList
            #
            # ------------------------------------------
            # Get object index for the target container
            #   store updates if needed --
            #
            ky = containerName + "||__index__"
            if (cExists):
                objectNameList = db[ky]
            else:
                objectNameList = []

            oExists = True
            if objectName in objectNameList:
                idx = objectNameList.index(objectName)
            else:
                oExists = False
                objectNameList.append(objectName)
                db[ky] = objectNameList

            # ---------------------------------
            #    Update the object contents --
            #
            ky = containerName + "||" + objectName
            db[ky] = inputObject
            db.close()
            return True
        except Exception as e:
            if (self.__verbose):
                logger.info("+ERROR- PdbxPersist.__updateObjectShelve() update failed for file %s %s \n" % (dbFileName, containerName))
            if (self.__debug):
                logger.exception("Failing with %s" % str(e))
            return False

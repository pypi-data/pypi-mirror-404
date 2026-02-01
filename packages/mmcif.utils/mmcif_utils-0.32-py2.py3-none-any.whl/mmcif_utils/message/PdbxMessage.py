##
# File:    PdbxMessage.py
# Author:  J. Westbrook
# Date:    6-Aug-2013
# Version: 0.001 Initial version
#
# Updates:
#     7-Aug-2013 jdw  added file reference data
#    15-Aug-2013 jdw  added class PdbxMessageStatus()
#    15-Aug-2013 jdw  chain read status to send status in PdbxMessageInfo()
#    15-Aug-2013 rps  correcting typo for 'send_status' default value
#    12-Sep-2013 rps  switching from use of localtime to GMT time for standardization of message timestamps across sites.
#    30-Oct-2013 rps  support for UI feature for classifying messages (e.g. "action required" or "unread")
#    29-Jul-2014 rps  added set/getUploadFileName to support multiple file references for a single message
#                        (i.e. so that original name can be used to more easily distinguish one file reference from another).
#    09-Sep-2014 rps  Added PdbxMessageOrigCommReference.
##
"""
A class for managing message data --

"""
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "john.westbrook@rcsb.org"
__license__ = "Apache 2.0"
__version__ = "V0.001"

import sys
import time

import logging
logger = logging.getLogger(__name__)

from mmcif_utils.style.PdbxMessageCategoryStyle import PdbxMessageCategoryStyle


class PdbxMessageInfo(object):

    def __init__(self, verbose=True, log=sys.stderr):
        self.__verbose = verbose
        self.__lfh = log
        self.__stObj = PdbxMessageCategoryStyle()
        self.__attributeIdList = self.__stObj.getAttributeNameList('pdbx_deposition_message_info')
        self.__D = self.__setup()

    def __getMessageId(self):
        try:
            import uuid
            return str(uuid.uuid4())
        except Exception as e:
            import random
            import string
            chars = string.ascii_lowercase + string.digits
            string = ''.join(random.choice(chars) for x in range(8))
            string += '-' + ''.join(random.choice(chars) for x in range(4))
            string += '-' + ''.join(random.choice(chars) for x in range(4))
            string += '-' + ''.join(random.choice(chars) for x in range(4))
            string += '-' + ''.join(random.choice(chars) for x in range(12))
            return string

    def __setup(self):
        # initialize the dictionary
        d = {}
        for ky in self.__attributeIdList:
            d[ky] = None
        #
        # set default values -
        gmtTmStmp = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
        d["message_id"] = self.__getMessageId()
        d["parent_message_id"] = d["message_id"]
        d["timestamp"] = gmtTmStmp
        d["message_type"] = "text"
        d["send_status"] = "N"
        #
        return d

    def get(self):
        return self.__D

    def set(self, messageDict={}):
        d = {}
        d = self.__setup()
        for k, v in messageDict.items():
            # only add know attributes --
            if k in self.__attributeIdList:
                d[k] = v
        #
        self.__D = d
        return d

    def write(self, ofh=sys.stdout):
        for attributeId in self.__attributeIdList:
            ofh.write("%-30s : %-s\n" % (attributeId, self.__D[attributeId]))

    def setOrdinalId(self, id=None):
        self.__D['ordinal_id'] = id

    def getOrdinalId(self):
        return self.__D["ordinal_id"]

    def setMessageId(self, id=None):
        if id is None:
            d["message_id"] = str(uidd.uidd4())

    def getMessageId(self):
        return self.__D["message_id"]

    def setDepositionId(self, id=None):
        self.__D['deposition_data_set_id'] = id

    def getDepositionId(self):
        return self.__D['deposition_data_set_id']

    def setSender(self, sender=None):
        self.__D["sender"] = sender

    def getSender(self):
        return self.__D["sender"]

    def setContextType(self, type=None):
        self.__D["context_type"] = type

    def getContextType(self):
        return self.__D["context_type"]

    def setContextValue(self, val=None):
        self.__D["context_value"] = val

    def getContextValue(self):
        return self.__D["context_value"]

    def setParentMessageId(self, id=None):
        self.__D["parent_message_id"] = id

    def getParentMessageId(self):
        return self.__D["parent_message_id"]

    def setMessageType(self, type=None):
        self.__D["message_type"] = type

    def getMessageType(self):
        return self.__D["message_type"]

    def setMessageSubject(self, txt=None):
        self.__D["message_subject"] = txt

    def getMessageSubject(self):
        return self.__D["message_subject"]

    def setMessageText(self, txt=None):
        self.__D["message_text"] = txt

    def getMessageText(self):
        return self.__D["message_text"]

    def setSendStatus(self, status='N'):
        self.__D["send_status"] = status

    def getSendStatus(self):
        return self.__D["send_status"]

    def getValueList(self, attributeIdList=[]):
        vL = []
        for attributeId in attributeIdList:
            if attributeId in self.__D:
                vL.append(self.__D[attributeId])
            else:
                vL.append(None)
        return vL


class PdbxMessageFileReference(object):

    def __init__(self, verbose=True, log=sys.stderr):
        self.__verbose = verbose
        self.__lfh = log
        self.__stObj = PdbxMessageCategoryStyle()
        self.__attributeIdList = self.__stObj.getAttributeNameList('pdbx_deposition_message_file_reference')
        self.__D = self.__setup()

    def __setup(self):
        # initialize the dictionary
        d = {}
        for ky in self.__attributeIdList:
            d[ky] = None
        #
        #
        return d

    def get(self):
        return self.__D

    def set(self, messageDict={}):
        d = {}
        d = self.__setup()
        for k, v in messageDict.items():
            # only add know attributes --
            if k in self.__attributeIdList:
                d[k] = v
        #
        self.__D = d
        return d

    def write(self, ofh=sys.stdout):
        for attributeId in self.__attributeIdList:
            ofh.write("%-30s : %-s\n" % (attributeId, self.__D[attributeId]))

    def setOrdinalId(self, id=None):
        self.__D['ordinal_id'] = id

    def getOrdinalId(self):
        return self.__D["ordinal_id"]

    def setMessageId(self, id=None):
        self.__D["message_id"] = id

    def getMessageId(self):
        return self.__D["message_id"]

    def setDepositionId(self, id=None):
        self.__D['deposition_data_set_id'] = id

    def getDepositionId(self):
        return self.__D['deposition_data_set_id']

    def setContentType(self, type=None):
        self.__D["content_type"] = type

    def getContentType(self):
        return self.__D["content_type"]

    def setContentFormat(self, type=None):
        self.__D["content_format"] = type

    def getContentFormat(self):
        return self.__D["content_format"]

    def setUploadFileName(self, fileName=""):
        self.__D["upload_file_name"] = fileName

    def getUploadFileName(self):
        return self.__D["upload_file_name"]

    def setStorageType(self, type=None):
        self.__D["storage_type"] = type

    def getStorageType(self):
        return self.__D["storage_type"]

    def setPartitionNumber(self, val=None):
        self.__D["partition_number"] = val

    def getPartitionNumber(self):
        return self.__D["partition_number"]

    def setVersionId(self, val=None):
        self.__D["version_id"] = val

    def getVersionId(self):
        return self.__D["version_id"]


class PdbxMessageOrigCommReference(object):

    def __init__(self, verbose=True, log=sys.stderr):
        self.__verbose = verbose
        self.__lfh = log
        self.__stObj = PdbxMessageCategoryStyle()
        self.__attributeIdList = self.__stObj.getAttributeNameList('pdbx_deposition_message_origcomm_reference')
        self.__D = self.__setup()

    def __setup(self):
        # initialize the dictionary
        d = {}
        for ky in self.__attributeIdList:
            d[ky] = None
        #
        #
        return d

    def get(self):
        return self.__D

    def set(self, messageDict={}):
        d = {}
        d = self.__setup()
        for k, v in messageDict.items():
            # only add know attributes --
            if k in self.__attributeIdList:
                d[k] = v
        #
        self.__D = d
        return d

    def write(self, ofh=sys.stdout):
        for attributeId in self.__attributeIdList:
            ofh.write("%-30s : %-s\n" % (attributeId, self.__D[attributeId]))

    def setOrdinalId(self, id=None):
        self.__D['ordinal_id'] = id

    def getOrdinalId(self):
        return self.__D["ordinal_id"]

    def setMessageId(self, id=None):
        self.__D["message_id"] = id

    def getMessageId(self):
        return self.__D["message_id"]

    def setDepositionId(self, id=None):
        self.__D['deposition_data_set_id'] = id

    def getDepositionId(self):
        return self.__D['deposition_data_set_id']

    def setOrigMessageId(self, origId=None):
        self.__D["orig_message_id"] = origId

    def getOrigMessageId(self):
        return self.__D["orig_message_id"]

    def setOrigDepositionId(self, origDepId=None):
        self.__D["orig_deposition_data_set_id"] = origDepId

    def getOrigDepositionId(self):
        return self.__D["orig_deposition_data_set_id"]

    def setOrigTimeStamp(self, origTimeStamp=None):
        self.__D["orig_timestamp"] = origTimeStamp

    def getOrigTimeStamp(self):
        return self.__D["orig_timestamp"]

    def setOrigSender(self, origSender=None):
        self.__D["orig_sender"] = origSender

    def getOrigSender(self):
        return self.__D["orig_sender"]

    def setOrigRecipient(self, origRecipient=None):
        self.__D["orig_recipient"] = origRecipient

    def getOrigRecipient(self):
        return self.__D["orig_recipient"]

    def setOrigMessageSubject(self, subject=None):
        self.__D["orig_message_subject"] = subject

    def getOrigMessageSubject(self):
        return self.__D["orig_message_subject"]

    def setOrigAttachments(self, origAttachments=None):
        self.__D["orig_attachments"] = origAttachments

    def getOrigAttachments(self):
        return self.__D["orig_attachments"]


class PdbxMessageStatus(object):

    def __init__(self, verbose=True, log=sys.stderr):
        self.__verbose = verbose
        self.__lfh = log
        self.__stObj = PdbxMessageCategoryStyle()
        self.__attributeIdList = self.__stObj.getAttributeNameList('pdbx_deposition_message_status')
        self.__D = self.__setup()

    def __setup(self):
        # initialize the dictionary
        d = {}
        for ky in self.__attributeIdList:
            d[ky] = None
        #
        #
        return d

    def get(self):
        return self.__D

    def set(self, messageDict={}):
        d = {}
        d = self.__setup()
        for k, v in messageDict.items():
            # only add know attributes --
            if k in self.__attributeIdList:
                d[k] = v
        #
        self.__D = d
        return d

    def write(self, ofh=sys.stdout):
        for attributeId in self.__attributeIdList:
            ofh.write("%-30s : %-s\n" % (attributeId, self.__D[attributeId]))

    def setMessageId(self, id=None):
        self.__D["message_id"] = id

    def getMessageId(self):
        return self.__D["message_id"]

    def setDepositionId(self, id=None):
        self.__D['deposition_data_set_id'] = id

    def getDepositionId(self):
        return self.__D['deposition_data_set_id']

    def setReadStatus(self, status='N'):
        self.__D["read_status"] = status

    def getReadStatus(self):
        return self.__D["read_status"]

    def setActionReqdStatus(self, status='N'):
        self.__D["action_reqd"] = status

    def getActionReqdStatus(self):
        return self.__D["action_reqd"]

    def setReadyForRelStatus(self, status='N'):
        self.__D["for_release"] = status

    def getReadyForRelStatus(self):
        return self.__D["for_release"]

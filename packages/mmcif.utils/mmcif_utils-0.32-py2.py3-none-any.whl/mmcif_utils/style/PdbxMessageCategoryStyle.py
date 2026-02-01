##
# File: PdbxMessageInfoCategoryStyle.py
# Date: 6-Aug-2013  John Westbrook
#
# Updates:
#  2013-08-13   RPS  corrected typos in category name identifiers
#
#  15-Aug-2013  jdw  change read_status to send_status in  'pdbx_deposition_message_info'
#  15-Aug-2013  jdw  add category 'pdbx_deposition_message_status'
#  15-Aug-2013  RPS  changed 'read_status' to 'send_status' in 'pdbx_deposition_message_info'
#  30-Oct-2013  rps  added _pdbx_deposition_message_status.action_reqd to support UI feature
#                    for classifying messages (e.g. "action required", "unread")
#  29-Jul-2014  rps  added '_pdbx_deposition_message_file_reference.upload_file_name' to support
#                    multiple file references for a single message (i.e. so that original name can be
#                    used to more easily distinguish one file reference from another).
#  04-Dec-2014  rps  Added category, pdbx_deposition_message_origcomm_reference.
#                    Added item, pdbx_deposition_message_status.for_release.
#   5-Mar-2018  jdw Py2-Py3 and refactor for Python Packaging
##
"""
Standard style details for depositor message data.

"""
from __future__ import absolute_import
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "john.westbrook@rcsb.org"
__license__ = "Apache 2.0"


from mmcif_utils.style.PdbxCategoryStyleBase import PdbxCategoryStyleBase


class PdbxMessageCategoryStyle(PdbxCategoryStyleBase):
    #
    _styleId = "PDBX_DEPOSITION_MESSAGE_INFO_V1"

    _categoryInfo = [('pdbx_deposition_message_info', 'table'),
                     ('pdbx_deposition_message_data', 'table'),
                     ('pdbx_deposition_message_file_reference', 'table'),
                     ('pdbx_deposition_message_origcomm_reference', 'table'),
                     ('pdbx_deposition_message_status', 'table')
                     ]

    _cDict = {
        'pdbx_deposition_message_info': [
            ('_pdbx_deposition_message_info.ordinal_id', '%s', 'str', ''),
            ('_pdbx_deposition_message_info.message_id', '%s', 'str', ''),
            ('_pdbx_deposition_message_info.deposition_data_set_id', '%s', 'str', ''),
            ('_pdbx_deposition_message_info.timestamp', '%s', 'str', ''),
            ('_pdbx_deposition_message_info.sender', '%s', 'str', ''),
            ('_pdbx_deposition_message_info.context_type', '%s', 'str', ''),
            ('_pdbx_deposition_message_info.context_value', '%s', 'str', ''),
            ('_pdbx_deposition_message_info.parent_message_id', '%s', 'str', ''),
            ('_pdbx_deposition_message_info.message_subject', '%s', 'str', ''),
            ('_pdbx_deposition_message_info.message_text', '%s', 'str', ''),
            ('_pdbx_deposition_message_info.message_type', '%s', 'str', ''),
            ('_pdbx_deposition_message_info.send_status', '%s', 'str', '')
        ],
        'pdbx_deposition_message_data': [
            ('_pdbx_deposition_message_data.ordinal_id', '%s', 'str', ''),
            ('_pdbx_deposition_message_data.message_id', '%s', 'str', ''),
            ('_pdbx_deposition_message_data.deposition_data_set_id', '%s', 'str', ''),
            ('_pdbx_deposition_message_data.message_type', '%s', 'str', ''),
            ('_pdbx_deposition_message_data.message_subject', '%s', 'str', ''),
            ('_pdbx_deposition_message_data.message_text', '%s', 'str', '')
        ],
        'pdbx_deposition_message_file_reference': [
            ('_pdbx_deposition_message_file_reference.ordinal_id', '%s', 'str', ''),
            ('_pdbx_deposition_message_file_reference.message_id', '%s', 'str', ''),
            ('_pdbx_deposition_message_file_reference.deposition_data_set_id', '%s', 'str', ''),
            ('_pdbx_deposition_message_file_reference.content_type', '%s', 'str', ''),
            ('_pdbx_deposition_message_file_reference.content_format', '%s', 'str', ''),
            ('_pdbx_deposition_message_file_reference.partition_number', '%s', 'str', ''),
            ('_pdbx_deposition_message_file_reference.version_id', '%s', 'str', ''),
            ('_pdbx_deposition_message_file_reference.storage_type', '%s', 'str', ''),
            ('_pdbx_deposition_message_file_reference.upload_file_name', '%s', 'str', '')
        ],
        'pdbx_deposition_message_origcomm_reference': [
            ('_pdbx_deposition_message_origcomm_reference.ordinal_id', '%s', 'str', ''),
            ('_pdbx_deposition_message_origcomm_reference.message_id', '%s', 'str', ''),
            ('_pdbx_deposition_message_origcomm_reference.deposition_data_set_id', '%s', 'str', ''),
            ('_pdbx_deposition_message_origcomm_reference.orig_message_id', '%s', 'str', ''),
            ('_pdbx_deposition_message_origcomm_reference.orig_deposition_data_set_id', '%s', 'str', ''),
            ('_pdbx_deposition_message_origcomm_reference.orig_timestamp', '%s', 'str', ''),
            ('_pdbx_deposition_message_origcomm_reference.orig_sender', '%s', 'str', ''),
            ('_pdbx_deposition_message_origcomm_reference.orig_recipient', '%s', 'str', ''),
            ('_pdbx_deposition_message_origcomm_reference.orig_message_subject', '%s', 'str', ''),
            ('_pdbx_deposition_message_origcomm_reference.orig_attachments', '%s', 'str', '')
        ],
        'pdbx_deposition_message_status': [
            ('_pdbx_deposition_message_status.message_id', '%s', 'str', ''),
            ('_pdbx_deposition_message_status.deposition_data_set_id', '%s', 'str', ''),
            ('_pdbx_deposition_message_status.read_status', '%s', 'str', ''),
            ('_pdbx_deposition_message_status.action_reqd', '%s', 'str', ''),
            ('_pdbx_deposition_message_status.for_release', '%s', 'str', '')
        ]
    }
    _suppressList = []
    _excludeList = []
    #

    def __init__(self):
        super(PdbxMessageCategoryStyle, self).__init__(styleId=PdbxMessageCategoryStyle._styleId,
                                                       catFormatL=PdbxMessageCategoryStyle._categoryInfo,
                                                       catItemD=PdbxMessageCategoryStyle._cDict,
                                                       excludeList=PdbxMessageCategoryStyle._excludeList,
                                                       suppressList=PdbxMessageCategoryStyle._suppressList)

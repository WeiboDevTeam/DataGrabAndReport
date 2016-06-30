#!/usr/bin /python
from EsQueryCrashInfluenceDepth import EsQueryCrashInfluenceDepth
from EsQueryCrashUidCount import EsQueryCrashUidCount
from EsCrashQueryParams import EsCrashQueryParams
from Request_Performance import InsertUtils
from Request_Performance import WorkbookManager
from Request_Performance import RequestParams
from EsQueryHelper import EsQueryHelper
import xlsxwriter
import os,sys
import difflib

params = EsCrashQueryParams(1);
params.setFromValues(['1066193010'])
#test = EsQueryCrashUidCount(params)
#test.doRequest()
test = EsQueryCrashInfluenceDepth(params)
test.doRequest()
ratio = difflib.SequenceMatcher(None,"str1","str2").ratio()
print ratio

#!/usr/bin /python
from EsQueryCrashInfluenceDepth import EsQueryCrashInfluenceDepth
from EsQueryCrashUidCount import EsQueryCrashUidCount
from EsQueryWeiboFromValue import EsQueryWeiboFromValue
from EsCrashQueryParams import EsCrashQueryParams
from Request_Performance import InsertUtils
from Request_Performance import WorkbookManager
from Request_Performance import RequestParams
from EsQueryHelper import EsQueryHelper
import xlsxwriter
import os,sys
import difflib

platforms = ['Android','iphone']
for platform in platforms:
	params = EsCrashQueryParams(1, platform);
	test = EsQueryWeiboFromValue(params)
	fromvalues = test.doRequest()
	params.setFromValues(fromvalues)

	#test = EsQueryCrashUidCount(params)
	#test.doRequest()
	test = EsQueryCrashInfluenceDepth(params)
	test.doRequest()

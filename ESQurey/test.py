#!/usr/bin /python
from EsQueryCrashUidCount import EsQueryCrashUidCount
from EsCrashQueryParams import EsCrashQueryParams
from Request_Performance import InsertUtils
from Request_Performance import WorkbookManager
from Request_Performance import RequestParams

params = EsCrashQueryParams(1);
params.setFromValues(['1066195010'])
test = EsQueryCrashUidCount(params)
test.doRequest()
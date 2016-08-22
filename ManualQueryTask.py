#!/usr/bin /python
# -*- coding: utf-8 -*-
from ESQurey import EsQueryWeiboFromValue
from ESQurey import EsCrashQueryParams
from ESQurey import EsQueryTop20CrashLog
from ManagerUtils import WorkbookManager
from ManagerUtils import WriteEmail
from Request_Performance import RequestParams
from datetime import timedelta, date
import time

top_number=20
timeformat="%Y.%m.%d %H:%M:%S"

# 自定义查询时间，不是每日定时任务
temp_time_from="11:50:00"
temp_time_to="11:55:00"
today=date.today()
test_timefrom=int(time.mktime(time.strptime(today.strftime('%Y.%m.%d')+" "+temp_time_from,timeformat)))*1000
test_timeto=int(time.mktime(time.strptime(today.strftime('%Y.%m.%d')+" "+temp_time_to,timeformat)))*1000

def doTask():
	tablelist=grabData()
	sendMail(tablelist)

def sendMail(tablelist):
	writeEmail=WriteEmail.WriteEmail()
	content=writeEmail.getMailContent(tablelist,top_number)
	writeEmail.mailSend(content)

def grabData():
	platforms = ['Android']
	tablelist=[]

	for platform in platforms:
		params = EsCrashQueryParams.EsCrashQueryParams(1, platform);
		params.daysIndex=[today.strftime('%Y.%m.%d'),(today - timedelta(1)).strftime('%Y.%m.%d')]
		params.setTimeFrom(test_timefrom)
		params.setTimeTo(test_timeto)
		test = EsQueryWeiboFromValue.EsQueryWeiboFromValue(params)
		fromvalues = test.doRequest()
		params.setFromValues(fromvalues)

		# 抓取Top20的crash
		top_crash=EsQueryTop20CrashLog.EsQueryTop20CrashLog(params)
		top_crash.doRequest()
		filepath3=top_crash.getWorkbookPath()
		tableinfo3={}
		tableinfo3['filepath']=filepath3
		tableinfo3['sheet']=0
		tableinfo3['theme']=str(platform)+'端Top'+str(top_number)+'的crash('+str(today)+')'
		tableinfo3['title']=['序号','crash原因','fingerprint','影响用户数']
		tablelist.append(tableinfo3)

	return tablelist

def main():
	doTask()

if __name__ == '__main__':
	main()

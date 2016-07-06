#!/usr/bin /python
# -*- coding: utf-8 -*-
from ESQurey import EsQueryCrashInfluenceDepth
from ESQurey import EsQueryCrashUidCount
from ESQurey import EsQueryWeiboFromValue
from ESQurey import EsCrashQueryParams
from ESQurey import EsQueryTop20CrashLog
from Request_Performance import InsertUtils
from Request_Performance import WorkbookManager
from Request_Performance import RequestParams
from ESQurey import EsQueryHelper
from JiraCreate import JiraCreateHelper
import WriteEmail
import xlsxwriter
import os,sys
import difflib
import time

top_number=10
searchformat="%Y.%m.%d"

def doTask():
	print "do timer task"
	tablelist=grabData()
	sendMail(tablelist)

def sendMail(tablelist):
	writeEmail=WriteEmail.WriteEmail()
	content=writeEmail.getMailContent(tablelist,top_number)
	writeEmail.mailSend(content)

def grabData():
	platforms = ['Android','iphone']
	tablelist=[]

	for platform in platforms:
		params = EsCrashQueryParams.EsCrashQueryParams(1, platform);
		test = EsQueryWeiboFromValue.EsQueryWeiboFromValue(params)
		fromvalues = test.doRequest()
		params.setFromValues(fromvalues)

		date=time.strftime(searchformat,time.localtime(params.getTimeTo()/1000))

		#test = EsQueryCrashUidCount(params)
		#test.doRequest()

		# 影响用户数统计
		count=EsQueryCrashUidCount.EsQueryCrashUidCount(params)
		count.doRequest()
		filepath2=count.getWorkbookPath()
		tableinfo2={}
		tableinfo2['filepath']=filepath2
		tableinfo2['sheet']=0
		tableinfo2['theme']=str(platform)+'影响用户数('+str(date)+')'
		tableinfo2['title']=['序号','微博版本','影响用户数']
		tablelist.append(tableinfo2)
		
		# 影响用户深度Top10的crash统计
		test = EsQueryCrashInfluenceDepth.EsQueryCrashInfluenceDepth(params)
		test.doRequest()
		filepath=test.getWorkbookPath()
		tableinfo={}
		tableinfo['filepath']=filepath
		tableinfo['sheet']=0
		tableinfo['theme']=str(platform)+'影响用户深度Top'+str(top_number)+'的crash('+str(date)+')'
		tableinfo['title']=['序号','uid','crash内容','影响用户数']
		tablelist.append(tableinfo)

		# 抓取Top10的crash
		top_crash=EsQueryTop20CrashLog.EsQueryTop20CrashLog(params)
		top_crash.doRequest()
		filepath3=top_crash.getWorkbookPath()
		tableinfo3={}
		tableinfo3['filepath']=filepath3
		tableinfo3['sheet']=0
		tableinfo3['theme']=str(platform)+'端Top'+str(top_number)+'的crash('+str(date)+')'
		tableinfo3['title']=['序号','crash原因','影响用户数']
		tablelist.append(tableinfo3)

	return tablelist

def main():
	doTask()

if __name__ == '__main__':
	main()

#!/usr/bin /python
# -*- coding: utf-8 -*-
from ESQurey import EsQueryCrashInfluenceDepth
from ESQurey import EsQueryCrashUidCount
from ESQurey import EsQueryWeiboFromValue
from ESQurey import EsCrashQueryParams
from Request_Performance import InsertUtils
from Request_Performance import WorkbookManager
from Request_Performance import RequestParams
from ESQurey import EsQueryHelper
from JiraCreate import JiraCreateHelper
import WriteEmail
import xlsxwriter
import os,sys
import difflib

top_number=10

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

	# 影响用户深度Top20的crash统计
	for platform in platforms:
		params = EsCrashQueryParams.EsCrashQueryParams(1, platform);
		test = EsQueryWeiboFromValue.EsQueryWeiboFromValue(params)
		fromvalues = test.doRequest()
		params.setFromValues(fromvalues)

		#test = EsQueryCrashUidCount(params)
		#test.doRequest()

		test = EsQueryCrashInfluenceDepth.EsQueryCrashInfluenceDepth(params)
		test.doRequest()
		filepath=test.getWorkbookPath()
		tableinfo={}
		tableinfo['filepath']=filepath
		tableinfo['sheet']=0
		tableinfo['theme']=str(platform)+'影响用户深度Top'
		tableinfo['title']=['uid','crash reason','crash log', 'fingerprint', 'jira_status', 'counts']
		tablelist.append(tableinfo)


	return tablelist

def main():
	doTask()

if __name__ == '__main__':
	main()

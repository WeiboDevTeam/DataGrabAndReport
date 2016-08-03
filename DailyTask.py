#!/usr/bin /python
# -*- coding: utf-8 -*-
from ESQurey import EsQueryCrashInfluenceDepth
from ESQurey import EsQueryCrashUidCount
from ESQurey import EsQueryWeiboFromValue
from ESQurey import EsCrashQueryParams
from ESQurey import EsQueryCrashSingleLog
from ESQurey import EsQueryTop20CrashLog
from ManagerUtils import WorkbookManager
from ManagerUtils import WriteEmail
from Request_Performance import RequestParams
from datetime import timedelta, date
from AnalysizeDailyCrash import CalculateDailyCrash

top_number=10
searchformat="%Y.%m.%d"

def test():
	params = EsCrashQueryParams.EsCrashQueryParams(3, "iphone");
	test = EsQueryWeiboFromValue.EsQueryWeiboFromValue(params)
	fromvalues = test.doRequest()
	params.setFromValues(fromvalues)
	querySingelLog = EsQueryCrashSingleLog.EsQueryCrashSingleLog(params)
	printfingers=['e283c1a525c2e63640ee702a1cf1b1f6']
	for printfinger in printfingers:
		print querySingelLog.doRequest('1068093010',printfinger)

def doTask():
	print "do timer task"
	platforms = ['Android','iphone']
	for platform in platforms:
		tablelist=grabData(platform)
		sendMail(tablelist,platform)

def sendMail(tablelist,platform):
	writeEmail=WriteEmail.WriteEmail()
	content=writeEmail.getMailContent(tablelist,top_number)
	writeEmail.mailSend(content,platform)

def grabData(platform):
	tablelist=[]

	params = EsCrashQueryParams.EsCrashQueryParams(1, platform);
	test = EsQueryWeiboFromValue.EsQueryWeiboFromValue(params)
	fromvalues = test.doRequest()
	params.setFromValues(fromvalues)

	tdate=(date.today()-timedelta(1)).strftime(searchformat)

	#test = EsQueryCrashUidCount(params)
	#test.doRequest()

	# 影响用户数统计
	count=EsQueryCrashUidCount.EsQueryCrashUidCount(params)
	crashUidCount=count.doRequest()
	filepath2=count.getWorkbookPath()
	tableinfo2={}
	tableinfo2['filepath']=filepath2
	tableinfo2['sheet']=0
	tableinfo2['theme']=str(platform)+'影响用户数('+str(tdate)+')'
	tableinfo2['title']=['序号','微博版本','影响用户数']
	tablelist.append(tableinfo2)

	# 抓取Top10的crash
	top_crash=EsQueryTop20CrashLog.EsQueryTop20CrashLog(params)
	topCrashList=top_crash.doRequest()
	filepath3=top_crash.getWorkbookPath()
	tableinfo3={}
	tableinfo3['filepath']=filepath3
	tableinfo3['sheet']=0
	tableinfo3['theme']=str(platform)+'端Top'+str(top_number)+'的crash('+str(tdate)+')'
	tableinfo3['title']=['序号','crash原因','jira状态','jira分配人','crash次数']
	tablelist.append(tableinfo3)
	
	calResult = calculateCrashRatio(crashUidCount,topCrashList)
	CalculateDailyCrash.writeDataToFile(calResult,tdate.replace('.','')+'.csv')

	# 影响用户深度Top10的crash统计
	test = EsQueryCrashInfluenceDepth.EsQueryCrashInfluenceDepth(params)
	test.doRequest()
	filepath=test.getWorkbookPath()
	tableinfo={}
	tableinfo['filepath']=filepath
	tableinfo['sheet']=0
	tableinfo['theme']=str(platform)+'影响用户深度Top'+str(top_number)+'的crash('+str(tdate)+')  单个用户单个crash的影响次数/天'
	tableinfo['title']=['序号','uid','crash内容','crash次数']
	tablelist.append(tableinfo)

	return tablelist

def calculateCrashRatio(crashUidCount,topCrashList): 
	if(len(topCrashList)>0):
		resultList=[]
		fromvalue=topCrashList[0].get('fromvalue')
		totalCrashCount=crashUidCount.get(fromvalue)
		if(totalCrashCount ==None):
			print 'total crash uid count is none of version %s' % fromvalue[2:5]
		for topCrash in topCrashList:
			topCrashCount = topCrash.get('counts')
			crashRatio = (topCrashCount+0.0)/totalCrashCount
			resultItem = {}
			resultItem['fingerprint'] = topCrash.get('fingerprint')
			resultItem['fromvalue'] = topCrash.get('fromvalue')
			resultItem['jsonlog'] = topCrash.get('jsonlog')
			resultItem['counts'] = str(topCrash.get('counts'))
			resultItem['crash_total_count']=str(totalCrashCount)
			resultItem['crash_ratio']=str('%.4f' % crashRatio)
			resultItem['jira_id'] = topCrash.get('jira_id')
			resultItem['jira_assignee'] = topCrash.get('jira_assignee')
			resultItem['component'] = 'None'
			resultList.append(resultItem)
		return resultList

def main():
	doTask()
	

if __name__ == '__main__':
	main()

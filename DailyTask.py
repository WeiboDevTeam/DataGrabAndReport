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
from ManagerUtils import SendEmail
from SLAQuery import SLAQueryHelper
from SLAQuery import SLAQuery
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
		print 'platform:' + platform
		sendMail(tablelist,platform)

def sendMail(tablelist,platform):
	# 编辑邮件内容
	write=WriteEmail.WriteEmail()
	content=write.writeEmail(tablelist,top_number)
	# 发送邮件
	send=SendEmail.SendEmail()
	send.sendEmail(content,platform)

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
	# filepath2=count.getWorkbookPath()
	# tableinfo2={}
	# tableinfo2['needsort']=True
	# tableinfo2['filepath']=filepath2
	# tableinfo2['sheet']=0
	# tableinfo2['theme']=str(platform)+'影响用户数('+str(tdate)+')'
	# tableinfo2['title']=['序号','微博版本','影响用户数','crash次数']
	# tablelist.append(tableinfo2)

	# 抓取Top10的crash
	top_crash=EsQueryTop20CrashLog.EsQueryTop20CrashLog(params)
	topCrashList=top_crash.doRequest()
	tableinfo3={}
	tableinfo3['key']='crash'
	tableinfo3['data']=topCrashList
	tablelist.append(tableinfo3)
	
	calResult = calculateCrashRatio(crashUidCount,topCrashList)
	CalculateDailyCrash.writeDataToFile(calResult,tdate.replace('.','')+'.csv')

	# 影响用户深度Top10的crash统计
	test = EsQueryCrashInfluenceDepth.EsQueryCrashInfluenceDepth(params)
	test.doRequest()
	filepath=test.getWorkbookPath()
	# tableinfo={}
	# tableinfo['needsort']=True
	# tableinfo['filepath']=filepath
	# tableinfo['sheet']=0
	# tableinfo['theme']=str(platform)+'影响用户深度Top'+str(top_number)+'的crash('+str(tdate)+')  单个用户单个crash的影响次数/天'
	# tableinfo['title']=['序号','uid','crash内容','crash次数']
	# tablelist.append(tableinfo)

	# 业务错误率统计
	if platform=='Android':
		platform='android'
	slaquery = SLAQuery.SLAQuery()
	slaquery_data= slaquery.doQuery(platform)
	tableinfo4={}
	tableinfo4['key']='slaquery'
	tableinfo4['data']=slaquery_data
	tablelist.append(tableinfo4)
	# print tablelist

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

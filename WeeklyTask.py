#!/usr/bin/python
# -*- coding: utf-8 -*-
import WriteEmail
from ESQurey import EsCrashQueryParams
from ESQurey import EsQueryWeiboFromValue
from ESQurey import EsQureyTopCrashLastVersions
from ESQurey import EsQueryMostVersionCrash

# 定义摘取的记录条数
top_number=20

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
		params = EsCrashQueryParams.EsCrashQueryParams(4, platform);
		test = EsQueryWeiboFromValue.EsQueryWeiboFromValue(params)
		fromvalues = test.doRequest()
		params.setFromValues(fromvalues)

		tag=str(params.getTimeFrom())+'-'+str(params.getTimeTo())

		# 抓取最近2版top_number的crash
		crash=EsQureyTopCrashLastVersions.EsQureyTopCrashLastVersions(params)
		crash.doRequest()
		filepath1=crash.getWorkbookPath()
		two_versions=crash.getFromValues()
		tableinfo1={}
		tableinfo1['filepath']=filepath1
		tableinfo1['sheet']=0
		tableinfo1['theme']=str(platform)+'端Top'+str(top_number)+'的crash('+tag+')'
		tableinfo1['title']=['crash内容',str(two_versions[1][2:5]),str(two_versions[0][2:5])]
		tablelist.append(tableinfo1)

		# 覆盖版本数top_number的crash
		versions=EsQueryMostVersionCrash.EsQueryMostVersionCrash(params)
		versions.doRequest()
		filepath2=versions.getWorkbookPath()
		tableinfo2={}
		tableinfo2['filepath']=filepath2
		tableinfo2['sheet']=0
		tableinfo2['theme']=str(platform)+'端覆盖版本Top'+str(top_number)+'的crash('+tag+')'
		tableinfo2['title']=['crash内容','影响版本数','影响用户数']
		tablelist.append(tableinfo2)

	return tablelist

def main():
	doTask()

if __name__ == '__main__':
	main()
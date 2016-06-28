#!/usr/bin/python
# -*- coding: utf-8 -*-
import time
from datetime import datetime, timedelta
import WriteEmail
import CrashHandler
from Request_Performance import WorkbookManager

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
	crash_handler=CrashHandler.CrashHandler()
	print 'timefrom:' + str(crash_handler.timefrom)
	print 'timeto:' + str(crash_handler.timeto)

	fromvalues=crash_handler.getFieldValues("Android",CrashHandler.fromfield)
	versions=crash_handler.getFieldValues("Android",CrashHandler.versionfield)
	print fromvalues
	print versions

	latest_from=crash_handler.getValue(fromvalues,1)
	latest_version=crash_handler.getValue(versions,1)
	print 'latest_from:'+ latest_from
	print 'latest_version:'+ latest_version

	versions=crash_handler.getValues(versions,6)
	print versions

	wbm=WorkbookManager.WorkbookManager()

	tablelist=[]	

	# 抓取最近2版top_number的crash
	two_versions=crash_handler.getValues(fromvalues,2)
	outputfile2=crash_handler.startTopCrashCollectionWithFromValues("Android",wbm,two_versions)
	tableinfo2={}
	tableinfo2['filepath']=outputfile2
	tableinfo2['sheet']=0
	tableinfo2['theme']='Android端Top'+str(top_number)+'的crash('+crash_handler.searchdate+')'
	tableinfo2['title']=['crash内容',str(two_versions[1]),str(two_versions[0])]
	tablelist.append(tableinfo2)

	# 覆盖版本数top_number的crash
	outputfile=crash_handler.startCrashCoverageCollectionWithVersions("Android",wbm,versions)
	tableinfo={}
	tableinfo['filepath']=outputfile
	tableinfo['sheet']=0
	tableinfo['theme']='Android端影响版本数Top'+str(top_number)+'的crash('+crash_handler.searchdate+')'
	tableinfo['title']=['crash内容','影响版本数','影响用户数']
	tablelist.append(tableinfo)

	wbm.closeWorkbooks()

	return tablelist

def main():
	doTask()

if __name__ == '__main__':
	main()
#!/usr/bin/python
# -*- coding: utf-8 -*-
import time
from datetime import datetime, timedelta
import WriteEmail
import CrashHandler
from Request_Performance import WorkbookManager

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

	# 抓取最近6版的crash影响用户数	
	for i in range(len(CrashHandler.systems)):		
		outputfile=crash_handler.startCrashUidsCollectionWithVersions(CrashHandler.systems[i],wbm,versions)
		tableinfo={}
		tableinfo['filepath']=outputfile
		tableinfo['sheet']=i
		tableinfo['theme']=CrashHandler.systems[i]+'端crash用户数统计('+crash_handler.searchdate+')'
		tableinfo['title']=['微博版本','影响用户数']
		tablelist.append(tableinfo)

	# 影响用户深度Top20的crash统计
	outputfile=crash_handler.startCrashInfluenceDCollectionWithFromvalue("Android",wbm,latest_from)
	tableinfo={}
	tableinfo['filepath']=outputfile
	tableinfo['sheet']=0
	tableinfo['theme']='Android影响用户深度Top'+str(top_number)+'的crash('+crash_handler.searchdate+')'
	tableinfo['title']=['crash内容','用户uid','crash次数']
	tablelist.append(tableinfo)

	# 抓取最近一版Top20的crash
	outputfile2=crash_handler.startCrashCollectionWithFromvalue("Android",wbm,latest_from)
	tableinfo2={}
	tableinfo2['filepath']=outputfile2
	tableinfo2['sheet']=0
	tableinfo2['theme']='Android端Top'+str(top_number)+'的crash('+crash_handler.searchdate+')'
	tableinfo2['title']=['crash内容','影响用户数']
	tablelist.append(tableinfo2)

	

	wbm.closeWorkbooks()

	return tablelist

def main():
	doTask()

if __name__ == '__main__':
	main()
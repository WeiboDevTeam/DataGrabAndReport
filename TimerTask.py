#!/usr/bin/python
# -*- coding: utf-8 -*-
import time
from datetime import datetime, timedelta
import WriteEmail
import CrashHandler
from Request_Performance import WorkbookManager

'''
每天凌晨两点执行
'''
INTERVAL_HOUR = 2
SECONDS_PER_INTERVAL=(INTERVAL_HOUR+1)*60*60

def doTask():
	print "do timer task"
	tablelist=grabData()
	sendMail(tablelist)

def getSleepSeconds():
	curTime=datetime.now()
	desTime = curTime.replace(hour=23, minute=0, second=0, microsecond=0)
	delta = desTime - curTime
	skipSeconds = SECONDS_PER_INTERVAL + delta.total_seconds()
	print curTime
	print delta
	return skipSeconds

def sendMail(tablelist):
	writeEmail=WriteEmail.WriteEmail()
	content=writeEmail.getMailContent(tablelist)
	writeEmail.mailSend(content)

def grabData():
	crash_handler=CrashHandler.CrashHandler()
	print 'timefrom:' + str(crash_handler.timefrom)
	print 'timeto:' + str(crash_handler.timeto)
	print crash_handler.getLatestFromValue(crash_handler.getTopVersionFromvalues())
	wbm=WorkbookManager.WorkbookManager()

	tablelist=[]

	# 影响用户深度Top20的crash统计
	outputfile=crash_handler.startCrashInfluenceDepthCollection("Android",wbm)
	print outputfile
	tableinfo={}
	tableinfo['filepath']=outputfile
	tableinfo['sheet']=0
	tableinfo['theme']='影响用户深度Top20的crash'
	tableinfo['title']='<th>用户uid</th><th>crash内容</th><th>crash次数</th>'
	# 追加sheet数
	tablelist.append(tableinfo)

	# 抓取最近几版的crash影响用户数	
	# for i in range(len(crash_handler.systems)):		
	# 	outputfile=crash_handler.startCrashVersionCollection(crash_handler.systems[i],wbm)
	# 	tableinfo={}
	# 	tableinfo['filepath']=outputfile
	# 	tableinfo['sheet']=i
	# 	tableinfo['theme']=crash_handler.systems[i]+'端影响用户Top20的crash'
	# 	tableinfo['title']='<th>crash内容</th><th>影响用户数</th>'
	# 	tablelist.append(tableinfo)

	# wbm.closeWorkbooks()

	return tablelist

def main():
	print getSleepSeconds()
	# i=1
	# while i<=5:
	# 	print datetime.now()
	# 	doTask()
	# 	i+=1
	# 	time.sleep(2)
	# print 'done!'
	doTask()

if __name__ == '__main__':
	main()
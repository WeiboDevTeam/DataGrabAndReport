#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import Request_Performance
from Request_Performance import PerformanceAvgCostTimeHandler
from Request_Performance import PerformanceErrorCodeHandler
from Request_Performance import PerformanceSucRatioHandler
from Request_Performance import PerformanceRequestParams
from Request_Performance import HttpRequest
from Request_Performance import WorkbookManager
from Request_Performance import InsertUtils
from Request_Performance.Constants import Const
from datetime import timedelta, date

def getAllSubBusinessType():
	'''
	获取性能日志下所有子业务的类型
	'''
	sub_business_type=[]
	requestParam = PerformanceRequestParams.PerformanceRequestParams()
	requestParam.setFromDay(fromDay)
	requestParam.setEndDay(endDay)
	requestParam.setApi('getSelectDataProvider.getWorkNames')
	url = requestParam.getCompleteUrl()
	httprequest = HttpRequest.HttpRequest(url)
	data = httprequest.request()
	decodedData = json.loads(data)
	code = decodedData['code']
	if code == '2000':
		subtypes = decodedData['data']['uris']
		for subtype in subtypes:
			if subtype['value']==u"全部":
				continue 
			else:
				sub_business_type.append(subtype)
		return sub_business_type
	else:
		print 'fetch all sub_business_type failed'

	return None

def getCurrentWeiboVersion():
	'''
	获取当前的微博版本，一般是最近的5个版本
	'''
	requestParam = PerformanceRequestParams.PerformanceRequestParams()
	requestParam.setFromDay(fromDay)
	requestParam.setEndDay(endDay)
	requestParam.setApi('weiboMobileClientPerformance.getCurrentVersion')
	httprequest = HttpRequest.HttpRequest(requestParam.getCompleteUrl())
	data = httprequest.request()
	decodedData = json.loads(data)
	code = decodedData['code']
	if code == '2000':
		version = decodedData['data']['versions']
		return version.split(',')
	else:
		print 'fetch current weibo version failed'

	return None

def getPerformanceAvgCostTime(system,workbookmanager,targetVersion,file,type):
	'''
	获取各个业务的平均响应时间
	'''
	avgCostTimeHandler = PerformanceAvgCostTimeHandler.PerformanceAvgCostTimeHandler(file)
	avgCostTimeHandler.version = targetVersion
	avgCostTimeHandler.system = system
	avgCostTimeHandler.endday = endDay
	avgCostTimeHandler.fromday = fromDay
	avgCostTimeHandler.sub_business_type = sub_business_type
	avgCostTimeHandler.doRequest(workbookmanager,type)

def getPerformanceErroCodeTrend(system,workbookmanager,targetVersion,file,type):
	'''
	获取各个业务模块的错误码趋势数据
	'''
	errorCodeHandler = PerformanceErrorCodeHandler.PerformanceErrorCodeHandler(file)
	errorCodeHandler.version = targetVersion
	errorCodeHandler.system = system
	errorCodeHandler.endday = endDay
	errorCodeHandler.fromday = fromDay
	errorCodeHandler.sub_business_type = sub_business_type
	errorCodeHandler.doRequest(workbookmanager,type)

def getPerformanceSucRatioTrend(system,workbookmanager,targetVersion,file,type):
	'''
	获取各个业务模块的成功率
	'''
	sucRatioHandler = PerformanceSucRatioHandler.PerformanceSucRatioHandler(file)
	sucRatioHandler.version = targetVersion
	sucRatioHandler.system = system
	sucRatioHandler.endday = endDay
	sucRatioHandler.fromday = fromDay
	sucRatioHandler.sub_business_type = sub_business_type
	sucRatioHandler.doRequest(workbookmanager,type)

systems=['android',"iphone"]
dayInterval = -7
fromDay=(date.today() + timedelta(dayInterval)).strftime('%Y%m%d')
endDay=(date.today() + timedelta(-1)).strftime('%Y%m%d')

sub_business_type=getAllSubBusinessType()

version=getCurrentWeiboVersion()
version.sort()


def startGrabWeeklyData(wbm):
	targetVersion=version[len(version)-3:len(version)]
	for system in systems:
		fileName = system+'_'+Const.PATH_WEEKLY_DATA
		getPerformanceAvgCostTime(system,wbm,targetVersion,fileName,Const.TYPE_WEEKLY_DATA)
		getPerformanceSucRatioTrend(system,wbm,targetVersion,fileName,Const.TYPE_WEEKLY_DATA)
		getPerformanceErroCodeTrend(system,wbm,targetVersion,fileName,Const.TYPE_WEEKLY_DATA)

def startGrabWeeklyAvgData(wbm):
	# # get recent 6 version data
	targetVersion=version
	for system in systems:
		fileName = system+'_'+Const.PATH_WEEKLY_AVG_DATA
		getPerformanceAvgCostTime(system,wbm,targetVersion,fileName,Const.TYPE_WEEKLY_AVG_DATA)
		getPerformanceSucRatioTrend(system,wbm,targetVersion,fileName,Const.TYPE_WEEKLY_AVG_DATA)

def main():
	wbm=WorkbookManager.WorkbookManager()
	startGrabWeeklyData(wbm)
	startGrabWeeklyAvgData(wbm)
	wbm.closeWorkbooks()

if __name__ == '__main__':
	main()



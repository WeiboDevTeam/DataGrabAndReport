#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import os,sys
import PerformanceAvgCostTimeHandler
import PerformanceErrorCodeHandler
import PerformanceSucRatioHandler
import PerformanceRequestParams
from SLAQuery import HttpRequest
from ManagerUtils import WorkbookManager
from ManagerUtils import InsertUtils
from SLAQuery.Constants import Const
from datetime import timedelta, date
from SLAQuery import SLAQueryHelper
import ConfigParser

systems=['android',"iphone"]
dayInterval = -8
fromDay=(date.today() + timedelta(dayInterval)).strftime('%Y%m%d')
endDay=(date.today() + timedelta(-1)).strftime('%Y%m%d')
dirname = os.path.abspath(os.path.dirname(sys.argv[0]))
path=dirname+'/output/'

config_path=dirname+'/errorcode.config'

errorcodes_config={}
errorcodes_list=[]

'''
获取性能日志下所有子业务的类型
'''
def getAllSubBusinessType(system):
	sub_business_type=[]
	requestParam = PerformanceRequestParams.PerformanceRequestParams()
	requestParam.setSystemType(system)
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

'''
获取当前的微博版本，一般是最近的5个版本
'''
def getCurrentWeiboVersion(system):
	list_versions=[]
	requestParam = PerformanceRequestParams.PerformanceRequestParams()
	requestParam.setSystemType(system)
	requestParam.setFromDay(fromDay)
	requestParam.setEndDay(endDay)
	requestParam.setApi('WeiboMobileClientPerformance.getTopClientHits')
	httprequest = HttpRequest.HttpRequest(requestParam.getCompleteUrl())
	data = httprequest.request()
	decodedData = json.loads(data)
	code = decodedData['code']
	if code == '2000':
		versions = decodedData['data']['data']
		for version in versions:
			list_versions.append(version)
		return list_versions
	else:
		print 'fetch current weibo version failed'

	return None

'''
获取各个业务的平均响应时间
'''
def getPerformanceAvgCostTime(system,workbookmanager,targetVersion,file,type):
	avgCostTimeHandler = PerformanceAvgCostTimeHandler.PerformanceAvgCostTimeHandler(file)
	avgCostTimeHandler.version = targetVersion
	avgCostTimeHandler.system = system
	avgCostTimeHandler.endday = endDay
	avgCostTimeHandler.fromday = fromDay
	avgCostTimeHandler.sub_business_type = getAllSubBusinessType()
	avgCostTimeHandler.doRequest(workbookmanager,type)

'''
获取各个业务模块的错误码趋势数据
'''
def getPerformanceErroCodeTrend(system,workbookmanager,targetVersion,file,type):
	errorCodeHandler = PerformanceErrorCodeHandler.PerformanceErrorCodeHandler(file)
	errorCodeHandler.version = targetVersion
	errorCodeHandler.system = system
	errorCodeHandler.endday = endDay
	errorCodeHandler.fromday = fromDay
	errorCodeHandler.sub_business_type = getAllSubBusinessType()
	errorCodeHandler.doRequest(workbookmanager,type)

'''
获取各个业务模块的成功率
'''
def getPerformanceSucRatioTrend(system,workbookmanager,targetVersion,file,type):
	sucRatioHandler = PerformanceSucRatioHandler.PerformanceSucRatioHandler(file)
	sucRatioHandler.version = targetVersion
	sucRatioHandler.system = system
	sucRatioHandler.endday = endDay
	sucRatioHandler.fromday = fromDay
	sucRatioHandler.sub_business_type = getAllSubBusinessType(system)
	sucRatioHandler.doRequest(workbookmanager,type)

# grab data from sla and write to excel files with basic chart
def startGrabWeeklyData(wbm,system):
	version=getCurrentWeiboVersion(system)
	version.sort()
	targetVersion=version[len(version)-1]['client_version']
	print 'targetVersion:' + targetVersion
	fileName = path+ system+'_'+endDay+Const.PATH_WEEKLY_DATA
		# getPerformanceAvgCostTime(system,wbm,targetVersion,fileName,Const.TYPE_WEEKLY_DATA)
	getPerformanceSucRatioTrend(system,wbm,targetVersion,fileName,Const.TYPE_WEEKLY_DATA)
		# getPerformanceErroCodeTrend(system,wbm,targetVersion,fileName,Const.

def init_config():
	config_read = ConfigParser.RawConfigParser()
	config_read.read(config_path)
	secs = config_read.sections()
	print 'secs:' + str(secs)
	for sec in secs:
		errorcodes = config_read.options(sec)
		for code in errorcodes:
			errorcodes_config[code]=config_read.get(sec,code)
	return errorcodes

# 选取top3的错误码以及列出错误原因
def parseErrorCode(codes,errorcodes_list):	
	reasons=[]
	if codes!= None:
		if len(codes) >=3:					
			codes=codes[0:3]
		for i in range(0,len(codes)):
			code=codes[i]
			reason=code
			if code in errorcodes_list:
				if errorcodes_config.get(code) != None:
					reason = str(errorcodes_config.get(code))+ '('+str(code)+')' 
			reason_str='top'+str((i+1))+':'+ reason
			reasons.append(reason_str)
	return reasons

def main():
	wbm=WorkbookManager.WorkbookManager()
	for system in systems:	
	wbm.closeWorkbooks() # must close workbook
	print path


if __name__ == '__main__':
	main()



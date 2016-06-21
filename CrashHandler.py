#!/usr/bin/python
# -*- coding: utf-8 -*-

from urllib2 import Request,urlopen,URLError,HTTPError
from Request_Performance import WorkbookManager
from Request_Performance import InsertUtils
import httplib,urllib,urllib2,json
import time
import os,sys

perinterval=24*60*60*1000
interval=3

localtime="00:00:00"
timeformat="%Y.%m.%d %H:%M:%S"
searchformat="%Y.%m.%d"

localdate=time.strftime(searchformat,time.localtime())
to=time.mktime(time.strptime(localdate+" "+localtime,timeformat))
timeto=int(round(to*1000))
timefrom=timeto-perinterval*interval

currenttime=timeto-interval
searchdate=time.strftime(searchformat,time.localtime(currenttime/1000))


host="10.19.0.64"
port=9200
logtype="logstash-mweibo-"
fromvalues=[1066195010,1066095010,1065195010]
versions=["6.6.1","6.6.0","6.5.1","6.5.0","6.4.2","6.4.1","6.4.0"]
fromfield="jsoncontent.from"
versionfield="jsoncontent.weibo_version"



'''
获取输出文件夹的路径
'''
def getOutputPath():
	dirname = os.path.abspath(os.path.dirname(sys.argv[0]))
	path=dirname+'/output/'
	if os.path.isdir(path)==False:
		print 'create dir:' + path
		os.mkdir(path)
	return path


'''
构建curl中的查询参数部分
'''
def buildQueryString(field,datalist):
	strquery=""
	for f in range(0,len(datalist)):
		strquery += field+":"+str(datalist[f])
		if f < len(datalist)-1:
			strquery += " OR "
	return strquery

def buildVersionIndex():
	pass

'''
构建curl中的时间索引
'''
def buildIndex(type,currenttime,interval):
	strindex=type + time.strftime(searchformat,time.localtime(currenttime/1000)) + ","
	for i in range(1,interval+1):
		current_index=time.strftime(searchformat,time.localtime((currenttime-i*perinterval)/1000))
		strindex += (type + current_index)
		if i < interval:
			strindex += ","
	return strindex

def buildUri(type,currenttime,interval):
	uri="/"+buildIndex(type,currenttime,interval)+"/_search?search_type=count"
	print uri
	return uri

def httpRequest(method,host,port,requesturl,uri):
	headerdata={"Host":host}
	conn=httplib.HTTPConnection(host,port)
	conn.request(method=method,url=requesturl,body=uri,headers=headerdata)
	response=conn.getresponse()
	res=response.read()
	return res

'''
构建最近几个版本的Top50crash的查询语句，根据uid的量排序
'''
def buildTopCrashQuery():
	must=[]
	timestamp={"gte":timefrom,"lte":timeto,"format": "epoch_millis"}
	must.append({"range":{"@timestamp":timestamp}})
	must.append({"term":{"programname":"mweibo_client_crash"}})
	must.append({"term":{"jsoncontent.os_type":"Android"}})
	must.append({"query_string":{"query":buildQueryString(versionfield,versions)}})

	aggs={}
	aggs["terms"]={"size":50,"field":"jsoncontent.reson","order":{"count_uid":"desc"}}
	aggs["aggs"]={"count_uid":{"cardinality":{"field":"jsoncontent.uid"}},"count_versions":{"cardinality":{"field":versionfield}}}

	query={}
	query["query"]={"filtered":{"filter":{"bool":{"must":must}}}}
	query["aggs"]={"count_crash":aggs}
	return query

'''
构建最近三个版本的Top20crash的查询语句
'''
def buildRecentlyThreeVersionTopCrashQuery():
	must=[]
	timestamp={"gte":timefrom,"lte":timeto,"format": "epoch_millis"}
	must.append({"range":{"@timestamp":timestamp}})
	must.append({"term":{"programname":"mweibo_client_crash"}})
	must.append({"term":{"jsoncontent.os_type":"Android"}})
	must.append({"query_string":{"query":buildQueryString(fromfield,fromvalues)}})

	aggs1={}
	aggs1["terms"]={"size":20,"field":"jsoncontent.reson"}

	aggs2={}
	aggs2["terms"]={"field":fromfield,"size": 3}
	aggs2["aggs"]={"count_uid":{"cardinality":{"field":"jsoncontent.uid"}}}

	aggs1["aggs"]={"aggs2":aggs2}

	query={}
	query["query"]={"filtered":{"filter":{"bool":{"must":must}}}}
	query["aggs"]={"count_crash":aggs1}
	return query

'''
构建覆盖微博版本最多的Top1000 的crash查询语句
'''
def buildMostVersionCrashQuery():
	must=[]
	timestamp={"gte":timefrom,"lte":timeto,"format": "epoch_millis"}
	must.append({"range":{"@timestamp":timestamp}})
	must.append({"term":{"programname":"mweibo_client_crash"}})
	must.append({"term":{"jsoncontent.os_type":"Android"}})
	must.append({"query_string":{"query":buildQueryString(versionfield,versions)}})

	must_not=[]
	# must_not.append({"query":{"match":{"jsoncontent.subtype":{"query":"anr","type":"phrase"}}}})

	aggs1={}
	aggs1["terms"]={"size":1000,"field":"jsoncontent.reson","order":{"count_versions":"desc"}}

	aggs2={}
	aggs2["count_versions"]={"cardinality":{"field":versionfield}}
	aggs2["count_uid"]={"cardinality":{"field":"jsoncontent.uid"}}

	aggs1["aggs"]=aggs2

	query={}
	query["query"]={"filtered":{"filter":{"bool":{"must":must,"must_not":must_not}}}}
	query["aggs"]={"count_crash":aggs1}
	return query

'''
构建最近几个版本每日的crash uid的量的查询语句
'''
def buildRecentVersionsCrashQuery(sys):
	must=[]
	timestamp={"gte":timefrom,"lte":timeto,"format": "epoch_millis"}
	must.append({"range":{"@timestamp":timestamp}})
	must.append({"term":{"programname":"mweibo_client_crash"}})
	must.append({"term":{"jsoncontent.os_type":sys}})
	must.append({"query_string":{"query":buildQueryString(versionfield,versions)}})

	must_not=[]
	must_not.append({"query":{"match":{"jsoncontent.subtype":{"query":"anr","type":"phrase"}}}})

	filtered={}
	filtered['filter']={"bool":{"must":must,"must_not":must_not}}	

	date={}
	extended_bounds={"min": timefrom,"max": timeto} 
	date["date_histogram"]={"field": "@timestamp","interval": "1d","time_zone": "Asia/Shanghai", "min_doc_count": 1,"extended_bounds":extended_bounds}
	date["aggs"]={"count_uid":{"cardinality":{"field":"jsoncontent.uid"}}}

	aggs={}
	aggs["terms"]={"size":7,"field":versionfield}
	aggs["aggs"]={"date":date}

	query={}
	query["query"]={"filtered":filtered}
	query["aggs"]={"count_crash":aggs}
	return query

'''
抓取最近三个版本的Top20crash，根据uid的量排序
'''
def getRecenltyThreeVersionsCrashCounts(worksheet):
	query = buildRecentlyThreeVersionTopCrashQuery()
	json_string=json.dumps(query)
	res = httpRequest("POST",host,port,buildUri(logtype,currenttime,interval),json_string)
	json_data=json.loads(res)
	print json_data
	
	if json_data.get('aggregations')!=None:
		buckets= json_data['aggregations']['count_crash']['buckets']
		header=['reason']
		header.extend(fromvalues)

		utils=InsertUtils.InsertUtils()		
		utils.write_header(worksheet,0,0,header)
		index = 1
		for item in buckets:
			data=['null',0,0,0]
			data[0]=item.get('key')
			datalist=item.get('aggs2').get('buckets')
			for temp in datalist:
				version=temp.get('key')
				for x in range(0,len(fromvalues)):
					if version==str(fromvalues[x]):
						data[x+1]=temp.get('count_uid').get('value')
						break
			utils.write_crash_data_with_yxis(worksheet,data,header,index,0)
			index += 1
	else:
		print json_string
		print 'result: '+str(json_data)

'''
抓取最近几个版本的Top50crash的查询语句，根据uid的量排序
'''
def getTopCrashInfos(worksheet):
	query = buildTopCrashQuery()
	json_string=json.dumps(query)
	res = httpRequest("POST",host,port,buildUri(logtype,currenttime,interval),json_string)
	json_data=json.loads(res)
	
	if json_data.get('aggregations')!=None:
		buckets= json_data['aggregations']['count_crash']['buckets']
		header=['reason','uids','count_versions']

		utils=InsertUtils.InsertUtils()		
		utils.write_header(worksheet,0,0,header)
		index = 1
		for item in buckets:
			print item
			data=[]
			data.append(item.get('key'))
			data.append(item.get('count_uid').get('value'))
			data.append(item.get('count_versions').get('value'))
			utils.write_crash_data_with_yxis(worksheet,data,header,index,0)
			index += 1
	else:
		print json_string
		print 'result: '+str(json_data)

'''
抓取覆盖微博版本最多的crash，根据uid的量排序
'''
def getMostVersionCrashInfos(worksheet):
	query = buildMostVersionCrashQuery()
	json_string=json.dumps(query)
	res = httpRequest("POST",host,port,buildUri(logtype,currenttime,interval),json_string)
	json_data=json.loads(res)
	
	if json_data.get('aggregations')!=None:
		buckets= json_data['aggregations']['count_crash']['buckets']
		header=['reason','versions','uids']
		print header

		utils=InsertUtils.InsertUtils()		
		utils.write_header(worksheet,0,0,header)
		index = 1
		for item in buckets:
			print item
			data=[]
			data.append(item.get('key'))
			data.append(item.get('count_versions').get('value'))
			data.append(item.get('count_uid').get('value'))
			utils.write_crash_data_with_yxis(worksheet,data,header,index,0)
			index += 1
	else:
		print json_string
		print 'result: '+str(json_data)
	
'''
抓取最近几个版本每日的crash uid的量，结合DAU，用于对比个版本的crash率
'''
def getRecenltyVersionsCrashCounts(sys,worksheet):	
	query = buildRecentVersionsCrashQuery(sys)
	json_string=json.dumps(query)
	res = httpRequest("POST",host,port,buildUri(logtype,currenttime,interval),json_string)
	json_data=json.loads(res)
	
	if json_data.get('aggregations')!=None:
		buckets= json_data['aggregations']['count_crash']['buckets']
		utils=InsertUtils.InsertUtils()	
		
		header=['version']

		if len(buckets)>0:
			sub_buckets=buckets[0]
			dates=sub_buckets.get('date').get('buckets')
			for i in range (0,len(dates)):
				ltime=time.localtime(dates[i].get('key')/1000)
				timestr=time.strftime(searchformat,ltime)
				header.append(timestr)	
				
		utils.write_header(worksheet,0,0,header)		
			
		index = 1
		for item in buckets:
			data=[]
			data.append(item.get('key'))
			sub_buckets = item.get('date').get('buckets')		
			for i in range(0,len(sub_buckets)):
				data.append(sub_buckets[i].get('count_uid').get('value'))
			print data
			utils.write_crash_data_with_yxis(worksheet,data,header,index,0)
			index += 1
	else:
		print json_string
		print 'result: '+str(json_data)

'''
def copyData(workbookmanager,filename,sheetname,worksheet):
	utils=InsertUtils.InsertUtils()
	table=utils.copyData(filename,sheetname,worksheet,0,1)
	return table
'''

'''
开始抓取最近几个版本每日crash uids的统计
'''
def startCrashVersionCollection(sys,wbm):
	workbook=wbm.getWorkbook(getOutputPath()+"crash率统计"+searchdate+".xlsx")
	worksheet_topversioncrash = wbm.addWorksheet(workbook,sys)
	getRecenltyVersionsCrashCounts(sys,worksheet_topversioncrash)

'''
开始抓取最近三个／几个版本中Top20／Top50的crash
'''
def startTopCrashCollection(sys,wbm):
	workbook=wbm.getWorkbook(getOutputPath()+"最近三个版本Top20的crash对比分析"+searchdate+".xlsx")
	worksheet_topcrash = wbm.addWorksheet(workbook,sys)	
	getRecenltyThreeVersionsCrashCounts(worksheet_topcrash)
	# getTopCrashInfos(worksheet_topcrash)

'''
开始抓取覆盖微博版本最多的Top1000的crash
'''
def startMostVersionCrashCollection(sys,wbm):
	workbook=wbm.getWorkbook(getOutputPath()+"覆盖微博版本最多的crash统计"+searchdate+".xlsx")
	worksheet_mostcrash = wbm.addWorksheet(workbook,sys)
	getMostVersionCrashInfos(worksheet_mostcrash)

systems=['Android',"iphone"]

def main():
	wbm=WorkbookManager.WorkbookManager()

	'''
	最近几个版本的crash率统计
	'''
	for sys in systems:
		startCrashVersionCollection(sys,wbm)

	'''
	最近三个版本的Top20 crash的对比统计
	'''
	startTopCrashCollection("Android",wbm)

	'''
	覆盖版本最多的crash统计
	'''
	startMostVersionCrashCollection("Android",wbm)

	wbm.closeWorkbooks()

if __name__ == '__main__':
	main()
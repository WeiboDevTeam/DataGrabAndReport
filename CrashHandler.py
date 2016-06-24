#!/usr/bin/python
# -*- coding: utf-8 -*-

from urllib2 import Request,urlopen,URLError,HTTPError
from Request_Performance import WorkbookManager
from Request_Performance import InsertUtils
import httplib,urllib,urllib2,json
import time
import os,sys,re,difflib
import CrashHandler

perinterval=24*60*60*1000
interval=1

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
systems=['Android',"iphone"]
versionsNum=6

class CrashHandler(object):
	def __init__(self):
		self.versions=["6.6.1","6.6.0","6.5.1","6.5.0","6.4.2","6.4.1","6.4.0"]
		self.latesfromvalue = ""
		self.timeto=timeto
		self.timefrom=timefrom
		self.interval=interval
		self.systems=systems

	'''
	获取输出文件夹的路径
	'''
	def getOutputPath(self):
		dirname = os.path.abspath(os.path.dirname(sys.argv[0]))
		path=dirname+'/output/'
		if os.path.isdir(path)==False:
			print 'create dir:' + path
			os.mkdir(path)
		return path


	'''
	构建curl中的查询参数部分
	'''
	def buildQueryString(self,field,datalist):
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
	def buildIndex(self,type,currenttime,interval):
		strindex=type + time.strftime(searchformat,time.localtime(currenttime/1000)) + ","
		for i in range(1,interval+1):
			current_index=time.strftime(searchformat,time.localtime((currenttime-i*perinterval)/1000))
			strindex += (type + current_index)
			if i < interval:
				strindex += ","
		return strindex

	def buildUri(self,type,currenttime,interval):
		uri="/"+self.buildIndex(type,currenttime,interval)+"/_search?search_type=count"
		print uri
		return uri

	def httpRequest(self,method,host,port,requesturl,uri):
		headerdata={"Host":host}
		conn=httplib.HTTPConnection(host,port)
		conn.request(method=method,url=requesturl,body=uri,headers=headerdata)
		response=conn.getresponse()
		res=response.read()
		return res

	'''
	构建最近几个版本的from值查询语句，根据uid的量排序
	'''
	def buildTopVersionFromQuery(self):
		must=[]
		timestamp={"gte":timefrom,"lte":timeto,"format": "epoch_millis"}
		must.append({"range":{"@timestamp":timestamp}})
		must.append({"term":{"programname":"mweibo_client_crash"}})
		must.append({"term":{"jsoncontent.os_type":"Android"}})

		aggs={}
		aggs["terms"]={"size":versionsNum,"field":"jsoncontent.from"}
		aggs["aggs"]={"count_uid":{"cardinality":{"field":"jsoncontent.uid"}}}

		query={}
		query["query"]={"filtered":{"filter":{"bool":{"must":must}}}}
		query["aggs"]={"fromvalues":aggs}
		return query

	'''
	构建最近几个版本的Top50crash的查询语句，根据uid的量排序
	'''
	def buildTopCrashQuery(self):
		must=[]
		timestamp={"gte":timefrom,"lte":timeto,"format": "epoch_millis"}
		must.append({"range":{"@timestamp":timestamp}})
		must.append({"term":{"programname":"mweibo_client_crash"}})
		must.append({"term":{"jsoncontent.os_type":"Android"}})
		must.append({"query_string":{"query":self.buildQueryString(versionfield,versions)}})

		aggs={}
		aggs["terms"]={"size":50,"field":"jsoncontent.reson","order":{"count_uid":"desc"}}
		aggs["aggs"]={"count_uid":{"cardinality":{"field":"jsoncontent.uid"}},"count_versions":{"cardinality":{"field":versionfield}}}

		query={}
		query["query"]={"filtered":{"filter":{"bool":{"must":must}}}}
		query["aggs"]={"count_crash":aggs}
		return query

	'''
	构建单个版本的Top50crash的查询语句，根据uid的量排序
	'''
	def buildTopCrashQueryForSingleVersion(self,version):
		versions=[]
		versions.append(version)
		must=[]
		timestamp={"gte":timefrom,"lte":timeto,"format": "epoch_millis"}
		must.append({"range":{"@timestamp":timestamp}})
		must.append({"term":{"programname":"mweibo_client_crash"}})
		must.append({"term":{"jsoncontent.os_type":"Android"}})
		must.append({"query_string":{"query":self.buildQueryString(versionfield,versions)}})

		aggs={}
		aggs["terms"]={"size":50,"field":"jsoncontent.reson","order":{"count_uid":"desc"}}
		aggs["aggs"]={"count_uid":{"cardinality":{"field":"jsoncontent.uid"}}}

		query={}
		query["query"]={"filtered":{"filter":{"bool":{"must":must}}}}
		query["aggs"]={"count_crash":aggs}
		return query

	'''
	构建最近三个版本的Top20crash的查询语句
	'''
	def buildRecentlyThreeVersionTopCrashQuery(self):
		must=[]
		timestamp={"gte":timefrom,"lte":timeto,"format": "epoch_millis"}
		must.append({"range":{"@timestamp":timestamp}})
		must.append({"term":{"programname":"mweibo_client_crash"}})
		must.append({"term":{"jsoncontent.os_type":"Android"}})
		must.append({"query_string":{"query":self.buildQueryString(fromfield,fromvalues)}})

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
	def buildMostVersionCrashQuery(self):
		must=[]
		timestamp={"gte":timefrom,"lte":timeto,"format": "epoch_millis"}
		must.append({"range":{"@timestamp":timestamp}})
		must.append({"term":{"programname":"mweibo_client_crash"}})
		must.append({"term":{"jsoncontent.os_type":"Android"}})
		must.append({"query_string":{"query":self.buildQueryString(versionfield,versions)}})

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
	def buildRecentVersionsCrashQuery(self,sys):
		must=[]
		timestamp={"gte":timefrom,"lte":timeto,"format": "epoch_millis"}
		must.append({"range":{"@timestamp":timestamp}})
		must.append({"term":{"programname":"mweibo_client_crash"}})
		must.append({"term":{"jsoncontent.os_type":sys}})
		must.append({"query_string":{"query":self.buildQueryString(versionfield,self.versions)}})

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
	构建Crash影响用户深度查询语句，top20的影响用户，每个用户top5的crash内容
	'''
	def buildCrashInfluenceDepthQuery(self):
		must=[]
		timestamp={"gte":timefrom,"lte":timeto,"format": "epoch_millis"}
		must.append({"range":{"@timestamp":timestamp}})
		must.append({"term":{"programname":"mweibo_client_crash"}})
		must.append({"term":{"jsoncontent.os_type":"Android"}})
		must.append({"query_string":{"query":self.buildQueryString(fromfield,['1066195010'])}})

		aggs1={}
		aggs1["terms"]={"size":20,"field":"jsoncontent.uid"}

		aggs2={}
		aggs2["terms"]={"size":5,"field":"jsoncontent.reson"}
		aggs2["aggs"]={"crash_content":{"terms":{"size":5,"field":"jsoncontent.content"}}}

		aggs1["aggs"]={"crash_reson":aggs2}

		query={}
		query["query"]={"filtered":{"filter":{"bool":{"must":must}}}}
		query["aggs"]={"count_crash":aggs1}
		print query
		return query

	'''
	抓取最近三个版本的Top20crash，根据uid的量排序
	'''
	def getRecenltyThreeVersionsCrashCounts(self,worksheet):
		query = self.buildRecentlyThreeVersionTopCrashQuery()
		json_string=json.dumps(query)
		res = self.httpRequest("POST",host,port,self.buildUri(logtype,currenttime,self.interval),json_string)
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
	def getTopCrashInfos(self,worksheet):
		query = self.buildTopCrashQuery()
		json_string=json.dumps(query)
		res = self.httpRequest("POST",host,port,self.buildUri(logtype,currenttime,self.interval),json_string)
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
	抓取最近6个版本from值
	'''
	def getTopVersionFromvalues(self):
		fromvalues=[]
		query = self.buildTopVersionFromQuery()
		print query
		json_string=json.dumps(query)
		res = self.httpRequest("POST",host,port,self.buildUri(logtype,currenttime,self.interval),json_string)
		json_data=json.loads(res)
		print str(json_data)
		
		if json_data.get('aggregations')!=None:
			buckets= json_data['aggregations']['fromvalues']['buckets']
			header=['from','count_uid']

			# utils=InsertUtils.InsertUtils()		
			# utils.write_header(worksheet,0,0,header)
			index = 1
			for item in buckets:
				fromvalues.append(item.get('key'))
				# print item
				# data=[]
				# data.append(item.get('key'))
				# data.append(item.get('count_uid').get('value'))
				# utils.write_crash_data_with_yxis(worksheet,data,header,index,0)
				index += 1
		else:
			print 'result: '+str(json_data)
		fromvalues.sort()
		print fromvalues
		return fromvalues

	def getLatestFromValue(self,fromvalues):
		size = len(fromvalues)
		if size>0:
			return fromvalues[size-1]
		return ''

	'''
	抓取覆盖微博版本最多的crash，根据uid的量排序
	'''
	def getMostVersionCrashInfos(self,worksheet):
		query = self.buildMostVersionCrashQuery()
		json_string=json.dumps(query)
		res = self.httpRequest("POST",host,port,self.buildUri(logtype,currenttime,self.interval),json_string)
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
	def getRecenltyVersionsCrashCounts(self,sys,worksheet):	
		query = self.buildRecentVersionsCrashQuery(sys)
		json_string=json.dumps(query)
		res = self.httpRequest("POST",host,port,self.buildUri(logtype,currenttime,self.interval),json_string)
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
					if i >= self.interval:
						break
					data.append(sub_buckets[i].get('count_uid').get('value'))
				print data
				utils.write_crash_data_with_yxis(worksheet,data,header,index,0)
				index += 1
		else:
			print json_string
			print 'result: '+str(json_data)

	'''
	抓取crash影响用户深度数据，Top20的uid
	'''
	def getCrashInfluenceDepthQuery(self,worksheet):
		query = self.buildCrashInfluenceDepthQuery()
		json_string=json.dumps(query)
		res = self.httpRequest("POST",host,port,self.buildUri(logtype,currenttime,self.interval),json_string)
		json_data=json.loads(res)
		
		if json_data.get('aggregations')!=None:
			buckets= json_data['aggregations']['count_crash']['buckets']
			header=['uid','crash content','counts']		
			
			data_list={}
			for item in buckets:
				uid=item.get('key')
				print 'uid:'+uid
				crash_reson=item.get('crash_reson').get('buckets')
				for reson in crash_reson:
					crash_content=reson.get('crash_content').get('buckets')
					for content in crash_content:
						# 判断crash的content中是否包含crash的原因
						if reson.get('key') in content.get('key'):
							reson_content=content.get('key')
						else:
							reson_content=reson.get('key')+'\n'+content.get('key')
						# 过滤dexpathlist内容，这部分对相似度计算有影响
						filter_content=self.filterCrashContent(reson_content)
						if filter_content=="No Match!":
							filter_content = reson_content
						self.updateMatchedList(data_list,uid,filter_content,content.get('doc_count'))

			self.writeToExcel(worksheet,header,data_list)
		else:
			print 'result: '+str(json_data)

	'''
	将缓存在list中的数据写入excel表格
	'''
	def writeToExcel(self,worksheet,header,data_list):
		utils=InsertUtils.InsertUtils()		
		utils.write_header(worksheet,0,0,header)
		index = 1			
		for data in data_list.keys():
			crash_info = data_list.get(data)
			for key in crash_info.keys():
				row=[]
				row.append(data)
				row.append(key)
				row.append(crash_info.get(key).get('counts'))
				utils.write_crash_data_with_yxis(worksheet,row,header,index,0)
				index += 1

	'''
	crash content过滤dexpathlist
	'''
	def filterCrashContent(self,reason):
		regexDexPathList=r'(.*)DexPathList.*]](.*)'
		matchDexpath = re.match(regexDexPathList,reason,re.S|re.M|re.I)
		if matchDexpath:
			content=matchDexpath.group(1)+'DexPathList'+matchDexpath.group(2)
			return content
		else:
			return 'No Match!'

	'''
	计算crash content的相似度，相似度大于0.9及以上则视为同一crash
	'''
	def isSimilarCrashReason(self,str1,str2):
		s=difflib.SequenceMatcher(None,str1,str2)
		print "similarity ratio:" + str(s.ratio())
		if s.ratio()> 0.9:		
			return True
		else:
			return False

	'''
	进行相似度计算后，根据结果进行crash次数累加
	'''
	def updateMatchedList(self,data_list,uid,content,count):
		print 'count:' + str(count)
		if data_list.get(uid)==None:
			dic={}
			dic[content]={"counts":count}
			data_list[uid]=dic
		else:
			dic=data_list.get(uid)
			similar = False
			similar_reason = content
			for reason in dic.keys():
				if self.isSimilarCrashReason(content,reason):
					similar = True
					similar_reason = reason
					break
			if similar:
				print 'old count:' + str(dic.get(similar_reason).get('counts'))
				count=dic.get(similar_reason).get('counts')+count	
				print 'updated count :' + str(count)			

			data_list[uid][similar_reason]={"counts":count}
			

	'''
	def copyData(workbookmanager,filename,sheetname,worksheet):
		utils=InsertUtils.InsertUtils()
		table=utils.copyData(filename,sheetname,worksheet,0,1)
		return table
	'''

	'''
	开始抓取最近几个版本每日crash uids的统计
	'''
	def startCrashVersionCollection(self,sys,wbm):
		path=self.getOutputPath()+"crash率统计"+searchdate+".xlsx"
		workbook=wbm.getWorkbook(path)
		worksheet_topversioncrash = wbm.addWorksheet(workbook,sys)
		self.getRecenltyVersionsCrashCounts(sys,worksheet_topversioncrash)
		return path

	'''
	开始抓取最近三个／几个版本中Top20／Top50的crash
	'''
	def startTopCrashCollection(self,sys,wbm):
		workbook=wbm.getWorkbook(self.getOutputPath()+"最近三个版本Top20的crash对比分析"+searchdate+".xlsx")
		worksheet_topcrash = wbm.addWorksheet(workbook,sys)	
		self.getRecenltyThreeVersionsCrashCounts(worksheet_topcrash)
		# self.getTopCrashInfos(worksheet_topcrash)

	'''
	开始抓取覆盖微博版本最多的Top1000的crash
	'''
	def startMostVersionCrashCollection(self,sys,wbm):
		workbook=wbm.getWorkbook(self.getOutputPath()+"覆盖微博版本最多的crash统计"+searchdate+".xlsx")
		worksheet_mostcrash = wbm.addWorksheet(workbook,sys)
		self.getMostVersionCrashInfos(worksheet_mostcrash)

	'''
	开始抓取影响用户深度Top20的crash及uid
	'''
	def startCrashInfluenceDepthCollection(self,sys,wbm):
		output=self.getOutputPath()+"crash影响用户深度统计"+searchdate+".xlsx"
		workbook=wbm.getWorkbook(output)
		worksheet = wbm.addWorksheet(workbook,sys)
		self.getCrashInfluenceDepthQuery(worksheet)	
		return output

	def main():
		crash_handler=CrashHandler.CrashHandler()
		print 'timefrom:' + str(timefrom)
		print 'timeto:' + str(timeto)
		print crash_handler.getLatestFromValue(crash_handler.getTopVersionFromvalues())
		wbm=WorkbookManager.WorkbookManager()

		'''
		最近几个版本的crash率统计
		'''
		for sys in systems:
			crash_handler.startCrashVersionCollection(sys,wbm)

		'''
		影响用户Top20 crash的统计（对比三个版本）
		'''
		# crash_handler.startTopCrashCollection("Android",wbm)

		# '''
		# 影响微博版本最多的crash统计
		# '''
		# crash_handler.startMostVersionCrashCollection("Android",wbm)

		'''
		影响用户深度Top20的crash统计
		'''
		# crash_handler.startCrashInfluenceDepthCollection("Android",wbm)

		wbm.closeWorkbooks()

	if __name__ == '__main__':
		main()
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
versionsNum=10

localtime="00:00:00"
timeformat="%Y.%m.%d %H:%M:%S"
searchformat="%Y.%m.%d"

localdate=time.strftime(searchformat,time.localtime())
to=time.mktime(time.strptime(localdate+" "+localtime,timeformat))

host="10.19.0.64"
port=9200
logtype="logstash-mweibo-"

fromfield="jsoncontent.from"
versionfield="jsoncontent.weibo_version"
systems=['Android',"iphone"]


class CrashHandler(object):
	def __init__(self):
		self.interval=1		
		self.timeto=int(round(to*1000))
		self.timefrom=self.timeto-perinterval*self.interval
		self.currenttime=self.timeto-self.interval
		self.searchdate=time.strftime(searchformat,time.localtime(self.currenttime/1000))
		self.programname="mweibo_client_crash"		

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
	构建curl中查询参数部分，例如from值或版本
	'''
	def buildQueryString(self,field,datalist):
		strquery=""
		for f in range(0,len(datalist)):
			strquery += field+":"+str(datalist[f])
			if f < len(datalist)-1:
				strquery += " OR "
		return strquery

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
	执行	query，返回数据并转为json格式
	'''
	def doQuery(self,query):
		json_string=json.dumps(query)
		res = self.httpRequest("POST",host,port,self.buildUri(logtype,self.currenttime,self.interval),json_string)
		json_data=json.loads(res)
		return json_data

	'''
	构建curl查询语句中Must部分的配置内容
	'''
	def buildCurlMustField(self,sys,field,values):
		must=[]
		timestamp={"gte":self.timefrom,"lte":self.timeto,"format": "epoch_millis"}
		must.append({"range":{"@timestamp":timestamp}})
		must.append({"term":{"programname":self.programname}})
		must.append({"term":{"jsoncontent.os_type":sys}})
		if field!=None:
			must.append({"query_string":{"query":self.buildQueryString(field,values)}})
		return must

	'''
	构建最近versionsNum个版本的field值查询语句，根据uid的量排序
	'''
	def buildFieldValuesQuery(self,sys,queryfield):
		must=self.buildCurlMustField(sys,None,None)

		aggs={}
		aggs["terms"]={"size":versionsNum,"field":queryfield}
		aggs["aggs"]={"count_uid":{"cardinality":{"field":"jsoncontent.uid"}}}

		query={}
		query["query"]={"filtered":{"filter":{"bool":{"must":must}}}}
		query["aggs"]={"values":aggs}
		return query

	'''
	构建from值＝fromvalue的微博版本Top50的crash的查询语句，包括crash原因和crash内容，根据uid的量排序
	'''
	def buildCrashQueryWithFromvalue(self,sys,fromvalue):		
		fromvalues=[]
		fromvalues.append(fromvalue)
		must=self.buildCurlMustField(sys,fromfield,fromvalues)

		aggs={}
		aggs["terms"]={"size":50,"field":"jsoncontent.content"}
		aggs["aggs"]={"count_uid":{"cardinality":{"field":"jsoncontent.uid"}},"reason":{"terms":{"field":"jsoncontent.reson","size":5},"aggs":{"2":{"cardinality":{"field":"jsoncontent.uid"}}}}}

		query={}
		query["query"]={"filtered":{"filter":{"bool":{"must":must}}}}
		query["aggs"]={"count_crash":aggs}
		return query

	'''
	构建（版本的version包含在verions中）的Top50crash覆盖的版本数的查询语句，根据uid的量排序
	'''
	def buildTopCrashQueryWithVersions(self,sys,versions):
		must=self.buildCurlMustField(sys,versionfield,versions)

		aggs={}
		aggs["terms"]={"size":50,"field":"jsoncontent.reson","order":{"count_uid":"desc"}}
		aggs["aggs"]={"count_uid":{"cardinality":{"field":"jsoncontent.uid"}},"count_versions":{"cardinality":{"field":versionfield}}}

		query={}
		query["query"]={"filtered":{"filter":{"bool":{"must":must}}}}
		query["aggs"]={"count_crash":aggs}
		return query

	'''
	构建多个版本下（版本的from值包含在fromvalues）Top20crash的查询语句
	'''
	def buildTopCrashQueryWithFromValues(self,sys,fromvalues):
		must= self.buildCurlMustField(sys,fromfield,fromvalues)

		aggs1={}
		aggs1["terms"]={"size":20,"field":"jsoncontent.reson"}

		aggs2={}
		aggs2["terms"]={"field":fromfield,"size": len(fromvalues)}
		aggs2["aggs"]={"count_uid":{"cardinality":{"field":"jsoncontent.uid"}}}

		aggs1["aggs"]={"aggs2":aggs2}

		query={}
		query["query"]={"filtered":{"filter":{"bool":{"must":must}}}}
		query["aggs"]={"count_crash":aggs1}
		return query

	'''
	构建覆盖微博版本最多(版本值在versions之内）的Top1000 的crash查询语句，根据覆盖版本数排序
	'''
	def buildCrashCoverageQueryWithVerions(self,sys,versions):
		must=self.buildCurlMustField(sys,versionfield,versions)

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
	构建（版本的version包含在verions中）每日的crash uid的量的查询语句
	'''
	def buildCrashUidsQueryWithVersions(self,sys,versions):
		must=self.buildCurlMustField(sys,versionfield,versions)

		must_not=[]
		must_not.append({"query":{"match":{"jsoncontent.subtype":{"query":"anr","type":"phrase"}}}})

		filtered={}
		filtered['filter']={"bool":{"must":must,"must_not":must_not}}	

		date={}
		extended_bounds={"min":self.timefrom,"max":self.timeto} 
		date["date_histogram"]={"field": "@timestamp","interval": "1d","time_zone": "Asia/Shanghai", "min_doc_count": 1,"extended_bounds":extended_bounds}
		date["aggs"]={"count_uid":{"cardinality":{"field":"jsoncontent.uid"}}}

		aggs={}
		aggs["terms"]={"size":len(versions),"field":versionfield}
		aggs["aggs"]={"date":date}

		query={}
		query["query"]={"filtered":filtered}
		query["aggs"]={"count_crash":aggs}
		return query

	'''
	构建from值＝fromvalue的Crash影响用户深度查询语句，top20的影响用户，每个用户top5的crash内容
	'''
	def buildCrashInfluenceDepthQuery(self,sys,fromvalue):
		fromvalues=[]
		fromvalues.append(fromvalue)
		must=self.buildCurlMustField(sys,fromfield,fromvalues)		

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
	抓取from值包含在fromvalues中的Top20crash内容，根据uid的量排序，计算各版本在同一crash的uids量
	'''
	def getTopCrashWithFromValues(self,worksheet,sys,fromvalues):
		query = self.buildTopCrashQueryWithFromValues(sys,fromvalues)
		json_data =self.doQuery(query)
		
		if json_data.get('aggregations')!=None:
			buckets= json_data['aggregations']['count_crash']['buckets']
			header=['reason']
			header.extend(fromvalues)

			utils=InsertUtils.InsertUtils()		
			utils.write_header(worksheet,0,0,header)
			index = 1
			for item in buckets:
				data=[]
				data.append(item.get('key'))
				for i in range(0,len(fromvalues)):
					data.append(0)
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
	抓取版本from值＝fromvalue的Top50的crash，根据uid的量排序
	'''
	def getCrashInfosWithFromvalue(self,worksheet,sys,fromvalue):
		query = self.buildCrashQueryWithFromvalue(sys,fromvalue)
		json_data =self.doQuery(query)
		
		if json_data.get('aggregations')!=None:
			buckets= json_data['aggregations']['count_crash']['buckets']
			header=['crash content','counts']		

			data_list={}
			for item in buckets:
				content=item.get('key')
				crash_resons=item.get('reason').get('buckets')
				for reson in crash_resons:
					# 判断crash的content中是否包含crash的原因
					if reson.get('key') in content:
						reson_content=content
					else:
						reson_content=reson.get('key')+'\n'+content
					# 过滤dexpathlist内容，这部分对相似度计算有影响
					filter_content=self.filterCrashContent(reson_content)
					if filter_content=="No Match!":
						filter_content = reson_content

					self.updateMatchedList(data_list,'uid',filter_content,item.get('doc_count'))

			self.writeSortedToExcel(worksheet,header,self.sortDataList(data_list,len(header)-1))
		else:
			print 'result: '+str(json_data)


	'''
	抓取Top50的crash（version为versions范围内），根据uid的量排序，统计每个crash覆盖的版本数
	'''
	def getTopCrashWithVersions(self,worksheet,sys,versions):
		query = self.buildTopCrashQueryWithVersions(sys,versions)
		json_data =self.doQuery(query)
		
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
	抓取最近versionNum个版本from值／version
	'''
	def getFieldValues(self,sys,field):
		values=[]
		query = self.buildFieldValuesQuery(sys,field)
		print query
		json_data =self.doQuery(query)
		
		if json_data.get('aggregations')!=None:
			buckets= json_data['aggregations']['values']['buckets']
			for item in buckets:
				values.append(item.get('key'))
		else:
			print 'result: '+str(json_data)
		values.sort()
		return values

	# index代表某个field的顺序，如version，1就代表最新的版本
	def getValue(self,values,index):
		size = len(values)
		if size>=index:
			return values[size-index]
		return ''

	# index代表某个field的个数，如version，6就代表最新的6版本
	def getValues(self,values,num):
		new_values=[]
		size = len(values)
		if size>=num:
			for i in range(1,num+1):
				new_values.append(values[size-i])
		else:
			print 'field counts bigger than Max values counts!!'
		return new_values

	'''
	抓取覆盖微博版本最多的crash（version在versions范围内），根据uid的量排序
	'''
	def getCrashCoverageWithVersions(self,worksheet,sys,versions):
		query = self.buildCrashCoverageQueryWithVerions(sys,versions)
		json_data =self.doQuery(query)
		
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
	抓取from值包含在fromvalues中的版本每日的crash uid的量，结合DAU，用于对比个版本的crash率
	'''
	def getCrashUidsWithVersions(self,sys,worksheet,versions):	
		query = self.buildCrashUidsQueryWithVersions(sys,versions)
		json_data =self.doQuery(query)
		
		if json_data.get('aggregations')!=None:
			buckets= json_data['aggregations']['count_crash']['buckets']
			utils=InsertUtils.InsertUtils()	
			
			header=['version']

			if len(buckets)>0:
				sub_buckets=buckets[0]
				dates=sub_buckets.get('date').get('buckets')
				for i in range (0,self.interval):
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
	def getCrashInfluenceDWithFromvalue(self,worksheet,sys,fromvalue):
		query = self.buildCrashInfluenceDepthQuery(sys,fromvalue)
		json_data =self.doQuery(query)
		
		if json_data.get('aggregations')!=None:
			buckets= json_data['aggregations']['count_crash']['buckets']
			header=['uid','crash content','counts']		
			
			data_list={}
			for item in buckets:
				uid=item.get('key')
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

			self.writeSortedToExcel(worksheet,header,self.sortDataList(data_list,len(header)-1))
		else:
			print 'result: '+str(json_data)

	'''
	对列表做排序,指定列进行降序排序
	'''
	def sortDataList(self,data_list,sort_index):
		datalist=[]
		for data in data_list.keys():
			crash_info = data_list.get(data)
			for key in crash_info.keys():
				row=[]				
				if data != 'uid':
					row.append(data)
				row.append(key)
				row.append(crash_info.get(key).get('counts'))
				datalist.append(row)
		return sorted(datalist,key=lambda x:x[sort_index],reverse=True)

	'''
	将已排序的数据写入excel表格
	'''
	def writeSortedToExcel(self,worksheet,header,data_list):
		utils=InsertUtils.InsertUtils()		
		utils.write_header(worksheet,0,0,header)
		index = 1			
		for data in data_list:
			utils.write_crash_data_with_yxis(worksheet,data,header,index,0)
			index += 1

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
				if data != 'uid':
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
		if s.ratio()> 0.9:		
			return True
		else:
			return False

	'''
	进行相似度计算后，根据结果进行crash次数累加
	'''
	def updateMatchedList(self,data_list,uid,content,count):
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
				count=dic.get(similar_reason).get('counts')+count			

			data_list[uid][similar_reason]={"counts":count}
			

	'''
	开始抓取version包含在versions中的各版本每日crash uids量，每天抓取
	'''
	def startCrashUidsCollectionWithVersions(self,sys,wbm,versions):
		output=self.getOutputPath()+"crash率统计"+self.searchdate+".xlsx"
		workbook=wbm.getWorkbook(output)
		worksheet_topversioncrash = wbm.addWorksheet(workbook,sys)
		self.getCrashUidsWithVersions(sys,worksheet_topversioncrash,versions)
		return output

	'''
	开始抓取from值包含在fromvalues的微博版本的Top50的crash，每周抓取
	'''
	def startTopCrashCollectionWithFromValues(self,sys,wbm,fromvalues):
		output=self.getOutputPath()+"最近"+str(len(fromvalues))+"个版本Top20的crash对比分析"+self.searchdate+".xlsx"
		workbook=wbm.getWorkbook(output)
		worksheet_topcrash = wbm.addWorksheet(workbook,sys)	
		self.getTopCrashWithFromValues(worksheet_topcrash,sys,fromvalues)
		return output

	'''
	开始抓取覆盖微博版本最多的Top1000的crash，每周抓取
	'''
	def startCrashCoverageCollectionWithVersions(self,sys,wbm,versions):
		output=self.getOutputPath()+"覆盖微博版本最多的crash统计"+self.searchdate+".xlsx"
		workbook=wbm.getWorkbook(output)
		worksheet_mostcrash = wbm.addWorksheet(workbook,sys)
		self.getCrashCoverageWithVersions(worksheet_mostcrash,sys,versions)
		return output

	'''
	开始抓取from值＝fromvalue的影响用户深度Top20的crash及uid，每天抓取
	'''
	def startCrashInfluenceDCollectionWithFromvalue(self,sys,wbm,fromvalue):
		output=self.getOutputPath()+"crash影响用户深度统计"+self.searchdate+".xlsx"
		workbook=wbm.getWorkbook(output)
		worksheet = wbm.addWorksheet(workbook,sys)
		self.getCrashInfluenceDWithFromvalue(worksheet,sys,fromvalue)	
		return output

	'''
	开始抓取from值＝fromvalue的Top50的crash，每天抓取
	'''
	def startCrashCollectionWithFromvalue(self,sys,wbm,fromvalue):
		output=self.getOutputPath()+"Top50的crash统计"+self.searchdate+".xlsx"
		workbook=wbm.getWorkbook(output)
		worksheet = wbm.addWorksheet(workbook,sys)
		self.getCrashInfosWithFromvalue(worksheet,sys,fromvalue)	
		return output
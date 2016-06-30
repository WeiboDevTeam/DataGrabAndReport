#coding:utf-8
from EsCrashQueryParams import  EsCrashQueryParams
from EsQueryHelper import  EsQueryHelper
from Request_Performance import InsertUtils
import json
import time

__metaclass__=type
class EsQueryCrashUidCount(object):
	"""docstring for EsQueryCrashUidCount
	查询crash影响用户数"""

	def __init__(self, params):
		super(EsQueryCrashUidCount, self).__init__()
		self.params = params
		self.__initWorkSheet()
		

	def __initWorkSheet(self):
		platform = self.params.getPlatform()
		workbookName = "crash影响用户统计.xlsx"
		worksheetName = platform
		xlsx = EsQueryHelper.addworksheet(platform,workbookName,worksheetName)
		self.workbook = xlsx[0]
		self.worksheet = xlsx[1]

	def __getCompleteUrl(self):
		return self.params.getUrlPattern()+"?search_type=count"

	def __buildRecentVersionsCrashQuery(self):
		must=[]
		timeFrom = self.params.getTimeFrom()
		timeTo = self.params.getTimeTo()
		print timeFrom,timeTo
		programname = self.params.getProgramName()
		timestamp={"gte":timeFrom,"lte":timeTo,"format": "epoch_millis"}
		must.append({"range":{"@timestamp":timestamp}})
		must.append({"term":{"programname":programname}})
		must.append({"query_string":{"query":EsQueryHelper.buildQueryString("jsoncontent.from",self.params.getFromValues())}})

		must_not=[]
		must_not.append({"query":{"match":{"jsoncontent.subtype":{"query":"anr","type":"phrase"}}}})

		filtered={}
		filtered['filter']={"bool":{"must":must,"must_not":must_not}}	

		date={}
		extended_bounds={"min": timeFrom,"max": timeTo} 
		date["date_histogram"]={"field": "@timestamp","interval": "1d","time_zone": "Asia/Shanghai", "min_doc_count": 1,"extended_bounds":extended_bounds}
		date["aggs"]={"count_uid":{"cardinality":{"field":"jsoncontent.uid"}}}

		aggs={}
		aggs["terms"]={"size":7,"field":"jsoncontent.from"}
		aggs["aggs"]={"date":date}

		query={}
		query["query"]={"filtered":filtered}
		query["aggs"]={"count_crash":aggs}
		return query

	def doRequest(self):
		requeryBody = self.__buildRecentVersionsCrashQuery()

		param = self.params
		result = EsQueryHelper.httpPostRequest(param.getHost(), param.getPort(), self.__getCompleteUrl(), requeryBody)

		self.__parseAndWriteToExcel(result)
		

	def __parseAndWriteToExcel(self,result):
		json_data=json.loads(result)
		interval = self.params.getInterval()
		if(json_data.get('aggregations')!=None):
			buckets= json_data['aggregations']['count_crash']['buckets']
			utils = InsertUtils.InsertUtils()	
			
			header=['version']

			if len(buckets)>0:
				sub_buckets=buckets[0]
				dates=sub_buckets.get('date').get('buckets')
				for i in range (0,interval):
					ltime=time.localtime(dates[i].get('key')/1000)
					timestr=time.strftime("%Y.%m.%d",ltime)
					header.append(timestr)	
				print header
			utils.write_header(self.worksheet,0,0,header)		
				
			index = 1
			for item in buckets:
				data=[]
				data.append(item.get('key'))
				sub_buckets = item.get('date').get('buckets')		
				for i in range(0,len(sub_buckets)):
					if i >= interval:
						break
					data.append(sub_buckets[i].get('count_uid').get('value'))
				print data
				utils.write_crash_data_with_yxis(self.worksheet,data,header,index,0)
				index += 1
			self.workbook.close()
		else:
			print 'result: '+str(json_data)
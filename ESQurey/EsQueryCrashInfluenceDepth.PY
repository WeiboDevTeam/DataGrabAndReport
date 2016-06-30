#encoding:utf-8
from EsCrashQueryParams import  EsCrashQueryParams
from EsQueryHelper import  EsQueryHelper
from EsQueryCrashSingleLog import  EsQueryCrashSingleLog 
from Request_Performance import InsertUtils
import json
import difflib

__metaclass__=type
class EsQueryCrashInfluenceDepth(object):
	"""docstring for EsQueryCrashInfluenceDepth
	   查询crash次数top20的用户及对应的crash log
	"""
	def __init__(self, params):
		super(EsQueryCrashInfluenceDepth, self).__init__()
		self.params = params
		self.__initWorksheet()

	def __initWorksheet(self):
		platform = self.params.getPlatform()
		workbookName = "影响用户最深crash.xlsx"
		worksheetName = platform
		xlsx = EsQueryHelper.addworksheet(platform,workbookName,worksheetName)
		self.workbook = xlsx[0]
		self.worksheet = xlsx[1]

	def __getCompleteUrl(self):
		return self.params.getUrlPattern()+"?search_type=count"

	def __buildQueryBody(self):
		must=[]
		timeFrom = self.params.getTimeFrom()
		timeTo = self.params.getTimeTo()
		programname = self.params.getProgramName()
		timestamp={"gte":timeFrom,"lte":timeTo,"format": "epoch_millis"}
		must.append({"range":{"@timestamp":timestamp}})
		must.append({"term":{"programname":programname}})
		must.append({"query_string":{"query":EsQueryHelper.buildQueryString("jsoncontent.from",self.params.getFromValues())}})

		aggs1={}
		aggs1["terms"]={"size":20,"field":"jsoncontent.uid"}

		aggs2={}
		aggs2["terms"]={"size":5,"field":"jsoncontent.reson"}
		aggs2["aggs"]={"fingerprint":{"terms":{"size":5,"field":"fingerprint"}}}

		aggs1["aggs"]={"crash_reson":aggs2}

		query={}
		query["query"]={"filtered":{"filter":{"bool":{"must":must}}}}
		query["aggs"]={"count_crash":aggs1}
		return query


	def doRequest(self):
		requeryBody = self.__buildQueryBody()

		param = self.params
		result = EsQueryHelper.httpPostRequest(param.getHost(), param.getPort(), self.__getCompleteUrl(), requeryBody)

		self.__parseAndWrite(result)

	def __parseAndWrite(self,result):
		json_data = json.loads(result)
		if json_data.get('aggregations')!=None:
			buckets= json_data['aggregations']['count_crash']['buckets']	
			data_list=[]
			for item in buckets:
				uid=item.get('key')
				bukcet_crash_reson=item.get('crash_reson').get('buckets')
				for crash_reson in bukcet_crash_reson:
					reason = crash_reson['key']
					fingerprint_bucket = crash_reson.get('fingerprint').get('buckets')
					for crash_fingerprint in fingerprint_bucket:
						fingerprint = crash_fingerprint.get('key')
						count = crash_fingerprint.get('doc_count')
						jsonlog = self.__queryCrashLogByFingerPrinter(self.params.getFromValues()[0], fingerprint)
						result_item={"uid":uid,"reason":reason,"fingerprint":fingerprint,"count":count,"jsonlog":jsonlog}
						data_list.append(result_item)
			print len(data_list)
			filteredList=[]
			for item in data_list:
				if(len(filteredList) == 0):
					filteredList.append(item)
				else:
					needAppend = False
					for filteredCrashItem in filteredList:
						crashReason = filteredCrashItem['reason']
						if(difflib.SequenceMatcher(None,crashReason,item['reason']).ratio() > 0.95):
							crashLog = filteredCrashItem['jsonlog']
							similarRatio = difflib.SequenceMatcher(None,crashLog, item['jsonlog'])
							ratio = similarRatio.ratio()
							print ratio
							if(ratio > 0.9):
								filteredCrashItem['count']=filteredCrashItem['count']+item['count']
							else:
								needAppend = True
							break
						else:
							needAppend = True
					if(needAppend):
						filteredList.append(item)	

			filteredList.sort(key=lambda k: (k.get('count', 0)),reverse=True)
			self.__writeToExcel(filteredList)
		else:
			print 'result: '+str(json_data)

	def __queryCrashLogByFingerPrinter(self,fromvalue,fingerprint):
		querySingerCrashLog = EsQueryCrashSingleLog	(self.params)
		return querySingerCrashLog.doRequest(fromvalue,fingerprint)

	def __writeToExcel(self,data_list):
		utils=InsertUtils.InsertUtils()		
		header=['uid','crash reason','crash log','counts']	
		utils.write_header(self.worksheet,0,0,header)
		index = 1			
		for data in data_list:
			row=[]
			row.append(data['uid'])
			row.append(data['reason'])
			row.append(data['jsonlog'])
			row.append(data['count'])
			utils.write_crash_data_with_yxis(self.worksheet,row,header,index,0)
			index += 1
		self.workbook.close()
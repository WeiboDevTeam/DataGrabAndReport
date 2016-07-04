#encoding:utf-8
import json
from EsCrashQueryParams import  EsCrashQueryParams
from EsQueryHelper import  EsQueryHelper
from Request_Performance import InsertUtils

class EsQueryMostVersionCrash(object):
	"""docstring for EsQueryMostVersionCrash
	   查询最近6个版本都存在的crash
	"""
	def __init__(self, params):
		super(EsQueryMostVersionCrash, self).__init__()
		self.params = params
		fromvalues = self.params.getFromValues()
		if(len(fromvalues) > 6):
			self.fromvalues = fromvalues[0:6]
		else:
			self.fromvalues = fromvalues
		self.__initWorksheet()

	def __initWorksheet(self):
		platform = self.params.getPlatform()
		workbookName = "最近6个版本都存在的crash.xlsx"
		worksheetName = platform
		xlsx = EsQueryHelper.addworksheet(platform,workbookName,worksheetName)
		self.workbook = xlsx[0]
		self.worksheet = xlsx[1]
		self.workbookPath = xlsx[2]

	def __getCompleteUrl(self):
		return self.params.getUrlPattern()+"?search_type=count"

	def __buildQueryBody(self):
		must=[]
		timeFrom = self.params.getTimeFrom()
		timeTo = self.params.getTimeTo()
		programname = self.params.getProgramName()
		platform = self.params.getPlatform()
		timestamp={"gte":timeFrom,"lte":timeTo,"format": "epoch_millis"}
		must.append({"range":{"@timestamp":timestamp}})
		must.append({"term":{"programname":programname}})
		must.append({"term":{"jsoncontent.os_type":platform}})
		must.append({"query_string":{"query":EsQueryHelper.buildQueryString("jsoncontent.from",self.fromvalues)}})
		must_not=[]
		# must_not.append({"query":{"match":{"jsoncontent.subtype":{"query":"anr","type":"phrase"}}}})

		aggs1={}
		aggs1["terms"]={"size":100,"field":"jsoncontent.reson","order":{"count_versions":"desc"}}

		aggs2={}
		aggs2["count_versions"]={"cardinality":{"field":"jsoncontent.from"}}
		aggs2["count_uid"]={"cardinality":{"field":"jsoncontent.uid"}}

		aggs1["aggs"]=aggs2

		query={}
		query["query"]={"filtered":{"filter":{"bool":{"must":must,"must_not":must_not}}}}
		query["aggs"]={"count_crash":aggs1}
		return query

	def doRequest(self):
		requeryBody = self.__buildQueryBody()

		param = self.params
		result = EsQueryHelper.httpPostRequest(param.getHost(), param.getPort(), self.__getCompleteUrl(), requeryBody)

		self.__parseAndWrite(result)

	def __parseAndWrite(self, result):
		json_data = json.loads(result)
		if json_data.get('aggregations')!=None:
			buckets= json_data['aggregations']['count_crash']['buckets']
			header=['reason','versions','uids']
			print header

			utils=InsertUtils.InsertUtils()		
			utils.write_header(self.worksheet,0,0,header)
			index = 1
			for item in buckets:
				print item
				data=[]
				data.append(item.get('key'))
				data.append(item.get('count_versions').get('value'))
				data.append(item.get('count_uid').get('value'))
				utils.write_crash_data_with_yxis(self.worksheet,data,header,index,0)
				index += 1
		else:
			print json_string
			print 'result: '+str(json_data)
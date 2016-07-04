#encoding:utf-8

import json
from EsCrashQueryParams import  EsCrashQueryParams
from EsQueryHelper import  EsQueryHelper
from Request_Performance import InsertUtils
__metaclass__ = type

class EsQureyTopCrashLastVersions(object):
	"""docstring for EsQureyTopCrashLastVersions
	查询最近几个版本top20 crash
	"""
	def __init__(self, params):
		super(EsQureyTopCrashLastVersions, self).__init__()
		self.params = params
		self.fromvalues = self.params.getFromValues()[0:2]
		self.__initWorksheet()


	def __initWorksheet(self):
		platform = self.params.getPlatform()
		workbookName = "top20crash_"+('_'.join(self.fromvalues))+".xlsx"
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

		aggs1={}
		aggs1Field = 'jsoncontent.reson'
		if(self.fromvalues[0].endswith('0310')):
			aggs1Field = 'jsoncontent.content'
		aggs1["terms"]={"size":20,"field":aggs1Field}

		aggs2={}
		aggs2["terms"]={"field":'jsoncontent.from',"size": len(self.fromvalues)}
		aggs2["aggs"]={"count_uid":{"cardinality":{"field":"jsoncontent.uid"}}}

		aggs1["aggs"]={"aggs2":aggs2}

		query={}
		query["query"]={"filtered":{"filter":{"bool":{"must":must}}}}
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
			header=['reason']
			header.extend(self.fromvalues)

			utils=InsertUtils.InsertUtils()		
			utils.write_header(self.worksheet,0,0,header)

			index = 1
			for item in buckets:
				data=[]
				data.append(item.get('key'))
				for i in range(0,len(self.fromvalues)):
					data.append(0)
				datalist=item.get('aggs2').get('buckets')
				for temp in datalist:
					version=temp.get('key')
					for x in range(0,len(self.fromvalues)):
						if version==str(self.fromvalues[x]):
							data[x+1]=temp.get('count_uid').get('value')
							break
				utils.write_crash_data_with_yxis(self.worksheet,data,header,index,0)
				index += 1
			self.workbook.close()
		else:
			print json_string
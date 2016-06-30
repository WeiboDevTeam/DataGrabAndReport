#encoding:utf-8
import json
from EsQueryHelper import EsQueryHelper
from EsCrashQueryParams import EsCrashQueryParams

__metaclass__ = type
class EsQueryWeiboFromValue(object):
	"""docstring for EsQueryWeiboFromValue
		查询客户端最近6个版本from值
	"""
	def __init__(self, params):
		super(EsQueryWeiboFromValue, self).__init__()
		self.params = params

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

		aggs={}
		aggs["terms"]={"size":6,"field":"jsoncontent.from"}
		aggs["aggs"]={"count_uid":{"cardinality":{"field":"jsoncontent.uid"}}}

		query={}
		query["query"]={"filtered":{"filter":{"bool":{"must":must}}}}
		query["aggs"]={"values":aggs}
		return query

	def doRequest(self):
		requeryBody = self.__buildQueryBody()

		param = self.params
		result = EsQueryHelper.httpPostRequest(param.getHost(), param.getPort(), self.__getCompleteUrl(), requeryBody)

		return self.__parse(result)

	def __parse(self,result):
		json_data =json.loads(result)
		values = []
		if json_data.get('aggregations')!=None:
			buckets= json_data['aggregations']['values']['buckets']
			for item in buckets:
				values.append(item.get('key'))
		else:
			print 'result: '+str(json_data)
		values.sort(reverse=True)
		return values
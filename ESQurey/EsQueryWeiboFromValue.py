#encoding:utf-8
import json
from EsQueryHelper import EsQueryHelper
from EsCrashQueryParams import EsCrashQueryParams
from EsQueryJob import EsQueryJob

__metaclass__ = type
class EsQueryWeiboFromValue(EsQueryJob):
	"""docstring for EsQueryWeiboFromValue
		查询客户端最近6个版本from值
	"""
	def __init__(self, params):
		super(EsQueryWeiboFromValue, self).__init__(params)	

	def getWorkbookName(self):
		return ''

	def buildQueryAgg(self):
		
		aggs={}
		aggs["terms"]={"size":6,"field":"jsoncontent.from"}
		aggs["aggs"]={"count_uid":{"cardinality":{"field":"jsoncontent.uid"}}}

		return aggs

	def parseAndWrite(self,result):
		json_data =json.loads(result)
		values = []
		if json_data.get('aggregations')!=None:
			buckets= json_data['aggregations']['count_crash']['buckets']
			for item in buckets:
				values.append(item.get('key'))
		else:
			print 'result: '+str(json_data)
		values.sort(reverse=True)
		return values
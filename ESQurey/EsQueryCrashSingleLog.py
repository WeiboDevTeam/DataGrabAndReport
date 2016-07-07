#encoding:utf-8

import urllib
import urllib2
from urllib2 import Request,urlopen
from EsQueryHelper import EsQueryHelper
from EsCrashQueryParams import EsCrashQueryParams
import json

__metaclass__ = type
class EsQueryCrashSingleLog(object):
	"""docstring for EsCrashQuerySingleLog
		根据fingerprint查询单条crash日志
	"""
	def __init__(self, params):
		super(EsQueryCrashSingleLog, self).__init__()
		self.params = params
		
	def __getCompleteUrl(self):
		return self.params.getUrlPattern()+"?pretty"

	def __buildQuery(self,fromvalue,fingerprint):
		must=[]
		timeFrom = self.params.getTimeFrom()
		timeTo = self.params.getTimeTo()
		programname = self.params.getProgramName()
		timestamp={"gte":timeFrom,"lte":timeTo,"format": "epoch_millis"}
		must.append({"range":{"@timestamp":timestamp}})
		must.append({"term":{"programname":programname}})
		must.append({"term":{"fingerprint":fingerprint}})
		must.append({"term":{"jsoncontent.from":fromvalue}})

		aggs1={}
		aggs1["terms"]={"size":1,"field":"jsoncontent.content"}

		query={}
		query["query"]={"filtered":{"filter":{"bool":{"must":must}}}}
		query["aggs"]={"count_crash":aggs1}
		return query

	def doRequest(self,fromvalue,fingerprint):
		requeryBody = self.__buildQuery(fromvalue,fingerprint)

		param = self.params
		result = EsQueryHelper.httpPostRequest(param.getHost(), param.getPort(), self.__getCompleteUrl(), requeryBody)

		esItem = self.__parse(result)

		if(fromvalue.endswith("3010")):
			return self.__translateIosLog(fromvalue,esItem)
		else:
			return esItem['jsonlog']

	def __parse(self,result):
		json_data=json.loads(result)
		hits = json_data['hits']
		hits_all = hits['hits']
		crash_info = hits_all[0]
		return crash_info['_source']

	def __translateIosLog(self,fromvalue,esItem):
		body = {"from":fromvalue,"arch":esItem["jsoncontent"]["sytem"]["arch"],"imgadd":esItem["jsoncontent"]["sytem"]["loadaddress"],"content":esItem['jsonlog']}
		urlencodeBody = urllib.urlencode(body)
		req = urllib2.Request("http://crash.client.weibo.cn/query/sla_full", urlencodeBody, headers={"Content-Type":"application/x-www-form-urlencoded"}) 
		response = urllib2.urlopen(req) 
		the_page = response.read()
		content = json.loads(the_page).get('content')
		return content
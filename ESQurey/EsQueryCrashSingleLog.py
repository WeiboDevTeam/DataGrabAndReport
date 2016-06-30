from urllib2 import Request,urlopen
from EsQueryHelper import EsQueryHelper
from EsCrashQueryParams import EsCrashQueryParams

__metaclass__ = type

class EsCrashQuerySingleLog(object):
	"""docstring for EsCrashQuerySingleLog
		根据fingerprint查询单条crash日志
	"""
	def __init__(self, params):
		super(EsCrashQuerySingleLog, self).__init__()
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

	def doRequest(self,fromvalue,fingerprint):
		requeryBody = self.__buildQuery(fromvalue,fingerprint)

		param = self.params
		result = EsQueryHelper.httpPostRequest(param.getHost(), param.getPort(), self.__getCompleteUrl(), requeryBody)

		esItem = __parse()

		if(self.fromvalue.endswith("3010")):
			return __translateIosLog(esItem)
		else:
			return esItem.get['jsonlog']

	def __parse(self):
		json_data=json.loads(result)
		hits = json_data['hits']
		hits_all = hits['hits']
		crash_info = hits_all[0]
		return crash_info['_source']

	def __translateIosLog(self,esItem):
		body = {"from":self.fromvalue,"arch":esItem["jsoncontent.sytem"]["arch"],"imgadd":esItem["jsoncontent.sytem"]["loadaddress"],"content":esItem.get['jsonlog']}
		req = urllib2.Request("http://wbcrash.sinaapp.com/query/sla_full", body) 
		response = urllib2.urlopen(req) 
		the_page = response.read()
		return json.loads(result).get('content')
	
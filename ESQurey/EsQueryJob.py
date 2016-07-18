#encoding:utf-8
from abc import ABCMeta,abstractmethod
from EsQueryHelper import EsQueryHelper
from EsCrashQueryParams import  EsCrashQueryParams

class EsQueryJob(object):
	__metaclass__ = ABCMeta

	"""docstring for EsQueryJob"""
	def __init__(self, params):
		super(EsQueryJob, self).__init__()
		self.params = params
		self.initFromValues()
		self.__initWorksheet()

	def initFromValues(self):
		self.fromvalues = self.params.getFromValues()

	def getFromValues(self):
		return self.fromvalues

	def getWorkbookPath(self):
		return self.workbookPath

	@abstractmethod
	def getWorkbookName(self):
		pass

	def __initWorksheet(self):
		workbookName = self.getWorkbookName()
		print workbookName
		platform = self.params.getPlatform()
		if(workbookName != None and workbookName.strip('') != ''):
			worksheetName = platform
			xlsx = EsQueryHelper.addworksheet(platform,workbookName,worksheetName)
			self.workbook = xlsx[0]
			self.worksheet = xlsx[1]
			self.workbookPath = xlsx[2]

	def getCompleteUrl(self):
		return self.params.getUrlPattern()+"?search_type=count"

	#构建es查询的条件
	def __buildQueryMust(self):
		must=[]
		timeFrom = self.params.getTimeFrom()
		timeTo = self.params.getTimeTo()
		programname = self.params.getProgramName()
		platform = self.params.getPlatform()
		timestamp={"gte":timeFrom,"lte":timeTo,"format": "epoch_millis"}
		must.append({"range":{"@timestamp":timestamp}})
		must.append({"term":{"programname":programname}})
		must.append({"term":{"jsoncontent.os_type":platform}})
		if(self.fromvalues != None and len(self.fromvalues) > 0):
			must.append({"query_string":{"query":EsQueryHelper.buildQueryString("jsoncontent.from",self.fromvalues)}})
		return must

	def buildQueryMustNot(self):
		return []

	#构建es查询的聚合条件
	@abstractmethod
	def buildQueryAgg(self):
		pass

	def __buildQueryBody(self):
		query={}
		query["query"]={"filtered":{"filter":{"bool":{"must":self.__buildQueryMust(),"must_not":self.buildQueryMustNot()}}}}
		query["aggs"]={"count_crash":self.buildQueryAgg()}
		print query
		return query

	@abstractmethod
	def parseAndWrite(self,result):
		pass

	def doRequest(self):
		requeryBody = self.__buildQueryBody()

		param = self.params
		result = EsQueryHelper.httpPostRequest(param.getHost(), param.getPort(), self.getCompleteUrl(), requeryBody)

		return self.parseAndWrite(result)
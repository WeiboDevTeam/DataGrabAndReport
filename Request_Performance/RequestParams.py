import urllib
__metaclass__ = type
class RequestParams():
	def __init__(self, url='http://sla.weibo.cn/php/start.php'):
		self.requestUrl = url
		self.api=''
		self.businessType = ''
		self.systemType = ''
		self.subType = ''
		self.docid = ''
		self.fromDay=''
		self.endDay = ''



	def setApi(self, api):
		self.api =  api

	def getApi(self):
		return self.api

	def setBusinessType(self, businessType):
		self.businessType = businessType

	def getBusinessType(self):
		return self.businessType

	def setSystemType(self, system):
		self.systemType = system

	def getSystemType():
		return self.systemType

	def setSubType(self, subType):
		self.subType = subType

	def getSubType(self):
		return self.subType

	def setDocid(self, docid):
		self.docid = docid

	def getDocid(self):
		return self.docid

	def setFromDay(self, fromDay):
		self.fromDay = fromDay

	def getFromDay(self):
		return self.fromDay

	def setEndDay(self, endDay):
		self.endDay = endDay

	def getEndDay(self):
		return self.endDay

	def getCompleteUrl(self):
		values = {'api':self.api,
					'from':self.fromDay,
					'to':self.endDay,
					'type':self.businessType,
					'sub_type':self.subType,
					'systerm':self.systemType,
					'docid':self.docid}
		return self.requestUrl+'?'+urllib.urlencode(values) 
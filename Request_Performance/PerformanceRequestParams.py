from Request_Performance import RequestParams
import urllib

__metaclass__=type
class PerformanceRequestParams(RequestParams.RequestParams):
	def __init__(self, url='http://sla.weibo.cn/php/start.php'):
		super(PerformanceRequestParams,self).__init__(url)
		self.businessType = 'ClientPerformance'
		self.country = ''
		self.province=''
		self.city=''
		self.weibo_version=[]
		self.systerm_version=[]
		self.netType = []
		self.mobile_type=[]

	def setCountry(self,country):
		self.country = country

	def getCountry(self):
		return self.country

	def setProvince(self,province):
		self.province = province

	def getProvince(self):
		return self.province

	def setCity(self,city):
		self.city = city

	def getCity(self):
		return self.city

	def setWeiboVersion(self,weibo_version):
		self.weibo_version = weibo_version

	def getWeiboVersion(self):
		return self.weibo_version

	def setSystemVersion(self,systerm_version):
		self.systerm_version = systerm_version

	def getSystemVersion(self):
		return self.systerm_version

	def setNetType(self,netType):
		self.netType = netType

	def getNetType(self):
		return self.netType

	def setMobileType(self,mobile_type):
		self.mobile_type = mobile_type

	def getMobileType(self):
		return self.mobile_type

	def getCompleteUrl(self):
		url = super(PerformanceRequestParams,self).getCompleteUrl()
		values = {'country':self.country,
					'province':self.province,
					'city':self.getDefaultCityParam(),
					'version':self.getParamOfList(self.weibo_version),
					'systerm_version':self.getParamOfList(self.systerm_version),
					'netType':self.getParamOfList(self.netType),
					'mobile_type':self.getParamOfList(self.mobile_type)}
		return url+'&'+urllib.urlencode(values)

	def getParamOfList(self, data):
		index = 0
		param = ''
		length = len(data)
		for item in data:
			index += 1
			if index < length:
				param = param + item + ','
			else:
				param = param + item
		return param

	def getDefaultCityParam(self):
		if len(self.city)==0 :
			return 'null'
		return  self.city



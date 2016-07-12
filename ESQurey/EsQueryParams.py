#encoding:utf-8
from datetime import timedelta, date
import time

__metaclass__=type

class EsQueryParams(object):

	"""docstring for EsQueryParams
		query parameters for pass ES platform
	"""
	def __init__(self, interval, platform="Android"):
		super(EsQueryParams, self).__init__()
		self.host = '10.19.0.64'
		self.port = 9200
		self.interval = interval

		self.daysIndex = []
		currentDay = date.today()
		timstamp = time.mktime(time.strptime(str(currentDay)+" 00:00:00",'%Y-%m-%d %H:%M:%S'))
		self.timeTo  = (int(timstamp))*1000
		self.timeFrom = self.timeTo
		endDay = (currentDay-timedelta(1)).strftime('%Y.%m.%d')
		self.daysIndex.append(endDay)
		for i in range(0,interval):
			self.timeFrom = (self.timeFrom - 24*60*60*1000)
			currentDay = currentDay - timedelta(1)
			self.daysIndex.append(currentDay.strftime('%Y.%m.%d'))

		self.platform = platform

	def setInterval(sel,interval):
		self.interval = interval
	
	def getInterval(self):
		return self.interval

	def getHost(self):
		return self.host

	def getPort(self):
		return self.port

	def setTimeFrom(self,timeFrom):
		self.timeFrom=timeFrom
	
	def getTimeFrom(self):
		return self.timeFrom

	def setTimeTo(self,timeTo):
		self.timeTo=timeTo

	def getTimeTo(self):
		return self.timeTo

	def getPlatform(self):
		return self.platform

	def setPlatform(self,platform):
		self.platform = platform

	def getUrlPattern(self):
		url = "/"
		for day in self.daysIndex:
			url = url + ("logstash-mweibo-%s" % day)
			if(self.daysIndex.index(day) < len(self.daysIndex)-1):
				url = url + ","
		return url +"/_search"

	def getEsQueryBody():
		return ''
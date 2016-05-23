from Request_Performance import RequestParams
from Request_Performance import HttpRequest
from Request_Performance import PerformanceAvgCostTimeHandler
import json

__metaclass__ = type

class PerformanceErrorCodeHandler(PerformanceAvgCostTimeHandler.PerformanceAvgCostTimeHandler):

	def __init__(self,filename):
		super(PerformanceErrorCodeHandler, self).__init__(filename)
		self.api = "weiboMobileClientPerformance.getTypeTrend"
		self.docid = ''
		self.sheetname='ErrorCode'


	def requestStart(self, sub_type):
		print 'fetch errorcode trend of %s_%s started' % (self.system,sub_type)

	
	def requestEnd(self, sub_type, data):
		print 'fetch errorcode trend of %s_%s end. the resut is: %s' % (self.system,sub_type,data)
		
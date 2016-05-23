from Request_Performance import RequestParams
from Request_Performance import HttpRequest
from Request_Performance import PerformanceAvgCostTimeHandler
import json

__metaclass__ = type

class PerformanceSucRatioHandler(PerformanceAvgCostTimeHandler.PerformanceAvgCostTimeHandler):

	def __init__(self,filename):
		super(PerformanceSucRatioHandler, self).__init__(filename)
		self.api = "weiboMobileClientPerformance.getSuccRatio"
		self.docid = "versionSuccRatioContaine"
		self.sheetname='SucRatio'

	def requestStart(self, sub_type):
		print 'fetch successed ratio of %s_%s started' % (self.system,sub_type)


	def requestEnd(self, sub_type, data):
		print 'fetch successed ratio of %s_%s end. the resut is: %s' % (self.system,sub_type,data)
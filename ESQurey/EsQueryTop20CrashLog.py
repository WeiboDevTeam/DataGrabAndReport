from EsCrashQueryParams import  EsCrashQueryParams
from EsQueryHelper import  EsQueryHelper
from Request_Performance import InsertUtils

__metaclass__=type

class EsQueryTop20CrashLog(object):
	"""docstring for EsQueryTop20CrashLog
		query top 20 crash log
	"""
	def __init__(self, params):
		super(EsQueryTop20CrashLog, self).__init__()
		self.params = params

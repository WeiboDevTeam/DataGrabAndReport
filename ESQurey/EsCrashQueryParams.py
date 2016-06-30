from EsQueryParams import EsQueryParams
__metaclass__=type

class EsCrashQueryParams(EsQueryParams):
	"""docstring for EsCrashQueryParams
		query crash of ES platform
	"""
	def __init__(self, interval, platform):
		super(EsCrashQueryParams, self).__init__(interval, platform)
		self.programName = "mweibo_client_crash"
		self.fromValues = []
		self.querySize = 1

	def setFromValues(self,fromValues):
		for fromvalue in fromValues:
			self.fromValues.append(fromvalue)

	def getFromValues(self):
		return self.fromValues

	def setQuerySize(self, size):
		self.querySize = size

	def getQuerySize(self):
		return self.querySize

	def getProgramName(self):
		return self.programName

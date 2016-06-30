from EsQueryParams import EsQueryParams
__metaclass__=type

class EsCrashQueryParams(EsQueryParams):
	"""docstring for EsCrashQueryParams
		query crash of ES platform
	"""
	def __init__(self, interval):
		super(EsCrashQueryParams, self).__init__(interval)
		self.programName = "mweibo_client_crash"
		self.fromValues = []
		self.querySize = 1
		self.fingerprint=""

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

	def setFingerPrint(self,fingerprint):
		self.fingerprint = fingerprint

	def getFingerPrint(self):
		return self.fingerprint
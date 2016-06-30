from JiraCreator import JiraCreator

__metaclass__ = type
class JiraCreateHelper(object):
	WEIBO_ANDROID_PROJECT = "MOBILEWEIBOANDROIDPHONE"
	WEIBO_IPHONE_PROJECT = "MOBLEWEIBOIPHONE"

	"""docstring for JiraCreateHelper"""
	def __init__(self):
		super(JiraCreateHelper, self).__init__()

	@staticmethod
	def getVersion(fromvalue):
		version = fromvalue[2:5]
		return '.'.join(version) 

	@staticmethod
	def getProjectKey(fromvalue):
		if(fromvalue.endswith('5010')):
			return WEIBO_ANDROID_PROJECT
		else:
			return WEIBO_IPHONE_PROJECT

	def createJiraIssue(crashLogList):
		if(crashLogList == False || len(crashLogList) == 0):
			return False

		jiraCreator = JiraCreator()
		jiraCreator.login()

		remoteVersion = JiraCreateHelper.getRemoteVersion(jiraCreator,crashLogList[0])
		for crashLogInfo in crashLogList:


			if(JiraCreateHelper.checkCrashInfoValid(crashLogInfo) == False):
				continue
			
			fromvalue = crashLogInfo['fromvalue']
			crashReason = crashLogInfo['reason']
			if(fromvalue.endswith('5010') && crashReason.find('java.lang.OutOfMemoryError')):
				continue
			fingerprint = crashLogInfo['fingerprint']

			projectKey = JiraCreateHelper.getProjectKey(fromvalue)
			issue = jiraCreator.queryJiraIssue(projectKey, [fingerprint])
			if(issue == None):
				#create new jira issue
				jiraCreator.outPutToJira(crashLogInfo,remoteVersion)
			else:
				findversion = False
				affectVersions = issue['affectsVersions']
				for version in affectsVersions:
					if(version['name']==JiraCreateHelper.getVersion(fromvalue)):
						findversion = True
						break
				if(findversion == False):
					#jiraCreator.updateJiraVersion(issue, crashLogInfo)

	@staticmethod
	def getRemoteVersion(self,jiraCreator,crashlogInfo):
		fromvalue = crashlogInfo['fromvalue']
		version = JiraCreateHelper.getVersion(fromvalue)
		projectKey = JiraCreateHelper.getProjectKey(fromvalue)
		return jiraCreator.getRemoteVersion(projectKey,version)

	@staticmethod
	def checkCrashInfoValid(crashLogInfo):
		if(crashLogInfo == False):
			return False
		fromvalue = crashLogInfo['fromvalue']
		fingerprint = crashLogInfo['fingerprint']
		crashlog = crashLogInfo['jsonlog']
		return fromvalue == True && fingerprint == True && crashlog == True

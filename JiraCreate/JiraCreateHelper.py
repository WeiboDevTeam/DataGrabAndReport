#encoding:utf-8
from JiraCreator import JiraCreator

__metaclass__ = type
class JiraCreateHelper(object):
	WEIBO_ANDROID_PROJECT = "MOBILEWEIBOANDROIDPHONE"
	WEIBO_IPHONE_PROJECT = "MOBLEWEIBOIPHONE"
	JIRA_STATUS = {'1':"开放中",'3':'解决中','5':'已解决','6':'已关闭','7':'重开'}
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
			return JiraCreateHelper.WEIBO_ANDROID_PROJECT
		else:
			return JiraCreateHelper.WEIBO_IPHONE_PROJECT

	def createJiraIssue(self,crashLogList):
		if(crashLogList == False or len(crashLogList) == 0):
			return False

		jiraCreator = JiraCreator()
		jiraCreator.login()

		#remoteVersion = JiraCreateHelper.getRemoteVersion(jiraCreator,crashLogList[0])
		for crashLogInfo in crashLogList:

			if(JiraCreateHelper.checkCrashInfoValid(crashLogInfo) == False):
				continue
			
			fromvalue = crashLogInfo['fromvalue']
			crashReason = crashLogInfo['reason']
			if((fromvalue.endswith('5010')) and (crashReason.find('java.lang.OutOfMemoryError')>0)):
				continue
			fingerprint = crashLogInfo['fingerprint']

			projectKey = JiraCreateHelper.getProjectKey(fromvalue)
			version = JiraCreateHelper.getVersion(fromvalue)
			issue = jiraCreator.queryJiraIssue(projectKey, [fingerprint])
			if(issue == None):
				#create new jira issue
				jiraCreator.outPutToJira(crashLogInfo,projectKey,version)
			else:
				findversion = False
				affectVersions = issue['affectsVersions']
				for versionInfo in affectVersions:
					if(versionInfo['name']==version):
						findversion = True
						break
				if(findversion == False):
					status = issue['status']
					if(status == 5 or status == 6):
						print status
						status = 7 #reopen
					jiraCreator.updateJiraVersion(issue, crashLogInfo, version)
				else:
					pass
				crashLogInfo['jira_status'] = JiraCreateHelper.JIRA_STATUS[issue['status']]

	@staticmethod
	def getRemoteVersion(jiraCreator,crashlogInfo):
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
		result = ((fromvalue != False) and (fingerprint != False ) and (crashlog != False))
		return result

#encoding:utf-8
from JiraCreator import JiraCreator

__metaclass__ = type
class JiraCreateHelper(object):
	WEIBO_ANDROID_PROJECT = "MOBILEWEIBOANDROIDPHONE"
	WEIBO_IPHONE_PROJECT = "MOBLEWEIBOIPHONE"
	JIRA_STATUS = {'1':"open",'3':'inprogress','5':'resolved','6':'closed','7':'reopen'}
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
			print crashLogInfo['jsonlog']
			issue = jiraCreator.queryJiraIssue(projectKey, [fingerprint,crashLogInfo['jsonlog'][0:72]])
			print issue
			if(issue == None):
				#create new jira issue
				issue = jiraCreator.outPutToJira(crashLogInfo,projectKey,version)
				pass
			else:
				description = issue['description']
				find = description.find(crashLogInfo['jsonlog'])
				if(find!=-1):

					findversion = False
					affectVersions = issue['affectsVersions']
					for versionInfo in affectVersions:
						if(versionInfo['name']==version):
							findversion = True
							break
					if(findversion == False):
						status = issue['status']
						if(status == '5' or status == '6'):
							issue['status'] = '7' #reopen
						jiraCreator.updateJiraVersion(issue, crashLogInfo, version)
					else:
						pass
				else:
					issue = jiraCreator.outPutToJira(crashLogInfo,projectKey,version)

			crashLogInfo['jira_status'] = JiraCreateHelper.JIRA_STATUS[(int)(issue['status'])]

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

#encoding:utf-8
from JiraCreator import JiraCreator

__metaclass__ = type
class JiraCreateHelper(object):
	WEIBO_ANDROID_PROJECT = "MOBILEWEIBOANDROIDPHONE"
	WEIBO_IPHONE_PROJECT = "MOBLEWEIBOIPHONE"
	JIRA_STATUS = {'1':"open",'3':'inprogress','5':'resolved','6':'closed','7':'reopen'}
	JIRA_EXPECT_EXCEPTION=['java.lang.OutOfMemoryError','android.view.InflateException','java.lang.UnsatisfiedLinkError','java.lang.NoClassDefFoundError']
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

		MAX_LENGTH = 20
		length = len(crashLogList);
		if(length > MAX_LENGTH):
			crashLogList = crashLogList[0:MAX_LENGTH]

		jiraCreator = JiraCreator()
		jiraCreator.login()

		#remoteVersion = JiraCreateHelper.getRemoteVersion(jiraCreator,crashLogList[0])
		for crashLogInfo in crashLogList:

			if(JiraCreateHelper.checkCrashInfoValid(crashLogInfo) == False):
				continue
			
			fromvalue = crashLogInfo['fromvalue']
			crashReason = crashLogInfo['reason']

			isAndroid = fromvalue.endswith('5010')
			if(isAndroid and (JiraCreateHelper.isExceptCrashLog(crashReason))):
				continue
			fingerprint = crashLogInfo['fingerprint']

			projectKey = JiraCreateHelper.getProjectKey(fromvalue)
			version = JiraCreateHelper.getVersion(fromvalue)

			print crashLogInfo['jsonlog']
			issueFind = None
			try:
				if(isAndroid):
					query = [fingerprint,crashLogInfo['jsonlog'][0:72]]
				else:
					query = fingerprint

				issues = jiraCreator.queryJiraIssue(projectKey,query)
				if(issues == None):
					#create new jira issue
					print 'query nothing'
					issueFind = jiraCreator.outPutToJira(crashLogInfo,projectKey,version)
					pass
				else:
					find = False
					if(isAndroid):
						for issue in issues:
							description = issue['description']
							index = description.find(crashLogInfo['jsonlog'])
							if(index!=-1):
								find=True
								issueFind = issue
								print description
								break
					else:
						find = True
						issueFind = issues[0]
					print 'already create jira :'+str(find)
					if(find):
						findversion = False
						affectVersions = issue['affectsVersions']
						# for versionInfo in affectVersions:
						# 	if(versionInfo['name']==version):
						# 		findversion = True
						# 		break
						# if(findversion == False):
						# 	status = issue['status']
						# 	if(status == '5' or status == '6'):
						# 		issue['status'] = '7' #reopen
						# 	jiraCreator.updateJiraVersion(issue, crashLogInfo, version)
						# else:
						# 	pass
					else:
						issueFind = jiraCreator.outPutToJira(crashLogInfo,projectKey,version)
						print "didn't find "
					print issueFind
					if(issueFind != None):
						crashLogInfo['jira_status'] = JiraCreateHelper.JIRA_STATUS[issueFind['status']]
						crashLogInfo['jira_assignee'] = issueFind['assignee']
			except Exception, e:
				print str(e)
			else:
				pass

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
		result = ((fromvalue != None) and (fingerprint != None ) and (crashlog != None))
		return result

	@staticmethod
	def isExceptCrashLog(crashLogInfo):
		for exceptCrash in JiraCreateHelper.JIRA_EXPECT_EXCEPTION:
			find = crashLogInfo.find(exceptCrash)
			if(find>=0):
				return True

#encoding:utf-8
from JiraCreator import JiraCreator
import re
import hmac
import hashlib

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
	def getIOSCriticalLog(log):
		if log == None:
			return None
		else:
			log_lines = log.split('\n')
			groups=[]
			previous_is_weibo_moudle = False
			for log_line in log_lines:
				log_line = re.sub(' +',' ',log_line)
				log_line_splited = log_line.split(' ')

				if(len(log_line_splited)<2):
					continue

				moduleName = log_line_splited[1]
				is_weibo_module = moduleName.startswith('Weibo')
				result_line=''
				if(is_weibo_module):
					className = log_line_splited[len(log_line_splited)-1]
					index = className.find(':')
					classNameWithoutLineNum = className[0:index]+')'

					line = log_line_splited[1:2]+log_line_splited[3:-1]
					line = line + [classNameWithoutLineNum]
					log_line = " ".join(line)
					result_line = log_line + '\n'
					result_line = re.sub(r'__\d+','',result_line)
					print result_line

					print len(groups)
					if not previous_is_weibo_moudle:
						groups.append(result_line)
					else:
						last_group=groups[len(groups)-1]
						groups[len(groups)-1]=last_group+result_line
					previous_is_weibo_moudle = True
				else:
					previous_is_weibo_moudle = False
			selectedIndex = -1
			if(len(groups)<1):
				return None
			else:
				for groupIndex in range(0,len(groups)):
					if(groups[groupIndex].find('WBRecordCrashLog')>=0):
						selectedIndex = groupIndex
						break
				if(selectedIndex>=0 and (selectedIndex+1) < len(groups)):
					return groups[selectedIndex+1]
				elif(groups[0].find('main.m')<0):
					return groups[0]
				else:
					return None

	@staticmethod
	def getEsMd5(infomation,key="SUPERSECRET"):
		 return hmac.new(key,infomation,hashlib.md5).hexdigest()[0:32]

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

		jiraCreator = JiraCreator()
		jiraCreator.login()

		#remoteVersion = JiraCreateHelper.getRemoteVersion(jiraCreator,crashLogList[0])
		loopCount = 0 #用来控制创建jira的数量
		for crashLogInfo in crashLogList:
			loopCount += 1
			if(JiraCreateHelper.checkCrashInfoValid(crashLogInfo) == False):
				continue
			
			fromvalue = crashLogInfo['fromvalue']
			crashReason = crashLogInfo['jsonlog']

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
					query = fingerprint
				else:

					log = JiraCreateHelper.getIOSCriticalLog(crashLogInfo['jsonlog'])
 					if(log == None):
 						query = fingerprint
 					else:
 						query = JiraCreateHelper.getEsMd5(log)
 				crashLogInfo['jira_query_key']=query
				issues = jiraCreator.queryJiraIssue(projectKey,query)
				if(issues == None):
					#create new jira issue
					print 'query nothing'
					if(loopCount <= MAX_LENGTH):
						issueFind = jiraCreator.outPutToJira(crashLogInfo,projectKey,version)
						print "create jira"
				else:
					find = False
					if(isAndroid):
						for issue in issues:
							# 检查版本是否一致
							description = issue['description']
							index = description.find(fromvalue)
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
						affectVersions = issueFind['affectsVersions']
					elif(loopCount <= MAX_LENGTH):
						issueFind = jiraCreator.outPutToJira(crashLogInfo,projectKey,version)
						print "didn't find and create"
					else:
						print loopCount
				print issueFind
				if(issueFind != None):
					crashLogInfo['jira_status'] = JiraCreateHelper.JIRA_STATUS[issueFind['status']]
					crashLogInfo['jira_assignee'] = issueFind['assignee']
					crashLogInfo['jira_id'] = issueFind['key']
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

def test():
	jiraCreator = JiraCreator()
	jiraCreator.login()
	issues = jiraCreator.queryJiraIssue('MOBILEWEIBOANDROIDPHONE','0a6df814b9e7348c04ce210c7e22a7d3')
	print issues

if __name__ == '__main__':
	test()

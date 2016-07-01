#encoding:utf-8
import xmlrpclib
from datetime import date
import datetime
import time
import random
__metaclass__=type
class JiraCreator(object):
	"""docstring for JiraCreator
	   创建jira
	"""
	JIRA_URL = 'http://issue.internal.sina.com.cn/rpc/xmlrpc'
	JIRA_USER = 'guizhong'
	JIRA_PASS = '19880808.lgz6'
	ISSUE_TYPE_ID = "1";
	PRIORITY_ID = "3";

	ISSUE_STATUS_OPEN = 1
	SSUE_STATUS_IN_PROGRESS = 3
	ISSUE_STATUS_RESOLVED = 5
	ISSUE_STATUS_CLOSED = 6
	ISSUE_STATUS_REOPEN = 7

	def __init__(self):
		super(JiraCreator, self).__init__()

	def login(self):
		self.session = xmlrpclib.ServerProxy(JiraCreator.JIRA_URL)
		self.auth = self.session.jira1.login(JiraCreator.JIRA_USER,JiraCreator.JIRA_PASS)
		print self.auth

	def checkSession(self):
		if(self.auth == False):
			return False
		else:
			return True
		
	def outPutToJira(self,crashLogInfo,projectKey,version):
		'''
		output data to the jira by xmlRPC.  
		'''
		if(self.checkSession() == False):
			print 'please login first'
			return None
		sudsDict = {}
		sudsDict['project'] = projectKey
		sudsDict['type'] = JiraCreator.ISSUE_TYPE_ID
		sudsDict['priority'] = JiraCreator.PRIORITY_ID
		sudsDict['summary'] = self.createJiraSummary(crashLogInfo)
		sudsDict['description'] = self.createJiraDesc(crashLogInfo)

		if(crashLogInfo['fromvalue'].endswith("3010")):
			sudsDict['assignee'] = 'chengwei2'
		else:
			sudsDict['assignee'] = 'guizhong'
		
		sudsDict['duedate']= datetime.datetime.now()
		sudsDict['affectsVersions'] = [{'id':str(random.randint(1,100000)),'name':version}]
		print sudsDict
		newIssue = self.session.jira1.createIssue(self.auth, sudsDict)
		time.sleep(1)

		return newIssue['key']

	def isNeedToUpdateIssue(self,issueKey):
		if(self.checkSession() == False):
			print 'please login first'
			return None

		issue = self.session.jira1.getIssue(self.auth,issueKey)
		if issue['status'] != '6':
			return True
		else:
			return False

	def queryJiraIssue(self, project_key, terms):
		if(self.checkSession() == False):
			print 'please login first'
			return None
		if isinstance(terms, (list, tuple)):
			terms = ' '.join(terms)
		issues = self.session.jira1.getIssuesFromTextSearchWithProject(self.auth, [project_key], terms, 1)
		if(issues != None and (len(issues) == 1)):
			issue = issues[0]
			return issue
		return None

	def getRemoteVersion(self,project_key,version):
		if(self.checkSession() == False):
			print 'please login first'
			return None
		versions = self.session.jira1.getVersions(self.auth, project_key)
		for remoteVersion in versions:
			if remoteVersion['name'] == version:
				return remoteVersion
		return None

	def updateJiraVersion(self,issue,crashLogInfo,version):
		if(self.checkSession() == False):
			print 'please login first'
			return None

		affectsVersions = issue['affectsVersions']
		affectsVersions.append({'id':str(random.randint(1,100000)),'name':version})
		print affectsVersions
		self.session.jira1.updateIssue(self.auth,issue['key'],{'status':[issue['status']],'affectsVersions':affectsVersions})
		time.sleep(1)

	def createJiraSummary(self, crashLogInfo):
		summary = "crash by:"+crashLogInfo['reason']
		if(len(summary) > 255):
			return summary[0:255]
		else:
			return summary

	def createJiraDesc(self,crashLog):
		desc="log fingerprint: "+crashLog['fingerprint']+ \
		"\ncrash uid: "+crashLog['uid']+ \
		"\nseatch in kibana :"+"http://sla.weibo.cn/mweibo/#/dashboard/elasticsearch/mweibo_client_crash_for_jira?fingerprint="+ \
		crashLog['fingerprint']+"&from="+crashLog['fromvalue'] + \
		"\nin version:"+crashLog['fromvalue']+"\n"+crashLog['jsonlog']
		print desc
		return desc
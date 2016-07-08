#encoding:utf-8
import xmlrpclib
from datetime import date
import datetime
import time
import random
import urllib
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
	ES_CRASH_URL='''http://sla.weibo.cn:5601/app/kibana#/discover/New_Discover_mweibo_clent_crash?'''
	ES_CRASH_QUERY_STRING ='''(filters:!((query:(match:(jsoncontent.reson:(query:'%s',type:phrase))))),query:(query_string:(analyze_wildcard:!t,query:'programname:mweibo_client_crash AND fingerprint:%s AND jsoncontent.from:%s')))'''
	

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
		sudsDict['affectsVersions'] = [{'id':'versions','name':version}]
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
		issues = self.session.jira1.getIssuesFromTextSearchWithProject(self.auth, [project_key], terms, 3)
		if(issues != None and (len(issues) >	 0)):
			return issues
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
		self.session.jira1.updateIssue(self.auth,issue['key'],{'status':[issue['status']],'affectsVersions':affectsVersions})
		time.sleep(1)

	def createJiraSummary(self, crashLogInfo):
		summary = "crash by:"+crashLogInfo['reason']
		if(len(summary) > 255):
			return summary[0:255]
		else:
			return summary

	def createJiraDesc(self,crashLog):
		es_query = JiraCreator.ES_CRASH_QUERY_STRING % (crashLog.get('reason'), crashLog.get('fingerprint'),crashLog.get('fromvalue'))
		es_query_body = {'_g':'(time:(from:now-12h,to:now))','_a':es_query}
		es_query_url = JiraCreator.ES_CRASH_URL+urllib.urlencode(es_query_body)
		desc="log fingerprint: "+crashLog.get('fingerprint')+ \
		"\nsearch in kibana :"+ es_query_url + \
		"\nin version:"+crashLog.get('fromvalue')+"\n"+crashLog.get('jsonlog')

		if(crashLog.get('uid') != None):
			desc = desc+"\ncrash uid: " + crashLog.get('uid')
		if(crashLog.get('counts') != None):
			desc = desc+"\ncrash count: " + str(crashLog.get('counts'))
		print desc
		return desc
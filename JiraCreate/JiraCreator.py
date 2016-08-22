#encoding:utf-8
import xmlrpclib
from datetime import date
import datetime
import time
import random
import urllib
import ConfigParser
import re
from ManagerUtils import Utils

__metaclass__=type
class JiraCreator(object):
	"""docstring for JiraCreator
	   创建jira
	"""
	ISSUE_TYPE_ID = "1";
	PRIORITY_ID = "3";
	ES_CRASH_URL='''http://sla.weibo.cn:5601/app/kibana#/discover/New_Discover_mweibo_clent_crash?'''
	ES_CRASH_ANDROID_QUERY_STRING ='''(filters:!((query:(match:(jsoncontent.reson:(query:'%s',type:phrase))))),query:(query_string:(analyze_wildcard:!t,query:'programname:mweibo_client_crash AND fingerprint:%s AND jsoncontent.from:%s')))'''
	ES_CRASH_IOS_QUERY_STRING ='''(filters:query:(query_string:(analyze_wildcard:!t,query:'programname:mweibo_client_crash AND fingerprint:%s AND jsoncontent.from:%s')))'''

	ISSUE_STATUS_OPEN = 1
	SSUE_STATUS_IN_PROGRESS = 3
	ISSUE_STATUS_RESOLVED = 5
	ISSUE_STATUS_CLOSED = 6
	ISSUE_STATUS_REOPEN = 7

	def __init__(self):
		super(JiraCreator, self).__init__()
		self.init_jira_config()

	def init_jira_config(self):
		config_read = ConfigParser.RawConfigParser()
		config_read.read(Utils.getConfigFolder()+'account.config')
		secs = config_read.sections()
		print secs
		for sec in secs:
			if sec == u'jira_config':
				options = config_read.options(sec)
				self.jira_config = {}
				for key in options:
					self.jira_config[key]=config_read.get(sec,key)

	def login(self):
		jira_url = self.jira_config.get('jira_url')
		if(jira_url == None):
			print 'jira_url is null'
			return
		
		jira_user = self.jira_config.get('jira_user')
		if(jira_user == None):
			print 'jira_user is null'
			return

		jira_pwd = self.jira_config.get('jira_pwd')
		if(jira_pwd == None):
			print 'jira_pwd is null'
			return

		self.session = xmlrpclib.ServerProxy(jira_url)
		self.auth = self.session.jira1.login(jira_user,jira_pwd)
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
			sudsDict['assignee'] = self.jira_config.get('jira_ios_assign')
		else:
			sudsDict['assignee'] = self.jira_config.get('jira_android_assign')
		
		sudsDict['duedate']= datetime.datetime.now()
		sudsDict['affectsVersions'] = [{'id':'versions','name':version}]
		print sudsDict
		newIssue = self.session.jira1.createIssue(self.auth, sudsDict)
		time.sleep(1)

		return newIssue

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
		issues = self.session.jira1.getIssuesFromTextSearchWithProject(self.auth, [project_key], terms, 10)
		if(issues != None and (len(issues) >	 0)):
			return sorted(issues,key=lambda x:(x.get('duedate', 0)),reverse=True)
		return None

	def queryIssueById(self,issueId):
		if(self.checkSession() == False):
			print 'please login first'
			return None
		issue = self.session.jira1.getIssue(self.auth, issueId)
		if(issue != None ):
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
		self.session.jira1.updateIssue(self.auth,issue['key'],{'status':[issue['status']],'affectsVersions':affectsVersions})
		time.sleep(1)

	def addComment(self,issueKey,crashLogInfo):
		if(self.checkSession() == False):
			print 'please login first'
			return None
		else:
			return self.session.jira1.addComment(self.auth,issueKey,self.createJiraComment(crashLogInfo))

	def getComments(self,issueKey):
		if(self.checkSession() == False):
			print 'please login first'
			return None
		else:
			return self.session.jira1.getComments(self.auth,issueKey)

	def createJiraSummary(self, crashLogInfo):
		summary = "crash by:"+self.__getCrashReason(crashLog)
		if(len(summary) > 255):
			return summary[0:255]
		else:
			return summary

	def createJiraDesc(self,crashLog):		
		print "createJiraDesc"
		desc = "log fingerprint: "+crashLog.get('jira_query_key')
		desc = desc + "\nsearch in kibana :"+ self.__buildESQueryUrl(crashLog) + \
		"\nin version:"+crashLog.get('fromvalue')+"\n"+crashLog.get('jsonlog')

		if(crashLog.get('uid') != None):
			desc = desc+"\ncrash uid: " + crashLog.get('uid')
		if(crashLog.get('counts') != None):
			desc = desc+"\ncrash count: " + str(crashLog.get('counts'))
		print desc
		return desc

	#构建jira备注信息
	def createJiraComment(self,crashLog):
		comment = "search in kibana :"+ self.__buildESQueryUrl(crashLog) + \
		"\nin version:"+crashLog.get('fromvalue')
		if(crashLog.get('counts') != None):
			comment = comment+"\ncrash count: " + str(crashLog.get('counts'))
		return comment
	
	#构建es查询地址
	def __buildESQueryUrl(self,crashLog):
		fromvalue = crashLog.get('fromvalue')
		if(fromvalue.endswith('5010')):
			#将单引号替换成'!\''
			replacedReson = re.sub('\'','!\'',crashLog.get('reason'))
			es_query = JiraCreator.ES_CRASH_ANDROID_QUERY_STRING % (replacedReson, crashLog.get('fingerprint'),crashLog.get('fromvalue'))
		else:
			es_query = JiraCreator.ES_CRASH_IOS_QUERY_STRING % (crashLog.get('fingerprint'),crashLog.get('fromvalue'))
		es_query_body = {'_g':'(time:(from:now-24h,to:now))','_a':es_query}
		es_query_url = JiraCreator.ES_CRASH_URL+urllib.urlencode(es_query_body)
		return es_query_url

	#ios crash原因并不是直接用的es返回的结果，本地做过处理，所以在summary中展示的是处理过的原因，在es查询url中用到的是es返回的reason
	def __getCrashReason(self,crashLog):
		reason = crashLog.get('real_reason')
		if(reason == None):
			reason = crashLog.get('reason')
		return reason
		
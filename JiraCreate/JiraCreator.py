#encoding:utf-8
import xmlrpclib
import datetime
__metaclass__=type
class JiraCreator(object):
	"""docstring for JiraCreator
	   创建jira
	"""
	JIRA_URL = 'http://issue.internal.sina.com.cn/rpc/soap/jirasoapservice-v2?wsdl'
	JIRA_USER = 'guizhong'
	JIRA_PASS = '19880808.lgz6'
	ISSUE_TYPE_ID = "1";
	PRIORITY_ID = "3";

	ISSUE_STATUS_OPEN = 1
	SSUE_STATUS_IN_PROGRESS = 3
	ISSUE_STATUS_RESOLVED = 5
	ISSUE_STATUS_CLOSED = 6
	ISSUE_STATUS_REOPEN = 7

	def __init__(self, arg):
		super(JiraCreator, self).__init__()
		self.arg = arg


	def login(self):
		self.session = xmlrpclib.ServerProxy(JIRA_URL)
		self.auth = self.session.jira1.login(JIRA_USER,JIRA_PASS)

	def checkSession(self):
		if(self.session == False || self.auth == False):
			return False
		else:
			return True
		
	def outPutToJira(self,crashLogInfo,projectKey,version):
		'''
		output data to the jira by xmlRPC.  
		'''
		if(self.checkSession() == False):
			print 'please login first'
		sudsDict = {}
		sudsDict['project'] = projectKey
		sudsDict['type'] = ISSUE_TYPE_ID
		sudsDict['priority'] = PRIORITY_ID
		sudsDict['summary'] = self.createJiraSummary(crashLogInfo)
		sudsDict['description'] = self.createJiraDesc(crashLogInfo)

		if(crashLogInfo['fromvalue'].endswith("3010")):
			sudsDict['assignee'] = 'chengwei2'
		else:
			sudsDict['assignee'] = 'guizhong'
		
		sudsDict['duedate']= datetime.today()
		sudsDict['affectsVersions'] = [{'id':version['name']}]
		newIssue = self.seesion.jira1.createIssue(self.auth, sudsDict)
		time.sleep(1)

		return newIssue['key']

	def isNeedToUpdateIssue(self,issueKey):
		if(self.checkSession() == False):
			print 'please login first'

		issue = self.session.jira1.getIssue(self.auth,issueKey)
		if issue['status'] != '6':
			return True
		else:
			return False

	def queryJiraIssue(self, project_key, terms):
		if(self.checkSession() == False):
			print 'please login first'
		if isinstance(terms, (list, tuple)):
            terms = ' '.join(terms)
		issues = self.seesion.jira1.getIssuesFromTextSearchWithProject(self.auth, [project_key], terms, 1)
		if(issues != None && len(issues) == 1):
			issue = issues[0]
			return issue
		return None

	def getRemoteVersion(self,project_key,version):
		if(self.checkSession() == False):
			print 'please login first'
		versions = self.seesion.jira1.getVersions(self.auth, project_key)
		for remoteVersion in versions:
			if remoteVersion['name'] == version:
				return remoteVersion
		return None

	def updateJiraIssue(self,issueKey,description):
		if(self.checkSession() == False):
			print 'please login first'

		self.seesion.jira1.updateIssue(self.auth,issueKey,{'description':[description]})
		time.sleep(1)

	def createJiraSummary(self, crashLogInfo):
		summary = ''
		fromvalue = crashLog['fromvalue']
		summary = "crash by:"+crashLog['reason']
		if(len(summary) > 255):
			return summary[0:255]
		else:
			return summary

	def createJiraDesc(self,crashLog):
		return "log fingerprint: "+crashLog['fingerprint']
				+"\n seatch in kibana :"
				+"http://sla.weibo.cn/mweibo/#/dashboard/elasticsearch/mweibo_client_crash_for_jira?fingerprint="
				+crashLog['fingerprint']+"&from="+crashLog['fromvalue']
				+"\n in version:"+crashLog['fromvalue']
				+"\n"
				+crashLog['jsonlog']
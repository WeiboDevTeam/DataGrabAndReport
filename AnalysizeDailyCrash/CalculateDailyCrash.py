#encoding=utf-8
import os,sys
import csv
from CSVFileUtils import UnicodeReader
from CSVFileUtils import UnicodeWriter
from JiraCreate import JiraCreator
import ConfigParser
import codecs

csv_header_field_names=[u'fingerprint',u'fromvalue',u'jsonlog',u'counts',u'crash_total_count',u'crash_ratio',u'jira_id',u'jira_assignee',u'component']
max_top_crash = 10

def getOutputPath(platform):
	rootDir=os.path.abspath(os.path.dirname(sys.argv[0]))
	outputDir = rootDir + os.sep + 'output' + os.sep + 'top_crash_ratio' + os.sep + platform
	if os.path.isdir(outputDir)==False:
	  print 'create dir:' + outputDir
	  os.makedirs(outputDir)
	return outputDir

def writeDataToFile(rows,fileName):
	if(len(rows)<=0):
		return
	fromvalue = rows[0].get('fromvalue')
	if fromvalue.endswith('5010'):
		platform = 'android'
	else:
		platform = 'iphone'
	verion=fromvalue[2:5]
	filePathParent = getOutputPath(platform) + os.sep + verion
	if(os.path.isdir(filePathParent)==False):
		os.makedirs(filePathParent)
	filePath = filePathParent + os.sep + fileName
	with open(filePath,'wb') as f:
		unicodeWriter = UnicodeWriter(f,csv_header_field_names)
		unicodeWriter.writeHeader()
		unicodeWriter.writerows(rows)

class CalculateDailyCrash(object):
	"""docstring for CalculateDailyCrash"""
	def __init__(self, csvFileDir):
		super(CalculateDailyCrash, self).__init__()
		self.dir = csvFileDir
		self.client_staffs=self.__readClientStaffsInfo()

	def __readClientStaffsInfo(self):
		config_read = ConfigParser.RawConfigParser()
		config_read.readfp(codecs.open('wb_client_staff.data', "r", "utf-8-sig"))  
		options = config_read.options('wb_client_staff')
		if(options != None):
			result = {}
			for o in options:
				result[o]=config_read.get('wb_client_staff',o)
			return result
		else:
			return None

	def __readDataFromFile(self,path):
		with open(path,'rb') as f:
			data=[]
			unicodeReader = UnicodeReader(f)
			for row in unicodeReader:
				data.append(row)
			return data		

	def __getAppendData(self,item):
		if item == None:
			return None
		else:
			return (item.pop('counts'),item.pop('crash_total_count'),item.pop('crash_ratio'))

	# def __queryCrashComponent(self,resultList):
	# 	if(resultList == None):
	# 		pass
	# 	jiraCreator = JiraCreator.JiraCreator()
	# 	jiraCreator.login()
	# 	for crashItem in resultList.values():
	# 		issueid=crashItem.get('jira_id')
	# 		if(issueid != None and issueid != u'None'):
	# 			issue = jiraCreator.queryIssueById(issueid)
	# 			components = issue.get('components')
	# 			if(len(components)>0):
	# 				crashItem['component']=components[0].get('name')

	def __queryCrashComponent(self,resultList):
		if(resultList == None or self.client_staffs == None):
			pass
		for crashItem in resultList.values():
			issuer=crashItem.get('jira_assignee')
			if(issuer != None and issuer != u'None'):
				for component in self.client_staffs.keys():
					if(self.client_staffs.get(component).find(issuer)>=0):
						crashItem['component']=component
						break
			else:
				crashlog = crashItem.get('jsonlog')
				if(crashlog.find('java.lang.OutOfMemoryError')>=0 or crashlog.find('android.view.InflateException')>=0):
					crashItem['component']=u'OOM'

	def calculate(self):
		topMaxCrashCollection={}
		dataCollection={}
		for fileName in os.listdir(self.dir):
			filePath = os.path.join(self.dir,fileName)
   			if os.path.isfile(filePath):
   				if(fileName.endswith('.csv')==False):
   					continue
   				index = fileName.index('.')
   				fileName = fileName[0:index]
				data = self.__readDataFromFile(filePath)
				data.sort(key=lambda k: (k.get('crash_ratio', 0)))
				topMaxList=[]
				for i in range(0,max_top_crash):
					topMaxList.append(data.pop())

				for keyitem in topMaxCrashCollection.keys():
					find = False
					for item in topMaxList:
						if(keyitem==item.get("fingerprint")):
							find =  True
							break
					if(find==False):
						for item in data:
							if(keyitem==item.get("fingerprint")):
								findedItem=data.pop(data.index(item))
								topMaxCrashCollection.get(keyitem).get('data')[fileName]=self.__getAppendData(findedItem)
								topMaxCrashCollection.get(keyitem)['jira_id']=findedItem['jira_id']
								topMaxCrashCollection.get(keyitem)['jira_assignee']=findedItem['jira_assignee']
								break

				for item in topMaxList:
					fingerprint = item.get("fingerprint")
					collectionInfo = topMaxCrashCollection.get(fingerprint)
					if(collectionInfo != None):
						collectionInfo.get('data')[fileName]=self.__getAppendData(item)
					elif(dataCollection.get(fingerprint)!=None):
						itemSelected = dataCollection.pop(fingerprint)
						itemSelected.get('data')[fileName]=self.__getAppendData(item)
						collectionInfo = itemSelected
					else:
						item['data']={fileName:self.__getAppendData(item)}
						collectionInfo = item
					collectionInfo['jira_id']=item['jira_id']
					collectionInfo['jira_assignee']=item['jira_assignee']
					topMaxCrashCollection[fingerprint]=collectionInfo
				for sortedItem in data:
					fingerprint = sortedItem.get("fingerprint")
					collectionInfo = dataCollection.get(fingerprint)
					if(collectionInfo != None):
						collectionInfo.get('data')[fileName]=self.__getAppendData(sortedItem)
					else:
						sortedItem['data']={fileName:self.__getAppendData(sortedItem)}
						collectionInfo = sortedItem
					collectionInfo['jira_id']=sortedItem['jira_id']
					collectionInfo['jira_assignee']=sortedItem['jira_assignee']
					dataCollection[fingerprint]=collectionInfo
				for keyitem in topMaxCrashCollection.keys():
					data = topMaxCrashCollection.get(keyitem).get('data')
					if(data.has_key(fileName) == False):
						data[fileName]=None
		self.__queryCrashComponent(topMaxCrashCollection)
		return topMaxCrashCollection


		

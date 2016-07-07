#encoding:utf-8
from EsCrashQueryParams import  EsCrashQueryParams
from EsQueryHelper import  EsQueryHelper
from EsQueryCrashSingleLog import  EsQueryCrashSingleLog 
from ManagerUtils import InsertUtils
from JiraCreate import JiraCreateHelper
from EsQueryJob import EsQueryJob
import json
import difflib,re

__metaclass__=type
class EsQueryCrashInfluenceDepth(EsQueryJob):
	"""docstring for EsQueryCrashInfluenceDepth
	   查询crash次数top20的用户及对应的crash log
	"""
	def __init__(self, params):
		super(EsQueryCrashInfluenceDepth, self).__init__(params)
		
	def getWorkbookPath(self):
		return self.workbookPath

	def initFromValues(self):
		self.fromvalues = self.params.getFromValues()[0:1]

	def getWorkbookName(self):
		return "影响用户最深crash.xlsx"

	def buildQueryAgg(self):
		aggs1={}
		aggs1["terms"]={"size":20,"field":"jsoncontent.uid"}

		aggs2={}
		aggs2["terms"]={"size":3,"field":"jsoncontent.reson"}
		aggs2["aggs"]={"fingerprint":{"terms":{"size":5,"field":"fingerprint"}}}

		aggs1["aggs"]={"crash_reson":aggs2}
		return aggs1

	def parseAndWrite(self,result):
		json_data = json.loads(result)
		if json_data.get('aggregations')!=None:
			buckets= json_data['aggregations']['count_crash']['buckets']
			fromvalue = self.fromvalues[0]
			data_list=[]
			for item in buckets:
				uid=item.get('key')
				bukcet_crash_reson=item.get('crash_reson').get('buckets')
				for crash_reson in bukcet_crash_reson:
					reason = crash_reson['key']
					fingerprint_bucket = crash_reson.get('fingerprint').get('buckets')
					for crash_fingerprint in fingerprint_bucket:
						fingerprint = crash_fingerprint.get('key')
						count = crash_fingerprint.get('doc_count')
						jsonlog = self.__queryCrashLogByFingerPrinter(fromvalue, fingerprint)
						filterJsonlog = self.__filterCrashContent(jsonlog)
						result_item={"uid":uid,'fromvalue':fromvalue, "reason":reason,"fingerprint":fingerprint,"count":count,"jsonlog":filterJsonlog}
						data_list.append(result_item)
			print len(data_list)
			filteredList=[]
			for item in data_list:
				if(len(filteredList) == 0):
					filteredList.append(item)
				else:
					needAppend = False
					for filteredCrashItem in filteredList:
						crashReason = filteredCrashItem['reason']
						if(difflib.SequenceMatcher(None,crashReason,item['reason']).ratio() > 0.95):
							crashLog = filteredCrashItem['jsonlog']
							similarRatio = difflib.SequenceMatcher(None,crashLog, item['jsonlog'])
							ratio = similarRatio.ratio()
							if(fromvalue.endswith('0510')):
								threoldRatio = 0.9
							else:
								threoldRatio = 0.8
							if(ratio > threoldRatio):
								needAppend = False
								if(filteredCrashItem['uid'] == item['uid']):
									filteredCrashItem['count']=filteredCrashItem['count']+item['count']
								else:
									if(filteredCrashItem['count']<item['count']):
										needAppend = True
										filteredList.remove(filteredCrashItem)
									else:
										pass
								break
							else:
								needAppend = True
						else:
							needAppend = True
					if(needAppend):
						filteredList.append(item)	

			filteredList.sort(key=lambda k: (k.get('count', 0)),reverse=True)
			print 'after filtered length ' +str(len(filteredList))
			# jiraCreater = JiraCreateHelper.JiraCreateHelper()
			# jiraCreater.createJiraIssue(filteredList)

			self.__writeToExcel(filteredList)
		else:
			print 'result: '+str(json_data)

	def __queryCrashLogByFingerPrinter(self,fromvalue,fingerprint):
		querySingerCrashLog = EsQueryCrashSingleLog	(self.params)
		return querySingerCrashLog.doRequest(fromvalue,fingerprint)

	def __writeToExcel(self,data_list):
		utils=InsertUtils.InsertUtils()		
		# header=['uid','crash reason','crash log', 'fingerprint', 'jira_status', 'counts']	
		header=['uid','crash content','counts']
		utils.write_header(self.worksheet,0,0,header)
		index = 1			
		for data in data_list:
			row=[]
			row.append(data['uid'])
			# row.append(data['reason'])
			row.append(data['jsonlog'])
			# row.append(data['fingerprint'])
			#row.append(data['jira_status'])
			row.append(data['count'])
			utils.write_crash_data_with_yxis(self.worksheet,row,header,index,0)
			index += 1
		self.workbook.close()

	'''
	crash content过滤dexpathlist
	'''
	def __filterCrashContent(self,reason):
		regexDexPathList=r'(.*)DexPathList.*]](.*)'
		matchDexpath = re.match(regexDexPathList,reason,re.S|re.M|re.I)
		if matchDexpath:
			content=matchDexpath.group(1)+'DexPathList'+matchDexpath.group(2)
			return content
		else:
			return reason
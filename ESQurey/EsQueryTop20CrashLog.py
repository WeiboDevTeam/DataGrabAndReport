#!/usr/bin/python
# -*- coding: utf-8 -*-
from EsCrashQueryParams import  EsCrashQueryParams
from EsQueryCrashSingleLog import EsQueryCrashSingleLog
from EsQueryHelper import  EsQueryHelper
from ManagerUtils import InsertUtils
from EsQueryJob import EsQueryJob
from JiraCreate import JiraCreateHelper
import os,sys,re,difflib,json

__metaclass__=type

class EsQueryTop20CrashLog(EsQueryJob):
	"""docstring for EsQueryTop20CrashLog
		query top 20 crash log
	"""
	def __init__(self, params):
		super(EsQueryTop20CrashLog, self).__init__(params)

	def getWorkbookPath(self):
		return self.workbookPath

	def initFromValues(self):
		self.fromvalues = self.params.getFromValues()[0:1]
		# for fromvalue in self.params.getFromValues():
		# 	if fromvalue.find('672')>=0:
		# 		self.fromvalues = [fromvalue]
		# 		break
		
	def getWorkbookName(self):
		return 'Top20的crash.xlsx'

	def buildQueryMustNot(self):		
		must_not=[]
		return must_not

	def buildQueryAgg(self):
		aggs={}
		if(self.fromvalues[0].endswith('5010')):
			print True
			aggs["terms"]={"size":50,"field":"jsoncontent.content","order":{"_count":"desc"}}
			aggs["aggs"]={"count_uid":{"cardinality":{"field":"jsoncontent.uid"}},"fingerprint":{"terms":{"field":"fingerprint","size":1,"order":{"_count":"desc"}},"aggs":{"2":{"cardinality":{"field":"jsoncontent.uid"}},"reasons":{"terms":{"field":"jsoncontent.reson","size":1,"order":{"_count":"desc"}},"aggs":{"2":{"cardinality":{"field":"jsoncontent.uid"}}}}}}}
		else:
			aggs["terms"]={"size":50,"field":"fingerprint"}
			aggs["aggs"]={"count_uid":{"cardinality":{"field":"jsoncontent.uid"}},"reason":{"terms":{"field":"jsoncontent.reson","size":1}}}
		return aggs

	def parseAndWrite(self,result):
		json_data=json.loads(result)
		fromvalue=self.fromvalues[0]
		if json_data.get('aggregations')!=None:
			buckets= json_data['aggregations']['count_crash']['buckets']
			header=['crashlog','counts', 'jira_status', 'jira_assignee','jira_id']		

			data_list={}
			for item in buckets:
				content=item.get('key')			
				if(fromvalue.endswith("5010")):
					fingerprints=item.get('fingerprint').get('buckets')
					count=item.get('doc_count')
					for f in fingerprints:
						# 判断crash的content中是否包含crash的原因
						fingerprint = f.get('key')
						reasons=f.get('reasons').get('buckets')
						crashItem = self.__queryCrashLogByFingerPrinter(fromvalue, fingerprint)
						if(crashItem == None):
							continue
						# jsonlog = crashItem.get('jsonlog')
						crashReason = crashItem.get('crash_reason')
						if crashReason in content:
							reson_content=content
						else:
							reson_content=crashReason+'\n'+content
						# 过滤dexpathlist内容，这部分对相似度计算有影响
						filter_content=self.filterCrashContent(reson_content)
						if filter_content=="No Match!":
							filter_content = reson_content

						self.updateMatchedList(data_list,'uid',filter_content,fingerprint,crashReason,count)
				else:
					crashItem = self.__queryCrashLogByFingerPrinter(fromvalue, content)
					if(crashItem == None):
						continue
					jsonlog = crashItem.get('jsonlog')
					reason = crashItem.get('crash_reason')
					self.updateMatchedList(data_list,'uid',jsonlog,content,reason,item.get('doc_count'))

			sortedList = self.sortDataList(data_list,len(header)-1)
			# if(fromvalue.endswith('5010')):
			jiraCreater = JiraCreateHelper.JiraCreateHelper()
			jiraCreater.createJiraIssue(sortedList)

			self.writeSortedToExcel(header,sortedList)
			return sortedList
		else:
			print 'result: '+str(json_data)
			return None


	def __queryCrashLogByFingerPrinter(self,fromvalue,fingerprint):
		querySingerCrashLog = EsQueryCrashSingleLog	(self.params)
		return querySingerCrashLog.doRequest(fromvalue,fingerprint)

	'''
	对列表做排序,指定列进行降序排序
	'''
	def sortDataList(self,data_list,sort_index):
		datalist=[]
		for data in data_list.keys():
			crash_info = data_list.get(data)
			for key in crash_info.keys():
				row={'jsonlog':key,'reason':crash_info.get(key).get('reason'),'fingerprint':crash_info.get(key).get('fingerprint'),'fromvalue':self.fromvalues[0],'counts':crash_info.get(key).get('counts')}				
				datalist.append(row)
		return sorted(datalist,key=lambda x:(x.get('counts', 0)),reverse=True)

	'''
	将已排序的数据写入excel表格
	'''
	def writeSortedToExcel(self,header,data_list):
		utils=InsertUtils.InsertUtils()		
		utils.write_header(self.worksheet,0,0,header)
		index = 1			
		for data in data_list:
			row=[]
			row.append(data.get('reason'))
			# row.append(data.get('fingerprint'))
			jira_status = data.get('jira_status')
			if(jira_status != None):
				row.append(jira_status)
			else:
				row.append("No Jira")
			jira_assignee = data.get('jira_assignee')
			if(jira_assignee != None):
				row.append(jira_assignee)
			else:
				row.append("None")
			jira_id = data.get('jira_id')
			if(jira_id != None):
				row.append(jira_id)
			else:
				row.append('None')
			row.append(data.get('counts'))
			utils.write_crash_data_with_yxis(self.worksheet,row,header,index,0)
			index += 1

	'''
	crash content过滤dexpathlist
	'''
	def filterCrashContent(self,reason):
		regexDexPathList=r'(.*)DexPathList[\[][\[].*[\]][\]]([\s\S]*)'
		matchDexpath = re.match(regexDexPathList,reason,re.S|re.M|re.I)
		content='No Match!'
		while matchDexpath:
			content=matchDexpath.group(1)+'DexPathList...'+matchDexpath.group(2)
			matchDexpath=re.match(regexDexPathList,content,re.S|re.M|re.I)
			if matchDexpath:
				print 'matched again'
		return content
		
		

	'''
	计算crash content的相似度，相似度大于0.9及以上则视为同一crash
	'''
	def isSimilarCrashReason(self,str1,str2):
		s=difflib.SequenceMatcher(None,str1,str2)
		if s.ratio()> 0.9:		
			return True
		else:
			return False

	'''
	进行相似度计算后，根据结果进行crash次数累加
	'''
	def updateMatchedList(self,data_list,uid,content,fingerprint,crashReason,count):
		if data_list.get(uid)==None:
			dic={}
			dic[content]={"counts":count,'fingerprint':fingerprint,"reason":crashReason}
			data_list[uid]=dic
		else:
			dic=data_list.get(uid)
			similar = False
			similar_reason = content
			for reason in dic.keys():
				if self.isSimilarCrashReason(content,reason):
					similar = True
					similar_reason = reason
					break
			if similar:
				count=dic.get(similar_reason).get('counts')+count
				fingerprint=dic.get(similar_reason).get('fingerprint')	
				crashReason=dic.get(similar_reason).get('reason')

			data_list[uid][similar_reason]={"counts":count,'fingerprint':fingerprint,"reason":crashReason}	
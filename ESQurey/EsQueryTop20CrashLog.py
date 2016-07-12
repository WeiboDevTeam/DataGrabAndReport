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
		
	def getWorkbookName(self):
		return 'Top20的crash.xlsx'

	def buildQueryMustNot(self):		
		must_not=[]
		return must_not

	def buildQueryAgg(self):
		aggs={}
		if(self.fromvalues[0].endswith('5010')):
			aggs["terms"]={"size":50,"field":"jsoncontent.content"}
			aggs["aggs"]={"count_uid":{"cardinality":{"field":"jsoncontent.uid"}},"reason":{"terms":{"field":"jsoncontent.reson","size":5},"aggs": {"1": {"cardinality": {"field": "jsoncontent.uid"}},"fingerprint":{"terms":{"field":"fingerprint","size":1},"aggs":{"2":{"cardinality":{"field":"jsoncontent.uid"}}}}}}}
		else:
			aggs["terms"]={"size":50,"field":"fingerprint"}
			aggs["aggs"]={"count_uid":{"cardinality":{"field":"jsoncontent.uid"}},"reason":{"terms":{"field":"jsoncontent.reson","size":1}}}
		return aggs

	def parseAndWrite(self,result):
		json_data=json.loads(result)
		fromvalue=self.fromvalues[0]
		if json_data.get('aggregations')!=None:
			buckets= json_data['aggregations']['count_crash']['buckets']
			header=['crashlog','counts']		

			data_list={}
			for item in buckets:
				content=item.get('key')
				crash_resons=item.get('reason').get('buckets')
				if(fromvalue.endswith("5010")):
					for reson in crash_resons:
						# 判断crash的content中是否包含crash的原因
						crashReason = reson.get('key')
						if crashReason in content:
							reson_content=content
						else:
							reson_content=reson.get('key')+'\n'+content
						# 过滤dexpathlist内容，这部分对相似度计算有影响
						filter_content=self.filterCrashContent(reson_content)
						if filter_content=="No Match!":
							filter_content = reson_content
						fingerprint = ''
						inner_buckets=reson.get('fingerprint').get('buckets')
						for f in inner_buckets:
							fingerprint = f.get('key')

						self.updateMatchedList(data_list,'uid',filter_content,fingerprint,crashReason,item.get('doc_count'))
				else:
					reason = crash_resons[0].get('key')
					jsonlog = self.__queryCrashLogByFingerPrinter(fromvalue, content)
					self.updateMatchedList(data_list,'uid',jsonlog,content,reason,item.get('doc_count'))

			sortedList = self.sortDataList(data_list,len(header)-1)
			# if(fromvalue.endswith('5010')):
			jiraCreater = JiraCreateHelper.JiraCreateHelper()
			jiraCreater.createJiraIssue(sortedList)

			self.writeSortedToExcel(header,sortedList)
		else:
			print 'result: '+str(json_data)


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
			row.append(data.get('jsonlog'))
			# row.append(data.get('fingerprint'))
			row.append(data.get('counts'))
			utils.write_crash_data_with_yxis(self.worksheet,row,header,index,0)
			index += 1

	'''
	crash content过滤dexpathlist
	'''
	def filterCrashContent(self,reason):
		regexDexPathList=r'(.*)DexPathList.*]](.*)'
		matchDexpath = re.match(regexDexPathList,reason,re.S|re.M|re.I)
		if matchDexpath:
			content=matchDexpath.group(1)+'DexPathList'+matchDexpath.group(2)
			return content
		else:
			return 'No Match!'

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
			dic[content]={"counts":count}
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
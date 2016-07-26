#coding:utf-8
from EsCrashQueryParams import  EsCrashQueryParams
from EsQueryHelper import  EsQueryHelper
from ManagerUtils import InsertUtils
from EsQueryJob import EsQueryJob
import json
import time

__metaclass__=type
class EsQueryCrashUidCount(EsQueryJob):
	"""docstring for EsQueryCrashUidCount
	查询crash影响用户数"""

	def __init__(self, params):
		super(EsQueryCrashUidCount, self).__init__(params)

	def getWorkbookPath(self):
		return self.workbookPath
		
	def getWorkbookName(self):
		return 'crash影响用户统计.xlsx'

	def buildQueryMustNot(self):
		
		must_not=[]
		# must_not.append({"query":{"match":{"jsoncontent.subtype":{"query":"anr","type":"phrase"}}}})
		return must_not

	def buildQueryAgg(self):
		# date={}
		# extended_bounds={"min": self.params.getTimeFrom(),"max": self.params.getTimeTo()} 
		# date["date_histogram"]={"field": "@timestamp","interval": "1d","time_zone": "Asia/Shanghai", "min_doc_count": 1,"extended_bounds":extended_bounds}
		# date["aggs"]={"count_uid":{"cardinality":{"field":"jsoncontent.uid"}}}

		aggs={}
		aggs["terms"]={"size":7,"field":"jsoncontent.from"}
		aggs["aggs"]={"count_uid":{"cardinality":{"field":"jsoncontent.uid"}}}

		return aggs

	def parseAndWrite(self,result):
		json_data=json.loads(result)
		interval = self.params.getInterval()
		if(json_data.get('aggregations')!=None):
			buckets= json_data['aggregations']['count_crash']['buckets']
			utils = InsertUtils.InsertUtils()	
			
			header=['version']

			
			ltime=time.localtime(self.params.getTimeFrom()/1000)
			timestr=time.strftime("%Y.%m.%d",ltime)
			header.append(timestr)	
			print header
			utils.write_header(self.worksheet,0,0,header)		
			
			dictResult={}
			index = 1
			for item in buckets:
				data=[]
				# 从from值中提取版本号
				fromValue = item.get('key')
				count_uid = item.get('count_uid').get('value')
				data.append(fromValue[2:5]) 
				data.append(count_uid)
				print data
				
				utils.write_crash_data_with_yxis(self.worksheet,data,header,index,0)
				dictResult[fromValue]=count_uid
				index += 1
			self.workbook.close()
			return dictResult
		else:
			print 'result: '+str(json_data)
			return None
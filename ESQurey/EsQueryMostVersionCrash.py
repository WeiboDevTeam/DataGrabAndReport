#encoding:utf-8
import json
from EsCrashQueryParams import  EsCrashQueryParams
from EsQueryHelper import  EsQueryHelper
from Request_Performance import InsertUtils
from EsQueryJob import EsQueryJob

class EsQueryMostVersionCrash(EsQueryJob):
	"""docstring for EsQueryMostVersionCrash
	   查询最近6个版本都存在的crash
	"""
	def __init__(self, params):
		super(EsQueryMostVersionCrash, self).__init__(params)

	def getWorkbookName(self):
		return "最近6个版本都存在的crash.xlsx"

	def initFromValues(self):
		fromvalues = self.params.getFromValues()
		if(len(fromvalues) > 6):
			self.fromvalues = fromvalues[0:6]
		else:
			self.fromvalues = fromvalues

	def buildQueryAgg(self):
		aggs1={}
		aggs1["terms"]={"size":100,"field":"jsoncontent.reson","order":{"count_versions":"desc"}}

		aggs2={}
		aggs2["count_versions"]={"cardinality":{"field":"jsoncontent.from"}}
		aggs2["count_uid"]={"cardinality":{"field":"jsoncontent.uid"}}

		aggs1["aggs"]=aggs2

		return aggs1

	def parseAndWrite(self, result):
		json_data = json.loads(result)
		if json_data.get('aggregations')!=None:
			buckets= json_data['aggregations']['count_crash']['buckets']
			header=['reason','versions','uids']
			print header

			utils=InsertUtils.InsertUtils()		
			utils.write_header(self.worksheet,0,0,header)
			index = 1
			for item in buckets:
				print item
				data=[]
				data.append(item.get('key'))
				data.append(item.get('count_versions').get('value'))
				data.append(item.get('count_uid').get('value'))
				utils.write_crash_data_with_yxis(self.worksheet,data,header,index,0)
				index += 1
		else:
			print json_string
			print 'result: '+str(json_data)
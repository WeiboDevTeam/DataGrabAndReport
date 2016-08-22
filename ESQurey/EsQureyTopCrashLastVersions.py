#encoding:utf-8

import json
from EsCrashQueryParams import  EsCrashQueryParams
from EsQueryHelper import  EsQueryHelper
from ManagerUtils import InsertUtils
from EsQueryJob import EsQueryJob
__metaclass__ = type

class EsQureyTopCrashLastVersions(EsQueryJob):
	"""docstring for EsQureyTopCrashLastVersions
	查询最近几个版本top20 crash
	"""
	def __init__(self, params):
		super(EsQureyTopCrashLastVersions, self).__init__(params)

	def getWorkbookName(self):
		return "top20crash_"+('_'.join(self.fromvalues))+".xlsx"

	def initFromValues(self):
		self.fromvalues = self.params.getFromValues()[0:2]

	def buildQueryAgg(self):
		aggs1={}
		aggs1Field = 'jsoncontent.reson'
		if(self.fromvalues[0].endswith('0310')):
			aggs1Field = 'jsoncontent.content'
		aggs1["terms"]={"size":20,"field":aggs1Field}

		aggs2={}
		aggs2["terms"]={"field":'jsoncontent.from',"size": len(self.fromvalues)}
		aggs2["aggs"]={"count_uid":{"cardinality":{"field":"jsoncontent.uid"}}}

		aggs1["aggs"]={"aggs2":aggs2}
		return aggs1

	def parseAndWrite(self, result):
		json_data = json.loads(result)
		if json_data.get('aggregations')!=None:
			buckets= json_data['aggregations']['count_crash']['buckets']
			header=['reason']
			header.extend(self.fromvalues)
			print self.fromvalues

			utils=InsertUtils.InsertUtils()		
			utils.write_header(self.worksheet,0,0,header)

			index = 1
			for item in buckets:
				data=[]
				data.append(item.get('key'))
				for i in range(0,len(self.fromvalues)):
					data.append(0)
				datalist=item.get('aggs2').get('buckets')
				for temp in datalist:
					version=temp.get('key')
					for x in range(0,len(self.fromvalues)):
						if version==str(self.fromvalues[x]):
							data[x+1]=temp.get('count_uid').get('value')
							break
				utils.write_crash_data_with_yxis(self.worksheet,data,header,index,0)
				index += 1
			self.workbook.close()
		else:
			print json_string
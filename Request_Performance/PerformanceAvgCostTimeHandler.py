from Request_Performance import PerformanceRequestParams
from Request_Performance import HttpRequest
from urllib2 import URLError
from InsertUtils import InsertUtils
from Constants import Const
import json

__metaclass__=type
class PerformanceAvgCostTimeHandler(object):
	def __init__(self,filename):
		super(PerformanceAvgCostTimeHandler, self).__init__()
		self.api = "weiboMobileClientPerformance.getAvgCostTime"
		self.docid="versionCostTimeContainer"
		self.version=[]
		self.sub_business_type=[]
		self.system=''
		self.fromday=''
		self.endday=''
		self.filename=filename
		self.sheetname='AvgCostTime'

	def requestStart(self, sub_type):
		print 'fetch average cost time of %s_%s started' % (self.system,sub_type)

	def doRequest(self,workbookmanager,type):
		if type == Const.TYPE_WEEKLY_DATA:
			self.__doRequestWeeklyData(workbookmanager)
		elif type == Const.TYPE_WEEKLY_AVG_DATA:
			self.__doRequestWeeklyAvgData(workbookmanager)	

	def __doRequestWeeklyData(self,workbookmanager):
		workbook=workbookmanager.getWorkbook(self.filename)
		Max_Retry = 3
		for sub_type in self.sub_business_type:
			requestCount = 0
			netError = False
			parseError = False
			worksheet = workbookmanager.getWorksheet(workbook,sub_type['label'])
			while requestCount < Max_Retry and parseError == False:
				try:
					sub_type_value = sub_type['value']
					self.requestStart(sub_type_value)
					requestParam = PerformanceRequestParams.PerformanceRequestParams()
					requestParam.setApi(self.api)
					requestParam.setDocid(self.docid)
					requestParam.setSystemType(self.system)
					requestParam.setFromDay(self.fromday)
					requestParam.setEndDay(self.endday)
					requestParam.setSubType(sub_type_value)
					requestParam.setWeiboVersion(self.version)
					url = requestParam.getCompleteUrl()
					httpRequest = HttpRequest.HttpRequest(url)
					data = httpRequest.request();
					parsedData = self.__parseData(data, sub_type_value)
					requestCount += 1
				except URLError, e:
					netError = True
				except ValueError,e:
					parseError = True
					print "json parsed error"
				else:
					self.requestEnd(sub_type_value, parsedData)
					count=workbookmanager.getInsertCount(worksheet)
					self.__inserToExcel(workbook,worksheet,parsedData,count,sub_type['label'])
					break		
			# break			

	def __doRequestWeeklyAvgData(self,workbookmanager):
		workbook=workbookmanager.getWorkbook(self.filename)
		worksheet = workbookmanager.addWorksheet(workbook,self.sheetname)
		count_subtype=1
		Max_Retry = 3
		for sub_type in self.sub_business_type:
			requestCount = 0
			netError = False
			parseError = False
			while requestCount < Max_Retry and parseError == False:
				try:
					sub_type_value = sub_type['value']
					self.requestStart(sub_type_value)
					requestParam = PerformanceRequestParams.PerformanceRequestParams()
					requestParam.setApi(self.api)
					requestParam.setDocid(self.docid)
					requestParam.setSystemType(self.system)
					requestParam.setFromDay(self.fromday)
					requestParam.setEndDay(self.endday)
					requestParam.setSubType(sub_type_value)
					requestParam.setWeiboVersion(self.version)
					url = requestParam.getCompleteUrl()
					httpRequest = HttpRequest.HttpRequest(url)
					data = httpRequest.request();
					parsedData = self.__parseData(data, sub_type_value)
					requestCount += 1
				except URLError, e:
					netError = True
				except ValueError,e:
					parseError = True
					print "json parsed error"
				else:
					self.requestEnd(sub_type_value, parsedData)
					count=workbookmanager.getInsertCount(worksheet)
					self.__inserAvgToExcel(workbook,worksheet,parsedData,count_subtype,sub_type['label'])
					count_subtype+=1
					break		

	def requestEnd(self, sub_type, data):
		print 'fetch average cost time of %s_%s  end. the resut is: %s' % (self.system,sub_type,data)

	def __parseData(self, data, sub_type):
		result={}
		versionList=[]
		dataList=[]
		decodedData = json.loads(data,encoding="utf-8")
		code = decodedData['code']
		if code == '2000':
			lineData = decodedData['data']['lineData']
			for element in lineData:
				versionList.append(element['name'])
				dataList.append(element['data'])
			dateArr = decodedData['data']['dateArr']
			result['date']=dateArr
			result['version']=versionList
			result['data']=dataList
		else:
			print 'request sub_type error'
		return result

	# insert data sheet by sheetname
	def __inserAvgToExcel(self,workbook,worksheet,parsedData,count,subtype):
		insert_instance=InsertUtils()
		insert_instance.write_avg_data(workbook,worksheet,self.sheetname,parsedData,count,subtype)
		# insert_instance.plotAvg(workbook,worksheet,self.sheetname,count,len(self.sub_business_type),len(parsedData.get('version')),subtype)		
		return True

	# insert data sheet by subtype
	def __inserToExcel(self,workbook,worksheet,parsedData,count,subtype):
		insert_instance=InsertUtils()
		insert_instance.write_data(workbook,worksheet,subtype,parsedData,count,self.sheetname)
		insert_instance.plot(workbook,worksheet,subtype,count,len(parsedData.get('version')),len(parsedData.get('date')),self.sheetname)
		return True

#!/usr/bin/python
# -*- coding: utf-8 -*-
from ManagerUtils import WorkbookManager
from ManagerUtils import InsertUtils
from Request_Performance.Constants import Const
from datetime import timedelta, date
from Request_Performance import SLAQueryHelper
import os,sys,ConfigParser
reload(sys)
sys.setdefaultencoding('utf8')

__metaclass__=type

class SLAQuery():
	def __init__(self):
		self.dirname=os.path.abspath(os.path.dirname(sys.argv[0]))
		self.errorcodes_config={}
		self.errorcodes=[]
		self.subtypes_config={}
		self.subtypes=[]
		self.date= (date.today() - timedelta(1)).strftime('%Y%m%d')
		self.config_path=self.dirname+'/errorcode.config'
		self.workbookname='result.xlsx'

	'''
	获取输出文件夹的路径
	'''
	def getOutputPath(self,platform):
		dirname = os.path.abspath(os.path.dirname(sys.argv[0]))
		path=dirname+'/output/'+self.date +'/'+platform+'/'
		if os.path.isdir(path)==False:
			print 'create dir:' + path
			os.makedirs(path)
		return path

	def _init_config(self):
		config_read = ConfigParser.RawConfigParser()
		config_read.read(self.config_path)
		secs = config_read.sections()
		for sec in secs:
			if sec=='error_code':
				self.errorcodes = config_read.options(sec)
				for code in self.errorcodes:
					self.errorcodes_config[code]=config_read.get(sec,code)
			elif sec=='sub_type':
				self.subtypes = config_read.options(sec)
				for subtype in self.subtypes:
					self.subtypes_config[subtype]=config_read.get(sec,subtype)					

	# 选取top3的错误码以及列出错误原因
	def _parseErrorCode(self,codes):	
		reasons=[]
		if codes!= None:
			if len(codes) >=3:					
				codes=codes[0:3]
			for i in range(0,len(codes)):
				code=codes[i]
				reason=code
				if code == '0':
					continue
				if code in self.errorcodes:
					if self.errorcodes_config.get(code) != None:
						reason = str(self.errorcodes_config.get(code))+ '('+str(code)+')' 
				reason_str='top'+str((i+1))+':'+ reason
				reasons.append(reason_str)
		return reasons

	def _parseSubtype(self,sub_type):
		if sub_type in self.subtypes:
			if self.subtypes_config.get(sub_type) != None:
				sub_type = self.subtypes_config.get(sub_type)
		return sub_type

	def _startQuery(self,system):
		result_data={}
		# 初始化错误码列表
		self._init_config()
		# 获取版本,会有个默认值
		version='680'
		result=[]
		query_1 = SLAQueryHelper.SLAQueryHelper('WeiboMobileClientPerformance.getTopClientHits',system,'','refresh_feed')
		versions = query_1.doRequest(Const.QUERY_TYPE_VERSIONS)
		if versions != None:
			version = versions[0]
			print 'version:'+str(version)
		else:
			'failed to get version list'		
		result_data['version']=version

		# 获取业务列表
		query_2 = SLAQueryHelper.SLAQueryHelper('getSelectDataProvider.getWorkNames',system,'','undefined')
		subtypes = query_2.doRequest(Const.QUERY_TYPE_SUBTYPES)
		print 'subtypes:'+ str(subtypes)

		if subtypes!= None:
			for subtype in subtypes:
				data=[]
				# 获取成功率
				ratio_query = SLAQueryHelper.SLAQueryHelper('weiboMobileClientPerformance.getEveryDaySucc',system,version,subtype)
				ratio = ratio_query.doRequest(Const.QUERY_TYPE_SUCCESSRATIO)				
				# 获取错误码
				codes_query = SLAQueryHelper.SLAQueryHelper('weiboMobileClientPerformance.getTypeRatio',system,version,subtype)
				codes = codes_query.doRequest(Const.QUERY_TYPE_ERRORCODE)
				parse_codes = self._parseErrorCode(codes)

				data.append(self._parseSubtype(subtype))
				data.append(100-ratio)
				data.append(','.join(parse_codes))

				result.append(data)

			result_data['data']=sorted(result,key=lambda x:x[1],reverse=True)
		return result_data

	def _insertToExcel(self,data,platform):
		wbm=WorkbookManager.WorkbookManager()	
		workbook=wbm.getWorkbook(self.getPath(platform))
		worksheet = wbm.addWorksheet(workbook,platform)

		header=['业务名','错误率','错误原因']
		utils=InsertUtils.InsertUtils()	
		utils.write_header(worksheet,0,0,header)

		for i in range(0,len(data)):
			utils.write_crash_data_with_yxis(worksheet,data[i],header,i+1,0)

		wbm.closeWorkbooks() # must close workbook


	def doQuery(self,platform):
		print 'do query ' + platform
		result = self._startQuery(platform)
		if len(result.get('data'))>0:
			self._insertToExcel(result.get('data'),platform)
		return result.get('version')

	def getPath(self,platform):
		return self.getOutputPath(platform) + "sla_query.xlsx"

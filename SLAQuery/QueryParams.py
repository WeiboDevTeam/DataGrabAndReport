#encoding:utf-8
from Constants import Const
from datetime import timedelta, date
import urllib
__metaclass__ = type

class QueryParams():
	def __init__(self,api,systerm,version,sub_type):
		self.dayInterval= 1
		self.url = 'http://sla.weibo.cn/php/start.php'
		self.api=api
		self.type='ClientPerformance_new'
		self.fromDay = (date.today() - timedelta(self.dayInterval)).strftime('%Y%m%d')
		self.toDay = (date.today() - timedelta(1)).strftime('%Y%m%d')
		self.sub_type = sub_type
		self.systerm = systerm
		self.internal='1'
		self.particle='day'
		self.client_version=version

	def _getCommonParams(self):
		params={}
		params['api']=self.api
		params['from']=self.fromDay
		params['to']=self.toDay
		params['sub_type']=self.sub_type
		params['systerm']=self.systerm
		params['type']=self.type
		return params

	def getQueryUrl(self,query_type):
		params=self._getCommonParams()
		if query_type==Const.QUERY_TYPE_SUCCESSRATIO:
			params['internal']=self.internal
			params['particle']=self.particle
			params['client_version']=self.client_version
			params['docid']='everyDaySuccContainer'
		elif query_type==Const.QUERY_TYPE_ERRORCODE:
			params['internal']=self.internal
			params['particle']=self.particle
			params['client_version']=self.client_version
			params['docid']='errTypeTrendContainer'
		return self._getCompleteUrl(params)

	def _getCompleteUrl(self,params):
		request_params=''
		if params!=None:
			request_params=urllib.urlencode(params)
		return self.url+'?'+request_params
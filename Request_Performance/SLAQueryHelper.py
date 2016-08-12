#!/usr/bin/python
# -*- coding: utf-8 -*-
from Request_Performance import HttpRequest
from Request_Performance import QueryParams
from Request_Performance.Constants import Const
from urllib2 import URLError
import json

__metaclass__=type
class SLAQueryHelper(QueryParams.QueryParams):
	def __init__(self,api,systerm,version,sub_type):
		super(SLAQueryHelper,self).__init__(api,systerm,version,sub_type)
		self.errorcode_config={}
		self.errorcodes=[]

	def doRequest(self,query_type):
		url=self.getQueryUrl(query_type)
		Max_Retry = 3
		requestCount = 0
		netError = False
		parseError = False
		while requestCount < Max_Retry and parseError == False:
			result = None
			try:
				httpRequest = HttpRequest.HttpRequest(url)
				response = httpRequest.request();
				data = json.loads(response)
				if query_type==Const.QUERY_TYPE_VERSIONS:
					result = self._parseVersions(data)
				elif query_type==Const.QUERY_TYPE_SUBTYPES:
					result = self._parseSubtypes(data)
				elif query_type==Const.QUERY_TYPE_SUCCESSRATIO:
					result = self._parseSuccessRatio(data)
				elif query_type==Const.QUERY_TYPE_ERRORCODE:
					result = self._parseErrorCode(data)
				requestCount += 1
			except URLError, e:
				netError = True
			except ValueError,e:
				parseError = True
				print "json parsed error"
			else:
				return result
				break

	def _parseVersions(self,data):
		list_versions=[]
		code = data['code']
		if code == '2000':
			versions = data['data']['data']
			for version in versions:
				list_versions.append(version['client_version'])
			return list_versions
		else:
			print 'fetch current weibo version failed'

		return None

	def _parseSubtypes(self,data):
		sub_business_type=[]
		code = data['code']
		if code == '2000':
			subtypes = data['data']['uris']
			for subtype in subtypes:
				if subtype['value']==u"全部":
					continue 
				else:
					sub_business_type.append(subtype['value'])
			return sub_business_type
		else:
			print 'fetch all sub_business_type failed'

		return None

	def _parseSuccessRatio(self,data):
		result= None
		code = data['code']
		if code == '2000':
			lineData = data['data']['lineData']			
			if self.dayInterval==1:
				if lineData!= None:
					result = lineData[0]['data'][0]
			else:				
				dataList=[]
				for element in lineData:
					dataList.append(element['data'])
				result = dataList
		else:
			print 'request sub_type error'
		return result


	def _parseErrorCode(self,data):
		error_codes={}
		code = data['code']
		if code == '2000':
			error_codes = data['data']['names']
		return error_codes


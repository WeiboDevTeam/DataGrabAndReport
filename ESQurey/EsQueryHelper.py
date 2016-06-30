#coding:utf-8
import os,sys
import httplib
import json
from Request_Performance import WorkbookManager

__metaclass__ = type
class EsQueryHelper(object):
	"""docstring for EsQueryHelper"""
	def __init__(self):
		super(EsQueryHelper, self).__init__()

	'''
	获取输出文件夹的路径
	'''
	@staticmethod
	def getOutputPath():
		dirname = os.path.abspath(os.path.dirname(sys.argv[0]))
		path=dirname+'/output/'
		if os.path.isdir(path)==False:
		  print 'create dir:' + path
		  os.mkdir(path)
		return path

	@staticmethod
	def buildQueryString(field,datalist):
		strquery=""
		for f in range(0,len(datalist)):
		  strquery += field+":"+str(datalist[f])
		  if f < len(datalist)-1:
		    strquery += " OR "
		return strquery

	@staticmethod
	def httpPostRequest(host,port,requesturl,requestBody):
		headerdata={"Host":host}
		conn=httplib.HTTPConnection(host,port)
		json_string=json.dumps(requestBody)
		conn.request("POST",url=requesturl,body=json_string,headers=headerdata)
		response=conn.getresponse()
		res=response.read()
		return res

	@staticmethod
	def addworksheet(workbookname, worksheetname):
		path = EsQueryHelper.getOutputPath()+workbookname
		wbm = WorkbookManager.WorkbookManager()
		workbook = wbm.getWorkbook(path)
		return wbm.addWorksheet(workbook,worksheetname)
# !/usr/bin/python
import xlsxwriter

__metaclass__ = type
class WorkbookManager(object):
	"""docstring for ClassName"""
	def __init__(self):
		self.workbookList=[]
		self.worksheetList=[]

	def getWorkbook(self,filename):
		newfile=True
		for item in self.workbookList:
			if filename == item.get('name'):
				newfile = False
				workbook = item.get('workbook')
				break
		if newfile:			
			workbook=xlsxwriter.Workbook(filename)
			list_item={}
			list_item['name'] = filename
			list_item['workbook'] = workbook
			self.workbookList.append(list_item)
		return workbook

	def addWorksheet(self,workbook,sheetname):
		worksheet = workbook.add_worksheet(sheetname)
		return worksheet

	def getWorksheet(self,workbook,sheetname):
		newsheet=True
		for sheet in self.worksheetList:
			if sheetname == sheet.get('name'):
				if workbook == sheet.get('workbook'):
					newsheet=False
					worksheet=sheet.get('worksheet')
					dict_temp={'count':sheet.get('count') +1}
					sheet.update(dict_temp)
					break
		if newsheet:
			worksheet=self.addWorksheet(workbook,sheetname)
			list_item={}
			list_item['name'] = sheetname
			list_item['workbook'] = workbook
			list_item['worksheet'] = worksheet
			list_item['count'] =0
			self.worksheetList.append(list_item)
		return worksheet

	def getInsertCount(self,worksheet):
		count = 0
		for sheet in self.worksheetList:
			if worksheet == sheet.get('worksheet'):
				 count = sheet.get('count')
		print 'count:' + str(count)
		return count
	'''
	def updateInsertCount(self,worksheet):
		for sheet in self.worksheetList:
			if worksheet == sheet.get('worksheet'):
				dict_temp={'count':sheet.get('count') +1}
				sheet.update(dict_temp)
	'''
	def closeWorkbook(self,workbook):
		workbook.close()

	def closeWorkbooks(self):
		for item in self.workbookList:
			print item
			workbook=item.get('workbook')
			print workbook
			workbook.close()
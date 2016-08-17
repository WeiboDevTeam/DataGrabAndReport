#!/usr/bin/python
# -*- coding: utf-8 -*-

import xlrd
from ManagerUtils import Utils

class WriteEmail(object):

	def __init__(self):
		super(WriteEmail, self).__init__()

	# 编辑邮件正文
	def writeEmail(self,tablelist,size):
		header='<!DOCTYPE html><html><head><meta http-equiv="Content-Type" content="text/html; charset=utf-8"/></head>'
		body='<body>'
		content=self._buildMailContent(tablelist,size)
		tail='</body></html>'
		mail=header+body+content+tail
		return mail

	# 构建邮件正文内容
	def _buildMailContent(self,tablelist,size):
		content=''
		for i in range(0,len(tablelist)):
			table=tablelist[i]
			print 'key='+table.get('key')
			if table.get('key')=='crash':
				data=self._buildDailyCrashInfo(i,size,table)
			elif table.get('key')=='slaquery':
				data=self._buildSLAQueryInfo(i,size,table)
			content=content+data
		return content

	def _buildDailyCrashInfo(self,index,limit_size,dict_data):
		content=''
		table=''
		title=''
		# 表格外的标题
		header='<h4>'+str(index+1)+'.'+'Crash情况汇总（Top'+str(limit_size)+'）'+'</h4>'
		table_tag='<table border="1" cellspacing="0" cellpadding="3">'
		# 表格里的标题						
		table_title=['序号','crash次数','crash原因','jira状态','jira分配人','jira地址']
		for i in range(0,len(table_title)):
			title=title+'<th>'+table_title[i]+'</th>'
		# 表格里的数据
		data_list=dict_data.get('data')
		if(len(data_list)>limit_size):
			size=limit_size
		else:
			size=len(data_list)
		for i in range(0,size):
			td_num='<td>'+str(i+1)+'</td>'
			data=data_list[i]
			counts=data.get('counts')
			td_counts='<td>'+str(counts)+'</td>'
			td_reason='<td>'+data.get('reason')+'</td>'
			jira_status=data.get('jira_status')
			if jira_status!=None:				
				td_jira_status='<td>'+jira_status+'</td>'
			else:
				td_jira_status='<td>None</td>'
			jira_assignee=data.get('jira_assignee')
			if jira_assignee!=None:				
				td_jira_assignee='<td>'+jira_assignee+'</td>'
			else:
				td_jira_assignee='<td>None</td>' 
			jira_id=data.get('jira_id')
			if jira_id!=None:
				jira_link=Utils.generateJiraLink(jira_id)
				td_jira_id='<td><a href='+jira_link+'>'+jira_id+'</a></td>'
			else:
				td_jira_id='<td>None</td>'		
			td=td_num+td_counts+td_reason+td_jira_status+td_jira_assignee+td_jira_id
			if counts>10000:
				tr='<tr style="color:red;">'+td+'</tr>'
			else:
				tr='<tr>'+td+'</tr>'
			tr=tr.encode('utf-8')
			table=table+tr
		content=header+table_tag+self._getTableTitle(title)+table+'</table>'
		return content

	def _buildSLAQueryInfo(self,index,limit_size,dict_data):
		content=''
		table=''
		title=''
		# 表格外的标题
		header='<h4>'+str(index+1)+'.'+'各业务错误情况（Top'+str(limit_size)+'）'+'</h4>'
		table_tag='<table border="1" cellspacing="0" cellpadding="3">'
		# 表格里的标题						
		table_title=['序号','业务名','错误率','错误原因']
		for i in range(0,len(table_title)):
			title=title+'<th>'+table_title[i]+'</th>'
		# 表格里的数据
		data_list=dict_data.get('data')
		if(len(data_list)>limit_size):
			size=limit_size
		else:
			size=len(data_list)
		for i in range(0,size):
			td_num='<td>'+str(i+1)+'</td>'
			data=data_list[i]			
			td_subtype='<td>'+data.get('subtype')+'</td>'
			ratio=data.get('ratio')
			td_ratio='<td>'+str(ratio)+'</td>'
			td_reason='<td>'+data.get('errorcodes')+'</td>'				
			td=td_num+td_subtype+td_ratio+td_reason
			if ratio>10:
				tr='<tr style="color:red;">'+td+'</tr>'
			else:
				tr='<tr>'+td+'</tr>'
			tr=tr.encode('utf-8')
			table=table+tr
		content=header+table_tag+self._getTableTitle(title)+table+'</table>'
		return content
		
	# 获取表格标题
	def _getTableTitle(self,title):
		tr_start='<tr bgcolor="#F79646" align="left" >'
		tr_end='</tr>'
		return tr_start+title+tr_end

	# 读取文件里的数据，并提取前num个数据构建邮件内容
	def _buildTableContent(self,filepath,sheet,num,needsort):
		data=self.readData(filepath,sheet,needsort)
		content=''
		if(len(data)>num):
			number=num
		else:
			number=len(data)
		for i in range(0,number):
			td='<td>'+str(i+1)+'</td>'
			for j in range(len(data[i])):
				cellData=data[i][j]
				try:
					tip='<td>'+cellData+'</td>'
				except:
					print cellData
					tip='<td>'+str(cellData)+'</td>'
				td=td+tip
			tr='<tr>'+td+'</tr>'
			tr=tr.encode('utf-8')
			content=content+tr
		return content

	# 读取excel并对内容，并根据需要进行排序，通常根据表格的最后一列排序
	def _readData(self,filepath,sheet,needsort):
		book=xlrd.open_workbook(filepath)
		table=book.sheet_by_index(sheet)
		data=[]
		ncols=table.ncols
		for i in range(1,table.nrows):
			row=[]
			for j in range(0,ncols):
				# 解决excel中保存的int值在读取时会自动转为float格式的问题
				# ctype :0 empty,1 string, 2 number, 3 date, 4 boolean, 5 error
				if (table.cell(i,j).ctype==2 and int(table.cell(i,j).value)/1.0==table.cell(i,j).value):
					row.append(int(table.cell(i,j).value))
				else:
					row.append(table.cell(i,j).value)
			data.append(row)
		if needsort==True:
			data=sorted(data,key=lambda x:x[ncols-1],reverse=True)
		return data

#!/usr/bin/python
# -*- coding: utf-8 -*-

import xlrd,os,sys,time,smtplib,email
from email import encoders
from email.mime.text import MIMEText
from email.header import Header
import base64
import WriteEmail

class WriteEmail(object):

	# 编辑邮件正文
	def getMailContent(self,tablelist):
		header='<!DOCTYPE html><html><head><meta http-equiv="Content-Type" content="text/html; charset=utf-8"/></head>'
		body='<body>'
		content=self.buildMailContent(tablelist)
		tail='</body></html>'
		mail=header+body+content+tail
		return mail

	# 构建邮件正文内容
	def buildMailContent(self,tablelist):
		count=1
		content=''
		for table in tablelist:
			# 表格外的标题
			header='<h4>'+str(count)+'.'+table.get('theme')+'</h4>'
			table_tag='<table border="1" cellspacing="0" cellpadding="3">'			
			# 表格里的标题
			table_title=self.getTableTitle(table.get('title'))
			# 表格里的数据
			data=self.buildTableContent(table.get('filepath'),table.get('sheet'))
			content=content+header+table_tag+table_title+data+'</table>'
			count=count+1
		return content

		
	# 获取表格标题
	def getTableTitle(self,title):
		tr_start='<tr bgcolor="#F79646" align="left" >'
		tr_end='</tr>'
		return tr_start+title+tr_end

	# 不排序直接构建表格内容
	def readData(self,filepath):
		print filepath
		content=''
		book=xlrd.open_workbook(filepath)
		sheet=book.sheet_by_index(0)
		nrows=sheet.nrows
		ncols=sheet.ncols
		for i in range(0,nrows):
			td=''
			for j in range(ncols):
				cellData=sheet.cell_value(i,j)				
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

	# 根据排序后的内容选取Top20的数据构建表格内容
	def buildTableContent(self,filepath,sheet):
		data=self.readAndSortData(filepath,sheet)
		content=''
		if(len(data)>20):
			number=20
		else:
			number=len(data)
		for i in range(0,number):
			td=''
			for j in range(len(data[i])):
				cellData=data[i][j]
				tip='<td>'+str(cellData)+'</td>'
				td=td+tip
			tr='<tr>'+td+'</tr>'
			tr=tr.encode('utf-8')
			content=content+tr
		return content

	# 读取excel并对内容进行排序，通常根据表格的最后一列排序
	def readAndSortData(self,filepath,sheet):
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
		data=sorted(data,key=lambda x:x[ncols-1],reverse=True)
		return data

	# 发送邮件
	def mailSend(self,mail):
		# 设置发件人
		sender = 'xiaofei9@staff.weibo.com'
		# 设置接收人
		receiver='xiaofei9@staff.weibo.com'
		# 设置邮件主题
		subject='测试邮件，请忽略！'
		#设置发件服务器，即smtp服务器
		smtpserver='mail.staff.sina.com.cn'
		# 配置端口
		smtpport=25
		#设置登陆名称
		username='xiaofei9'
		#设置登陆密码
		password='Wazm20160606'
		#实例化写邮件到正文区，邮件正文区需要以HTML文档形式写入
		msg= MIMEText(mail,'html','utf-8')
		#输入主题
		msg['Subject']= subject
		#调用邮件发送方法，需配合导入邮件相关模块
		smtp = smtplib.SMTP(smtpserver,smtpport)
		#输入用户名，密码，登陆服务器
		print smtp.login(username, password)
		#
		#发送邮件
		smtp.sendmail(sender, receiver, msg.as_string())
		#退出登陆并关闭与发件服务器的连接
		smtp.quit()

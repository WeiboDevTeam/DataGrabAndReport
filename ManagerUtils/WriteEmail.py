#!/usr/bin/python
# -*- coding: utf-8 -*-

import xlrd,os,sys,time,smtplib,email
from email import encoders
from email.mime.text import MIMEText
from email.header import Header
from email.utils import COMMASPACE
import base64
import ConfigParser

class WriteEmail(object):

	def __init__(self):
		super(WriteEmail, self).__init__()
		self.init_config()
		

	def init_config(self):
		config_read = ConfigParser.RawConfigParser()
		config_read.read('./account.config')
		secs = config_read.sections()
		for sec in secs:
			if sec == u'mail_config':
				options = config_read.options(sec)
				self.email_config = {}
				for key in options:
					self.email_config[key]=config_read.get(sec,key)

	# 编辑邮件正文
	def getMailContent(self,tablelist,num):
		header='<!DOCTYPE html><html><head><meta http-equiv="Content-Type" content="text/html; charset=utf-8"/></head>'
		body='<body>'
		content=self.buildMailContent(tablelist,num)
		tail='</body></html>'
		mail=header+body+content+tail
		return mail

	# 构建邮件正文内容
	def buildMailContent(self,tablelist,num):
		count=1
		content=''
		for table in tablelist:
			# 表格外的标题
			header='<h4>'+str(count)+'.'+table.get('theme')+'</h4>'
			table_tag='<table border="1" cellspacing="0" cellpadding="3">'
			# 表格里的标题
			title=''						
			table_title=table.get('title')
			for i in range(0,len(table_title)):
				title=title+'<th>'+table_title[i]+'</th>'
			# 表格里的数据
			data=self.buildTableContent(table.get('filepath'),table.get('sheet'),num)
			content=content+header+table_tag+self.getTableTitle(title)+data+'</table>'
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
			td='<td>'+str(i+1)+'</td>'
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
	def buildTableContent(self,filepath,sheet,num):
		data=self.readAndSortData(filepath,sheet)
		content=''
		if(len(data)>num):
			number=num
		else:
			number=len(data)
		for i in range(0,number):
			td='<td>'+str(i+1)+'</td>'
			for j in range(len(data[i])):
				cellData=data[i][j]
				if isinstance(cellData,int):
					tip='<td>'+str(cellData)+'</td>'
				else:
					tip='<td>'+cellData+'</td>'
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
	def mailSend(self,mail,platform):
		# 设置发件人
		sender = self.email_config.get('mail_sender')
		if sender == None:
			print 'mail_sender is null'
			return

		# 设置接收人
		if(platform == u'Android'):
			receiver = self.email_config.get('mail_android_receiver').split(',')
			# receiver = [testReceiver]
		else:
			receiver = self.email_config.get('mail_ios_receiver').split(',')
			# receiver = ['guizhong@staff.weibo.com']
		if receiver == None:
			print 'mail_receiver is null'
			return

		# 设置邮件主题
		subject=platform+'每日crash反馈'
		#设置发件服务器，即smtp服务器
		smtpserver=self.email_config.get('mail_smtpserver')
		# 配置端口
		smtpport=self.email_config.get('mail_smtpport')
		if(smtpserver == None or smtpport == None):
			print 'smtpserver or smtpport is null'
			return

		#设置登陆名称
		username=self.email_config.get('mail_username')
		#设置登陆密码
		password=self.email_config.get('mail_pwd')
		if(username == None or password == None):
			print 'username or password is null'
			return

		#实例化写邮件到正文区，邮件正文区需要以HTML文档形式写入
		msg= MIMEText(mail,'html','utf-8')
		#输入主题
		msg['Subject']= subject
		msg['From']= username
		msg['To']= COMMASPACE.join(receiver)
		#调用邮件发送方法，需配合导入邮件相关模块
		smtp = smtplib.SMTP(smtpserver,smtpport)
		#输入用户名，密码，登陆服务器
		print smtp.login(username, password)
		#
		#发送邮件
		smtp.sendmail(sender, receiver, msg.as_string())
		#退出登陆并关闭与发件服务器的连接
		smtp.quit()

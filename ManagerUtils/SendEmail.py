#!/usr/bin/python
# -*- coding: utf-8 -*-
import smtplib,email
from email import encoders
from email.mime.text import MIMEText
from email.header import Header
from email.utils import COMMASPACE
from ManagerUtils import Utils
import base64
import ConfigParser

class SendEmail(object):

	def __init__(self):
		super(SendEmail, self).__init__()
		self.init_config()

	def init_config(self):
		config_read = ConfigParser.RawConfigParser()
		config_read.read(Utils.getConfigFolder()+'account.config')
		secs = config_read.sections()
		for sec in secs:
			if sec == u'mail_config':
				options = config_read.options(sec)
				self.email_config = {}
				for key in options:
					self.email_config[key]=config_read.get(sec,key)

	# 发送邮件
	def sendEmail(self,mail,platform):
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

#!/usr/bin/python
# -*- coding: utf-8 -*-
import os,sys
reload(sys)
sys.setdefaultencoding('utf8')

'''
获取输出文件夹的路径
'''
def getOutputPath(date,platform):
	dirname = os.path.abspath(os.path.dirname(sys.argv[0]))
	path=dirname+'/output/'+date +'/'+platform+'/'
	if os.path.isdir(path)==False:
		print 'create dir:' + path
		os.makedirs(path)
	return path

def getConfigFolder():
	dirname = os.path.abspath(os.path.dirname(sys.argv[0]))
	path=dirname+'/Config/'
	return path

def generateJiraLink(jira_id):
	return "http://issue.internal.sina.com.cn/browse/"+jira_id
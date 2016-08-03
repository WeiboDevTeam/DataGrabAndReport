#encoding=utf-8
from AnalysizeDailyCrash import CalculateDailyCrash
import sys,os
import xlsxwriter
import ConfigParser

def __handleAfterCal(resultDict):
	if resultDict!=None:
		ratioDict = {}
		keys = resultDict.keys()
		for key in keys:
			resultItem = resultDict.get(key)
			ratioData = resultItem.pop('data')
			component = resultItem.get('component')

			if(component != None and component != u'None'):
				key = component
			if(ratioDict.has_key(key)):
				print ratioData
				for dateKey in ratioDict.get(key).keys():
					#同一天的数据相加，但是总数不相加
					data = []
					value = ratioDict.get(key)
					tmpData = value.get(dateKey)
					crashUidNumData = ratioData.get(dateKey)
					if(crashUidNumData != None and crashUidNumData != u'None'):
						crashUidNum = int(crashUidNumData[0])
					else:
						crashUidNum = 0
					if(tmpData != None and tmpData != u'None'):
						tmpCrashUidNum = int(tmpData[0])
					else:
						tmpCrashUidNum = 0
					sumNum = tmpCrashUidNum+crashUidNum
					data.append(str(sumNum))

					if(crashUidNumData != None and crashUidNumData != u'None'):
						data.append(crashUidNumData[1])
					elif(tmpData != None and tmpData != u'None'):
						data.append(tmpData[1])
					
					value[dateKey]=tuple(data)
			else:
				ratioDict[key]=ratioData
		return ratioDict
	else:
		return None

#data的数据结构{"fingerprint":['7.27':(count,total_count)]}
def __writeRatioData(data,worksheet,rowStart,columnStart):
	keys = data.keys()
	dateIndexs = data.get(keys[0]).keys()
	columns=len(dateIndexs)+1#加上第一列的id
	rows = len(keys)
	worksheet.set_column(0,0,35) #设定第一列的宽度为35，id比较长
	worksheet.set_column(1,columns,15)
	worksheet.write(0,columns/2,'crash percentage of top rank')
	header=[]
	header.append({'header':'component'})
	for key in dateIndexs:
		header.append({'header':key})
	worksheet.add_table(rowStart,columnStart,rows,columns-1,{'columns':header})

	startRow = 2
	startColumn=0
	worksheet.write_column(startRow,startColumn,keys)   #第3行第一列
	for key in keys:
		values = data.get(key).values()
		for value in values:
			startColumn += 1
			format = workbook.add_format()
			format.set_num_format('0.0000')
			if value == None:
				worksheet.write(startRow,startColumn,0,format)
				continue
			count = int(value[0])
			totalCount = int(value[1])
			formula = '=%d/(%d+(0.0))' % (count,totalCount)
			worksheet.write_formula(startRow,startColumn,formula,format)
		startColumn = 0
		startRow += 1
	return (rows,columns)

#data的数据结构{"fingerprint":{'jsonlog':'','jia_id':'',.....}}
def __writeCrahLogData(data,worksheet,rowStart,columnStart):
	values = data.values()
	keys = data.keys()
	columnIndexs = data.get(keys[0]).keys()
	columns = len(columnIndexs)
	rows = len(keys)+1
	header=[]
	for key in columnIndexs:
		header.append({'header':key})
	worksheet.write(0,columns/2,'crash detail of top rank')
	worksheet.add_table(rowStart,columnStart,rows+rowStart,columns-1,{'columns':header})
	for value in values:
		rowStart += 1
		rowdata = value.values()
		worksheet.write_row(rowStart,0,rowdata)

def __closeWorkbook(workbook):
	workbook.close()


platforms=['android','iphone']
version = sys.argv[1]
#正则匹配from值的合法性
for platform in platforms:
	targetDir = CalculateDailyCrash.getOutputPath(platform) + os.sep + version
	if os.path.isdir(targetDir)==False:
		print "file %s does't exists,please input correct fromvalue!" % targetDir
	else:
		calculate = CalculateDailyCrash.CalculateDailyCrash(targetDir)
		result = calculate.calculate()
		ratioData = __handleAfterCal(result)
		if(ratioData!=None):
			try:
				workbook = xlsxwriter.Workbook(targetDir+ os.sep+'result.xlsx')
				worksheet = workbook.add_worksheet('crash_ratio')
				rowStart = 1
				columnStart = 0
				table = __writeRatioData(ratioData,worksheet,rowStart,columnStart)
				tableRows = table[0]
				tableColumns = table[1]-1

				#insert chart
				gapRows = 15
				gapColumns = 5  
				startRow = 2    #数据起始行
				categoryRow = 1  #类别所在的行
				chartNum = 0
				chartPositionIndexX = tableRows+5
				chartPositionIndexY = 0
				for i in range(0,tableRows):

					if(i%3==0):
						chartNum += 1
						chart = workbook.add_chart({'type':'line'})
						chart.add_series({'name':[worksheet.get_name(),startRow+i,0],
											'values':[worksheet.get_name(),startRow+i,1,startRow+i,tableColumns],
											'categories':[worksheet.get_name(),categoryRow,1,categoryRow,tableColumns],
											'marker': {'type': 'automatic'},
											'data_labels': {'value': True,'position': 'above'}})
						chart.set_x_axis({'label_position': 'high','name': 'Date'})
						chart.set_y_axis({'name': 'Crash Percentage'})
						worksheet.insert_chart(chartPositionIndexX,chartPositionIndexY,chart)
						if(chartNum%2 == 0):
							chartPositionIndexX += gapRows
							chartPositionIndexY = 0
						else:
							chartPositionIndexY += gapColumns
					else:
						chart.add_series({'values':[worksheet.get_name(),startRow+i,1,startRow+i,tableColumns],
							'name':[worksheet.get_name(),startRow+i,0],
							'marker': {'type': 'automatic'},
							'data_labels': {'value': True},'position': 'below'})


				worksheet1 = workbook.add_worksheet('crash_info')
				__writeCrahLogData(result,worksheet1,rowStart,columnStart)
			except Exception, e:
				print e
			
			finally:
				__closeWorkbook(workbook)
			
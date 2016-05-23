
# !/usr/bin/python
# encoding:utf-8

import urllib2
import json
import xlsxwriter
import xlrd

class InsertUtils(object):
    """docstring for WriteUtils"""
    def __init__(self,filename):
        self.hasHeader=False
        self.filename=filename

    # write data to excel file and plot line
    def write_data(self,workbook,worksheet,sheetname,data,count,subtype):
        Bold = workbook.add_format({'bold': 1}) 
        # write table header
        if self.hasHeader:
            pass
        else:
            header=['subtype','version']
            # header append date
            header.extend(data.get('date'))
            worksheet.write_row(0,0,header,Bold)       
            self.hasHeader=True
        # write version and data
        versions=data.get('version')
        if len(versions) == 0:
            return
        worksheet.write(count*16+1,0,subtype,Bold)
        rows=data.get('data')
        for x in range(0,len(versions)):
            worksheet.write(count*16+1+x,1,versions[x],Bold)
            worksheet.write_row(count*16+1+x,2,rows[x])
        print 'write ' + subtype + ' done!'

    # write data to excel file and plot line
    def write_avg_data(self,workbook,worksheet,sheetname,data,count,subtype):
        Bold = workbook.add_format({'bold': 1}) 
        # write table header
        if self.hasHeader:
            pass
        else:
            header=['subtype']
            # header append date
            header.extend(data.get('version'))
            worksheet.write_row(0,0,header,Bold)       
            self.hasHeader=True
        # write version and data
        datas=data.get('data')
        if len(datas) == 0:
            return       
        worksheet.write(count,0,subtype,Bold)
        for x in range(0,len(datas)):
            row_data=datas[x]
            result=0.0
            add_count=0
            for e in row_data:
                if e != None:
                    result +=float(e)
                    add_count+=1
            if add_count!=0:
                worksheet.write(count,1+x,result/add_count,Bold)
        print 'write ' + subtype + ' done!'

    # add series
    def plot(self,workbook,worksheet,sheetname,count,x_num,y_num,subtype):
        try:
            if x_num<=1:
                return
            if y_num<=1:
                return
            print count
            if count==0:
                plottype='line'
            elif count==1:
                plottype='column'
            else:
                plottype='scatter'

            print plottype
            chart = workbook.add_chart({'type': plottype})
            for x in range(0,x_num):
                chart.add_series({
                    'name':       [sheetname, count*16+1+x,1],
                    'categories': [sheetname, 0,2,0,1+y_num],
                    'values':     [sheetname, count*16+1+x,2,count*16+1+x,1+y_num],
                })
            # Add a chart title and some axis labels.
            chart.set_title ({'name': subtype})
            chart.set_x_axis({'name': 'Date'})
            chart.set_y_axis({'name': 'Value'})

            # Set an Excel chart style.
            chart.set_style(11)
            chart.set_table()
            # Insert the chart into the worksheet (with an offset).
            worksheet.insert_chart(count*16+1,9, chart, {'x_offset': 25, 'y_offset': 10})
            print 'plot ' + subtype + ' done!'
        except Exception, e:
            raise e
        finally:
            return

    # add series
    def plotAvg(self,workbook,worksheet,sheetname,count,x_num,y_num,subtype):
        try:
            if count<x_num:
                return
            if x_num<=1:
                return
            if y_num<=1:
                return

            plottype='line'

            print plottype
            chart = workbook.add_chart({'type': plottype})
            for x in range(0,x_num):
                chart.add_series({
                    'name':       [sheetname, x+1,0],
                    'categories': [sheetname, 0,1,0,y_num],
                    'values':     [sheetname, x+1,1,x+1,y_num],
                })
            # Add a chart title and some axis labels.
            chart.set_title ({'name': subtype})
            chart.set_x_axis({'name': 'Date'})
            chart.set_y_axis({'name': 'Value'})

            # Set an Excel chart style.
            chart.set_style(11)
            chart.set_table()
            # Insert the chart into the worksheet (with an offset).
            worksheet.insert_chart(1,9, chart, {'x_offset': 25, 'y_offset': 10})
            print 'plot ' + subtype + ' done!'
        except Exception, e:
            raise e
        finally:
            return

    def combineChart(self,chart1,chart2):
        return chart1.combine(chart2)

    '''
    def getRowNumber(self,sheetname):
        try:
            data=xlrd.open_workbook(self.filename)
            table=data.sheet_by_name(sheetname)
            print table.nrows
            return table.nrows
        except Exception, e:
            print str(e)
            return 1
    ''' 

    def copyData(self,filename,sheetname,worksheet):
        try:
            data=xlrd.open_workbook(filename)
            table=data.sheet_by_name(sheetname)
            nrows=table.nrows
            print table.row_values(0)
            print nrows
            for x in range(0,nrows):
                print table.row_values(x)
                worksheet.write_row(x,0,table.row_values(x))
        except Exception, e:
            print str(e)  
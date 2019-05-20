# -*- coding: utf-8 -*-
import requests
import re
import math
import uuid
import json
from datetime import datetime
from dateutil.rrule import rrule, DAILY
import pandas as pd
from bs4 import BeautifulSoup

class rosterParser():
    def __init__(self, username, password, startDate, endDate, outFile):
        self.username = username
        self.password = password

        self.startDate = self.format2DightTimeStr(startDate.day)
        self.endDate = self.format2DightTimeStr(endDate.day)
        self.startMonth = self.format2DightTimeStr(startDate.month)
        self.endMonth = self.format2DightTimeStr(endDate.month)
        self.startYear = self.format2DightTimeStr(startDate.year)
        self.endYear = self.format2DightTimeStr(endDate.year)

        self.outFile = outFile

        self.loginUrl = "http://tpeweb02.china-airlines.com/cia/LoginHandler"
        self.rosterUrl = "http://tpeweb02.china-airlines.com/cia/cia_inq_view_rostreport.jsp?" + \
                            "strDay=" + self.startDate + "&strMonth=" + self.startMonth + "&strYear=" + self.startYear + \
                            "&endDay=" + self.endDate + "&endMonth=" + self.endMonth + "&endYear=" + self.endYear + \
                            "&staffNum=" + self.username + "&display_timezone=Port+Local&B1=Query"

    def sendRosterRequest(self):
        # Request session
        rs = requests.session()

        # Login data
        data = {
            'userid': self.username,
            'password': self.password,
            'queryType': 'Login'
        }

        # Login
        res = rs.post(self.loginUrl, data = data)

        if not res.ok:
            print("Post request fail!")
            return

        # Get roster page contents
        return rs.get(self.rosterUrl)

    def parseRosterResonpse(self, rosterQueryResult):
        # Get items
        soup = BeautifulSoup(rosterQueryResult.text, "lxml")
        return soup.findAll('td')

    def processRosterData(self, rosterData):
        # Process roster contents and stores into a dataframe
        dataColumns = ['Date', 'Pattern', 'Duty', 'COP Duty', 'Flight Number', 'Fleet' ,'SignIn', 'ETD', 'Sector', 'ETA', 'Duration', 'Remarks']
        rosterFrame = pd.DataFrame(columns=dataColumns)

        i = 0
        colSize = len(dataColumns)

        for line in rosterData:
            line = re.sub('<.*?>', '', line.text)
            rosterRecord = line.split()

            rawIndex, colIndex = math.floor(i/colSize), i%colSize

            if i == 0 and rosterRecord == []:
                continue
            elif len(rosterRecord) > 0 and rosterRecord[0] == 'Date':
                break
            elif len(rosterRecord) > 0:
                rosterFrame.at[rawIndex, dataColumns[colIndex]] = rosterRecord[0]

            i+=1

        return rosterFrame

    def transformRosterData(self, rosterFrame):
        rosterColumns = ['Subject', 'Start Date', 'Start Time', 'End Date', 'End Time', 'All Day Event', 'Description']
        excelFrame = pd.DataFrame(columns=rosterColumns)

        rawIndex = 0

        for index, row in rosterFrame.iterrows():
            #print(index)
            if not pd.isnull(row['Date']):
                currDate = self.formatDate(row['Date'])

                if row['Duty'] == 'FLY':
                    if pd.isnull(row['SignIn']):
                        if row['Sector'][3:6] != 'TPE':
                            continue
                        else:
                            excelFrame.at[rawIndex, 'End Date']      = self.formatDate(row['Date'])
                            excelFrame.at[rawIndex, 'End Time']      = self.formatTime(row['ETA'])
                            excelFrame.at[rawIndex, 'All Day Event'] = ''
                            rawIndex += 1
                    elif row['SignIn'][0:2] == '23': #sign in time over 23:00
                        excelFrame.at[rawIndex, 'End Date']      = self.formatDate(row['Date'])
                        excelFrame.at[rawIndex, 'End Time']      = self.formatTime(row['ETA'])
                        excelFrame.at[rawIndex, 'All Day Event'] = ''
                    else:
                        excelFrame.at[rawIndex, 'Start Date']    = self.formatDate(row['Date'])
                        excelFrame.at[rawIndex, 'Start Time']    = self.formatTime(row['SignIn'])
                        excelFrame.at[rawIndex, 'Subject']       = row['Flight Number']
                        excelFrame.at[rawIndex, 'Description']   = row['Sector']
                elif row['Duty'][0] == 'S':
                    excelFrame.at[rawIndex, 'Start Date']    = self.formatDate(row['Date'])
                    excelFrame.at[rawIndex, 'Subject']       = row['Duty']
                    excelFrame.at[rawIndex, 'Start Time']    = self.formatTime(row['SignIn'])
                    excelFrame.at[rawIndex, 'End Date']      = self.formatDate(row['Date'])
                    excelFrame.at[rawIndex, 'End Time']      = self.formatTime(row['ETA'])
                    excelFrame.at[rawIndex, 'All Day Event'] = ''
                    excelFrame.at[rawIndex, 'Description']   = row['Duty']
                    rawIndex += 1
                elif row['Duty'] == 'ADO' or row['Duty'] == 'RDO':
                    excelFrame.at[rawIndex, 'Start Date']    = self.formatDate(row['Date'])
                    excelFrame.at[rawIndex, 'Subject']       = row['Duty']
                    excelFrame.at[rawIndex, 'Start Time']    = ''
                    excelFrame.at[rawIndex, 'End Date']      = self.formatDate(row['Date'])
                    excelFrame.at[rawIndex, 'End Time']      = ''
                    excelFrame.at[rawIndex, 'All Day Event'] = 'TRUE'
                    excelFrame.at[rawIndex, 'Description']   = row['Duty']
                    rawIndex += 1
                elif row['Duty'] == 'AL':
                    excelFrame.at[rawIndex, 'Start Date']    = self.formatDate(row['Date'])
                    excelFrame.at[rawIndex, 'Subject']       = row['Duty']
                    excelFrame.at[rawIndex, 'Start Time']    = ''
                    excelFrame.at[rawIndex, 'End Date']      = self.formatDate(row['Date'])
                    excelFrame.at[rawIndex, 'End Time']      = ''
                    excelFrame.at[rawIndex, 'All Day Event'] = 'TRUE'
                    excelFrame.at[rawIndex, 'Description']   = row['Duty']
                    rawIndex += 1
                elif row['Duty'] == 'TVL':
                    excelFrame.at[rawIndex, 'Start Date']    = self.formatDate(row['Date'])
                    excelFrame.at[rawIndex, 'Start Time']    = self.formatTime(row['SignIn'])
                    excelFrame.at[rawIndex, 'Subject']       = row['Flight Number']
                    excelFrame.at[rawIndex, 'All Day Event'] = ''
                    excelFrame.at[rawIndex, 'Description']   = row['Sector']
                elif row['Duty'][0] == 'R':
                    excelFrame.at[rawIndex, 'Start Date']    = self.formatDate(row['Date'])
                    excelFrame.at[rawIndex, 'Subject']       = row['Duty']
                    excelFrame.at[rawIndex, 'Start Time']    = self.formatTime(row['SignIn'])
                    excelFrame.at[rawIndex, 'End Date']      = currDate
                    excelFrame.at[rawIndex, 'End Time']      = self.formatTime(row['ETA'])
                    excelFrame.at[rawIndex, 'All Day Event'] = ''
                    excelFrame.at[rawIndex, 'Description']   = row['Duty']
                    rawIndex += 1
                elif row['Duty'] == 'LO':
                    continue
                else:
                    continue

            else:
                if row['Duty'] == 'LO':
                    continue
                elif row['Duty'] == 'TVL':
                    excelFrame.at[rawIndex, 'End Date']      = currDate
                    excelFrame.at[rawIndex, 'End Time']      = self.formatTime(row['ETA'])
                    excelFrame.at[rawIndex, 'All Day Event'] = 'TRUE'
                    rawIndex += 1
                elif row['Duty'][0] == 'R':
                    excelFrame.at[rawIndex, 'Start Date']    = currDate
                    excelFrame.at[rawIndex, 'Subject']       = row['Duty']
                    excelFrame.at[rawIndex, 'Start Time']    = self.formatTime(row['SignIn'])
                    excelFrame.at[rawIndex, 'End Date']      = currDate
                    excelFrame.at[rawIndex, 'End Time']      = self.formatTime(row['ETA'])
                    excelFrame.at[rawIndex, 'All Day Event'] = ''
                    excelFrame.at[rawIndex, 'Description']   = row['Duty']
                    rawIndex += 1
                elif row['ETA'] == '2359':
                    continue
                elif (row['Sector'][3:6] != 'TPE') and (row['Sector'][3:6] != 'TSA'):
                    continue
                elif not pd.isnull(row['SignIn']):
                    excelFrame.at[rawIndex, 'End Date']      = currDate
                    excelFrame.at[rawIndex, 'End Time']      = self.formatTime(row['ETA'])
                    excelFrame.at[rawIndex, 'All Day Event'] = ''
                    rawIndex += 1
                else:
                    excelFrame.at[rawIndex, 'End Date']      = currDate
                    excelFrame.at[rawIndex, 'End Time']      = self.formatTime(row['ETA'])
                    excelFrame.at[rawIndex, 'All Day Event'] = ''
                    rawIndex += 1

        dutyDateSet = set()

        firstDateStr = self.startDate + self.startMonth + self.startYear
        LastDateStr = self.endDate + self.endMonth + self.endYear
        firstDate = datetime.strptime(firstDateStr, '%d%m%Y').date()
        LastDate = datetime.strptime(LastDateStr, '%d%m%Y').date()
        startDate = None
        endDate = None

        # Add 'OFF' events in empty days
        for index, row in excelFrame.iterrows():
            try:
                startDate = datetime.strptime(row['Start Date'], '%d/%m/%Y').date()
                endDate = datetime.strptime(row['End Date'], '%d/%m/%Y').date()
            except TypeError as e:
                print(e)
                if not startDate:
                    startDate = firstDate
                if not endDate:
                    endDate = LastDate

            for singleDate in rrule(DAILY, dtstart=startDate, until=endDate):
                dutyDateSet.add(singleDate)

        startDate = datetime.strptime(firstDateStr, '%d%m%Y').date()
        endDate = datetime.strptime(LastDateStr, '%d%m%Y').date()

        for singleDate in rrule(DAILY, dtstart=startDate, until=endDate):
            if singleDate not in dutyDateSet:
                excelFrame.at[rawIndex, 'Subject']       = 'OFF'
                excelFrame.at[rawIndex, 'Start Date']    = singleDate.strftime('%d/%m/%Y')
                excelFrame.at[rawIndex, 'Start Time']    = ''
                excelFrame.at[rawIndex, 'End Date']      = singleDate.strftime('%d/%m/%Y')
                excelFrame.at[rawIndex, 'End Time']      = ''
                excelFrame.at[rawIndex, 'All Day Event'] = 'TRUE'
                excelFrame.at[rawIndex, 'Description']   = 'OFF'
                rawIndex += 1

        excelFrame.dropna(inplace = True)
        return excelFrame

    def saveToFile(self, excelFrame, rosterList):
        excelFrame.to_csv(self.outFile + '.csv', index=False)
        with open(self.outFile + '.json', 'w') as outfile:
            json.dump(rosterList, outfile)

    def convertToJson(self, excelFrame):
        rosterList = []

        for index, row in excelFrame.iterrows():
            iCalUID = 'originalUID_' + str(uuid.uuid4())

            if (row['Subject'] == 'ADO') or (row['Subject'] == 'OFF') or (row['Subject'] == 'AL') or (row['Subject'] == 'RDO'):
                rosterList.append({
                    'summary': row['Subject'],
                    'start': {
                        'date': self.formatJsonDate(row['Start Date']),
                        'timeZone': 'Asia/Taipei'
                    },
                    'end': {
                        'date': self.formatJsonDate(row['End Date']),
                        'timeZone': 'Asia/Taipei'
                    },
                    'description': row['Description'],
                    'iCalUID': iCalUID,
                    'colorId': '11'
                })
            else:
                rosterList.append({
                    'summary': row['Subject'],
                    'start': {
                        'dateTime': self.formatJsonDateAndTime(row['Start Date'], row['Start Time']),
                        'timeZone': 'Asia/Taipei'
                    },
                    'end': {
                        'dateTime': self.formatJsonDateAndTime(row['End Date'], row['End Time']),
                        'timeZone': 'Asia/Taipei'
                    },
                    'description': row['Description'],
                    'iCalUID': iCalUID
                })

        self.saveToFile(excelFrame, rosterList)

    def format2DightTimeStr(self, time):
        timeStr = str(time)
        n = len(timeStr)

        if n < 2:
            return '0'*(2-n)+timeStr
        else:
            return timeStr

    def transformMonthStrToDigit(self, monthStr):
        if monthStr == 'Jan':
            return '01'
        elif monthStr == 'Feb':
            return '02'
        elif monthStr == 'Mar':
            return '03'
        elif monthStr == 'Apr':
            return '04'
        elif monthStr == 'May':
            return '05'
        elif monthStr == 'Jun':
            return '06'
        elif monthStr == 'Jul':
            return '07'
        elif monthStr == 'Aug':
            return '08'
        elif monthStr == 'Sep':
            return '09'
        elif monthStr == 'Oct':
            return '10'
        elif monthStr == 'Nov':
            return '11'
        elif monthStr == 'Dec':
            return '12'
        else:
            print('error!')
            return '00'

    def formatDate(self, dateStr):
        date = dateStr[0:2]
        month = dateStr[2:5]
        year = dateStr[5:7]
        return date + '/' + self.transformMonthStrToDigit(month) + '/20' + year

    def formatTime(self, timeStr):
        hour = timeStr[0:2]
        minute = timeStr[2:4]
        return hour + ':' + minute

    def formatJsonDateAndTime(self, dateStr, timeStr):
        #print(dateStr)
        date = dateStr[0:2]
        month = dateStr[3:5]
        year = dateStr[6:10]

        formatStr = year + '-' + month + '-' + date

        if timeStr == '':
            return formatStr
        else:
            hour = timeStr[0:2]
            minute = timeStr[3:5]
            return formatStr + 'T' + hour + ':' + minute + ':00'

    def formatJsonDate(self, dateStr):
        date = dateStr[0:2]
        month = dateStr[3:5]
        year = dateStr[6:10]
        return year + '-' + month + '-' + date
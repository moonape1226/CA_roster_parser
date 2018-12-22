# -*- coding: utf-8 -*-
import ca_roster_parser
from datetime import date

if __name__ == '__main__':
    startDate = date(2018, 12, 1)
    endDate = date(2018, 12, 31)
    parser = ca_roster_parser.rosterParser("account", "password", startDate, endDate)
    
    rosterQueryResult = parser.sendRosterRequest()

    if rosterQueryResult:
        rosterData = parser.parseRosterResonpse(rosterQueryResult)
    
    if rosterData:    
        rosterFrame = parser.processRosterData(rosterData)
    
    if not rosterFrame.empty:
        excelFrame = parser.transformRosterData(rosterFrame)
        
    if not excelFrame.empty:
        parser.convertToJson(excelFrame)
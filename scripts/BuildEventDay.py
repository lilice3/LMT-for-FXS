'''
Created on 21 mars 2019

@author: nicolas
'''

import sqlite3
from time import *
import datetime
from lmtanalysis.Util import *

from lmtanalysis.Animal import *
import matplotlib.pyplot as plt
from lmtanalysis.Event import *
from lmtanalysis.Measure import *
from lmtanalysis.FileUtil import getFilesToProcess
    
from psutil import virtual_memory

from tkinter.filedialog import askopenfilename
from lmtanalysis.TaskLogger import TaskLogger
import sys



class FileProcessException(Exception):
    pass

class Day(object):
    def __init__(self, startHour=None, endHour=None, startDate=None, endDate=None, cycle="normal"):
        '''
        Constructor
        '''
        self.startHour=startHour
        self.endHour=endHour
        self.startDate=startDate
        self.endDate=endDate
        self.cycle = cycle

        def __str__(self):        
            return "Day begin at :{startHour} and stop at :{endHour} -  startDate: {startDate} -> endDate: {endDate}"\
                .format( startHour=self.startHour, endHour=self.endHour, startDate=self.startDate, endDate=self.endDate )   


    def getStartHour(self):
        return self.startHour
    
    def getEndHour(self):
        return self.endHour
    
    def getStartDate(self):
        return self.startDate
    
    def getEndDate(self):
        return self.endDate
    
    def getCycle(self):
        return self.cycle
    
    def setStartHour(self, startHour):
        self.startHour=startHour
        
    def setEndHour(self, endHour):
        self.endHour=endHour
    
    def setStartDate(self, startDate):
        self.startDate=startDate
        
    def setEndDate(self, endDate):
        self.endDate=endDate
        
    def setCycle(self, cycle):
        '''normal or reverse'''
        self.cycle = cycle

    def setStartEndDate(self, startDate):
        self.startDate=startDate
        day = datetime.datetime.strftime(self.startDate, "%Y-%m-%d")
        day = datetime.datetime(int(day.split("-")[0]),  int(day.split("-")[1]), int(day.split("-")[2]))
        if(self.cycle == "reverse"):
            day = datetime.datetime.strftime(day, "%Y-%m-%d")
            self.endDate = datetime.datetime.strptime("%s %s" % (day, self.endHour), "%Y-%m-%d %H:%M:%S")
        else:
            day += datetime.timedelta(days=1)
            day = datetime.datetime.strftime(day, "%Y-%m-%d")
            self.endDate = datetime.datetime.strptime("%s %s" % (day, self.endHour), "%Y-%m-%d %H:%M:%S")
            

    def nextDay(self):
        currentStartDay = datetime.datetime.strftime(self.startDate, "%Y-%m-%d")
        currentStartDay = datetime.datetime(int(currentStartDay.split("-")[0]),  int(currentStartDay.split("-")[1]), int(currentStartDay.split("-")[2]))
        currentEndDay = datetime.datetime.strftime(self.endDate, "%Y-%m-%d")
        currentEndDay = datetime.datetime(int(currentEndDay.split("-")[0]),  int(currentEndDay.split("-")[1]), int(currentEndDay.split("-")[2]))
        currentStartDay += datetime.timedelta(days=1)
        currentEndDay += datetime.timedelta(days=1)
        currentStartDay = datetime.datetime.strftime(currentStartDay, "%Y-%m-%d")
        currentEndDay = datetime.datetime.strftime(currentEndDay, "%Y-%m-%d")
        self.startDate = datetime.datetime.strptime("%s %s" % (currentStartDay, self.startHour), "%Y-%m-%d %H:%M:%S")
        self.endDate = datetime.datetime.strptime("%s %s" % (currentEndDay, self.endHour), "%Y-%m-%d %H:%M:%S")
        
        
def flush( connection ):
     deleteEventTimeLineInBase(connection, "day" )

   
def insertDayEvent( file ):
    connection = sqlite3.connect( file )     

    print( "--------------")
    print( "Current file: ", file )
    print("Flush")
    flush( connection )

    print( "--------------")
    print( "Loading existing events...")
    dayTimeLine = EventTimeLine( connection, "day" , None, None, None , None )        

    print( "--------------")    
    print( "Event list:" )
    for event in dayTimeLine.eventList:
        print( event )
    print( "--------------")


    startDayInput = input( "Time of the beginning of the day (hh:mm:ss):" )
    try:
        startDayEvent = datetime.time(int(startDayInput.split(":")[0]),  int(startDayInput.split(":")[1]), int(startDayInput.split(":")[2]))
    except ValueError:
        raise ValueError("Incorrect time format, should be hh:mm:ss")

    endDayInput = input( "Time of the end of the day (hh:mm:ss):" )
    try:
        endDayEvent = datetime.time(int(endDayInput.split(":")[0]),  int(endDayInput.split(":")[1]), int(endDayInput.split(":")[2]))
    except ValueError:
        raise ValueError("Incorrect time format, should be hh:mm:ss")

    if (endDayEvent < startDayEvent):
        cycle = "normal"
    else:
        cycle = "reverse"

    current_Day = Day(startHour=startDayEvent, endHour=endDayEvent, cycle=cycle)

    startExperimentDate = getStartInDatetime(file)
    endExperimentDate = getEndInDatetime(file)

    currentDay = datetime.datetime.strftime(startExperimentDate, "%Y-%m-%d")
    currentDay = datetime.datetime(int(currentDay.split("-")[0]),  int(currentDay.split("-")[1]), int(currentDay.split("-")[2]))
    previousDay = currentDay - datetime.timedelta(days=1)
    previousDay = datetime.datetime.strftime(previousDay, "%Y-%m-%d")
    currentStartDayDate = datetime.datetime.strptime("%s %s" % (previousDay, startDayEvent), "%Y-%m-%d %H:%M:%S")
    lastFrame = getNumberOfFrames(file)

    current_Day.setStartEndDate(currentStartDayDate)



    while (True):
        if(current_Day.startDate > endExperimentDate):
            break

        tmpStartFrame = recoverFrame(file, str(current_Day.startDate))
        tmpEndFrame = recoverFrame(file, str(current_Day.endDate))
        if ((tmpStartFrame == 0) & (tmpEndFrame == 0)):
            if((current_Day.startDate < startExperimentDate) & (current_Day.endDate > endExperimentDate)):
                tmpStartFrame = 1
                tmpEndFrame = lastFrame
                dayTimeLine.addEvent( Event( tmpStartFrame, tmpEndFrame) )
                dayTimeLine.endRebuildEventTimeLine(connection)
            else:
                pass
        else:
            if (tmpStartFrame == 0):
                tmpStartFrame = 1

            if (tmpEndFrame == 0):
                tmpEndFrame = lastFrame

            dayTimeLine.addEvent( Event( tmpStartFrame, tmpEndFrame) )
            dayTimeLine.endRebuildEventTimeLine(connection)
                
            

            '''next day'''
        current_Day.nextDay()


if __name__ == '__main__':
    
    print("Code launched.")
    
    files = getFilesToProcess()

    chronoFullBatch = Chronometer("Full batch" )    
        
    if ( files != None ):
    
        for file in files:
            try:
                print ( "Processing file" , file )
                insertDayEvent( file )

            except FileProcessException:
                print ( "STOP PROCESSING FILE " + file , file=sys.stderr  )
              
    print( "*** ALL JOBS DONE ***")
        
  
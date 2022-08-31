# -*- coding: utf-8 -*-
"""
Created on Wed Aug 31 13:42:31 2022

@author: roksana
"""

import os
import numpy as np
#import matplotlib.pyplot as plt
#reading the directories and files
def FileDir( directory, nametag ):
    sessiondir = []
    dir = os.listdir(directory)
    for item in dir:
        if nametag in item:
            sessiondir.append(item)
    return sessiondir

#reading the raw g4 data and output the stim parameters and the g4 finger positions
def ReadG4( g4FileDir ):
    with open(g4FileDir) as g4: lines = g4.readlines()
    tableParam = False
    tableFingerPositions = False
    param = []
    g4Data = []
    for line in lines:
        if line.startswith("UserID"):
            tableParam = True 
            continue
        if line.startswith("Position"):
            tableFingerPositions = True
            continue
        if tableParam:
            param = line
            tableParam = False
            continue
        if tableFingerPositions:
            g4Data.append(line)
            continue       
    return param, g4Data

#separate sensor 1 and sensor 2 finger positions 
def SeparateSensors(g4Data):
    sensor1 = np.empty((7,))
    sensor2 = np.empty((7,))
    for i in range(0,len(g4Data)-1,2): #len(g4Data)-1 because of the empty last line 
        m1 = np.array([float(j) for j in g4Data[i].replace('\n','').split(",")])
        m2 = np.array([float(j) for j in g4Data[i+1].replace('\n','').split(",")])
        if i == 0:
            sensor1 = m1
            sensor2 = m2
        else:
            sensor1 = np.vstack((sensor1, m1))
            sensor2 = np.vstack((sensor2, m2))
    return sensor1, sensor2

#fit a line and find the  angle with x axis for sensor1 and sensor2 data
def FitLineG4(sensor):
    a,b = np.polyfit(sensor[:,1], sensor[:,0], 1)
    x0 = sensor[0,1]
    x1 = sensor[-1,1]
    y0 = x0 * a + b
    y1 = x1 * a + b
    return np.degrees(np.arctan2(x1-x0,y1-y0))

#fit a line to sensor1 and sensor2 data and find the angle and update the param line
def AddAngleToStimParametersLine(param, g4Data):
    sensor1,sensor2 = SeparateSensors(g4Data)
    if (np.std(sensor1[:,1]) < 1.0) & (np.std(sensor1[:,0]) < 1.0):
        angle1 = FitLineG4(sensor1)
        angle2 = FitLineG4(sensor2)
    else:
        angle1 = []
        angle2 = []
    parameters = np.hstack((np.array(param.replace("\n","").split(" ; ")),angle1,angle2))
    return parameters

def CombineAllTrials(mainDir):
    trials = []
    for item in FileDir(mainDir, "Session"):
        g4Files = FileDir(mainDir + "\\" + item, "G4")
        for g4 in g4Files:
            param,g4Data = ReadG4(mainDir + "\\" + item + "\\" + g4)
            trials.append(AddAngleToStimParametersLine(param, g4Data))
    return trials

    
CombineAllTrials(os.getcwd() + "\RelativeMappingData")

        











   
    
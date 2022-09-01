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
    return np.round(np.degrees(np.arctan2(y1-y0,x1-x0)),2)

#fit a line to sensor1 and sensor2 data and find the angle and update the param line
def AddAngleToStimParametersLine(param, g4Data):
    sensor1,sensor2 = SeparateSensors(g4Data)
    angle1 = "nan"
    angle2 = "nan"
    if len(sensor1)<8 or len(sensor2)<8:
        angle1 = "nan"
        angle2 = "nan"
    elif ((np.std(sensor1[:,1]) > 1.0) or (np.std(sensor1[:,0]) > 0.1)):
        angle1 = FitLineG4(sensor1)
    elif ((np.std(sensor2[:,1]) > 1.0) or (np.std(sensor2[:,0]) > 1.0)):
        angle2 = FitLineG4(sensor2)
    else:
        angle1 = "nan"
        angle2 = "nan"
    parameters = " ; ".join(np.hstack((np.array(param.replace("\n","").split(" ; ")),angle1,angle2)))
    return parameters

#combine all trials 
def CombineAllTrials(mainDir):
    trials = []
    for item in FileDir(mainDir, "Session"):
        g4Files = FileDir(mainDir + "\\" + item, "G4")
        for g4 in g4Files:
            param,g4Data = ReadG4(mainDir + "\\" + item + "\\" + g4)
            trials.append(AddAngleToStimParametersLine(param, g4Data))
    return trials

#separate the unique electrode groups and save them in an array for each trial
def SeparateElecGroups(allTrials):
    electrode = []
    for trial in allTrials:
        trial_electrode = np.array(trial.split(" ; ")[2].split(" , "))
        trial_electrode[1] = np.char.strip( trial_electrode[1].replace(trial_electrode[0],"") , chars = '-')
        electrode.append(trial_electrode)
    return np.array(electrode)        

#sort the trails
def SortTrials(electrode,allTrials):
    pairs = set()
    index = []
    for i in range(0,len(electrode)):
        if ((electrode[i,0],electrode[i,1]) in pairs) or ((electrode[i,1],electrode[i,0]) in pairs):continue
        else:
            pairs.add((electrode[i,0],electrode[i,1]))
            ind1 = electrode==[electrode[i,0],electrode[i,1]]
            ind2 = electrode==[electrode[i,1],electrode[i,0]]
            index.append( np.hstack((np.where(ind1[:,0]&ind1[:,1]),np.where(ind2[:,0]&ind2[:,1]))) )
    
    allTrials = np.array(allTrials)
    allTrials_sorted = []
    electrode_sorted = []
    for i in range(0,len(index)):
        allTrials_sorted.append( allTrials[index[i]] )
        electrode_sorted.append( electrode[index[i],:] )     
        
    return allTrials_sorted

#save the sorted trials in a text file
def SaveSortedTrials(allTrials_sorted, mainDir):
    textFile = mainDir + "\\RelativeLocation_AllTrials.txt"
    with open(textFile,'w') as f:
        for groups in allTrials_sorted:
            f.writelines('\n'.join(groups[0,:]) + '\n')
    
#assuming the saved text file is read and edited, read all trials from the text file
def ReadSortedTrials(mainDir):
    allTrials_txtFile = mainDir+"\\RelativeLocation_AllTrials.txt" 
    with open(allTrials_txtFile) as f: allTrials_sorted_and_checked = f.readlines()
    return allTrials_sorted_and_checked

#remove trials that only one percept detected or finger tracker didn't collect finger positions
def SeparateNonSeenTrials(allTrials_sorted_and_checked):
    keywords = [
        ["only","one"],
        ["didn't","see"],
        ["nothing",""],
        ["not","sure"],
        ["could","not"],
        ["only","saw"],
        ["couldnt",""],
        ["couldn't",""],
        ["cant",""],
        ["can't",""],
        ["anything",""],
        ["only","1"],
        ["differentiate",""]
                ]
    
    included = []
    excluded = []
    for info in allTrials_sorted_and_checked:
        var = False
        comment = info.split(" ; ")[14]
        ang1 = info.split(" ; ")[15].strip(" ")
        ang2 = info.split(" ; ")[16].strip("\n")
        for k in keywords:
            var = var or ((k[0] in comment)and(k[1] in comment))
        if var==False and (ang1!='nan' or ang2!='nan'):
            included.append(info)
        else:
            excluded.append(info)
    return included, excluded
            
# extract the electrodes and the directions
def ElectrodeGroups_and_Directions(included):
    electrode = []
    direction = []
    pairs = set()
    for trial in included:
        elecTxt = ""
        # seperate electrodes
        trial_electrode = np.array(trial.split(" ; ")[2].split(" , "))
        trial_electrode[1] = np.char.strip( trial_electrode[1].replace(trial_electrode[0],"") , chars = '-')
        electrode.append(trial_electrode)
        # get the angles
        ang1 = trial.split(" ; ")[15].strip(" ")
        ang2 = trial.split(" ; ")[16].strip("\n")
        ang = []
        if ang1 == 'nan' and ang2 != 'nan':
            ang = float(ang2)
        elif ang1 != 'nan' and ang2 == 'nan':
            ang = float(ang1)
        else:
            ang = 'nan'
        
        # check if it is in the set, adjust the direction
        if ang != 'nan':
            if ((trial_electrode[1],trial_electrode[0]) in pairs):
                elecTxt = trial_electrode[1] + " , " + trial_electrode[0]
                ang = 180 + ang
            elif ((trial_electrode[0],trial_electrode[1]) in pairs):
                elecTxt = trial_electrode[0] + " , " + trial_electrode[1]
            else:
                pairs.add((trial_electrode[0],trial_electrode[1]))
                elecTxt = trial_electrode[0] + " , " + trial_electrode[1]
            if ang < 0 : ang = 360 + ang
            if ang > 359 : ang = 360 - ang
        direction.append(elecTxt + " ; " + str(np.round(ang,2)))
                
    return direction        

# save the direction of the pairs for seen trials and save the excluded data separately
def SaveDirections(direction,excluded, mainDir):
    directionTxt = mainDir + "\\RelativeLocation_sortedTrials.txt"
    excludedTxt = mainDir + "\\RelativeLocation_excludedTrials.txt"
    with open(directionTxt,'w') as df:
        df.writelines('\n'.join(direction))
    with open(excludedTxt,'w') as exf:
        exf.writelines('\n'.join(excluded))
   
# mainDir = os.getcwd() + "\RelativeMappingData"
# allTrials = CombineAllTrials(mainDir)
# electrode = SeparateElecGroups(allTrials)
# allTrials_sorted = SortTrials(electrode,allTrials)
# SaveSortedTrials(allTrials_sorted, mainDir)

mainDir = os.getcwd() + "\RelativeMappingData"
allTrials_sorted_and_checked = ReadSortedTrials(mainDir)
included,excluded = SeparateNonSeenTrials(allTrials_sorted_and_checked)
direction = ElectrodeGroups_and_Directions(included)
SaveDirections(direction,excluded, mainDir)

# mainDir = os.getcwd() + "\RelativeMappingData"        
# for item in FileDir(mainDir, "Session"):
#     g4Files = FileDir(mainDir + "\\" + item, "G4")
#     for g4 in g4Files:
#         param,g4Data = ReadG4(mainDir + "\\" + item + "\\" + g4)
#         sensor1,sensor2 = SeparateSensors(g4Data)
#         if len(sensor1)<8 or len(sensor2)<8:
#             angle1 = []
#             angle2 = []
#         elif ((np.std(sensor1[:,1]) < 1.0) and (np.std(sensor1[:,0]) < 1.0)):
#             angle1 = FitLineG4(sensor1)
#             angle2 = FitLineG4(sensor2)
#         else:
#             angle1 = []
#             angle2 = []
#         parameters = np.hstack((np.array(param.replace("\n","").split(" ; ")),angle1,angle2))
        
















   
    
# -*- coding: utf-8 -*-
"""
Created on Wed Aug 31 13:42:31 2022

@author: roksana
"""

import os
import numpy as np
import matplotlib.pyplot as plt

class RelativeLocations:
    
    def CombineSessions( self, mainDir ):
        #mainDir = os.getcwd() + "\RelativeMappingData"
        allTrials = self.CombineAllTrials(mainDir)
        electrode = self.SeparateElecGroups(allTrials)
        allTrials_sorted = self.SortTrials(electrode,allTrials)
        self.SaveSortedTrials(allTrials_sorted, mainDir)
    
    def BetweenWFMAs( self, mainDir ):
        allTrials_sorted_and_checked = self.ReadSortedTrials(mainDir)
        included,excluded = self.SeparateNonSeenTrials(allTrials_sorted_and_checked)
        
        mainDir = mainDir + "\\betweenWFMAs"
        if not os.path.exists(mainDir):
            os.mkdir(mainDir)
        direction_sorted = self.ElectrodeGroups_and_Directions_betweenWFMAs(included,True)
        excluded_sorted = self.ElectrodeGroups_and_Directions_betweenWFMAs(excluded,False)
        self.SaveDirections(direction_sorted,excluded_sorted, mainDir)
        self.SaveQuantiles_betweenWFMAs(direction_sorted, mainDir)
        self.PlotQuartiles_betweenWFMAs(mainDir)
    
    def WithinWFMA( self, mainDir ):
        allTrials_sorted_and_checked = self.ReadSortedTrials(mainDir)
        included,excluded = self.SeparateNonSeenTrials(allTrials_sorted_and_checked)
        
        mainDir = mainDir + "\\withinWFMA"
        if not os.path.exists(mainDir):
            os.mkdir(mainDir)
        directionWithinWFMA_sorted = self.ElectrodeGroups_and_Directions_withinWFMA(included,True)
        excludedWithinWFMA_sorted = self.ElectrodeGroups_and_Directions_withinWFMA(excluded,False)
        self.SaveDirections(directionWithinWFMA_sorted,excludedWithinWFMA_sorted, mainDir)
        self.SaveQuantiles_withinWFMA(directionWithinWFMA_sorted, mainDir)
        self.PlotQuartiles_withinWFMA(mainDir)
    
    #reading the directories and files
    def FileDir( self, directory, nametag ):
        sessiondir = []
        dir = os.listdir(directory)
        for item in dir:
            if nametag in item:
                sessiondir.append(item)
        return sessiondir
    
    # reading the raw g4 data and output the stim parameters and the g4 finger positions
    def ReadG4( self, g4FileDir ):
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
    
    # separate sensor 1 and sensor 2 finger positions 
    def SeparateSensors( self, g4Data ):
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
    
    # fit a line and find the  angle with x axis for sensor1 and sensor2 data
    def FitLineG4( self, sensor ):
        a,b = np.polyfit(sensor[:,1], sensor[:,0], 1)
        x0 = sensor[0,1]
        x1 = sensor[-1,1]
        y0 = x0 * a + b
        y1 = x1 * a + b
        return np.round(np.degrees(np.arctan2(y1-y0,x1-x0)),2)
    
    # fit a line to sensor1 and sensor2 data and find the angle and update the param line
    def AddAngleToStimParametersLine( self, param, g4Data ):
        sensor1,sensor2 = self.SeparateSensors(g4Data)
        angle1 = "nan"
        angle2 = "nan"
        if len(sensor1)<8 or len(sensor2)<8:
            angle1 = "nan"
            angle2 = "nan"
        elif ((np.std(sensor1[:,1]) > 1.0) or (np.std(sensor1[:,0]) > 0.1)):
            angle1 = self.FitLineG4(sensor1)
        elif ((np.std(sensor2[:,1]) > 1.0) or (np.std(sensor2[:,0]) > 1.0)):
            angle2 = self.FitLineG4(sensor2)
        else:
            angle1 = "nan"
            angle2 = "nan"
        parameters = " ; ".join(np.hstack((np.array(param.replace("\n","").split(" ; ")),angle1,angle2)))
        return parameters
    
    # combine all trials 
    def CombineAllTrials( self, mainDir ):
        trials = []
        for item in self.FileDir(mainDir, "Session"):
            g4Files = self.FileDir(mainDir + "\\" + item, "G4")
            for g4 in g4Files:
                param,g4Data = self.ReadG4(mainDir + "\\" + item + "\\" + g4)
                trials.append( self.AddAngleToStimParametersLine(param, g4Data) )
        return trials
    
    # separate the unique electrode groups and save them in an array for each trial
    def SeparateElecGroups( self, allTrials ):
        electrode = []
        for trial in allTrials:
            trial_electrode = np.array(trial.split(" ; ")[2].split(" , "))
            trial_electrode[1] = np.char.strip( trial_electrode[1].replace(trial_electrode[0],"") , chars = '-')
            electrode.append(trial_electrode)
        return np.array(electrode)        
    
    # sort the trails
    def SortTrials( self, electrode,allTrials ):
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
    
    # save the sorted trials in a text file
    def SaveSortedTrials( self, allTrials_sorted, mainDir ):
        textFile = mainDir + "\\RelativeLocation_AllTrials.txt"
        with open(textFile,'w') as f:
            for groups in allTrials_sorted:
                f.writelines('\n'.join(groups[0,:]) + '\n')
        
    # assuming the saved text file is read and edited, read all trials from the text file
    def ReadSortedTrials( self, mainDir ):
        allTrials_txtFile = mainDir+"\\RelativeLocation_AllTrials.txt" 
        with open(allTrials_txtFile) as f: allTrials_sorted_and_checked = f.readlines()
        return allTrials_sorted_and_checked
    
    # remove trials that only one percept detected or finger tracker didn't collect finger positions
    def SeparateNonSeenTrials( self, allTrials_sorted_and_checked ):
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
    def ElectrodeGroups_and_Directions_betweenWFMAs( self, allTrials,ifIncluded ):
        direction = []
        wfma = []
        pairs = set()
        for trial in allTrials: 
            elecTxt = ""
            # seperate electrodes
            trial_electrode = np.array(trial.split(" ; ")[2].split(" , "))
            trial_electrode[1] = np.char.strip( trial_electrode[1].replace(trial_electrode[0],"") , chars = '-')
            
            # separate the WFMAs
            trial_wfma = []
            trial_wfma.append(trial_electrode[0][0:2])
            trial_wfma.append(trial_electrode[1][0:2])
            wfma.append(trial_wfma)
           
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
            if ang != 'nan' and ifIncluded:
                if ((trial_wfma[1],trial_wfma[0]) in pairs):
                    elecTxt = trial_electrode[1] + " ; " + trial_electrode[0]
                    ang = 180 + ang
                elif ((trial_wfma[0],trial_wfma[1]) in pairs):
                    elecTxt = trial_electrode[0] + " ; " + trial_electrode[1]
                else:
                    pairs.add((trial_wfma[0],trial_wfma[1]))
                    elecTxt = trial_electrode[0] + " ; " + trial_electrode[1]
                
                if ang < 0 : ang = 360 + ang
                if ang > 359 : ang = 360 - ang
            
                direction.append(elecTxt + " ; " + str(np.round(ang,2)))
                
            elif not ifIncluded:#for sorting excluded trials
                if ((trial_wfma[1],trial_wfma[0]) in pairs)or((trial_wfma[0],trial_wfma[1]) in pairs):
                    elecTxt = trial_electrode[0] + " , " + trial_electrode[1]
                else:
                    pairs.add((trial_wfma[0],trial_wfma[1]))
                    elecTxt = trial_electrode[0] + " , " + trial_electrode[1]
                direction.append(trial.strip('\n'))
    
        # sort the direction list based on the index
        direction_sorted = self.SortTrials(np.array(wfma),np.array(direction))
            
        return direction_sorted        
    
    # save the direction of the pairs for seen trials and save the excluded data separately
    def SaveDirections( self, direction_sorted,excluded_sorted, mainDir ):
        directionTxt = mainDir + "\\RelativeLocation_sortedDirections.txt"
        excludedTxt = mainDir + "\\RelativeLocation_excludedTrials.txt"
        with open(directionTxt,'w') as df:
            df.writelines('Group1 (Hex) ; Group2 (Hex) ; Direction From Group1 to Group2 Relative to Positive Horizontal Direction (degree)\n')
            for groups in direction_sorted:
                df.writelines('\n'.join(groups[0,:]) + '\n\n')
        with open(excludedTxt,'w') as exf:
            exf.writelines('UserID ; Time ; Electrodes ; Frequency (Hz) ; Cathodic Phase Duration (us) ; Train Length (ms) ; Duty On (ms); Duty Off (ms) ; Inter-train Length (ms) ; Amplitude (uA) ; Sent to Gateway ; Comments ; Sensor1 Angle (Degree) ; Sensor2 Angle (Degree)\n')
            for groups in excluded_sorted:
                exf.writelines('\n'.join(groups[0,:])+'\n\n')
    
    # save the median and 1/4 and 3/4 for each wfma pair
    def SaveQuantiles_betweenWFMAs( self, direction_sorted, mainDir ):
        lines = []
        for group in direction_sorted:
            ang = []
            txt = []
            for trial in group[0,:]:
               t = trial.split(' ; ') 
               ang.append(float(t[2]))
    
            if (t[0][0:2] == t[1][0:2]):continue
            wfma = t[0][0:2] + ' ; ' + t[1][0:2]
            q1 = np.round( np.quantile(np.array(ang), 0.25) , 2)
            q2 = np.round( np.quantile(np.array(ang), 0.5) , 2)
            q3 = np.round( np.quantile(np.array(ang), 0.75) , 2)
            txt.append( wfma )
            txt.append( str( q1 ) )
            txt.append( str( q2 ) )
            txt.append( str( q3 ) )
            txt.append( str( len(group[0,:]) ) )
            lines.append(' ; '.join(txt))
        
        quartilesTxt = mainDir + '\\RelativeLocation_medianDirections.txt'
        with open(quartilesTxt,'w') as m:
            m.writelines('WFMA1 (Hex) ; WFMA2 (Hex) ; First Quartile (degree) ; Second Quartile (degree) ; Third Quartile (degree) ; Number of Trials' )
            m.writelines('\n'.join(lines))
    
    # quartiles
    def PlotQuartiles_betweenWFMAs( self, mainDir ):
        quartilesTxt = mainDir + '\\RelativeLocation_medianDirections.txt'
        with open (quartilesTxt) as f: quartilesLines = f.readlines()
        quartilesLines = quartilesLines[1:]
        if not os.path.exists(mainDir + '\\plots_betweenWFMAs\\'):
            os.mkdir(mainDir + '\\plots_betweenWFMAs\\')
            
        for line in quartilesLines:
            t = line.split(' ; ')
            theta = np.radians(float(t[3]))
            radii = 1
            width = np.radians( np.abs(float(t[4]) - float(t[2])) )
            title = 'WFMA ' + str( int(t[0],16) ) + '-' + str( int(t[1],16) ) + ' : num. of trials = ' + t[5].strip('\n') + '\nMedian = ' +  t[3] + ' degrees'
            
            fig, ax = plt.subplots(subplot_kw={'projection': 'polar'},figsize=(7,7))
            ax.bar(theta, radii, width=width, bottom=0.0, alpha=0.5,label='Q1-Q3')
            ax.bar(theta, radii, width=0.01, bottom=0.0, alpha=1,label='Median')
            ax.set_title(title,size=12,wrap=False)
            plt.legend()
            plt.savefig(mainDir + '\\plots_betweenWFMAs\\'+'WFMA_' +
                        str( int(t[0],16) ) + '-' + str( int(t[1],16) ) +
                        '.png', bbox_inches='tight',dpi=300)
            
            plt.show()
    
    # extract the electrodes and the directions
    def ElectrodeGroups_and_Directions_withinWFMA( self, allTrials,ifIncluded ):
        direction = []
        electrode = []
        pairs = set()
        for trial in allTrials: 
            elecTxt = ""
            # seperate electrodes
            trial_electrode = np.array(trial.split(" ; ")[2].split(" , "))
            trial_electrode[1] = np.char.strip( trial_electrode[1].replace(trial_electrode[0],"") , chars = '-')
            
            # separate the WFMAs
            trial_wfma = []
            trial_wfma.append(trial_electrode[0][0:2])
            trial_wfma.append(trial_electrode[1][0:2])
            # only consider the trials within a WFMA
            if trial_wfma[0]!=trial_wfma[1]:continue
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
            if ang != 'nan' and ifIncluded:
                if ((trial_electrode[1],trial_electrode[0]) in pairs):
                    elecTxt = trial_electrode[1] + " ; " + trial_electrode[0]
                    ang = 180 + ang
                elif ((trial_electrode[0],trial_electrode[1]) in pairs):
                    elecTxt = trial_electrode[0] + " ; " + trial_electrode[1]
                else:
                    pairs.add((trial_electrode[0],trial_electrode[1]))
                    elecTxt = trial_electrode[0] + " ; " + trial_electrode[1]
                
                if ang < 0 : ang = 360 + ang
                if ang > 359 : ang = 360 - ang
            
                direction.append(elecTxt + " ; " + str(np.round(ang,2)))
                
            elif not ifIncluded:#for sorting excluded trials
                if ((trial_electrode[1],trial_electrode[0]) in pairs)or((trial_electrode[0],trial_electrode[1]) in pairs):
                    elecTxt = trial_electrode[0] + " , " + trial_electrode[1]
                else:
                    pairs.add((trial_electrode[0],trial_electrode[1]))
                    elecTxt = trial_electrode[0] + " , " + trial_electrode[1]
                direction.append(trial.strip('\n'))
    
        # sort the direction list based on the index
        direction_sorted = self.SortTrials(np.array(electrode),np.array(direction))
            
        return direction_sorted  
    
    # save the median and 1/4 and 3/4 for each wfma pair
    def SaveQuantiles_withinWFMA( self, direction_sorted, mainDir ):
        lines = []
        for group in direction_sorted:
            ang = []
            txt = []
            for trial in group[0,:]:
               t = trial.split(' ; ') 
               ang.append(float(t[2]))
    
            elec = t[0] + ' ; ' + t[1]
            q1 = np.round( np.quantile(np.array(ang), 0.25) , 2)
            q2 = np.round( np.quantile(np.array(ang), 0.5) , 2)
            q3 = np.round( np.quantile(np.array(ang), 0.75) , 2)
            txt.append( elec )
            txt.append( str( q1 ) )
            txt.append( str( q2 ) )
            txt.append( str( q3 ) )
            txt.append( str( len(group[0,:]) ) )
            lines.append(' ; '.join(txt))
        
        quartilesTxt = mainDir + '\\RelativeLocation_medianDirections.txt'
        with open(quartilesTxt,'w') as m:
            m.writelines('WFMA1 (Hex) ; WFMA2 (Hex) ; First Quartile (degree) ; Second Quartile (degree) ; Third Quartile (degree) ; Number of Trials' )
            m.writelines('\n'.join(lines))
    
    # quartiles
    def PlotQuartiles_withinWFMA( self, mainDir ):
        quartilesTxt = mainDir + '\\RelativeLocation_medianDirections.txt'
        with open (quartilesTxt) as f: quartilesLines = f.readlines()
        quartilesLines = quartilesLines[1:]
        if not os.path.exists(mainDir + '\\plots_withinWFMAs\\'):
            os.mkdir(mainDir + '\\plots_withinWFMAs\\')
            
        for line in quartilesLines:
            t = line.split(' ; ')
            theta = np.radians(float(t[3]))
            radii = 1
            width = np.radians( np.abs(float(t[4]) - float(t[2])) )
            title = 'WFMA ' + str( int(t[0][0:2],16) ) + ',' + str( int(t[0][2:4],16) + 1 ) + \
                '-' + str( int(t[1][0:2],16) ) + ',' + str( int(t[1][2:4],16) + 1 ) + \
                    ' : num. of trials = ' + t[5].strip('\n') + '\nMedian = ' + \
                        t[3] + ' degrees'
            
            fig, ax = plt.subplots(subplot_kw={'projection': 'polar'},figsize=(7,7))
            ax.bar(theta, radii, width=width, bottom=0.0, alpha=0.5,label='Q1-Q3')
            ax.bar(theta, radii, width=0.01, bottom=0.0, alpha=1,label='Median')
            ax.set_title(title,size=12,wrap=False)
            plt.legend()
            plt.savefig(mainDir + '\\plots_withinWFMAs\\' + 'WFMA ' +\
                        str( int(t[0][0:2],16) ) + ',' + str( int(t[0][2:4],16) + 1 ) + \
                            '-' + str( int(t[1][0:2],16) ) + ',' + str( int(t[1][2:4],16) + 1 ) +\
                                '.png', bbox_inches='tight',dpi=300)
            
            plt.show()
        
    
   
        
    
    
    

    
    
    
    
    
    
    








   
    
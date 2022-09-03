# -*- coding: utf-8 -*-
"""
Created on Fri Sep  2 19:48:18 2022

@author: roksana
"""

from RelativeLocations_Class import RelativeLocations 
import os
rl = RelativeLocations()
# mainDir = folder containing relative location sessions
mainDir = os.getcwd() + "\RelativeMappingData"
# combining trials from all sessions in one text file from G4 raw files
rl.CombineSessions( mainDir )
# extract trials for between WFMAs
rl.BetweenWFMAs( mainDir )
# extract trials for within WFMAs
rl.WithinWFMA( mainDir )
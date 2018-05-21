'''
Created on 2018/5/19

@author: Lulumi5129
'''
from LocalizationSystem.LocalizationAlg.L3M_System import L3M_Sys
nodeConfigFilePath = './config/node_config.cfg'
L3MSysConfigFilePath = './config/L3M_System_config_2D.cfg'

(anchorNodeList, targetNodeList, realRSSIDict, noiseDict, L3M_CoordinateDict, anchorCombDict, L3M_Comb_CoordinateDict) = L3M_Sys.L3M_Sys_main(L3MSysConfigFilePath, nodeConfigFilePath)

L3M_Sys.printTargetNode(targetNodeList)
L3M_Sys.printAnchorNode(anchorNodeList)
L3M_Sys.printRealRSSI(realRSSIDict, noiseDict)
L3M_Sys.printL3M_Coordinate(L3M_CoordinateDict)
L3M_Sys.printL3M_Comb_Coordinate(L3M_Comb_CoordinateDict, anchorCombDict)

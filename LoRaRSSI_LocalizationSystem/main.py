'''
Created on 2018/5/21

@author: Lulumi5129

 Flow : L3M -> EV
'''

import optparse
import sys
import multiprocessing
from LocalizationSystem.LocalizationAlg.L3M_System import L3M_Sys, L3M_Config
from LocalizationSystem.Node.node import node_Config
from LocalizationSystem.BackEndAlg.EvolutionaryComputation.EV import EV3, EV3_Config

nodeConfigFilePath = './config/node_config.cfg'
L3MSysConfigFilePath = './config/L3M_System_config_3D.cfg'
EVConfigFilePath = './config/EV_config.cfg'

def main(argv=None):
    if argv is None:
        argv = sys.argv
        
    try:
        #
        # get command-line options
        #
        parser = optparse.OptionParser()
        parser.add_option("-i", "--input", action="store", dest="inputFileName", help="input filename", default=None)
        parser.add_option("-q", "--quiet", action="store_true", dest="quietMode", help="quiet mode", default=False)
        parser.add_option("-d", "--debug", action="store_true", dest="debugMode", help="debug mode", default=False)
        (options, args) = parser.parse_args(argv)
        
        #validate options
        #if options.inputFileName is None:
            #raise Exception("Must specify input file name using -i or --input option.")
        
        #Get Node config params
        node_cfg = node_Config(nodeConfigFilePath)
        
        #print config params
        print(node_cfg)
        
        #Get L3M config params
        L3M_cfg = L3M_Config(L3MSysConfigFilePath)
        
        #print config params
        print(L3M_cfg)
        
        #run L3M
        (anchorNodeList, targetNodeList, realRSSIDict, noiseDict, L3M_CoordinateDict, anchorCombDict, L3M_Comb_CoordinateDict) = L3M_Sys.L3M_Sys_main()
        
        #print L3M System each node and data
        L3M_Sys.printTargetNode(targetNodeList)
        L3M_Sys.printAnchorNode(anchorNodeList)
        L3M_Sys.printRealRSSI(realRSSIDict, noiseDict)
        L3M_Sys.printL3M_Coordinate(L3M_CoordinateDict)
        L3M_Sys.printL3M_Comb_Coordinate(L3M_Comb_CoordinateDict, anchorCombDict)
        
        #Get EV3 config params
        EV3_cfg=EV3_Config(EVConfigFilePath)
        
        #print config params
        print(EV3_cfg)
        
        #run EV3
        for target in targetNodeList :
            L3M_Node = L3M_CoordinateDict[target.nodeName]
            L3M_Comb = L3M_Comb_CoordinateDict[target.nodeName]
            dataList = [anchorNodeList, target, L3M_Node, L3M_Comb, anchorCombDict]
            p = multiprocessing.Process(target=EV3.ev3_multiprocess, args=(EVConfigFilePath, L3MSysConfigFilePath, nodeConfigFilePath, dataList,))
            p.start()
            
        p.join()
        
        if not options.quietMode:                    
            print('Localization System Completed!')    
        
    except Exception as info:
        if 'options' in vars() and options.debugMode:
            from traceback import print_exc
            print_exc()
        else:
            print(info)

if __name__ == '__main__':
    main()
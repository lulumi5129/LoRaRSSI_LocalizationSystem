'''
Created on 2018/5/26

@author: Lulumi5129
'''

import optparse
import sys
import multiprocessing
from LocalizationSystem.LocalizationAlg.L3M_System import L3M, L3M_Config
from LocalizationSystem.Node.node import node_Config
from LocalizationSystem.LocalizationAlg.Localization import Localization_Config
from LocalizationSystem.BackEndAlg.EvolutionaryComputation.EV import EV3, EV3_Config

def main(argv=None):
    nodeConfigFilePath = './config/main/node.cfg'
    L3MConfigFilePath = './config/main/L3M.cfg'
    EV3ConfigFilePath = './config/main/EV3.cfg'
    LocalizationConfigFilePath = './config/main/Localization_3D.cfg'
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
        Localization_cfg = Localization_Config(LocalizationConfigFilePath)
        
        #print config params
        print(Localization_cfg)
        
        #Get L3M config params
        L3M_cfg = L3M_Config(L3MConfigFilePath)
        
        #print config params
        print(L3M_cfg)
        
        #Get EV3 config params
        EV3_cfg=EV3_Config(EV3ConfigFilePath)
        
        #print config params
        print(EV3_cfg)
        
        #run L3M
        LS_Obj = L3M()
        
        #print L3M System each node and data
        LS_Obj.printLocalizationSystemInfo()
        
        #run EV3
        for target in LS_Obj.targetList :
            settingPath = [EV3ConfigFilePath, L3MConfigFilePath, LocalizationConfigFilePath, nodeConfigFilePath]
            p = multiprocessing.Process(target=EV3.ev3_multiprocess, args=(settingPath, LS_Obj, target,))
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
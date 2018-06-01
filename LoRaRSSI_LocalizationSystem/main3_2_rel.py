'''
Created on 2018/5/26

@author: Lulumi5129
'''

import optparse
import sys
from multiprocessing import Pool
from LocalizationSystem.LocalizationAlg.L3M_System import L3M, L3M_Config
from LocalizationSystem.Node.node import node_Config
from LocalizationSystem.LocalizationAlg.Localization import Localization_Config
from LocalizationSystem.BackEndAlg.EvolutionaryComputation.EV import EV3 as EV3_1
from LocalizationSystem.BackEndAlg.EvolutionaryComputation2.EV import EV3 as EV3_2
import matplotlib.pyplot as plt

def main(argv=None):
    nodeConfigFilePath = './config/main2/node.cfg'
    L3MConfigFilePath = './config/main2/L3M.cfg'
    EV3CombConfigFilePath = './config/main2/EV3.cfg'
    EV3ConfigFilePath = './config/main3/EV3.cfg'
    LocalizationConfigFilePath = './config/main2/Localization_3D.cfg'
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
        
        #run L3M
        LS_Obj = L3M()
        
        #print L3M System each node and data
        LS_Obj.printLocalizationSystemInfo()
        
        
        pool = Pool(processes=6)
        result = []
        #run EV3_1
        for target in LS_Obj.targetList :
            settingPath1 = [EV3CombConfigFilePath, L3MConfigFilePath, LocalizationConfigFilePath, nodeConfigFilePath]
            job = pool.apply_async(EV3_1.ev3_multiprocess, args=(settingPath1, LS_Obj, target,))
            result.append(job)
            
        pool.close()
        pool.join()
        
        #get result
        EV3_1_res = {}
        for i in result :
            res = i.get()
            EV3_1_res[res[0].nodeName] = res[1]
            print(str(res[0].nodeName) + ' EV3_1, ' + str(res[1]))
        
        pool = Pool(processes=6)
        result = []
        #run EV3_2
        for target in LS_Obj.targetList :
            settingPath2 = [EV3ConfigFilePath, L3MConfigFilePath, LocalizationConfigFilePath, nodeConfigFilePath]
            job = pool.apply_async(EV3_2.ev3_multiprocess, args=(settingPath2, LS_Obj, target,))
            result.append(job)
            
        pool.close()
        pool.join()
        
        #get result
        EV3_2_res={}
        for i in result :
            res = i.get()
            EV3_2_res[res[0].nodeName] = res[1]
            print(str(res[0].nodeName) + ' EV3_2, ' + str(res[1]))
        
        #plot error
        fig = plt.figure(figsize=(8,6), dpi=120)
        fig.suptitle("Localization System error")
        ax = fig.add_subplot(111)
        ax.set_xlabel('target ID')
        ax.set_ylabel('error distance (m)')
        
        target_ID = []
        L3M_errList = []
        EV3_1_errList = []
        EV3_2_errList = []
        L3M_err_sum = 0
        EV3_1_errsum = 0
        EV3_2_errsum = 0
        for target in LS_Obj.targetList :
            target_ID.append(target.ID)
            L3M_err = LS_Obj.L3M_CoordinateDict[target.nodeName].getDistance(target)
            EV3_1_err = EV3_1_res[target.nodeName].getDistance(target)
            EV3_2_err = EV3_2_res[target.nodeName].getDistance(target)
            L3M_errList.append(L3M_err)
            EV3_1_errList.append(EV3_1_err)
            EV3_2_errList.append(EV3_2_err)
            L3M_err_sum += L3M_err
            EV3_1_errsum += EV3_1_err
            EV3_2_errsum += EV3_2_err
            
        #print(target_ID)
        #print(L3M_errList)
        #print(EV3_1_errList)
        #print(EV3_2_errList)
        ax.plot(target_ID, L3M_errList, label='L3M', marker = '*', color = 'b')
        ax.plot(target_ID, EV3_1_errList, label='EV3_1', marker = '*', color = 'g')
        ax.plot(target_ID, EV3_2_errList, label='EV3_2', marker = '*', color = 'r')
        legend = ax.legend(loc='center right', fontsize='x-small', shadow=True)
        legend.get_frame().set_facecolor('#00FFCC')
        textstr1 = 'L3M Avg distance error is %s'%(L3M_err_sum/len(L3M_errList)) + 'm\n'
        textstr2 = 'EV3_1 Avg distance error is %s'%(EV3_1_errsum/len(EV3_1_errList)) + 'm\n'
        textstr3 = 'EV3_2 Avg distance error is %s'%(EV3_2_errsum/len(EV3_2_errList)) + ' m'
        textstr = textstr1 + textstr2 + textstr3
        textstr = textstr.replace('\t', ' ')
        props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
        textbox = ax.text(x=0.05, y=0.95, s=textstr, transform=ax.transAxes, fontsize=10,bbox=props)
        textbox.set_horizontalalignment("left")
        textbox.set_verticalalignment("top")
        ax.grid(True)
        plt.show()
        
        
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
'''
Created on 2018/5/19

@author: Lulumi5129
'''
from LocalizationSystem.LocalizationAlg.L3M_System import L3M_Sys, L3M_Config
from LocalizationSystem.Node.node import node_Config
from mpl_toolkits.mplot3d import Axes3D, axes3d
import matplotlib.pyplot as plt
from itertools import cycle
import numpy as np
nodeConfigFilePath = './config/node_config.cfg'
L3MSysConfigFilePath = './config/L3M_System_config_2D.cfg'

#Get Node config params
node_cfg = node_Config(nodeConfigFilePath)
        
#print config params
print(node_cfg)

#Get L3M config params
L3M_cfg = L3M_Config(L3MSysConfigFilePath)
        
#print config params
print(L3M_cfg)

(anchorNodeList, targetNodeList, realRSSIDict, noiseDict, L3M_CoordinateDict, anchorCombDict, L3M_Comb_CoordinateDict) = L3M_Sys.L3M_Sys_main()

L3M_Sys.printTargetNode(targetNodeList)
L3M_Sys.printAnchorNode(anchorNodeList)
L3M_Sys.printRealRSSI(realRSSIDict, noiseDict)
L3M_Sys.printL3M_Coordinate(L3M_CoordinateDict)
L3M_Sys.printL3M_Comb_Coordinate(L3M_Comb_CoordinateDict, anchorCombDict)

# plot
fig = plt.figure(figsize=(8,6), dpi=120)
ax = fig.subplots()
cycol=cycle('bgrcmkyb')

for anchor in anchorNodeList :
    # center and radius
    (r,x) = anchor.getChannelDistance(targetNodeList[0])
    circle = plt.Circle(anchor.coordinate, r, color=next(cycol), fill=False)

    ax.add_artist(circle)
    #ax.plot_surface(x, y, z,  rstride=4, cstride=4, color='b')



x_anchor=[]
y_anchor=[]
target=targetNodeList[0]
    
# get anchor coordinate
for anchor in anchorNodeList :
    x_anchor.append(anchor.x)
    y_anchor.append(anchor.y)
            
# plot
ax.scatter(x_anchor, y_anchor, c='b', s=100, marker='^', label='Anchor')
ax.scatter(target.x, target.y, c='r', s=100, marker='o', label=target.nodeName)
legend = ax.legend(loc='center right', fontsize='x-small', shadow=True)
legend.get_frame().set_facecolor('#00FFCC')

# show
plt.show()
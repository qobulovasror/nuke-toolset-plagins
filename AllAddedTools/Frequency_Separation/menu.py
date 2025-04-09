import sys
import nuke
from AllAddedTools.menu import allAddedTools

#Cubichead Tools
toolbar = allAddedTools
cubicheadMenu = toolbar.addMenu("Cubichead Tools", "cubichead_menu.png")
cubicheadMenu.addCommand("CH_FrequencySeparation", "nuke.createNode('CH_FrequencySeparation')")
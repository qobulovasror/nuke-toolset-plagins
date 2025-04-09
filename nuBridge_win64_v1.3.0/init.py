import nuke

import sys
# import NukepediaDB
import os
if nuke.NUKE_VERSION_MAJOR < 11:
    os.environ['QT_PREFERRED_BINDING'] ='PySide'

nuke.pluginAddPath('./src')
nuke.pluginAddPath('./src/lib')
nuke.pluginAddPath('./src/controller')
nuke.pluginAddPath('./src/view/resources/icons/nuke')

sys.path.append(r"C:/Users/qobul/.nuke/nuBridge_win64_v1.3.0/src/")
sys.path.append(r"C:/Users/qobul/.nuke/nuBridge_win64_v1.3.0/src/model/")
# # V!ctor definitions

# VMenu.addCommand('V_CheckMatte', 'nuke.createNode("V_CheckMatte")', icon='V_CheckMatte.png')
# VMenu.addCommand('V_IdBuilder', 'nuke.createNode("V_IdBuilder")', icon='V_IdBuilder.png')
# VMenu.addCommand('V_IdPackage', 'nuke.createNode("V_IdPackage")', icon='V_IdPackage.png')
# VMenu.addCommand('V_IdFilter', 'nuke.createNode("V_IdFilter")', icon='V_IdFilter.png')
# VMenu.addCommand('V_ColorRenditionChart', 'nuke.createNode("V_ColorRenditionChart")', icon='V_ColorRenditionChart.png')
# VMenu.addCommand('V_ColorTracker', 'nuke.createNode("V_ColorTracker")', icon='V_ColorTracker.png')
# VMenu.addCommand('V_CompareView', 'nuke.createNode("V_CompareView")', icon='V_CompareView.png')
# VMenu.addCommand('V_Slate', 'nuke.createNode("V_Slate")', icon='V_Slate.png')



### nuke.pluginAddPath("./", addToSysPath=False);
import os
import os.path
global syspath

cwd = 'C://Users/qobul/.nuke/v_'
files = os.listdir(cwd)

fnames = []
dirs = []
for f in files:
    fsp = os.path.splitext(f)
    if '.gizmo' == fsp[1]:
        fnames.append(fsp[0])

toolbar = nuke.toolbar("Nodes")
VMenu = toolbar.addMenu('V!ctor', icon='V_Victor.png')


for n in fnames:
    VMenu.addCommand(n, 'nuke.createNode("' + n + '")')

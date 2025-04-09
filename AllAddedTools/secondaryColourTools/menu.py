import os
import sys
import os.path
from AllAddedTools.menu import allAddedTools

# Initialize syspath to the current working directory or any valid directory path
syspath = os.getcwd()

if sys.platform == "win32":
    cwd = os.path.join(os.environ['USERPROFILE'], '.nuke', 'AllAddedTools', 'secondaryColourTools')
else:
    cwd = os.path.join(os.environ['HOME'], '.nuke', 'secondaryColourTools')

files = os.listdir(cwd)

fnames = []
dirs = []
for f in files:
    print(f)
    fsp = os.path.splitext(f)
    if '.gizmo' == fsp[1]:
        fnames.append(fsp[0])

toolbar = allAddedTools
GMenu = toolbar.addMenu('secondaryColourTools', icon='secondaryGrade.png')

for n in fnames:
    GMenu.addCommand(n, 'nuke.createNode("' + n + '")')

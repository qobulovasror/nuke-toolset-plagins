import os
import os.path

# Initialize syspath to the current working directory or any valid directory path
syspath = os.getcwd()

# cwd = 'C://Users/qobul/.nuke/secondaryColourTools'
cwd = os.path.join(os.environ['USERPROFILE'], '.nuke', 'secondaryColourTools')

files = os.listdir(cwd)

fnames = []
dirs = []
for f in files:
    print(f)
    fsp = os.path.splitext(f)
    if '.gizmo' == fsp[1]:
        fnames.append(fsp[0])

toolbar = nuke.toolbar("Nodes")
GMenu = toolbar.addMenu('secondaryColourTools', icon='secondaryGrade.png')

for n in fnames:
    GMenu.addCommand(n, 'nuke.createNode("' + n + '")')

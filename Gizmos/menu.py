### nuke.pluginAddPath("./", addToSysPath=False);
import os
import os.path
global syspath

# Initialize syspath to the desired directory path
syspath = 'C://Users/qobul/.nuke/Gizmos'

# Set up the plugin path in Nuke
nuke.pluginAddPath(syspath, addToSysPath=False)

# List all files and directories in the specified path
files = os.listdir(syspath)

fnames = []
dirs = []

for f in files:
    fsp = os.path.splitext(f)
    if fsp[1] == '.gizmo':
        fnames.append(fsp[0])
    elif os.path.isdir(os.path.join(syspath, f)):
        dirs.append(f)

# Create a new menu in the Nuke toolbar
toolbar = nuke.toolbar("Nodes")
GxMenu = toolbar.addMenu('MyTools', icon='Gtool.png')

# Add commands for .gizmo files
for n in fnames:
    GxMenu.addCommand(n, f'nuke.createNode("{n}")')

# Add submenus and commands for directories
for d in dirs:
    GsubMenu = GxMenu.addMenu(d)
    nuke.pluginAddPath(f'./{d}')
    subDirFiles = os.listdir(os.path.join(syspath, d))
    for subF in subDirFiles:
        subFsp = os.path.splitext(subF)
        GsubMenu.addCommand(subFsp[0], f'nuke.createNode("{subFsp[0]}")')

import nuke # type: ignore
import os
import sys

from Run3PartSoftware.scripts.runXMEM import createXMEMNode

sys.path.append(os.path.dirname(__file__))


nuke.pluginAddPath('icons')
nuke.pluginAddPath('scripts')


toolbar = nuke.toolbar("Nodes")
TheridPartyTools = toolbar.addMenu('3PartyTools', icon='menu.png')
TheridPartyTools.addCommand("XMEM++", "createXMEMNode()", icon="icon.png")
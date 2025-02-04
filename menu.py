import os

import pixelfudger


toolbar = nuke.menu("Nodes")
toolbar.addCommand("Merge/Premult", "nuke.createNode('Premult')", "[", icon="Premult.png")
toolbar.addCommand("Time/FrameHold", "nuke.createNode('FrameHold')", "h", icon="FrameHold.png")
#toolbar.addCommand("Transform/Tracker", "nuke.createNode('Tracker', inpanel=False)", "]", icon="Tracker.png")
toolbar.addCommand("3D/3D Classic/CameraTracker", "nuke.createNode('CameraTracker')", "C", icon="CameraTracker.png")


toolbar.addMenu('Assorted Gizmos').addCommand('ColorDilate', 'nuke.createNode("ColorDilate")', icon='')
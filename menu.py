import os

toolbar = nuke.menu("Nodes")
toolbar.addCommand("Merge/Premult", "nuke.createNode('Premult')", "[", icon="Premult.png")
toolbar.addCommand("Time/FrameHold", "nuke.createNode('FrameHold')", "h", icon="FrameHold.png")
toolbar.addCommand("Transform/Tracker", "nuke.createNode('Tracker4')", "SHIFT+T", icon="Tracker.png")
toolbar.addCommand("3D/3D Classic/CameraTracker", "nuke.createNode('CameraTracker')", "C", icon="CameraTracker.png")



# Get the existing Nuke "Transform" menu
transform_menu = nuke.menu("Nodes").findItem("Transform")

# If the menu exists, find the "PlanarTracker" entry and update it
if transform_menu:
    planar_tracker = transform_menu.findItem("PlanarTracker")
    if planar_tracker:
        # Reassign the command with a hotkey
        planar_tracker.setShortcut("SHIFT+P")  # Change "P" to your desired hotkey
    tracker_node = transform_menu.findItem("Tracker")
    if tracker_node:
        # Reassign the command with a hotkey
        tracker_node.setShortcut("SHIFT+T")  # Change "P" to your desired hotkey

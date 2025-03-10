import nuke
import os
# from Custom import autoSelect #AutoRotoNode

toolbar = nuke.menu("Nodes")
toolbar.addCommand("Merge/Premult", "nuke.createNode('Premult')", "[", icon="Premult.png")
toolbar.addCommand("Time/FrameHold", "nuke.createNode('FrameHold')", "h", icon="FrameHold.png")
#toolbar.addCommand("Transform/Tracker", "nuke.createNode('Tracker4')", "SHIFT+T", icon="Tracker.png")
toolbar.addCommand("3D/3D Classic/CameraTracker", "nuke.createNode('CameraTracker')", "C", icon="CameraTracker.png")


# Get the existing Nuke "Transform" menu
transform_menu = nuke.menu("Nodes").findItem("Transform")

# If the menu exists, find the "PlanarTracker" entry and update it
if transform_menu:
    planar_tracker = transform_menu.findItem("PlanarTracker")
    if planar_tracker:
        planar_tracker.setShortcut("SHIFT+P")

    tracker_node = transform_menu.findItem("Tracker")
    if tracker_node:
        # Reassign the command with a hotkey
        tracker_node.setShortcut("SHIFT+T") 




##  ========================= Custom Nodes ===================

# toolbar.addCommand("Custom/Auto_Roto", "AutoRotoNode.create_auto_roto_node()", icon="Custom/icons/AutoRotoNode.png")
# toolbar.addCommand("Custom/Auto_select", "select_object()", icon="Custom/icons/AutoRotoNode.png")














custom_menu = toolbar.addMenu("Custom Tools", icon="Write.png")


# Taylor nodlarni o'shish tugmasini qo'shamiz
custom_menu.addCommand("Tayyor nodlar(L)", "createNodes()", icon="nods.png")




# Read to Write funksiyasi
def createNodes():
    # Nodlarni yaratamiz
    read = nuke.createNode("Read")
    rotoPaint = nuke.createNode("RotoPaint")
    frameHold = nuke.createNode("FrameHold")
    roto = nuke.createNode("Roto")
    copy = nuke.createNode("Copy")
    premult = nuke.createNode("Premult")
    merge = nuke.createNode("Merge")
    viewer = nuke.createNode("Viewer")
    
    # Nodlarni ulash
    rotoPaint.setInput(0, read)
    frameHold.setInput(0, rotoPaint)
    copy.setInput(0, frameHold)
    copy.setInput(1, roto)
    premult.setInput(0, copy)
    merge.setInput(0, read)
    merge.setInput(1, premult)
    viewer.setInput(0, merge)
    

    
    
    # Nodlarni joylashtirish
    read.setXYpos(100, 100)
    rotoPaint.setXYpos(300, 125)
    frameHold.setXYpos(300, 250)
    copy.setXYpos(300, 350)
    roto.setXYpos(500, 350)
    premult.setXYpos(300, 450)
    merge.setXYpos(100, 450)
    viewer.setXYpos(100, 550)

    
    # Vizual aniqlik uchun 'autoUpdate' funksiyasini chaqirish	
    nuke.zoom(1)
    nuke.autoplace_all()

# Shortcutni o'rnatish
nuke.menu('Nuke').addCommand('Custom/Create Nodes', 'createNodes()', 'L')





# Tayyor Write nodini o'shish
custom_menu.addCommand("Taylor Write(ctrl+w)", "createWriteNode()", icon="write.png")




# Funktsiyani aniqlaymiz
def createWriteNode():
    # Tanlangan `Read` nodini tekshiramiz
    selected_nodes = nuke.selectedNodes('Read')
    
    # Agar `Read` tanlanmagan bo'lsa, birinchi `Read` nodini avtomatik tanlaydi
    if not selected_nodes:
        all_reads = nuke.allNodes('Read')
        if not all_reads:
            nuke.message("Hech qanday Read nodi topilmadi!")
            return
        read_node = all_reads[0]  # Birinchi `Read` nodini olamiz
    else:
        read_node = selected_nodes[0]
    
    # Fayl yo'lini olamiz va yangi nom beramiz
    file_path = read_node['file'].value()
    new_file_path = file_path.rsplit('.', 1)[0] + " Final.mov"
    
    with nuke.root():
        # Write nodini yaratamiz
        write_node = nuke.nodes.Write()
        write_node['file'].setValue(new_file_path)
        write_node['file_type'].setValue("mov")
        
        # Output transformni Rec.709 ga sozlash
        if write_node.knob('colorspace'):
            write_node['colorspace'].setValue('rec709')
        
       
        
        # Viewer va Write nodlarining joylashuvini o'zgartiramiz
        read_x, read_y = read_node.xpos(), read_node.ypos()
        write_node.setXYpos(read_x + 150, read_y)
       
    
   

# Shortcutni o'rnatish
nuke.menu('Nuke').addCommand('Custom/Read to Write', 'createWriteNode()', 'Ctrl+W')







# FPS ni to'g'irlash
custom_menu.addCommand("FPS ni tog'irlash(Y)", "setFrameRate()", icon="sped.png")

def setFrameRate():
    # Tanlangan Read nodlarini tekshiramiz
    selected_nodes = nuke.selectedNodes('Read')
    
    # Agar Read tanlanmagan bo'lsa, birinchi Read nodini avtomatik tanlaymiz
    if not selected_nodes:
        all_reads = nuke.allNodes('Read')
        if not all_reads:
            nuke.message("Hech qanday Read nodi topilmadi!")
            return
        read_node = all_reads[0]  # Birinchi Read nodini olamiz
    else:
        read_node = selected_nodes[0]
    
    # Metadata dan frame_rate ni olish
    frame_rate = read_node.metadata('input/frame_rate')
    
    # Agar frame_rate topilmasa, xabar chiqaramiz
    if frame_rate is None:
        nuke.message("Frame rate ma'lumoti topilmadi!")
        return
    
    # Frame rate ni Nuke sozlamalaridagi FPS ga o'rnatamiz
    nuke.root()['fps'].setValue(frame_rate)
    nuke.message(f"Nuke FPS: {frame_rate} ga o'rnatildi!")

# Y tugmasi bosilganda ishga tushadigan qilib o'rnatamiz
nuke.menu('Nuke').addCommand('Custom/Set FPS from Read', 'setFrameRate()', 'Y')

# qushimcha  tugmalar
custom_menu.addCommand("Tugmalar", "tugmalar()", icon="menu.png")

def tugmalar():

    nuke.message("Tayyor nodlarni qo'shish-->L\n"
    "Write nodini qo'shish---> ctrl+W\n"
    "FPS ni to'g'irlash---> Y\n"
    "Premult--> H\n"
    "FrameHold-- J\n"
    "Tracker--> X\n"
    "SmartVector--> I\n"
    "VectorDistort--> U\n"
    
    )
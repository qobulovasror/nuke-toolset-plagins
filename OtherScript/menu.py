nuke.pluginAddPath('./gizmo')

toolbar = nuke.toolbar ( "Nodes" )
EMenu = toolbar.addMenu ( 'Elias', icon = 'E.png' )
LMenu = EMenu.addMenu ( 'Relight' )
SMenu = LMenu.addMenu ( 'Shadow' )


EMenu.addCommand( 'VrayPasses', 'nuke.createNode("VrayPasses")', icon = 'VrayPasses.png' )
EMenu.addCommand( 'RGB To Alpha', 'nuke.createNode("RGBToAlpha")', icon = 'RGBToAlpha.png' )
EMenu.addCommand( 'AutoRimLight', 'nuke.createNode("AutoRimLight")')



LMenu.addCommand( 'Lighting', 'nuke.createNode("Lighting")')
LMenu.addCommand( 'Mask_3D', 'nuke.createNode("Mask_3D")')
LMenu.addCommand( 'Relighting', 'nuke.createNode("Relighting")')
LMenu.addCommand( 'RelightingRig', 'nuke.createNode("RelightingRig")')
LMenu.addCommand( 'Fresnel', 'nuke.createNode("Fresnel")')
LMenu.addCommand( 'AA', 'nuke.createNode("AA")')


SMenu.addCommand( 'shadow3D', 'nuke.createNode("shadow3D")')
SMenu.addCommand( 'RenderBoth', 'nuke.createNode("RenderBoth")')
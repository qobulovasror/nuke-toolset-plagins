# This menu.py will create the Mango Suite toolbar in your nuke!
# DON'T CHANGE ANYTHING HERE unless you know how to properly do it ;)

# Mango Suite TOOLS by Johannes Kretschmer 

import nuke
import sys
import os
import webbrowser
from AllAddedTools.menu import allAddedTools

# Add PluginPaths to tools and icons
nuke.pluginAddPath('./python')
nuke.pluginAddPath('./icons')
nuke.pluginAddPath('./nk_files')

# Import some helpful functions for the MS
import MS_helper

# Store the location of this menu.py to help with nuke.nodePaste() which requires a filepath to paste
MS_FolderPath = os.path.dirname(__file__)
MS_helper.MS_FolderPath = MS_FolderPath

#create Mango Suite Menu
toolbar = allAddedTools
a = toolbar.addMenu('MangoSuite', icon='mangosuite_logo.png')

# adding items to toolbar
# A
a.addCommand('MS_Antialias', 'nuke.nodePaste("{}/nk_files/ms_antialias.nk")'.format(MS_FolderPath), icon='antialias_icon.png')
a.addCommand('MS_Alpha Eliminate', 'nuke.nodePaste("{}/nk_files/ms_alpha_eliminate.nk")'.format(MS_FolderPath), icon='alphaeliminate_icon.png')
a.addCommand('MS_Alpha From Range', 'nuke.nodePaste("{}/nk_files/ms_alpha_from_range.nk")'.format(MS_FolderPath), icon='alphafromrange_icon.png')
a.addCommand('MS_Arrange Flares', 'nuke.nodePaste("{}/nk_files/ms_arrange_flares.nk")'.format(MS_FolderPath), icon='arrangeflares_icon.png')
# B
a.addCommand('MS_Brightness', 'nuke.nodePaste("{}/nk_files/ms_brightness.nk")'.format(MS_FolderPath), icon='brightness_icon.png')
a.addCommand('MS_Blend Transforms', 'nuke.nodePaste("{}/nk_files/ms_blend_transforms.nk")'.format(MS_FolderPath), icon='blendtransforms_icon.png')
# C
a.addCommand('MS_Camerashake 2D', 'nuke.nodePaste("{}/nk_files/ms_camerashake_2D.nk")'.format(MS_FolderPath), icon='camerashake_icon.png')
a.addCommand('MS_Calculator', 'nuke.nodePaste("{}/nk_files/ms_calculator.nk")'.format(MS_FolderPath), icon='calculator_icon.png')
a.addCommand('MS_Cromatic', 'nuke.nodePaste("{}/nk_files/ms_cromatic.nk")'.format(MS_FolderPath), icon='cromatic_icon.png')
# D
a.addCommand('MS_Drop Quality', 'nuke.nodePaste("{}/nk_files/ms_drop_quality.nk")'.format(MS_FolderPath), icon='dropquality_icon.png')
# E
a.addCommand('MS_Edge Matte', 'nuke.nodePaste("{}/nk_files/ms_edge_matte.nk")'.format(MS_FolderPath), icon='edgematte_icon.png')
#a.addCommand('MS_Edge Overlap', 'nuke.nodePaste("{}/nk_files/ms_edge_overlap.nk")'.format(MS_FolderPath), icon='edgeoverlap_icon.png')
# F
a.addCommand('MS_Fine Keyer', 'nuke.nodePaste("{}/nk_files/ms_fine_keyer.nk")'.format(MS_FolderPath), icon='finekeyer_icon.png')
# G
a.addCommand('MS_Grain', 'nuke.nodePaste("{}/nk_files/ms_grain.nk")'.format(MS_FolderPath), icon='grain_icon.png')
a.addCommand('MS_Gridmaker', 'nuke.nodePaste("{}/nk_files/ms_gridmaker.nk")'.format(MS_FolderPath), icon='gridmaker_icon.png')
a.addCommand('MS_Guides', 'nuke.nodePaste("{}/nk_files/ms_guides.nk")'.format(MS_FolderPath), icon='guides_icon.png')
# H
a.addCommand('MS_Hue Satuaration', 'nuke.nodePaste("{}/nk_files/ms_hue_saturation.nk")'.format(MS_FolderPath), icon='huesaturation_icon.png')
# I
# J 
# K 
# L
a.addCommand('MS_Lens Breathing', 'nuke.nodePaste("{}/nk_files/ms_lens_breathing.nk")'.format(MS_FolderPath), icon='lensbreathing_icon.png')
a.addCommand('MS_Lens Filter', 'nuke.nodePaste("{}/nk_files/ms_lens_filter.nk")'.format(MS_FolderPath), icon='lensfilter_icon.png')
a.addCommand('MS_Lightwrap Mask', 'nuke.nodePaste("{}/nk_files/ms_lightwrap_mask.nk")'.format(MS_FolderPath), icon='lightwrapmask_icon.png')
# M 
a.addCommand('MS_Multiblur', 'nuke.nodePaste("{}/nk_files/ms_multiblur.nk")'.format(MS_FolderPath), icon='multiblur_icon.png')
a.addCommand('MS_Multi Vector Blur', 'nuke.nodePaste("{}/nk_files/ms_multi_vector_blur.nk")'.format(MS_FolderPath), icon='directionalblur_icon.png')
# N 
# O
a.addCommand('MS_Opacity', 'nuke.nodePaste("{}/nk_files/ms_opacity.nk")'.format(MS_FolderPath), icon='opacity_icon.png')
# P
# Q
a.addCommand('MS_Quick Shape', 'nuke.nodePaste("{}/nk_files/ms_quick_shape.nk")'.format(MS_FolderPath), icon='quickshape_icon.png')
# R 
a.addCommand('MS_Random', 'nuke.nodePaste("{}/nk_files/ms_random.nk")'.format(MS_FolderPath), icon='random_icon.png')
a.addCommand('MS_Reference', 'nuke.nodePaste("{}/nk_files/ms_reference.nk")'.format(MS_FolderPath), icon='reference_icon.png')
a.addCommand('MS_Reformat', 'nuke.nodePaste("{}/nk_files/ms_reformat.nk")'.format(MS_FolderPath), icon='reformat_icon.png')
a.addCommand('MS_Remap Spill', 'nuke.nodePaste("{}/nk_files/ms_remap_spill.nk")'.format(MS_FolderPath), icon='despill_icon.png')
a.addCommand('MS_Rolling Shutter', 'nuke.nodePaste("{}/nk_files/ms_rolling_shutter.nk")'.format(MS_FolderPath), icon='rollingshutter_icon.png')
# S 
a.addCommand('MS_Slate Overlay', 'nuke.nodePaste("{}/nk_files/ms_slate_overlay.nk")'.format(MS_FolderPath), icon='slate_icon.png')
# T
a.addCommand('MS_Turbulence', 'nuke.nodePaste("{}/nk_files/ms_turbulence.nk")'.format(MS_FolderPath), icon='turbulence_icon.png')
a.addCommand('MS_Tile Texture', 'nuke.nodePaste("{}/nk_files/ms_tile_texture.nk")'.format(MS_FolderPath), icon='tiletexture_icon.png')
# U 
# V 
a.addCommand('MS_Vignette', 'nuke.nodePaste("{}/nk_files/ms_vignette.nk")'.format(MS_FolderPath), icon='edgematte_icon.png')
# W 
# X
# Y 
# Z
a.addCommand('MS_Z Fix', 'nuke.nodePaste("{}/nk_files/ms_z_fix.nk")'.format(MS_FolderPath), icon='zprocess_icon.png')
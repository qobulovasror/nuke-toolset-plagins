# Rather old code for baking gizmos recursively
# Still seems to work ok though, so I didn't bother re-writing it

import nuke
import os

def getAllNodes(topLevel):
    '''
    recursively return all nodes starting at topLevel. Default topLevel is nuke.root()
    '''

    allNodes = nuke.allNodes(group=topLevel)
    for n in allNodes:
        allNodes = allNodes + getAllNodes(n)
    return allNodes

def getOutputs(node):
    '''
    Return a dictionary of the nodes and pipes that are connected to node
    '''
    depDict = {}
    dependencies = node.dependent( nuke.INPUTS | nuke.HIDDEN_INPUTS )
    for d in dependencies:
        depDict[ d ] = []
        for i in range( d.inputs() ):
            if d.input( i ) == node:
                depDict[ d ].append( i )
    return depDict

def isGizmo(node):
    '''
    return True if node is gizmo
    '''
    return 'gizmo_file' in node.knobs()

def gizmoIsDefault(gizmo):
    '''Check if gizmo is in default install path'''
    installPath = os.path.dirname(nuke.EXE_PATH)
    gizmoPath = gizmo.filename()
    installPathSet = set(installPath.split('/'))
    gizmoPathSet = set(gizmoPath.split('/'))
    gizmoPathSet.issubset(installPathSet)
    gizmoIsDefault = os.path.commonprefix([installPath, gizmoPath]) == installPath
    return gizmoIsDefault

def getParent(n):
    '''Return n's parent node, return nuke.root()n is on the top level'''

    return nuke.toNode( '.'.join( n.fullName().split('.')[:-1] ) ) or nuke.root()

def bakeGizmo(gizmo):
    '''
    Copy gizmo to group and replace it in the tree, so all inputs and outputs use the new group.
    returns the new group node
    '''

    parent = getParent(gizmo)
    #groupName = nuke.tcl('global no_gizmo; set no_gizmo 1; catch {in %s {%s -New}}; return [value [stack 0].name]' % (parent.fullName(), gizmo.Class()))
    errorMsg, groupName = nuke.tcl('global no_gizmo; set no_gizmo 1; catch {in %s {%s -New}} errorMsg; return "$errorMsg|[value [stack 0].name]"' % (parent.fullName(), gizmo.Class())).split('|')
    group = nuke.toNode('.'.join( (parent.fullName(), groupName)))
    group.setSelected(False)
    if getOutputs(gizmo):
        # RECONNECT OUTPUTS IF THERE ARE ANY
        for node, pipes in iter(getOutputs(gizmo).items()):
            for i in pipes:
                node.setInput(i, group)

    # RECONNECT INPUTS
    for i in range(gizmo.inputs()):
        group.setInput(i, gizmo.input(i))

    group.setXYpos(gizmo.xpos(), gizmo.ypos())
    # COPY VALUES
    group.readKnobs(gizmo.writeKnobs(nuke.TO_SCRIPT))
    gizmoName = gizmo.name()
    nuke.delete(gizmo)
    group.setName(gizmoName)
    return group, errorMsg

def bakeGizmoRecursively(gizmo, excludeDefaults=False):
    '''Main function to bake a gizmo in place and recursively'''
    
    # bake gizmo and catch version error
    newGroup, errorMsg = bakeGizmo(gizmo)
    
    # bake gizmo internals if needed
    for n in getAllNodes(newGroup):
        n.setSelected(False)
    for n in getAllNodes(newGroup):
        try:
            if isGizmo(n):
                if not gizmoIsDefault(n):
                    # ALWAYS BAKE CUSTOM GIZMOS
                    bakeGizmo(n)
                elif not excludeDefaults:
                    # BAKE NON-DEFAULT GIZMOS IF REQUESTED
                    bakeGizmo(n)

        except ValueError:
            pass

    # pop up version warning if applicable
    if errorMsg:
        nuke.message(errorMsg)

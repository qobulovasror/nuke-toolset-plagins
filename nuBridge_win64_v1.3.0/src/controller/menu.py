import logging
import os
import nuke
import Nukepedia
import sys
import common
from nukescripts.panels import WidgetKnob
from Installer import createNukepediaMenu
from nkpd_tools import bakeGizmoRecursively
from model.NukepediaDBLocal import NPDBLocal
from view.WidgetPage import ToolView
from view.FancyButton import FancyButton
from view.DetailsPage import HtmlView
#from PySide import QtGui, QtCore
from Qt import QtCore, QtWidgets, QtGui

class NKPDPanelWrapper(nukescripts.PythonPanel):
    def __init__(self):
        super(NKPDPanelWrapper, self).__init__(title='nuBridge',
                                               id='com.nukepedia.nuBridge',
                                               scrollable=False)
        self.pyKnob = nuke.PyCustom_Knob("", "", "pyKnob(QtWidgets.QWidget)")
        self.addKnob(self.pyKnob)

class pyKnob(WidgetKnob):
    '''Custom knob to draw the tool bowser as the UI for the wrapper class'''
    
    def makeUI(self):
        global nkpd_widgetInstance_app
        self.widget = nkpd_widgetInstance_app = Nukepedia.ToolBrowser()
        self.widget.setMinimumSize(self.widget.minimumSizeHint())
        return self.widget

class NKPD_GlobalEventFilter(QtWidgets.QWidget):
    """Event filter that restores buggy mouse wheel behaviour for custom panels
    !!!!!!!!!!!!!!!!!!!!
    NOT IN USE AS NUKE 13 CAUSES WEIRD RECURSION ERRORS WITH THIS
    !!!!!!!!!!!!!!!!!!!!
    """
    def __init__(self):
        super(NKPD_GlobalEventFilter, self).__init__()
        self.__nkpd_app = QtWidgets.QApplication.instance()
        self.__nkpd_app.installEventFilter(self)

    def eventFilter(self, widget, event):
        if event.type() == QtCore.QEvent.Wheel:
            widgetUnderPointer = self.__nkpd_app.widgetAt(self.mapToGlobal(QtGui.QCursor.pos()))
            if isinstance(widgetUnderPointer, (ToolView, FancyButton)):
                nkpd_widgetInstance_app.toolView.wheelEvent(event)
                return True
            elif isinstance(widgetUnderPointer, (HtmlView, )):
                nkpd_widgetInstance_app.ui.htmlView.wheelEvent(event)
                return True

        #return super(NKPD_GlobalEventFilter, self).eventFilter(widget, event)
        return QtWidgets.QWidget.eventFilter(self, widget, event)

def loadToolBrowserPanel():
    '''Load nuBridge as a docked panel'''

    global nkpd_widgetInstance
    try:
        # if panel instance already exists
        p = nkpd_widgetInstance
    except NameError:
        # else create it
        nkpd_widgetInstance = NKPDPanelWrapper()

    return nkpd_widgetInstance.addToPane()

def showNKPDPanel():
    '''Open nuBridge as a panel from the help menu'''

    global nkpd_widgetInstance
    try:
        p = nkpd_widgetInstance # check if instance exists
        # if instance exists already, check if it's docked anywhere
        if nuke.getPaneFor("com.nukepedia.nuBridge"):
            # instance is currently docked somewhere
            # so just bring it's panel to the front
            qwindow = QtWidgets.QApplication.instance().activeWindow()
            widget = qwindow.findChildren(QtWidgets.QWidget,'com.nukepedia.nuBridge')[0]
            stackedWidget =  widget.parentWidget()
            stackedWidget.setCurrentWidget(widget)

            #for widget in QtWidgets.QApplication.allWidgets():
                #name = widget.objectName()
                #if name == 'com.nukepedia.nuBridge':
                    #stackedWidget = widget.parentWidget()
                    #stackedWidget.setCurrentIndex(stackedWidget.indexOf(widget))
                    #break

    except NameError:
        # the panel hasn't been instantiated yet
        # so do it now
        nkpd_widgetInstance = NKPDPanelWrapper()
    nkpd_widgetInstance.show()
    
def NKPD_getRepoPath(relPath):
    '''
    Helper function to turn a relative path into an absolute path based on the current repo path.
    E.g. This is used by the default processor to import nk scripts
    '''

    return os.path.join(common.NKPDSettings().repoLocation, relPath)

def createGizmo(gizmoName, args='', inpanel=True):
    '''Simple wrapper that allows for gizmos to be baked on the fly based on the respective user settings'''

    try:
        e = ''
        # create the node
        node = nuke.createNode(gizmoName, args, inpanel)
    except RuntimeError as e:
        # This happens if the gizmo was created in a newer version of Nuke than currently in use
        # the version warning interrupts the usual things that happen during node creation
        # so we need to do fix that manually
        node = nuke.toNode(nuke.tcl('stack 0'))
        for i, n in enumerate(nuke.selectedNodes()):
            if i+1 > node.maxInputs():
                break
            node.setInput(i, n)
        node.readKnobs(args)
        node.autoplace()
        node.selectOnly()
        if inpanel:
            node.showControlPanel()
    finally:
        # check the settings and bake the gizmo if requested
        if common.NKPDSettings().bakeGizmos == 2:
            # options are set to never bake gizmos
            pass
        elif common.NKPDSettings().bakeGizmos or __NPDB_LOCAL_DB.getBakeGizmoByPath(node.filename()):
            # bake the node if either it's individual or the global setting are set to bake
            bakeGizmoRecursively(node)        


def main():
    #--------------- Add nuBridge as panel
    nuke.menu('Pane').addCommand("nuBridge", loadToolBrowserPanel, icon=common.NKPD_MENU_ICON_PATH)
    nukescripts.registerPanel('com.nukepedia.nuBridge', loadToolBrowserPanel)
    
    #--------------- Add nuBridge to Help menu
    helpMenu = nuke.menu('Nuke').findItem('Help')
    itemNames = [i.name() for i in helpMenu.items()]
    try:
        nkpdIndex = itemNames.index('Nukepedia') + 1
        helpMenu.addCommand('nuBridge', showNKPDPanel, index=nkpdIndex, icon='NukepediaMenuIcon.png')
    except ValueError:
        helpMenu.addCommand('nuBridge', showNKPDPanel, icon='NukepediaMenuIcon.png')
    
    #--------------- create Nukepedia menu based on local database content
    npdbLocal = NPDBLocal(os.path.join(common.NKPDSettings().repoLocation, common.NKPD_DB_NAME))
    menuCmds = npdbLocal.getMenuCmds()
    localTools = npdbLocal.getToolItems(activeOnly=True)
    fileTypes = set(i.fileType for i in localTools)
    logger.debug('installed tools: {}'.format(localTools))
    logger.debug('fileTypes are {}'.format(list(fileTypes)))
    
    #--------------- create main Nukepedia menu with icon if it's needed
    if menuCmds:
        logger.debug('found gizmo tool type')
        createNukepediaMenu()
    
    #--------------- add tools from database
    for cmd in npdbLocal.getMenuCmds():
        logger.debug('found menu command for local tools: {}'.format(cmd))
        
        try:
            eval(cmd)
        except:
            logger.critical('invalid menu command: {}'.format(cmd))

try:
    logger = logging.getLogger('Nukepedia.menu')
    # run main code
    main()
    # install event filter to fix scroll wheel behaviour - deactivating as it crashes Nuke 13 when downloading tools
    #__npdb_ef = NKPD_GlobalEventFilter()
except:
    # catch all to ensure Nuke starts
    print("ERROR {}".format(sys.exc_info()))
    logger.critical("MENU ERROR: {}".format(sys.exc_info()))
    pass
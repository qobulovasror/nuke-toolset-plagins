import os
import posixpath
import sys
import common
import webbrowser
from PySide2 import QtCore, QtGui, QtWidgets
    
from PySide2.QtWebEngineWidgets import QWebEngineView
from PySide2.QtWebEngineWidgets import QWebEnginePage

from .Buttons import ToolPushButton
from view.resources import ICON_CACHE

class ClickableImageLabel(QtWidgets.QLabel):
    '''clickable image label'''
    clicked = QtCore.Signal(int)
    
    def __init__(self, parent=None):
        super(ClickableImageLabel, self).__init__(parent)
        self.setMaximumSize(QtCore.QSize(50, 50))
        self.toolID = ''

    def mousePressEvent(self, event):
        self.clicked.emit(self.toolID)
    
    def enterEvent(self, event):
        self.setCursor(QtCore.Qt.PointingHandCursor)
        

class HtmlViewHeader(QtWidgets.QWidget):
    '''Draw header for tools' details page'''

    def __init__(self, parent=None):
        super(HtmlViewHeader, self).__init__(parent)
        self.toolID = 0
        self.setupUI()
        self.setFocusPolicy(QtCore.Qt.StrongFocus)        
        self.connectSignalsAndSlots()
        
    @staticmethod
    def goToToolWebsite(toolID=None):
        '''
        Open the respective tool's website. This can be called from inside the HtmlView, using it's current tool id,
        or from tool buttons in which case the tool argument holds the respective tool id.
        '''
        #requestedToolID = toolID or self.toolID
        requestedToolID = toolID
        toolUrl = 'http://www.nukepedia.com/index.php?option=com_remository&func=fileinfo&id={0}'.format(requestedToolID)
        #QtGui.QDesktopServices.openUrl(toolUrl)
        webbrowser.open(toolUrl)

    def connectSignalsAndSlots(self):
        self.title.linkActivated.connect(self.goToToolWebsite)
        self.imageLabel.clicked.connect(self.goToToolWebsite)
        self.pBar.valueChanged.connect(self.hideProgressWhenZero)

    def hideProgressWhenZero(self, value):
        '''Automatically hide the progress bar if progress is 0'''
        self.pBar.setHidden(value == 0)
        self.update()

    def setValue(self, value):
        self.pBar.setValue(value)

    def setupUI(self):
        # LAYOUT 
        mainLayout = QtWidgets.QVBoxLayout()
        btnLayout = QtWidgets.QHBoxLayout()
        #headerLayout = QtWidgets.QHBoxLayout()
        headerLayout = QtWidgets.QGridLayout()
        #headerLayout.setAlignment( QtCore.Qt.AlignLeft | QtCore.Qt.AlignBottom )
        detailsLayout = QtWidgets.QGridLayout()
        detailsLayout.setSpacing(0)
        #mainLayout.addStretch()
        mainLayout.addLayout(btnLayout)
        mainLayout.addLayout(headerLayout)
        mainLayout.addLayout(detailsLayout)
        self.setLayout(mainLayout)

        # WIDGETS
        self.backBtn = QtWidgets.QPushButton('Back')
        self.installBtn = ToolPushButton( 'Install')      
        self.stackBtn = ToolPushButton('Add To Stack')
        self.webBtn = ToolPushButton('Visit Website...')
        self.pBar = QtWidgets.QProgressBar()
        self.pBar.setMaximum(100)
        self.pBar.setTextVisible(False)
        self.pBar.setHidden(True)
        self.pBar.setMaximumHeight(10)
        
        self.backBtn.setToolTip('return to main tool pages\nHotkey:\nBackspace')
        self.installBtn.setToolTip('install this tool')
        self.stackBtn.setToolTip('add this tool to drop stack')
        self.webBtn.setToolTip('Open the tool website in a browser')

        # HEADER
        self.imageLabel = ClickableImageLabel()
        self.title = QtWidgets.QLabel()
        font = QtWidgets.QApplication.font()
        font.setPointSize(14)
        font.setBold(True)
        self.title.setFont(font)
        self.title.setAlignment( QtCore.Qt.AlignBottom )

        # DETAILS
        self.authorLabel = QtWidgets.QLabel()
        self.downLabel = QtWidgets.QLabel()
        self.versionLabel = QtWidgets.QLabel()
        self.shortDescLabel = QtWidgets.QLabel()
        self.shortDescLabel.setMaximumWidth(300)
        self.shortDescLabel.setWordWrap(True)

        # ASSIGN WIDGETS TO LAYOUTS
        for btn in ( self.backBtn, self.installBtn, self.stackBtn, self.stackBtn, self.webBtn ):
            btnLayout.addWidget(btn)
        headerLayout.addWidget(self.imageLabel, 0, 0)
        headerLayout.addWidget(self.title, 0, 1)
        detailsLayout.addWidget(self.authorLabel, 0, 0)
        detailsLayout.addWidget(self.downLabel, 1, 0)
        detailsLayout.addWidget(self.versionLabel, 0, 1)
        detailsLayout.addWidget(self.shortDescLabel, 1, 1)
        mainLayout.addWidget(self.pBar)

    def setTool(self, tool):
        '''
        sets the tool object for the page and distributes
        it's parameters to the relevant page attributes
        '''
        self.toolID = tool.id_
        self.installBtn.setTool(tool)
        self.stackBtn.setTool(tool)
        self.webBtn.setTool(tool)
        self.imageLabel.toolID = tool.id_
        self.toolUrl = '''http://www.nukepedia.com/index.php?option=com_remository&func=fileinfo&id={0}'''.format(tool.id_)
        httpText = '''<a style="color: #C74F24" href="{0}">{1} ({2}.{3})</a>'''.format(self.toolUrl, tool.title, tool.majorVersion, tool.minorVersion)
        self.title.setText(httpText)
        
        self.authorLabel.setText('author: %s' % tool.author)
        self.downLabel.setText('downloads: %s' % tool.downloads)
        self.versionLabel.setText('versions: %s' % ', '.join([str(v) for v in tool.nukeVersions]))
        self.setShortDesc(tool.shortDesc)
        self.setImage(ICON_CACHE.getPixmap(tool.category, 'large'))
        self.pBar.setValue(int(tool.hasBeenDownloaded) * 100)

    def setImage( self, pixmap ):
        '''set icon in upper left corner'''
        self.imageLabel.setPixmap( pixmap )

    def setShortDesc( self, descStr ):
        '''set version string to appear in header'''
        maxWords = 100
        words = descStr.split(' ')
        if len(words) > maxWords:
            self.shortDescLabel.setText( ' '.join(words[:maxWords]) + ' ...')
            self.shortDescLabel.setToolTip(descStr)
        else:
            self.shortDescLabel.setText(descStr)


class WebEnginePage(QWebEnginePage):
    """Open link in system browser"""
    
    def acceptNavigationRequest(self, url, _type, isMainFrame):
        if _type == QWebEnginePage.NavigationTypeLinkClicked:
            QtGui.QDesktopServices.openUrl(url)
        return True

class HtmlView(QWebEngineView):
    '''Draw tools' html content'''
    def __init__(self, parent=None):
        super(HtmlView, self).__init__(parent)
        headerPath = posixpath.join(common.NKPD_PROJECT_ROOT, 'view', 'resources', 'headerWithCSS.html')
        with open(headerPath, 'r') as fh:
            self.htmlBody = fh.read()
        #self.setPage(WebEnginePage(self))

    def setTool(self, tool):
        '''Set the url that should open the website (temp for PySide2 until web engine is fixed
        not actually used in PySide (only in PySide2)
        '''
        self.toolUrl = '''http://www.nukepedia.com/index.php?option=com_remository&func=fileinfo&id={0}'''.format(tool.id_)

    def sizeHint(self):
        return QtCore.QSize(400, 200)

    def setHtml(self, html, contextUrl='http://www.nukepedia.com'):
        super(HtmlView, self).setHtml(self.htmlBody.replace('>>TOKEN<<', html),
                                      QtCore.QUrl(contextUrl))

######################################################################
######### WORKAROUND TO PREVENT NUKE CRASHING ########################
######### REMOVE WHEN BUG 455085 IS FIXED ############################
## https://support.foundry.com/hc/en-us/articles/360017058299-ID-455085-Nuke-crashes-when-using-QWebEngineView-setHtml-after-installing-a-global-event-filter-macOS-and-Linux-
        
class HtmlView_Dummy(QtWidgets.QPushButton):
    '''Dummy class as placeholder until WebView issues are resolved in PySide2'''   
    loadFinished = QtCore.Signal()
    def __init__(self, parent=None):
        super(HtmlView_Dummy, self).__init__(parent)
        headerPath = posixpath.join(common.NKPD_PROJECT_ROOT, 'view', 'resources', 'headerWithCSS.html')
        with open(headerPath, 'r') as fh:
            self.htmlBody = fh.read()

    def openWebsite(self, url):
        #webbrowser.open(url.toString())
        webbrowser.open(url) # this is only for teh tempreary button in PySide2

    def sizeHint(self):
        return QtCore.QSize(400, 200)

    def setTool(self, tool):
        '''Set the url that should open the website (temp for PySide2 until web engine is fixed'''
        toolUrl = '''http://www.nukepedia.com/index.php?option=com_remository&func=fileinfo&id={0}'''.format(tool.id_)
        self.clicked.connect(lambda: self.openWebsite(toolUrl))

    def setHtml(self, html, contextUrl='http://www.nukepedia.com'):
        html = self.htmlBody.replace('>>TOKEN<<', html), QtCore.QUrl(contextUrl)
        #print "would show this page if web view wasn't bustes:", html
        self.setText('The web engine for PySide2 is not yet funcitonal.\n\nPlease click here to view the tool description online.')
        self.loadFinished.emit()

HtmlView = HtmlView_Dummy
######### END WORKAROUND #############################################
######################################################################


def getTestPage(parent=None):
    import os, sys
    projectRoot = os.path.sep.join(sys.path[0].split(os.path.sep)[:-1])
    sys.path.append(projectRoot)    
    from model.NKPD import ToolItem
    w = HtmlViewHeader(parent=parent)
    w.setShortDesc('yadda'*200)
    w.installBtn.clicked.connect(test)
    w.installBtn.altClicked.connect(test2)
    #w.setImage( '/ohufx/consulting/Nukepedia/NukeBridge/icons/categories/categories_merge.png' )
    #w.setHtml( '<b> test html' )
    return w

def test():
    print("a")

def test2():
    print("b")


if __name__ == '__main__':
    #from WidgetPage import getTestWidgetPage
    #from FaderWidget import PageFader
    from model.NukepediaDB import NPDB
    import requests
    app = QtWidgets.QApplication( sys.argv )

    #html = NPDB().getDescription(2011)
    html = requests.get('http://www.nukepedia.com/python/ui/nodetable').content
    print("html")
    w = HtmlView()
    w.setHtml(html, 'http://www.nukepedia.com')
    w.show()
    w.raise_()

    #mainWindow = QtWidgets.QWidget()
    #layout = QtWidgets.QVBoxLayout()
    #mainWindow.setLayout(layout)
    #btn1 = QtWidgets.QPushButton('show tools')
    #btn2 = QtWidgets.QPushButton('back')
    #detailView = getTestPage()
    #detailView.show()
    #detailView.raise_()
    #toolView = getTestWidgetPage()
    #fader = PageFader(detailView, toolView)
    
    #layout.addWidget(btn1)
    #layout.addWidget(btn2)
    #layout.addWidget(fader)
    
    #btn1.clicked.connect(fader.showViewB)
    #btn2.clicked.connect(fader.showViewA)
    
    #mainWindow.show()
    sys.exit( app.exec_() )

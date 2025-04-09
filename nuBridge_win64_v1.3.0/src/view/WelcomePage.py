import sys
import common
#from PySide import QtCore, QtGui
from Qt import QtCore, QtWidgets, QtGui
try:
    # Python2
    import urllib2
    from HTMLParser import HTMLParser

except ModuleNotFoundError:
    # Python3
    from urllib import request
    from html.parser import HTMLParser

from .resources import ICON_CACHE


class MyHtmlParser(HTMLParser):
    '''
    Parse simple url to extract data and image url.
    This is expecting a simple url containing only one data block and one image url.
    '''
    def __init__(self):
        HTMLParser.__init__(self)
        self.noImgHtml = ''
        self.imageUrl = ''

    def handle_starttag(self, tag, attrs):
        if tag == 'img':
            for attrName, attrValue in attrs:
                if attrName == 'src':
                    self.imageUrl = attrValue
        else:
            if tag == 'a':
                aTag = '<a style="color: #C74F24" %s="%s">' % attrs[0]
                self.noImgHtml += aTag
            else:
                self.noImgHtml += self.get_starttag_text()
  
    def handle_endtag(self, tag):
        if tag != 'img':
            self.noImgHtml += '</%s>' % tag

    def handle_data(self, data):
        self.noImgHtml += data
        self.text = data
        

class HtmlIconLabel(QtWidgets.QWidget):
    '''label widget that displays html text including a remote image'''
    def __init__(self, parent=None):
        super(HtmlIconLabel, self).__init__(parent)
        self.setLayout(QtWidgets.QHBoxLayout())
        self.setupUI()

    def setupUI(self):
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self.imgLabel = QtWidgets.QLabel()
        self.imgLabel.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        self.textLabel = QtWidgets.QLabel()
        self.textLabel.setTextFormat(QtCore.Qt.RichText)
        self.textLabel.setWordWrap(True)
        self.textLabel.setOpenExternalLinks(True)
        self.layout().addSpacing(10)
        self.layout().addWidget(self.imgLabel)
        self.layout().addSpacing(10)
        self.layout().addWidget(self.textLabel)
        self.layout().addSpacing(10)

    def setHtmlText(self, html, baseUrl='http://www.nukepedia.com/'):
        '''extract icon from html, download it and display it along with text contained in html'''
        parser = MyHtmlParser()
        parser.feed(html)
        try:
            # Python2
            req = urllib2.Request(baseUrl + parser.imageUrl, headers={'User-Agent':'Magic Browser'})
            f = urllib2.urlopen(req)
        except NameError:
            # Python3
            req = request.Request(baseUrl + parser.imageUrl, headers={'User-Agent':'Magic Browser'})
            f = request.urlopen(req)        

        imageFile = f.read()
        pixmap = QtGui.QPixmap()
        pixmap.loadFromData(QtCore.QByteArray(imageFile))
        self.pixmap = pixmap
        self.textLabel.setText(parser.noImgHtml)
        self.imgLabel.setPixmap(self.pixmap)
    
class WelcomePage(QtWidgets.QWidget):
    '''Info panel for after successful login'''
    def __init__(self, parent=None):
        super(WelcomePage, self).__init__(parent)
        # WIDGETS
        self.nuBridgeLogo = ICON_CACHE.getPixmap('nuBridge_logo')
        self.imageLabel = QtWidgets.QLabel()
        self.imageLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.imageLabel.setPixmap(self.nuBridgeLogo)
        
        self.updateAlertWidget = QtWidgets.QLabel()
        self.updateAlertWidget.setContentsMargins(20,20,20,20)
        self.updateAlertWidget.setStyleSheet("QLabel { background-color : rgb(199,89,50); color : white; }")
        self.updateAlertWidget.setAlignment(QtCore.Qt.AlignCenter)
        self.updateAlertWidget.setOpenExternalLinks(True)
        self.updateAlertWidget.setVisible(False)

        self.welcomeText = 'Welcome'
        self.toolCountText = 'Currently available tools:'
        self.downloadsCountText = 'downloads:'
        self.infoText = QtWidgets.QLabel(self.welcomeText)
        self.toolCountLabel = QtWidgets.QLabel(self.toolCountText)
        self.toolCountWidget = QtWidgets.QLabel()
        self.downloadsCountLabel = QtWidgets.QLabel(self.downloadsCountText)
        self.downloadsCountWidget = QtWidgets.QLabel()

        self.infoText.setAlignment(QtCore.Qt.AlignCenter)
        self.toolCountLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.toolCountWidget.setAlignment(QtCore.Qt.AlignCenter)
        self.downloadsCountWidget.setAlignment(QtCore.Qt.AlignCenter)
        self.downloadsCountLabel.setAlignment(QtCore.Qt.AlignCenter)
        
        font = QtWidgets.QApplication.font()
        font.setPointSize(30)
        font.setBold(True)
        self.toolCountWidget.setFont(font)
        font.setPointSize(20)
        #font.setBold(False)
        self.downloadsCountWidget.setFont(font)
        self.news = HtmlIconLabel()

        # LAYOUT
        layout = QtWidgets.QVBoxLayout()
        layout.setAlignment(QtCore.Qt.AlignCenter)
        self.setLayout(layout)
        layout.addWidget(self.updateAlertWidget)
        layout.addSpacing(20)
        layout.addWidget(self.infoText)
        layout.addSpacing(20)
        layout.addWidget(self.imageLabel)
        layout.addSpacing(50)
        layout.addWidget(self.toolCountLabel)
        layout.addWidget(self.toolCountWidget)
        layout.addSpacing(10)
        layout.addWidget(self.downloadsCountLabel)
        layout.addWidget(self.downloadsCountWidget)
        layout.addSpacing(100)
        layout.addWidget(self.news)

    def setUserName(self, name):
        self.name = name
        self.infoText.setText(self.welcomeText + ', %s' % name)

    def setToolCount(self, count):
        #self.toolCountWidget.setText(str(count))
        colour = 'a36955'
        self.toolCountWidget.setText('<a style="color: #{}">{:,}</a>'.format(colour, count))
    
    def setDownloadCount(self, count):
        colour = 'a36955'
        self.downloadsCountWidget.setText('<a style="color: #{}">{:,}</a>'.format(colour, count))

    def setNews(self, newsText):
        self.news.setHtmlText('<b>LATEST NEWS:</b>' + newsText)
        if newsText:
            self.news.setVisible(True)
        else:
            self.news.setVisible(False)
    def showUpdateAlert(self, currentVersion, availableVersion):
        platformDict = {'Darwin':'osx64',
                        'Linux':'linux64'}
        self.updateAlertWidget.setText('<b>Update available.</b><br>You are using {0}<br><a href="http://www.nukepedia.com/nuBridgeDownloads/nuBridge_{2}_v{1}.zip">Available: {1}</a>'.format(currentVersion,
                                                                                                                                                                                               availableVersion,
                                                                                                                                                                                               platformDict.get(common.NKPD_PLATFORM, 'win64')))
        self.updateAlertWidget.setVisible(True)

if __name__ == '__main__':
    from FaderWidget import PageFader
    app = QtWidgets.QApplication(sys.argv)
    
    w = WelcomePage()
    w.showUpdateAlert('v1.0.0', 'v1.0.1')
    w.setUserName('frank rueter')
    w.setToolCount(1000)
    w.setDownloadCount(1000000)
    w.setNews('''<img style="margin-right: 15px; vertical-align: top;" src="images/announcements.png" alt="announcements" />here comes <a href="http:/www.google.com">a link to google</a>''')
    #d = QtWidgets.QWidget()

    #fader = PageFader(w, d)
    #ww = QtWidgets.QWidget()
    #btn = QtWidgets.QPushButton('fade')
    #btn.clicked.connect(fader.showViewB)
    #ww.setLayout(QtWidgets.QVBoxLayout())
    #ww.layout().addWidget(btn)
    #ww.layout().addWidget(fader)
    w.show()
    w.raise_()
    sys.exit( app.exec_() )


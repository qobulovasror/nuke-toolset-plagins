import sys
#from PySide import QtCore, QtGui
from Qt import QtCore, QtWidgets, QtGui

class PageIndicator(QtWidgets.QWidget):
    '''simple text label that fades off'''

    def __init__(self, parent=None):
        super(PageIndicator, self).__init__(parent)
        self.color = QtGui.QColor(247, 147, 30, 255)
        self.fontType = 'Helvetica'
        self.fontSize = 15
        self.text = ''
        self.setupTimeline()

    def setText(self, text):
        self.text = text
        self.update()

    def paintEvent(self, event):
        '''Show current page as scroll bar is dragged'''

        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setPen(self.color)
        self.font = QtGui.QFont(self.fontType, self.fontSize, QtGui.QFont.Bold)
        painter.setFont(self.font)
        painter.drawText(self.rect(), QtCore.Qt.AlignCenter, str(self.text))

    def setupTimeline(self):
        '''for fading off page indicator'''
        self.timeLine = QtCore.QTimeLine()
        self.timeLine.valueChanged.connect(self.fadeIndicator)
        self.timeLine.finished.connect(self.hide)
        self.timeLine.setDuration(2500)

    def fadeIndicator(self, value):
        self.color.setAlpha(255-255*value)
        self.repaint()

    def showIndicator(self, page):
        self.setText(page+1)
        self.show()
        if self.timeLine.state() is QtCore.QTimeLine.State.Running:
            self.timeLine.stop()
        self.timeLine.start()


class PageScroller(QtWidgets.QScrollBar):
    '''Scroll widget for tool page'''

    signalPageChanged = QtCore.Signal(int)

    def __init__(self, parent=None):
        super(PageScroller, self).__init__(parent)
        self.pageIndicator = PageIndicator(parent)
        self.currentPage = 0    
        self.pageIndicator.hide()
        self.sliderPressed.connect(self.updateOnClick)
        self.signalPageChanged.connect(self.pageIndicator.showIndicator)
        self.valueChanged.connect(self.updateSlider)

        self.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.granularity = 1
        self.setPageStep(self.granularity)

    def setPageCount(self, pageCount):
        self.setMaximum((pageCount-1) * self.granularity)

    def updateOnClick(self):
        self.updateSlider(None)
        self.signalPageChanged.emit(self.currentPage)

    def updateSlider(self, event):
        newPage = self.sliderPosition()/self.granularity
        if newPage != self.currentPage:
            self.currentPage = newPage
            self.signalPageChanged.emit(self.currentPage)

        opt = QtWidgets.QStyleOptionSlider()
        self.initStyleOption(opt)
        style = self.style()
        #print style
        handle = style.subControlRect(style.CC_ScrollBar, opt,
                                      style.SC_ScrollBarSlider, None)

        sliderWidth = self.maximum() - self.minimum() + self.pageStep()
        offset = handle.center()
        if self.orientation() == QtCore.Qt.Orientation.Horizontal:
            offset.setY(-self.pageIndicator.height())
            offset.setX(offset.x() - handle.width())
        else:
            offset.setY(offset.y() - handle.height())
            offset.setX(-self.pageIndicator.width())           
        #sliderPos = (self.sliderPosition() + self.pageStep()/2.0) / float(sliderWidth) * self.width()
        #indicatorPos = QtCore.QPoint(sliderPos - self.pageIndicator.width()/2, -self.pageIndicator.height())
        #self.pageIndicator.move(self.mapToParent(indicatorPos))
        offset.setX(offset.x() - handle.width()/2)
        self.pageIndicator.move(self.mapToParent(offset))

        self.update()

    def previousPage(self):
        self.setValue(self.value() - self.pageStep())

    def nextPage(self):
        self.setValue(self.value() + self.pageStep())
        
    def firstPage(self):
        self.setValue(0)

    def resizeEvent(self, event):
        super(PageScroller, self).resizeEvent(event)
        self.updateSlider(event)

    def event(self, event):
        if event.type() == QtCore.QEvent.Wheel:
            if event.delta() > 0:
                self.previousPage()
            else:
                self.nextPage()
            return True
        else:
            super(PageScroller, self).event(event)
            return False


if __name__ == '__main__':
    def testSlot(i):
        print("Current index changed:", i)

    app = QtWidgets.QApplication(sys.argv)
    app.setStyle('plastique')
    mainWindow = QtWidgets.QWidget()
    layout = QtWidgets.QVBoxLayout(mainWindow)
    s = PageScroller(mainWindow)
    s.setAcceptDrops
    s.setPageCount(10)
    s.signalPageChanged.connect(testSlot)
    s.show()
    layout.addWidget(s)
    mainWindow.resize(400, 100)
    mainWindow.show()

    sys.exit(app.exec_())

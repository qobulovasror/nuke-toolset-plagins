import sys
#from PySide import QtCore, QtGui
from Qt import QtCore, QtWidgets

class SlidingDocksWidget(QtWidgets.QWidget):
    '''Widget with centre area as well as animated top and bottom docks.'''
    ANIMATION_DURATION = 1000

    def __init__(self, parent=None):
        super(SlidingDocksWidget, self).__init__(parent)
        self.setContentsMargins(0, 0, 0, 0)
        self.top = QtWidgets.QWidget(self)
        self.center = QtWidgets.QWidget(self)
        self.bottom = QtWidgets.QWidget(self)
        self.docksVisible = False
        self.topDockWidgets = []
        self.setMaximumSize(640, 800)

    def setupAnimation(self):
        self.resetGeometry()
        self.topAnimation = QtCore.QPropertyAnimation()
        self.topAnimation.setTargetObject(self.top)
        self.topAnimation.setStartValue(QtCore.QPoint(0, - self.topH))
        self.topAnimation.setEndValue(QtCore.QPoint(0, 0))

        self.bottomAnimation = QtCore.QPropertyAnimation()
        self.bottomAnimation.setTargetObject(self.bottom)
        self.bottomAnimation.setStartValue(QtCore.QPoint(0, self.height()))
        self.bottomAnimation.setEndValue(QtCore.QPoint(0, self.height() - self.bottomH))

        # PRECONFIGURE ANIMATION
        self.parallelAnimationGroup = QtCore.QParallelAnimationGroup()
        for anim in (self.topAnimation, self.bottomAnimation):
            anim.setPropertyName(b"pos")
            anim.setDuration(self.ANIMATION_DURATION)
            anim.setEasingCurve(QtCore.QEasingCurve.OutCubic)
            self.parallelAnimationGroup.addAnimation(anim)

    def resetGeometry(self):
        self.topH = max(self.top.height(), self.top.sizeHint().height())
        self.bottomH = self.bottom.sizeHint().height()
        h = max(self.minimumSizeHint().height(), self.height())
        self.centerH = max(self.minimumSizeHint().height(), self.height()) - self.topH - self.bottomH
        w = max(self.minimumSizeHint().width(), self.width())

        self.center.setGeometry(0, self.topH, w, self.centerH)

        if self.docksVisible:
            self.top.setGeometry(0, 0, w, self.topH)
            self.bottom.setGeometry(0, h - self.bottomH, w, self.bottomH)
        else:
            self.top.setGeometry(0, -self.topH, w, self.topH)
            self.bottom.setGeometry(0, h, w, self.bottomH)

    def setTopWidgets(self, topA, topB):
        '''Add two widgets for the top dock'''
        self.top = topA
        topB.hide()
        self.topDockWidgets = [topA, topB]
        self.resetGeometry()

    def changeTopDock(self, dockIndex):
        '''Hide current top dock and show new one'''
        self.top.hide()
        self.top = self.topDockWidgets[dockIndex]
        self.top.setParent(self)
        # print '\t\tSHOWING', self.top
        self.top.show()
        self.resetGeometry()


    def setCenter(self, center):
        self.center = center
        self.resetGeometry()

    def setBottom(self, bottom):
        self.bottom = bottom
        self.resetGeometry()

    def minimumSizeHint(self):
        w = max(self.top.sizeHint().width(), self.center.sizeHint().width(), self.bottom.sizeHint().width())
        h = self.top.sizeHint().height() + self.center.sizeHint().height() + self.bottom.sizeHint().height()
        return QtCore.QSize(w, h)

    def showDocks(self):
        '''Slides the top and bottom dock into view'''
        if not self.docksVisible:
            self.setupAnimation()
            self.parallelAnimationGroup.setDirection(QtCore.QAbstractAnimation.Forward)
            self.parallelAnimationGroup.start()
            self.docksVisible = True

    def hideDocks(self):
        '''Slides the top and bottom dock out of the view'''
        if self.docksVisible:
            self.setupAnimation()
            self.parallelAnimationGroup.setDirection(QtCore.QAbstractAnimation.Backward)
            self.parallelAnimationGroup.start()
            self.docksVisible = False

    def resizeEvent(self, event):
        self.resetGeometry()

def getDock(parent, large=False):
    d = QtWidgets.QWidget(parent)
    l = QtWidgets.QHBoxLayout(d)
    l.setContentsMargins(0, 0, 0, 0)
    btn1 = QtWidgets.QPushButton('asdf')
    btn2 = QtWidgets.QPushButton('asdf')
    if large:
        btn1.setMinimumHeight(90)
        btn1.setText('large buttons')
        btn2.setMinimumHeight(90)
        btn2.setText('large buttons')
    l.addWidget(btn1)
    l.addWidget(btn2)
    return d

def getTestDockWidget(parent=None):
    def getCenter(dockWidget):
        c = QtWidgets.QWidget(dockWidget)
        l = QtWidgets.QHBoxLayout(c)
        l.setContentsMargins(0, 0, 0, 0)
        btnIn = QtWidgets.QPushButton('in')
        btnOut = QtWidgets.QPushButton('out')
        btnIn.clicked.connect(dockWidget.showDocks)
        btnOut.clicked.connect(dockWidget.hideDocks)
        l.addWidget(btnIn)
        l.addWidget(btnOut)
        return c

    w = SlidingDocksWidget(parent)
    w.setTopWidgets(getDock(w, True), getDock(w))
    w.setBottom(getDock(w))
    w.setCenter(getCenter(w))
    return w


def getTestMainWindow():
    def changeTopDockContent(i):
        w.changeTopDock(i)
    m = QtWidgets.QMainWindow()
    cw = QtWidgets.QWidget(m)
    l = QtWidgets.QVBoxLayout(cw)
    m.setCentralWidget(cw)
    w = getTestDockWidget(m)
    l.addWidget(w)
    btn1 = QtWidgets.QPushButton('Dummy button1')
    btn2 = QtWidgets.QPushButton('Dummy button2')
    btn1.clicked.connect(lambda: changeTopDockContent(0))
    btn2.clicked.connect(lambda: changeTopDockContent(1))
    l.addWidget(btn1)
    l.addWidget(btn2)


    return m


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    # w = getTestDockWidget()
    w = getTestMainWindow()
    w.show()
    sys.exit(app.exec_())

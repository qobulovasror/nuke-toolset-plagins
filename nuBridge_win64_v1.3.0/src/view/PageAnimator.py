import sys
#from PySide import QtCore, QtGui
from Qt import QtCore, QtWidgets

class VerticalAnimator(QtWidgets.QWidget):
    '''A widget where other widgets may slide in or out animated'''

    def __init__(self, duration=700, parent=None):
        
        super(VerticalAnimator, self).__init__(parent)
        self.newWidget = None
        self.visibleWidget = None
        self.end = 0
        self.duration = duration

    def showWidget(self, widget):

        #print '\nshowing widget with', '\n'.join([t.title for t in widget.toolView.currentButtons])
        widget.setGeometry(self.geometry()) #ensure incoming page has correct width
        widget.setParent(self)
        self.newWidget = widget
        if self.visibleWidget is self.newWidget:
            return

        self.animGroup = QtCore.QParallelAnimationGroup()
        slideInAnimation = self.getMoveAnimation(self.newWidget, direction='enter')
        self.animGroup.addAnimation(slideInAnimation)
        if self.visibleWidget:
            slideOutAnimation = self.getMoveAnimation(self.visibleWidget, direction='leave')
            self.animGroup.addAnimation(slideOutAnimation)
            slideOutAnimation.finished.connect(self.visibleWidget.hide)
        self.newWidget.show()
        self.animGroup.start()
        self.visibleWidget = self.newWidget

    def resizeEvent(self, event):
        
        if self.visibleWidget:
            self.visibleWidget.resize(event.size().width(), self.visibleWidget.height())

    def getMoveAnimation(self, widget, direction):
        '''Animation, moves the widget from "start" position to "end" position.'''

        assert direction in ('enter', 'leave')
        if direction == 'enter':
            start = -self.height()
            end = 0

        elif direction == 'leave':
            start = 0
            end = self.height()

        moveAnimation = QtCore.QPropertyAnimation(widget, b"pos")
        moveAnimation.setDuration(self.duration)
        xpos = self.geometry().x()

        moveAnimation.setStartValue(QtCore.QPoint(xpos, start))
        moveAnimation.setEndValue(QtCore.QPoint(xpos, end))
        moveAnimation.setEasingCurve(QtCore.QEasingCurve.OutCubic)
        return moveAnimation


if __name__ == '__main__':
    import WidgetPage
    app = QtWidgets.QApplication(sys.argv)

    # WIDGETS
    toolView1 = WidgetPage.getTestWidgetPage()
    toolView2 = WidgetPage.getTestWidgetPage()
    mainWidget = QtWidgets.QWidget()
    btn1 = QtWidgets.QPushButton('page A')
    btn2 = QtWidgets.QPushButton('page B')

    # LAYOUTS
    mainLayout = QtWidgets.QVBoxLayout(mainWidget)
    animator = VerticalAnimator(duration=1000, parent=mainWidget)

    mainLayout.addWidget(btn1)
    mainLayout.addWidget(btn2)
    mainLayout.addWidget(animator)

    # CONNECT
    def changeToPage(widget):
        animator.showWidget(widget)

    btn1.clicked.connect(lambda: changeToPage(toolView1))
    btn2.clicked.connect(lambda: changeToPage(toolView2))

    # GO
    mainWidget.resize(750, 600)
    mainWidget.show()
    sys.exit(app.exec_())

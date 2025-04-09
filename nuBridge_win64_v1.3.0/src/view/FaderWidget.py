import sys
#from PySide import QtCore, QtGui
from Qt import QtCore, QtWidgets, QtGui
from compat import range

class PageFader(QtWidgets.QStackedWidget):
    '''Cross fade between tool view and html view'''

    def __init__(self, viewA, viewB, duration=1200, parent=None):
        super(PageFader, self).__init__(parent)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self.duration = duration
        self.addWidget(viewA)
        self.addWidget(viewB)
        self.widgets = [viewA, viewB] # keep track of assigned pages to re-parent them on the fly
                                      # this is needed so we can have the same widget (DetailPage)
                                      # be part of multiple PageFaders

    def __reparentWidgets(self):
        '''Re-parent widgets so we can use the same widget instance in multiple PageFaders (DetailPage in our case)'''
        for i in range(self.count()):
            self.removeWidget(self.widget(i))

        for w in self.widgets:
            self.addWidget(w)

    def setCurrentIndex(self, index):

        curWidget = self.currentWidget()
        self.__reparentWidgets()
        self.faderWidget = FaderWidget(curWidget, self.widgets[index], duration=self.duration)
        QtWidgets.QStackedWidget.setCurrentIndex(self, index)

    def showViewA(self):
        self.setCurrentIndex(0)

    def showViewB(self):
        self.setCurrentIndex(1)

    def showViewC(self):
        self.setCurrentIndex(2)
    
    def setViewA(self, widget):
        self.removeWidget(self.widget(0))
        try:
            self.widgets.pop(0)
        except IndexError:
            pass
        self.insertWidget(0, widget)
        self.widgets.insert(0, widget)
    
    def setViewB(self, widget):
        self.removeWidget(self.widget(1))
        try:
            self.widgets.pop(1)
        except IndexError:
            pass
        self.insertWidget(1, widget)
        self.widgets.insert(1, widget)

    def setViewC(self, widget):
        self.removeWidget(self.widget(2))
        try:
            self.widgets.pop(2)
        except IndexError:
            pass
        self.insertWidget(2, widget)
        self.widgets.insert(2, widget)

class FaderWidget(QtWidgets.QWidget):
    '''Cross fade between two widgets'''

    def __init__(self, oldWidget, newWidget, duration=800):
        QtWidgets.QWidget.__init__(self, newWidget)
        self.pixmapOpacity = 1.0
        pixmapSize = newWidget.size().expandedTo(oldWidget.size()) # take the largest of the given sizes
        newWidget.resize(pixmapSize)
        self.oldPixmap = QtGui.QPixmap(newWidget.size())
        oldWidget.render(self.oldPixmap)
        self.timeLine = QtCore.QTimeLine()
        self.timeLine.valueChanged.connect(self.animate)
        self.timeLine.finished.connect(self.close)
        self.timeLine.setDuration(duration)
        self.timeLine.start()
        
        self.resize(newWidget.size())
        self.show()

    def animate(self, value):
        self.pixmapOpacity = 1.0 - value
        self.repaint()

    def paintEvent(self, event):
        painter = QtGui.QPainter()
        painter.begin(self)
        painter.setOpacity(self.pixmapOpacity)
        painter.drawPixmap(0,0, self.oldPixmap)
        painter.end()

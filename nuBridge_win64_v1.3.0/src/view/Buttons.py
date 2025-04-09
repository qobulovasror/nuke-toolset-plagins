#from PySide import QtCore, QtGui
from PySide2 import QtCore, QtWidgets, QtGui

class ToolPushButton(QtWidgets.QPushButton):
    '''
    Normal QtWidgets.QPushButton with "tool" attribute so it can be used as
    sender() in slots (like FancyButton)
    '''
    altClicked = QtCore.Signal()

    def __init__(self, text, tool=None, parent=None):
        super(ToolPushButton, self).__init__(parent)
        self.tool=tool
        self.setText(text)

    def setTool(self, tool):
        self.tool = tool
        
    def mousePressEvent(self, event):
        if QtGui.QGuiApplication.keyboardModifiers() == QtCore.Qt.AltModifier:
            self.altClicked.emit()
            return

        super(ToolPushButton, self).mousePressEvent(event)
        
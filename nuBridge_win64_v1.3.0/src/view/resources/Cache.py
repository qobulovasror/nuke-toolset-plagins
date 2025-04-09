#from PySide import QtCore, QtGui
from Qt import QtCore, QtWidgets, QtGui

# first we need to import the resources, even if we do not
# directly use it, QtCore.Qt will register all resources by doing this
from . import resources
import os

class Cache(object):
    '''
    The cache class is intended to be used as s singleton.
    It holds all resources which are in resources.py.
    The resources are loaded on demand and are reused
    if requested via the getPixmap method.
    '''
    
    def __init__(self):
        '''
        Initializes the icons member with the names of
        the resources tree. Does not load any resource.
        '''
        self.icons = {} # is supposed to hold something like:
                        # {"iconname":[":/resource/path/to/icon.png",
                        #             {'original':QtGui.QPixmap, 'large':QtGui.QPixmap(large)}]}
        self.sizeLookup = {'original':None, 'small':QtCore.QSize(24, 24), 'medium1': QtCore.QSize(30,30), 'large':QtCore.QSize(50, 50)}
        # build icons member with names and filepaths for easy access
        it = QtCore.QDirIterator(':/icons',filter=QtCore.QDir.Files, flags=QtCore.QDirIterator.Subdirectories)
        while it.hasNext():
            it.next()
            info = it.fileInfo()
            if info.isFile():
                self.icons[info.baseName()]=[it.filePath(), {}]


    def getPixmap(self, name, size=None):
        '''
        Returns a resource as a QtGui.QPixmap.
        :param name: name of the resource in the resource filesystem
        size: size of the requested pixmap. current values can be "small", "medium1" or "large"
        '''
        nameConvert = {'colo(u)r':'color',
                       'miscellaneous':'other',
                       'misc':'other',
                       'import/export':'import_export'} # map from incoming name to icon name.
        name = nameConvert.get(name, name)
        try:
            sizeDict = self.icons[name][1]
            try:
                pixmap = sizeDict[size]
                return pixmap
            except KeyError:
                # requested size not available yet
                raise NameError

        except (IndexError, NameError): #do not except for KeyErrors! We only want to 
            #catch IndexErrors, which means we did not yet initialize the
            #QtGui.QPixmap (initial list has only one entry)
            if size:
                icon = QtGui.QIcon(self.icons[name][0])
                pixmap = icon.pixmap(self.sizeLookup[size]) # coudn't find another way to scale a pixmap before rasterising the svg file
            else:
                pixmap = QtGui.QPixmap(self.icons[name][0])
            self.icons[name][1][size] = pixmap # add pixmap to correct size key
            return pixmap
        except KeyError:
            return None
        
    def getIcon(self, name, size='small'):
        return QtGui.QIcon(self.getPixmap(name, size))

        
if __name__ == "__main__":
    import sys
    import os
    app = QtWidgets.QApplication([])
    c = Cache()
    pixmap = c.getPixmap('nuBridge_logo')
    print(pixmap)
    print(pixmap.isNull())
    #print c.getIcon("particles").isNull()
    #print c.getIcon("python").isNull()
    sys.exit(app.exec_())

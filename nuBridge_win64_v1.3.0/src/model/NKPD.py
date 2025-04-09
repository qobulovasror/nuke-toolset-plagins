import os
import sys
import time

from Qt import QtCore, QtGui, QtWidgets
from .NukepediaDB import PLATFORM_KEY
from view.resources import ICON_CACHE
from compat import uni_str, range


OBSOLETE_TOOL_DATA = {'files': [],
                      'category': '',
                      'updateAvailable': False,
                      'containerid': None,
                      'altCount': None,
                      'downloads': None,
                      'licenseagree': 0,
                      'majorVers': '',
                      'minorVers': '',
                      'submitdate': None,
                      'fileauthor': '',
                      'toolType': '',
                      'nukeVersions': None,
                      'filetitle': '',
                      'filetype': '',
                      'id': None,
                      'filedate': None,
                      'smalldesc': ''
                      }

class MissingActiveFileError(Exception):
    pass

class NkpdFavorite(object):
    '''A Nukepedia Favorite object that is a container for tools'''

    def __init__(self, data=None):
        if data:
            self.setData(data)

    def setData(self, data):
        self.favData = data

    @property
    def name(self):
        return self.favData['name']

    @property
    def desc(self):
        return self.favData['description']

    @property
    def id_(self):
        return self.favData['id']

    @property
    def toolProxies(self):
        return self.favData['items']

    @property
    def createDate(self):
        return self.favData['created']

    @name.setter
    def name(self, name):
        self.favData['name'] = name.__str__()

    @desc.setter
    def desc(self, desc):
        self.favData['description'] = desc

    @id_.setter
    def id_(self, id_):
        self.favData['id'] = id_

    @toolProxies.setter
    def tools(self, tools):
        self.favData['items'] = tools

    @createDate.setter
    def createDate(self, date):
        if isinstance(date, time.struct_time):
            self.favData['created'] = date
        elif isinstance(date, str) :
            self.favData['created'] = time.strptime(date, '%Y-%m-%d %H:%M:%S')
        else:
            raise TypeError

    def addTool(self, tool):
        assert isinstance(tool, ToolItemProxy), 'tool must be of type ToolItemProxy - {}'.format(tool)
        self.tools.append(tool)

    def removeTool(self, tool):
        assert isinstance(tool, ToolItemProxy)
        self.tools.remove(tool)
    
    def getOnlineData(self):
        '''
        Return the data that is expected by the class that communicates with the online API.
        Currently this is a list of dictionaries with tool id, file version and file platform string
        '''
        onlineData = []
        for t in self.tools:
            #print t
            try:
                onlineData.append(t.activeFileData)
            except AttributeError:
                # This happens when a favorite is re-saved with a tool that has since been deleted from the database
                dummyData = {'platform': '000000000', 'version': '0.0', 'id': t.id_}
                onlineData.append(dummyData)
        return onlineData
        
class FileItem(QtGui.QStandardItem):
    '''
    Class to represent a file on Nukepedia
    Each ToolItem has at least one file associated with it. Multiple files indicate older versions and/or different
    platform builds.
    '''

    def __init__(self, fileData):
        '''
        attrs are:
        filename, version, platform, osLinux, osOSX, osWindows, osLinux32, osLinux64, osMac32, osMac64, osWin32, osWin64'''
        super(FileItem, self).__init__(fileData['filename'])
        self.fileData = fileData
        for k, v in iter(self.fileData.items()):
            if k == 'platform':
                # set first three bits to 0 to be consistent with website download
                setattr(self, k, '0' * 3 + v[3:])
            else:
                setattr(self, k, v)

    @property
    def targetPlatform(self):
        '''return the target platform for ease of chosing the right icon'''

        pluginPlatformKey = PLATFORM_KEY.split(',')[3:] # first three entires are unused
        pluginPlatformInfo = self.platform[3:]
        searchIndex = pluginPlatformInfo.find('1')
        if searchIndex > 0:
            return pluginPlatformKey[searchIndex]
        else:
            # if platform string is all zeros, the file is source code 
            return 'sourceCode'

    def __eq__(self, other):
        return other.fileData == self.fileData        
   
    def __unicode__(self):
        '''Unicode representation of the this item.'''
        utf8_unicode = self.filename.decode('latin-1').encode('utf-8').decode('utf-8')
        return u'<%s>: %s' % (self.__class__.__name__, utf8_unicode)    

    def __repr__(self):
        '''Readable representation of this item.'''
        data = self.fileData.copy()
        data.update({'targetPlatform':self.targetPlatform})
        return uni_str('FileItem: ' + str(data))

class ToolItem(QtGui.QStandardItem):
    '''Item that stores data for a tool'''

    def __init__(self, container, data):
        super(ToolItem, self).__init__(data['filetitle'])
        self.container = container
        self.toolData = data
        self.title = data['filetitle']
        self.author = data['fileauthor']
        self.category = data['category']
        self.containerid = data['containerid']
        self.downloads = data['downloads']
        self.fileType = data['filetype']
        self.id_ = data['id']
        self.shortDesc = data['smalldesc']

        # TEST DATA WASN'T UPDATED TO INCLUDE THOSE KEYS SO USE GET TO KEEP TESTS WORKING (NEED TO UPDATE TEST DATA ONCE IT'S LOCKED
        self.majorVersion = data.get('majorVers', 0)    
        self.minorVersion = data.get('minorVers', 0)
        self.nukeVersions = data.get('nukeVersions', [0])
        self.toolType = data.get('toolType', None)
        self.fileCount = data.get('altCount', 0)

    def __unicode__(self):
        '''Unicode representation of the this item.'''

        utf8_unicode = self.title.decode('latin-1').encode('utf-8').decode('utf-8')
        return u'<%s>: %s' % (self.__class__.__name__, utf8_unicode)

    def __repr__(self):
        '''Readable representation of this item.'''
        return uni_str('ToolItem: ' + str(self.toolData)).encode('utf-8')

    def __eq__(self, other):
        '''Test two items for equality. Make sure to copmare the active file so we can support the handling of multiple builds for the same tool'''
        return (other.toolData == self.toolData) and (other.activeFile == self.activeFile)

    def getLatestVersions(self):
        '''Return a list of latest versions as file items'''

        # get all available version numbers
        # platformString = 'osLinux,osOSX,osWindows,osLinux32,osLinux64,osMac32,osMac64,osWin32,osWin64'
        latestVersion = sorted(list(set([f.version for f in self.files])))[-1]
        return [f for f in self.files if f.version == latestVersion]

    def data(self, role=QtCore.Qt.UserRole + 1):
        '''
        Return the name for displaying only, otherwise return the entire object.
        '''
        if role == QtCore.Qt.DisplayRole:
            return self.title

        return QtGui.QStandardItem.data(self, role)

    # --------- getters
    @property
    def hasBeenDownloaded(self):
        return self.toolData.get('hasBeenDownloaded', False)

    @property
    def files(self):
        return [FileItem(f) for f in self.toolData['files']]

    @property
    def updateAvailable(self):
        return self.toolData.get('updateAvailable', False)
    
    @property
    def createDate(self):
        return self.toolData['filedate']

    @property
    def modDate(self):
        return self.toolData['submitdate']

    # --------- setters
    @files.setter
    def files(self, fileItemList):
        self.toolData['files'] = [f.fileData for f in fileItemList]

    @hasBeenDownloaded.setter
    def hasBeenDownloaded(self, value):
        self.toolData['hasBeenDownloaded'] = value

    @updateAvailable.setter
    def updateAvailable(self, value):
        self.toolData['updateAvailable'] = value
    
    @createDate.setter
    def createDate(self, date):
        if isinstance(date, time.struct_time):
            self.toolData['createDate'] = date
        elif isinstance(date, str) :
            self.toolData['createDate'] = time.strptime(date, '%Y-%m-%d %H:%M:%S')
        else:
            raise TypeError

    @modDate.setter
    def modDate(self, date):
        if isinstance(date, time.struct_time):
            self.toolData['modDate'] = date
        elif isinstance(date, str) :
            self.toolData['modDate'] = time.strptime(date, '%Y-%m-%d %H:%M:%S')
        else:
            raise TypeError

class ToolItemProxy(ToolItem):
    def __init__(self, toolItem):
        '''
        toolItem is None if the tool was deleted from the database and we need
        a placeholder to represent it in existing favorite lists
        '''
        super(ToolItemProxy, self).__init__(toolItem.container, toolItem.toolData)
        #print 'inside proxy:', toolItem.toolData
        self.sourceTool = toolItem
        self.downloadInfo = {} # info that will get logged in the local database after download
        self.__activeFile = None
        self.__downloadPath = ''
        self.downloadPath = '' # only used for local tools (where they were initially downloaded to)
        self.isActive = False # only used for local tools

    def __unicode__(self):
        '''Unicode representation of the this item.'''
        utf8_unicode = self.title.decode('latin-1').encode('utf-8').decode('utf-8')
        return u'<%s>: %s' % (self.__class__.__name__, utf8_unicode)

    def __repr__(self):
        '''Readable representation of this item.'''
        #return uni_str('ToolItemProxy({}): active file {}'.format(self.title.encode('utf-8'), self.__activeFile))
        return 'ToolItemProxy({}): active file {}'.format(self.title.encode('utf-8'), self.__activeFile)

    def __lt__(self, other):
        '''Make ToolItemProxy sort by it's active file's version'''
        return self.activeFile.version < other.activeFile.version

    @property
    def downloadPath(self):
        return self.__downloadPath

    @property
    def activeFile(self):
        return self.__activeFile
    
    @property
    def version(self):
        return self.activeFile.version

    @activeFile.setter
    def activeFile(self, fileItem):
        self.__activeFile = fileItem
        if fileItem:
            self.downloadInfo['version'] = float(fileItem.version)
            self.downloadInfo['platform'] = fileItem.platform
            self.downloadInfo['filename'] = fileItem.filename
            self.fileName = fileItem.filename
            # Now set the activeFileData so the proxy can be saved to the database properly
            # Be explicit so it's obvious what we need in the DB
            self.setActiveFileData(version=fileItem.version,
                                   platform=fileItem.platform,
                                   id=self.id_)
    @downloadPath.setter
    def downloadPath(self, p):
        self.__downloadPath = p
        self.downloadInfo['downloadPath'] = p

    def setActiveFileData(self, **kwargs):
        '''Set the active file's data to hold the info that will be stored in the database'''

        self.activeFileData = {}
        for k, v in iter(kwargs.items()):
            if k == ' platform':
                # set first three bits to 0 to be consistent with website download
                self.activeFileData[k] = '0' * 3 + v[3:]
            else:
                self.activeFileData[k] = v

    def setActiveFileByData(self, fileData):
        '''
        Set the active file based on the sparse file data returned by the database,
        E.g. {'platform': '000010000', 'version': '1.0', 'id': 1889}
        If the fileData does not match any of the existing files associated with the tool,
        None is returned and self.obsoleteFileData stored the original fileData, so that
        a favorite lists can later be re-saved with missing tools.
        '''

        # Keep track of the data so even deleted files can be re-saved in favorite lists
        # until the user choses to remove them
        self.setActiveFileData(**fileData)
        for f in self.files:
            if f.version == fileData['version'] and f.platform == fileData['platform']:
                self.activeFile = f
                return
        # If we get this far, we have found no match and the fileData must have come from
        # a file that has since been deleted from the database.
        self.activeFile = None
        
    
    def getDownloadData(self):
        '''Combine info from tool item and file item and return a dictionary with the required data for downloading'''
        d = self.toolData.copy()
        d.update(self.downloadInfo)
        return d

class ToolUpdateItemDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self, parent=None):
        '''Delegate to draw pixmap for "update available" property'''

        super(ToolUpdateItemDelegate, self).__init__(parent)
        self.pixmap = ICON_CACHE.getPixmap('updateSimple', 'medium1')
        
    def paint(self, painter, option, index):
        
        if index.column() == 0:
            item = index.model().itemFromIndex(index)

            if item.text() and eval(item.text()):
                painter.save()
                rect = option.rect
                rect.setWidth(rect.height())
                painter.setRenderHint(QtGui.QPainter.Antialiasing) # NOT WORKING? NEED TO SYNC PIXMAP SIZE WITH ROW
                painter.drawPixmap(rect, self.pixmap)
                painter.restore()
        else:
            QtWidgets.QStyledItemDelegate.paint(self, painter, option, index)
        

    def sizeHint(self, option, index):
        if index.column() == 0:
            return self.pixmap.size()
        else:
            return QtWidgets.QStyledItemDelegate.sizeHint(self, option, index)

class ToolModel(QtGui.QStandardItemModel):
    '''Model for all containers and their categories and tools'''

    def __init__(self, parent=None):
        super(ToolModel, self).__init__(parent)
        self.containers = []
        #self.headerLabels = ['', 'title', 'type', 'version']
        
    def setTools(self, dataDict):
        '''Build the model with each tool in dataDict'''

        self.clear()
        self.containers = []

        row = 0
        for container, toolList in iter(dataDict.items()):
            if container.startswith('tcl'):
                # Tcl is no longer included
                continue
            if container == 'miscellaneous':
                container = 'misc'

            updatesAvailableForContainer = 0
            for tool in toolList:
                # instantiate tool item
                toolItem = ToolItem(container, tool)
                if isinstance(QtWidgets.QApplication.instance(), QtWidgets.QApplication):
                    # when Nuke is run in command line mode, make sure to avoid
                    # requests to QPixmaps and other objects that require QtWidgets.QApplication to be running
                    toolItem.setIcon(ICON_CACHE.getIcon('container_' + container))
                    
                # instantiate container item
                #containerItem = QtGui.QStandardItem(container)
                # instantiate update item
                updateItem = QtGui.QStandardItem(str(tool.get('updateAvailable', False)))

                self.setItem(row, 0, updateItem)
                self.setItem(row, 1, toolItem)
                self.setItem(row, 2, QtGui.QStandardItem(container))

                if tool.get('updateAvailable', False):
                    updatesAvailableForContainer += 1 # Count tools in this container that can be updated
                row += 1
                
            self.containers.append({'name':container, 'availableUpdates':updatesAvailableForContainer})
        #self.setHorizontalHeaderLabels(self.headerLabels)

    def getTools(self):
        '''Return a list of all tools in the model'''
        return [self.item(i, 1) for i in range(self.rowCount())]

    def getToolById(self, id_):
        '''Return the tool item with the given id'''
        #try:
            #return [t for t in self.getTools() if t.id_ == id_][0]
        #except IndexError:
            #return []
        return [t for t in self.getTools() if t.id_ == id_][0] # let this throw an IndexError if id can't be found

    def __unicode__(self):
        '''Unicode representation of the tree model, utf-8 decoded.'''
        result = u''
        for tool in self.getTools():
            result += '%s\n' % uni_str(tool)
        return result

    def __repr__(self):
        '''Readable representation of the model.'''
        return uni_str(self).encode('utf-8')

class ToolModelLocal(QtGui.QStandardItemModel):
    '''Model for local database'''

    def __init__(self, parent=None):
        super(ToolModelLocal, self).__init__(parent)
        self.containers = []
        self.headerLabels = ['file id', 'active', 'bake gizmo', 'tool id', 'title', 'type', 'version', 'localPaths']

    def setTools(self, toolProxyList):
        '''Build the model with list of tool proxies which represent the locally installed data'''

        self.clear()
        self.containers = []
        row = 0

        # removing "updateAvailable" attribute for now so we can use the local tool view
        # offline as well (to controll avtive versions for Nuke without having to log into Nukepedia)
        #updatesAvailableForContainer = 0
        for toolItemProxy in toolProxyList:
            isActiveItem = QtGui.QStandardItem()
            isActiveItem.setCheckable(True)
            isActiveItem.setCheckState(QtCore.Qt.Checked if toolItemProxy.isActive else QtCore.Qt.Unchecked)
            isActiveItem.setToolTip('controls which file is loaded in new Nuke sessions')
            
            bakeGizmosItem = QtGui.QStandardItem()
            bakeGizmosItem.setCheckable(True)
            bakeGizmosItem.setCheckState(QtCore.Qt.Checked if toolItemProxy.bakeGizmo else QtCore.Qt.Unchecked)
            bakeGizmosItem.setToolTip('check to automatically convert this gizmo to a group upon creation from the nuBridge menu.\nThis behaviour can be overridden by the global settings in the "Options" tab')
            
            self.setItem(row, 0, QtGui.QStandardItem(str(toolItemProxy.activeFile.id)))
            self.setItem(row, 1, isActiveItem)
            self.setItem(row, 2, bakeGizmosItem)
            self.setItem(row, 3, QtGui.QStandardItem(str(toolItemProxy.id_)))
            self.setItem(row, 4, toolItemProxy) # make sure to update this index in any functions that retrieve the tool item from the model
            self.setItem(row, 5, QtGui.QStandardItem(toolItemProxy.container))
            self.setItem(row, 6, QtGui.QStandardItem(str(toolItemProxy.activeFile.version)))
            self.setItem(row, 7, QtGui.QStandardItem(','.join(toolItemProxy.filePaths)))

            #if toolItemProxy.updateAvailable:
                #updatesAvailableForContainer += 1 # Count tools in this container that can be updated
            row += 1

        self.setHorizontalHeaderLabels(self.headerLabels)

    def getToolItemProxies(self):
        '''Return a list of all tools in the model.'''

        return [self.item(i, 3) for i in range(self.rowCount())]

    #def getToolById(self, id_):
        #'''Return the tool item with the given id'''
        #return [t for t in self.getTools() if t.id_ == id_][0]

    #def getTools(self):
        #'''Return a list of all tools in the model'''

        #return [self.item(i, 1) for i in range(self.rowCount())]

    def disableBakeGizmoItems(self):
        self.toggleBakeItems(True)

    def toggleBakeItems(self, value):
        '''Slot for activating and deactivating the bakeGizmoItem'''

        [self.item(i, 2).setEnabled(not bool(value)) for i in range(self.rowCount())]

    def __unicode__(self):
        '''Unicode representation of the tree model, utf-8 decoded.'''
        result = u''
        for tool in self.getTools():
            result += '%s\n' % uni_str(tool)
        return result

    def __repr__(self):
        '''Readable representation of the model.'''
        return uni_str(self).encode('utf-8')


class ToolProxyModel (QtCore.QSortFilterProxyModel):
    '''Proxy model for filtering and sorting tools.'''

    def __init__(self, parent=None):
        super(ToolProxyModel, self).__init__(parent)
        self.activeContainer = None
        self.activeCategory = None
        self.__searchText = ''
        self.__sortBy = ''
        self.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.setSortCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.setDynamicSortFilter(True)

    def setFilterContainer(self, containerName):
        '''Keep only the container with this name in the model.'''

        #print 'filtering model for container', containerName
        self.activeContainer = containerName
        self.invalidateFilter()
        self.layoutChanged.emit()

    def setFilterCategory(self, categoryName):
        '''Keep only the categories with this name in the model.'''
        self.activeCategory = categoryName
        self.invalidateFilter()
        self.layoutChanged.emit()

    def filterAcceptsRow(self, sourceRow, sourceParent):
        '''Accept only the rows that match the current filter.'''

        tool = self.sourceModel().item(sourceRow, 1)
        if self.activeContainer and not (tool.container == self.activeContainer):
            # filter by container
            return False
        
        if self.activeCategory and not tool.category == self.activeCategory and not tool.hasBeenDownloaded:
            # filter for "downloaded" only
            return False

        if self.activeCategory == 'available updates' and not tool.updateAvailable:
            # filter for "update available" only
            return False

        if self.__searchText:
            # converting unicode to string to avoid errors with special characters.
            # would be nice to find a better way to enable searching of special characters though
            #nameMatch = str(self.__searchText).lower() in tool.title.lower()
            #authorMatch = str(self.__searchText).lower() in tool.author.lower()
            
            nameMatch = self.__searchText.lower() in tool.title.lower()
            authorMatch = self.__searchText.lower() in tool.author.lower()            
            return nameMatch or authorMatch

        return True

    def searchFor(self, text):
        '''Set the string to filter the model later.'''

        #print 'searching for', text
        self.__searchText = text.strip()
        self.invalidateFilter()
        self.layoutChanged.emit()


    def sortBy(self, attr, ascending):
        '''Sort by attr and in ascending order if ascending is True.'''

        #print 'sorting by %s / ascending %s' % (attr, ascending)
        sortOrder = QtCore.Qt.AscendingOrder if ascending else QtCore.Qt.DescendingOrder
        self.__sortBy = attr
        self.invalidate()
        self.sort(1, sortOrder)

    def lessThan(self, left, right):
        '''Compare the current self.__sortBy attribute of left and right.'''

        leftTool = (self.sourceModel().itemFromIndex(left))
        rightTool = (self.sourceModel().itemFromIndex(right))

        leftData = getattr(leftTool, self.__sortBy)
        rightData = getattr(rightTool, self.__sortBy)
        return leftData < rightData


    def getContainer(self):
        '''Return the first ContainerItem matching the filter.'''
        return self.activeContainer

    def getCategories(self):
        '''
        Return the list of CategoryItems for the first
        ContainerItem matching the filter.
        '''
        #return list(set([t.category for t in self.getTools()]))
        return list(set([t.category for t in self.sourceModel().getTools() if t.container == self.activeContainer]))

    def getTools(self):
        '''
        Return the list of ToolItems for the first
        ContainerItem and all categories matching the filter.
        '''
        return [self.sourceModel().itemFromIndex(self.mapToSource(self.index(i, 1))) for i in range(self.rowCount())]

    def __unicode__(self):
        '''Unicode representation of the tree model, utf-8 decoded'''

        result = u''
        for tool in self.getTools():
            result += '%s\n' % uni_str(tool)
        return result

    def __repr__(self):
        '''Readable representation of the model'''
        return uni_str(self).encode('utf-8')



class FileModel(QtGui.QStandardItemModel):
    '''Model for all files available for a given tool'''

    def __init__(self, toolItem, parent=None):
        super(FileModel, self).__init__(parent)
        self.containers = []
        self.toolItem = toolItem
        self.setUp()

    def setUp(self):
        '''Build the model for all files in dataDict'''

        self.clear()
        self.setHorizontalHeaderLabels(['version', 'file name'])

        for row, fileItem in enumerate(self.toolItem.files):
            versionItem = QtGui.QStandardItem(str(fileItem.version))
            versionItem.setTextAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignCenter)

            font = QtWidgets.QApplication.font()
            font.setPointSize(10)
            fileItem.setFont(font)

            self.setItem(row, 0, versionItem)
            self.setItem(row, 1, fileItem)

class FileProxyModel(QtCore.QSortFilterProxyModel):
    '''Proxy to filter for latest versions only'''

    def __init__(self, parent=None):
        super(FileProxyModel, self).__init__(parent)
        self.latestOnly = True
        
    
    def filterAcceptsRow(self, sourceRow, sourceParent):
        toolObject = self.sourceModel().toolItem
        fileObject = self.sourceModel().item(sourceRow, 1)
        if self.latestOnly:
            return fileObject in toolObject.getLatestVersions()
        else:
            return True

    def getItemByIndex(self, index):
        return self.sourceModel().itemFromIndex(self.mapToSource(index))
    